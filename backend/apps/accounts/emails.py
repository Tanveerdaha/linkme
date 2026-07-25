"""Transactional email helpers for account flows."""

import logging
from urllib.parse import quote

from django.conf import settings
from django.core.mail import send_mail

from apps.accounts.tokens import make_email_verification_token, make_password_reset_token

logger = logging.getLogger(__name__)


def _frontend_url(path: str) -> str:
    base = getattr(settings, "FRONTEND_URL", "http://localhost:3000").rstrip("/")
    return f"{base}{path}"


def _send_account_email(*, subject: str, message: str, recipient: str, purpose: str) -> None:
    """Send a transactional email and log success/failure without leaking secrets."""
    logger.info(
        "Sending %s email to %s via %s",
        purpose,
        recipient,
        settings.EMAIL_BACKEND.rsplit(".", 1)[-1],
    )
    try:
        sent = send_mail(
            subject=subject,
            message=message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[recipient],
            fail_silently=False,
        )
        logger.info("%s email send result for %s: %s", purpose, recipient, sent)
        if not sent:
            logger.error("%s email was not accepted by the mail backend for %s", purpose, recipient)
    except Exception:
        logger.exception("Failed to send %s email to %s", purpose, recipient)
        raise


def send_verification_email(user) -> None:
    """Send email verification link to a newly registered user."""
    token = make_email_verification_token(user)
    verify_url = _frontend_url(f"/verify-email/{quote(token, safe='')}")
    subject = "Verify your LinkMe account"
    message = (
        f"Hi {user.first_name or user.username},\n\n"
        f"Thanks for joining LinkMe. Please verify your email by opening this link:\n\n"
        f"{verify_url}\n\n"
        f"If you did not create this account, you can ignore this email.\n"
    )
    _send_account_email(
        subject=subject,
        message=message,
        recipient=user.email,
        purpose="verification",
    )


def send_password_reset_email(user) -> None:
    """Send password reset link to the user."""
    token = make_password_reset_token(user)
    reset_url = _frontend_url(f"/reset-password/{quote(token, safe='')}")
    subject = "Reset your LinkMe password"
    message = (
        f"Hi {user.first_name or user.username},\n\n"
        f"We received a request to reset your LinkMe password. "
        f"Open this link to choose a new password:\n\n"
        f"{reset_url}\n\n"
        f"If you did not request a reset, you can ignore this email.\n"
    )
    _send_account_email(
        subject=subject,
        message=message,
        recipient=user.email,
        purpose="password_reset",
    )
