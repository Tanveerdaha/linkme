"""Signed tokens for email verification and password reset."""

from django.conf import settings
from django.core import signing

EMAIL_VERIFY_SALT = "linkme.email-verify"
PASSWORD_RESET_SALT = "linkme.password-reset"


def _max_age(setting_name: str, default_seconds: int) -> int:
    return int(getattr(settings, setting_name, default_seconds))


def make_email_verification_token(user) -> str:
    """Create a time-limited signed token for email verification."""
    return signing.dumps(
        {"uid": str(user.pk), "email": user.email},
        salt=EMAIL_VERIFY_SALT,
    )


def parse_email_verification_token(token: str) -> dict:
    """
    Validate an email verification token.

    Raises signing.BadSignature / signing.SignatureExpired on failure.
    """
    return signing.loads(
        token,
        salt=EMAIL_VERIFY_SALT,
        max_age=_max_age("EMAIL_VERIFICATION_TOKEN_MAX_AGE", 60 * 60 * 48),
    )


def make_password_reset_token(user) -> str:
    """Create a time-limited signed token for password reset."""
    return signing.dumps(
        {
            "uid": str(user.pk),
            "email": user.email,
            # Bind token to current password hash so it becomes invalid after reset.
            "pwd": user.password,
        },
        salt=PASSWORD_RESET_SALT,
    )


def parse_password_reset_token(token: str) -> dict:
    """
    Validate a password reset token.

    Raises signing.BadSignature / signing.SignatureExpired on failure.
    """
    return signing.loads(
        token,
        salt=PASSWORD_RESET_SALT,
        max_age=_max_age("PASSWORD_RESET_TOKEN_MAX_AGE", 60 * 60),
    )
