"""URL routes for authentication endpoints."""

from django.urls import path

from apps.accounts.views import (
    GoogleAuthView,
    LoginView,
    LogoutView,
    PasswordResetConfirmView,
    PasswordResetRequestView,
    PhoneSendCodeView,
    PhoneVerifyCodeView,
    SignupView,
    TokenRefreshAPIView,
    VerifyEmailView,
)

app_name = "accounts"

urlpatterns = [
    path("signup/", SignupView.as_view(), name="signup"),
    path(
        "verify-email/<path:token>/",
        VerifyEmailView.as_view(),
        name="verify-email",
    ),
    path("login/", LoginView.as_view(), name="login"),
    path("google/", GoogleAuthView.as_view(), name="google"),
    path("phone/send/", PhoneSendCodeView.as_view(), name="phone-send"),
    path("phone/verify/", PhoneVerifyCodeView.as_view(), name="phone-verify"),
    path("logout/", LogoutView.as_view(), name="logout"),
    path("token/refresh/", TokenRefreshAPIView.as_view(), name="token-refresh"),
    path("password-reset/", PasswordResetRequestView.as_view(), name="password-reset"),
    path(
        "password-reset-confirm/",
        PasswordResetConfirmView.as_view(),
        name="password-reset-confirm",
    ),
]
