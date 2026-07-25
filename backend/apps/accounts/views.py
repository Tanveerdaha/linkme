"""API views for authentication and account management."""

from drf_spectacular.utils import extend_schema
from rest_framework import status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.throttling import ScopedRateThrottle
from rest_framework.views import APIView
from rest_framework_simplejwt.views import TokenRefreshView

from apps.accounts import services
from apps.accounts.serializers import (
    GoogleAuthSerializer,
    LoginSerializer,
    LogoutSerializer,
    PasswordResetConfirmSerializer,
    PasswordResetRequestSerializer,
    PhoneSendSerializer,
    PhoneVerifySerializer,
    SignupSerializer,
)


class SignupView(APIView):
    permission_classes = [AllowAny]
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = "auth_signup"

    @extend_schema(
        request=SignupSerializer,
        responses={201: dict},
        tags=["auth"],
        summary="Register a new account",
    )
    def post(self, request):
        serializer = SignupSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            user = services.register_user(**serializer.validated_data)
        except services.AccountServiceError as exc:
            return Response(
                {"detail": exc.message, "code": exc.code},
                status=status.HTTP_400_BAD_REQUEST,
            )
        return Response(
            {
                "message": "Account created. Please verify your email.",
                "email": user.email,
            },
            status=status.HTTP_201_CREATED,
        )


class VerifyEmailView(APIView):
    permission_classes = [AllowAny]
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = "auth_signup"

    @extend_schema(
        responses={200: dict},
        tags=["auth"],
        summary="Verify email address",
    )
    def get(self, request, token: str):
        try:
            user = services.verify_email(token)
        except services.AccountServiceError as exc:
            return Response(
                {"detail": exc.message, "code": exc.code},
                status=status.HTTP_400_BAD_REQUEST,
            )
        return Response(
            {
                "message": "Email verified successfully. You can now log in.",
                "email": user.email,
            }
        )


class LoginView(APIView):
    permission_classes = [AllowAny]
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = "auth_login"

    @extend_schema(
        request=LoginSerializer,
        responses={200: dict},
        tags=["auth"],
        summary="Log in with email or username",
    )
    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        identifier = serializer.validated_data.get("login", "")
        ip = (
            (request.META.get("HTTP_X_FORWARDED_FOR") or "").split(",")[0].strip()
            or request.META.get("REMOTE_ADDR", "")
        )
        user_agent = request.META.get("HTTP_USER_AGENT", "")

        from apps.accounts.security.login_protection import (
            clear_login_attempts,
            detect_suspicious_login,
            is_login_locked,
            record_failed_login,
        )

        if is_login_locked(ip=ip, identifier=identifier):
            return Response(
                {
                    "detail": "Too many failed login attempts. Try again later.",
                    "code": "locked",
                },
                status=status.HTTP_429_TOO_MANY_REQUESTS,
            )

        try:
            user = services.authenticate_user(**serializer.validated_data)
        except services.AccountServiceError as exc:
            if exc.code == "invalid_credentials":
                record_failed_login(ip=ip, identifier=identifier)
            status_code = status.HTTP_401_UNAUTHORIZED
            if exc.code in {"unverified", "disabled", "suspended", "deleted"}:
                status_code = status.HTTP_403_FORBIDDEN
            return Response(
                {"detail": exc.message, "code": exc.code},
                status=status_code,
            )

        clear_login_attempts(ip=ip, identifier=identifier)
        detect_suspicious_login(user=user, ip=ip, user_agent=user_agent)
        return Response(services.issue_tokens(user))


class GoogleAuthView(APIView):
    permission_classes = [AllowAny]
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = "auth_google"

    @extend_schema(
        request=GoogleAuthSerializer,
        responses={200: dict},
        tags=["auth"],
        summary="Log in or sign up with a Google ID token",
    )
    def post(self, request):
        serializer = GoogleAuthSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            user = services.authenticate_or_create_google_user(
                code=serializer.validated_data.get("code"),
                token=serializer.validated_data.get("token"),
            )
        except services.AccountServiceError as exc:
            status_code = status.HTTP_401_UNAUTHORIZED
            if exc.code == "google_not_configured":
                status_code = status.HTTP_503_SERVICE_UNAVAILABLE
            elif exc.code in {"suspended", "deleted"}:
                status_code = status.HTTP_403_FORBIDDEN
            return Response(
                {"detail": exc.message, "code": exc.code},
                status=status_code,
            )
        return Response(services.issue_tokens(user))


class PhoneSendCodeView(APIView):
    permission_classes = [AllowAny]
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = "auth_phone_send"

    @extend_schema(
        request=PhoneSendSerializer,
        responses={200: dict},
        tags=["auth"],
        summary="Send WhatsApp phone verification code",
    )
    def post(self, request):
        serializer = PhoneSendSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            result = services.request_phone_otp(
                phone_number=serializer.validated_data["phone_number"],
            )
        except services.AccountServiceError as exc:
            status_code = status.HTTP_400_BAD_REQUEST
            if exc.code == "whatsapp_not_configured":
                status_code = status.HTTP_503_SERVICE_UNAVAILABLE
            elif exc.code == "otp_resend_cooldown":
                status_code = status.HTTP_429_TOO_MANY_REQUESTS
            return Response(
                {"detail": exc.message, "code": exc.code},
                status=status_code,
            )
        return Response(result)


class PhoneVerifyCodeView(APIView):
    permission_classes = [AllowAny]
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = "auth_phone_verify"

    @extend_schema(
        request=PhoneVerifySerializer,
        responses={200: dict},
        tags=["auth"],
        summary="Verify WhatsApp phone code and log in",
    )
    def post(self, request):
        serializer = PhoneVerifySerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            user = services.verify_phone_otp(
                phone_number=serializer.validated_data["phone_number"],
                code=serializer.validated_data["code"],
            )
        except services.AccountServiceError as exc:
            status_code = status.HTTP_400_BAD_REQUEST
            if exc.code in {"suspended", "deleted"}:
                status_code = status.HTTP_403_FORBIDDEN
            elif exc.code in {"otp_invalid", "otp_locked"}:
                status_code = status.HTTP_401_UNAUTHORIZED
            return Response(
                {"detail": exc.message, "code": exc.code},
                status=status_code,
            )
        return Response(services.issue_tokens(user))


class LogoutView(APIView):
    permission_classes = [IsAuthenticated]
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = "auth_login"

    @extend_schema(
        request=LogoutSerializer,
        responses={205: None},
        tags=["auth"],
        summary="Log out and blacklist refresh token",
    )
    def post(self, request):
        serializer = LogoutSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            services.blacklist_refresh_token(
                serializer.validated_data["refresh"],
                user=request.user,
            )
        except services.AccountServiceError as exc:
            return Response(
                {"detail": exc.message, "code": exc.code},
                status=status.HTTP_400_BAD_REQUEST,
            )
        return Response(status=status.HTTP_205_RESET_CONTENT)


class PasswordResetRequestView(APIView):
    permission_classes = [AllowAny]
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = "auth_password_reset"

    @extend_schema(
        request=PasswordResetRequestSerializer,
        responses={200: dict},
        tags=["auth"],
        summary="Request a password reset email",
    )
    def post(self, request):
        serializer = PasswordResetRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        services.request_password_reset(email=serializer.validated_data["email"])
        return Response(
            {
                "message": (
                    "If an account exists for that email, "
                    "a password reset link has been sent."
                )
            }
        )


class PasswordResetConfirmView(APIView):
    permission_classes = [AllowAny]
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = "auth_password_reset"

    @extend_schema(
        request=PasswordResetConfirmSerializer,
        responses={200: dict},
        tags=["auth"],
        summary="Confirm password reset with token",
    )
    def post(self, request):
        serializer = PasswordResetConfirmSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            services.confirm_password_reset(
                token=serializer.validated_data["token"],
                new_password=serializer.validated_data["password"],
            )
        except services.AccountServiceError as exc:
            return Response(
                {"detail": exc.message, "code": exc.code},
                status=status.HTTP_400_BAD_REQUEST,
            )
        return Response({"message": "Password has been reset successfully."})


class TokenRefreshAPIView(TokenRefreshView):
    """Thin wrapper so Swagger tags the refresh endpoint under auth."""

    throttle_classes = [ScopedRateThrottle]
    throttle_scope = "auth_login"

    @extend_schema(tags=["auth"], summary="Refresh access token")
    def post(self, request, *args, **kwargs):
        return super().post(request, *args, **kwargs)
