"""DRF serializers for authentication and account management."""

from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError as DjangoValidationError
from rest_framework import serializers

from apps.accounts.validators import validate_username


class SignupSerializer(serializers.Serializer):
    email = serializers.EmailField()
    username = serializers.CharField(min_length=3, max_length=30)
    password = serializers.CharField(write_only=True, min_length=8, max_length=128)
    first_name = serializers.CharField(max_length=150, required=False, allow_blank=True)
    last_name = serializers.CharField(max_length=150, required=False, allow_blank=True)

    def validate_email(self, value: str) -> str:
        return value.strip().lower()

    def validate_username(self, value: str) -> str:
        try:
            return validate_username(value)
        except DjangoValidationError as exc:
            raise serializers.ValidationError(exc.messages) from exc

    def validate_password(self, value: str) -> str:
        try:
            validate_password(value)
        except DjangoValidationError as exc:
            raise serializers.ValidationError(list(exc.messages)) from exc
        return value


class LoginSerializer(serializers.Serializer):
    login = serializers.CharField()
    password = serializers.CharField(write_only=True)


class GoogleAuthSerializer(serializers.Serializer):
    """Accept Google authorization `code` (redirect flow) or legacy ID `token`."""

    code = serializers.CharField(
        write_only=True,
        required=False,
        allow_blank=True,
        max_length=2048,
    )
    token = serializers.CharField(
        write_only=True,
        required=False,
        allow_blank=True,
        min_length=20,
        max_length=4096,
    )

    def validate(self, attrs):
        code = (attrs.get("code") or "").strip()
        token = (attrs.get("token") or "").strip()
        if not code and not token:
            raise serializers.ValidationError(
                {"code": "Google authorization code or ID token is required."}
            )
        attrs["code"] = code or None
        attrs["token"] = token or None
        return attrs


class PhoneSendSerializer(serializers.Serializer):
    phone_number = serializers.CharField(max_length=32)

    def validate_phone_number(self, value: str) -> str:
        from django.core.exceptions import ValidationError as DjangoValidationError

        from apps.accounts.phone import validate_phone_number

        try:
            return validate_phone_number(value)
        except DjangoValidationError as exc:
            raise serializers.ValidationError(exc.messages) from exc


class PhoneVerifySerializer(serializers.Serializer):
    phone_number = serializers.CharField(max_length=32)
    code = serializers.CharField(min_length=6, max_length=6)

    def validate_phone_number(self, value: str) -> str:
        from django.core.exceptions import ValidationError as DjangoValidationError

        from apps.accounts.phone import validate_phone_number

        try:
            return validate_phone_number(value)
        except DjangoValidationError as exc:
            raise serializers.ValidationError(exc.messages) from exc

    def validate_code(self, value: str) -> str:
        code = (value or "").strip()
        if not code.isdigit() or len(code) != 6:
            raise serializers.ValidationError("Enter the 6-digit verification code.")
        return code


class LogoutSerializer(serializers.Serializer):
    refresh = serializers.CharField()


class PasswordResetRequestSerializer(serializers.Serializer):
    email = serializers.EmailField()

    def validate_email(self, value: str) -> str:
        return value.strip().lower()


class PasswordResetConfirmSerializer(serializers.Serializer):
    token = serializers.CharField()
    password = serializers.CharField(write_only=True, min_length=8, max_length=128)

    def validate_password(self, value: str) -> str:
        try:
            validate_password(value)
        except DjangoValidationError as exc:
            raise serializers.ValidationError(list(exc.messages)) from exc
        return value


class AuthUserSerializer(serializers.Serializer):
    id = serializers.UUIDField()
    username = serializers.CharField()
    email = serializers.EmailField()
