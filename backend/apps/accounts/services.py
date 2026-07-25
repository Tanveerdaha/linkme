"""Domain services for account registration, auth, and password flows."""

from __future__ import annotations

import logging
import secrets
from urllib.error import URLError
from urllib.request import Request, urlopen

from django.contrib.auth import get_user_model
from django.core import signing
from django.core.files.base import ContentFile
from django.db import IntegrityError, transaction
from django.db.models import Q
from rest_framework_simplejwt.tokens import RefreshToken

from apps.accounts.bloom import get_username_bloom
from apps.accounts.emails import send_password_reset_email, send_verification_email
from apps.accounts.tokens import (
    parse_email_verification_token,
    parse_password_reset_token,
)
from apps.accounts.username_service import assert_username_available
from apps.accounts.validators import (
    RESERVED_USERNAMES,
    USERNAME_MAX_LENGTH,
    USERNAME_MIN_LENGTH,
)
from apps.common.utils.usernames import normalize_username

User = get_user_model()
logger = logging.getLogger(__name__)


class AccountServiceError(Exception):
    """Base error for account service operations."""

    def __init__(self, message: str, code: str = "error"):
        self.message = message
        self.code = code
        super().__init__(message)


@transaction.atomic
def register_user(
    *,
    email: str,
    username: str,
    password: str,
    first_name: str = "",
    last_name: str = "",
) -> User:
    """Create an inactive user and send a verification email."""
    email = email.strip().lower()
    username = assert_username_available(username)

    if User.objects.filter(email__iexact=email).exists():
        raise AccountServiceError(
            "A user with this email already exists.",
            code="duplicate_email",
        )

    try:
        user = User.objects.create_user(
            email=email,
            username=username,
            password=password,
            first_name=first_name.strip(),
            last_name=last_name.strip(),
            is_active=False,
            is_verified=False,
            auth_provider=User.AuthProvider.EMAIL,
        )
    except IntegrityError as exc:
        raise AccountServiceError(
            "A user with this username already exists.",
            code="duplicate_username",
        ) from exc

    get_username_bloom().add_username(username)
    send_verification_email(user)
    return user


def generate_username_from_email(email: str) -> str:
    """
    Build a unique LinkMe username from an email local-part.

    Example: azeem@gmail.com → azeem12345
    """
    local = normalize_username(email.split("@", 1)[0]) or "user"
    return _allocate_username(local)


def generate_username_from_phone(phone: str) -> str:
    """Build a unique username from phone digits (e.g. u3092670648)."""
    digits = "".join(ch for ch in phone if ch.isdigit())
    base = normalize_username(f"u{digits[-8:]}") or "user"
    return _allocate_username(base)


def _allocate_username(local: str) -> str:
    if local in RESERVED_USERNAMES:
        local = f"u{local}"

    max_base = max(USERNAME_MIN_LENGTH, USERNAME_MAX_LENGTH - 5)
    base = local[:max_base]
    if len(base) < USERNAME_MIN_LENGTH:
        base = (base + "user")[:USERNAME_MIN_LENGTH]

    for _ in range(40):
        suffix = f"{secrets.randbelow(100_000):05d}"
        candidate = f"{base}{suffix}"[:USERNAME_MAX_LENGTH]
        try:
            return assert_username_available(candidate)
        except AccountServiceError:
            continue

    fallback = f"user{secrets.token_hex(4)}"[:USERNAME_MAX_LENGTH]
    return assert_username_available(fallback)


def _ensure_account_allowed(user: User) -> None:
    if getattr(user, "is_deleted", False):
        raise AccountServiceError(
            "This account has been deleted.",
            code="deleted",
        )
    if hasattr(user, "is_currently_suspended") and user.is_currently_suspended():
        raise AccountServiceError(
            "This account is suspended.",
            code="suspended",
        )


def _maybe_set_profile_avatar(user: User, picture_url: str) -> None:
    """Best-effort download of Google profile picture into Profile.avatar."""
    if not picture_url:
        return
    try:
        profile = getattr(user, "profile", None)
        if profile is None:
            return
        if profile.avatar:
            return
        request = Request(
            picture_url,
            headers={"User-Agent": "LinkMe/1.0"},
        )
        with urlopen(request, timeout=8) as response:  # noqa: S310 — Google CDN URL
            content_type = (response.headers.get("Content-Type") or "").lower()
            data = response.read(2_000_000)
        if not data:
            return
        ext = "jpg"
        if "png" in content_type:
            ext = "png"
        elif "webp" in content_type:
            ext = "webp"
        profile.avatar.save(
            f"google.{ext}",
            ContentFile(data),
            save=True,
        )
    except (URLError, OSError, ValueError) as exc:
        logger.info("Skipped Google avatar for %s: %s", user.email, exc)


@transaction.atomic
def authenticate_or_create_google_user(
    *,
    code: str | None = None,
    token: str | None = None,
) -> User:
    """
    Authenticate via Google authorization code (preferred) or ID token.

    Frontend redirects to Google, receives `code` on callback, then POSTs it
    here. Backend exchanges the code (using client secret) and verifies identity.
    """
    from apps.accounts.google import exchange_authorization_code, verify_google_id_token

    if code:
        identity = exchange_authorization_code(code)
    elif token:
        identity = verify_google_id_token(token)
    else:
        raise AccountServiceError(
            "Unable to continue with Google. Please try again.",
            code="invalid_google_token",
        )

    user = User.objects.filter(google_id=identity.google_id).first()
    if user is None:
        user = User.objects.filter(email__iexact=identity.email).first()

    if user is not None:
        _ensure_account_allowed(user)

        updates: list[str] = []
        if not user.google_id:
            if (
                User.objects.filter(google_id=identity.google_id)
                .exclude(pk=user.pk)
                .exists()
            ):
                raise AccountServiceError(
                    "Unable to continue with Google. Please try again.",
                    code="google_account_conflict",
                )
            user.google_id = identity.google_id
            updates.append("google_id")

        if not user.is_verified:
            user.is_verified = True
            updates.append("is_verified")
        if not user.is_active:
            user.is_active = True
            updates.append("is_active")

        if identity.first_name and not user.first_name:
            user.first_name = identity.first_name
            updates.append("first_name")
        if identity.last_name and not user.last_name:
            user.last_name = identity.last_name
            updates.append("last_name")

        if updates:
            updates.append("updated_at")
            user.save(update_fields=updates)

        _maybe_set_profile_avatar(user, identity.picture)
        return user

    username = generate_username_from_email(identity.email)
    first_name = identity.first_name
    last_name = identity.last_name
    if not first_name and identity.full_name:
        parts = identity.full_name.split(None, 1)
        first_name = parts[0][:150]
        last_name = (parts[1] if len(parts) > 1 else "")[:150]

    try:
        user = User.objects.create_user(
            email=identity.email,
            username=username,
            password=None,
            first_name=first_name,
            last_name=last_name,
            is_active=True,
            is_verified=True,
            google_id=identity.google_id,
            auth_provider=User.AuthProvider.GOOGLE,
        )
    except IntegrityError as exc:
        raise AccountServiceError(
            "Unable to continue with Google. Please try again.",
            code="google_account_conflict",
        ) from exc

    get_username_bloom().add_username(username)
    _maybe_set_profile_avatar(user, identity.picture)
    return user


def request_phone_otp(*, phone_number: str) -> dict:
    """
    Validate phone, generate a 6-digit OTP, send via WhatsApp, and store hash.
    """
    from apps.accounts.phone import validate_phone_number
    from apps.accounts.phone_otp import (
        RESEND_COOLDOWN_SECONDS,
        assert_resend_allowed,
        generate_otp_code,
        get_resend_cooldown_remaining,
        store_otp,
    )
    from apps.accounts.whatsapp import send_whatsapp_message
    from django.core.exceptions import ValidationError as DjangoValidationError

    try:
        phone = validate_phone_number(phone_number)
    except DjangoValidationError as exc:
        message = "; ".join(exc.messages) if hasattr(exc, "messages") else str(exc)
        raise AccountServiceError(message, code="invalid_phone") from exc

    remaining = get_resend_cooldown_remaining(phone)
    if remaining > 0:
        raise AccountServiceError(
            f"Please wait {remaining} seconds before requesting a new code.",
            code="otp_resend_cooldown",
        )

    # assert_resend_allowed is redundant if we checked remaining, keep for clarity
    assert_resend_allowed(phone)

    code = generate_otp_code()
    message = (
        "*LinkMe*\n\n"
        f"Your verification code is: *{code}*\n\n"
        "This code expires in 10 minutes. Do not share it with anyone."
    )
    send_whatsapp_message(phone_number=phone, message=message)
    store_otp(phone=phone, code=code)

    return {
        "phone_number": phone,
        "message": "Verification code sent via WhatsApp.",
        "resend_available_in": RESEND_COOLDOWN_SECONDS,
        "expires_in": 600,
    }


@transaction.atomic
def verify_phone_otp(*, phone_number: str, code: str) -> User:
    """Verify OTP and login or create a phone-authenticated LinkMe user."""
    from apps.accounts.phone import validate_phone_number
    from apps.accounts.phone_otp import verify_otp
    from django.core.exceptions import ValidationError as DjangoValidationError

    try:
        phone = validate_phone_number(phone_number)
    except DjangoValidationError as exc:
        message = "; ".join(exc.messages) if hasattr(exc, "messages") else str(exc)
        raise AccountServiceError(message, code="invalid_phone") from exc

    verify_otp(phone=phone, code=(code or "").strip())

    user = User.objects.filter(phone_number=phone).first()
    if user is not None:
        _ensure_account_allowed(user)
        updates: list[str] = []
        if not user.is_verified:
            user.is_verified = True
            updates.append("is_verified")
        if not user.is_active:
            user.is_active = True
            updates.append("is_active")
        if updates:
            updates.append("updated_at")
            user.save(update_fields=updates)
        return user

    username = generate_username_from_phone(phone)
    try:
        user = User.objects.create_user(
            email=None,
            username=username,
            password=None,
            phone_number=phone,
            is_active=True,
            is_verified=True,
            auth_provider=User.AuthProvider.PHONE,
        )
    except IntegrityError as exc:
        raise AccountServiceError(
            "Unable to create account for this phone number.",
            code="phone_account_conflict",
        ) from exc

    get_username_bloom().add_username(username)
    return user


@transaction.atomic
def verify_email(token: str) -> User:
    """Activate a user account from a verification token."""
    try:
        payload = parse_email_verification_token(token)
    except signing.SignatureExpired as exc:
        raise AccountServiceError(
            "Verification link has expired.",
            code="token_expired",
        ) from exc
    except signing.BadSignature as exc:
        raise AccountServiceError(
            "Invalid verification link.",
            code="token_invalid",
        ) from exc

    try:
        user = User.objects.get(pk=payload["uid"], email=payload["email"])
    except User.DoesNotExist as exc:
        raise AccountServiceError(
            "Invalid verification link.",
            code="token_invalid",
        ) from exc

    if user.is_verified and user.is_active:
        return user

    user.is_verified = True
    user.is_active = True
    user.save(update_fields=["is_verified", "is_active", "updated_at"])
    return user


def authenticate_user(*, login: str, password: str) -> User:
    """
    Authenticate by email or username.

    Rejects invalid credentials, unverified users, and disabled accounts.
    """
    identifier = login.strip()
    if not identifier:
        raise AccountServiceError("Invalid credentials.", code="invalid_credentials")

    query = Q(email__iexact=identifier) | Q(username__iexact=identifier.lower())
    user = User.objects.filter(query).first()

    if user is None or not user.check_password(password):
        raise AccountServiceError("Invalid credentials.", code="invalid_credentials")

    if not user.is_verified:
        raise AccountServiceError(
            "Please verify your email before logging in.",
            code="unverified",
        )

    if getattr(user, "is_deleted", False):
        raise AccountServiceError(
            "This account has been deleted.",
            code="deleted",
        )

    if hasattr(user, "is_currently_suspended") and user.is_currently_suspended():
        raise AccountServiceError(
            "This account is suspended.",
            code="suspended",
        )

    if not user.is_active:
        raise AccountServiceError(
            "This account has been disabled.",
            code="disabled",
        )

    return user


def issue_tokens(user: User) -> dict:
    """Return access and refresh JWT pair plus a compact user payload."""
    from apps.moderation.audit import log_audit
    from apps.moderation.models import AuditLog

    refresh = RefreshToken.for_user(user)
    log_audit(
        user=user,
        action=AuditLog.Action.LOGIN,
        object_type="user",
        object_id=str(user.id),
    )
    return {
        "access": str(refresh.access_token),
        "refresh": str(refresh),
        "user": {
            "id": str(user.id),
            "username": user.username,
            "email": user.email or "",
            "phone_number": getattr(user, "phone_number", None) or "",
            "is_staff": bool(user.is_staff),
        },
    }


def blacklist_refresh_token(refresh_token: str, *, user=None) -> None:
    """Blacklist a refresh token (logout)."""
    try:
        token = RefreshToken(refresh_token)
        token.blacklist()
        if user is not None:
            from apps.moderation.audit import log_audit
            from apps.moderation.models import AuditLog

            log_audit(
                user=user,
                action=AuditLog.Action.LOGOUT,
                object_type="user",
                object_id=str(user.id),
            )
    except Exception as exc:  # noqa: BLE001 — surface as service error
        raise AccountServiceError(
            "Invalid or expired refresh token.",
            code="token_invalid",
        ) from exc


def request_password_reset(*, email: str) -> None:
    """
    Send a password reset email when the account exists.

    Always succeeds from the caller's perspective to avoid account enumeration.
    """
    email = email.strip().lower()
    user = User.objects.filter(email__iexact=email, is_active=True).first()
    if user is None:
        return
    send_password_reset_email(user)


@transaction.atomic
def confirm_password_reset(*, token: str, new_password: str) -> User:
    """Validate reset token and set a new password."""
    try:
        payload = parse_password_reset_token(token)
    except signing.SignatureExpired as exc:
        raise AccountServiceError(
            "Password reset link has expired.",
            code="token_expired",
        ) from exc
    except signing.BadSignature as exc:
        raise AccountServiceError(
            "Invalid password reset link.",
            code="token_invalid",
        ) from exc

    try:
        user = User.objects.get(pk=payload["uid"], email=payload["email"])
    except User.DoesNotExist as exc:
        raise AccountServiceError(
            "Invalid password reset link.",
            code="token_invalid",
        ) from exc

    if payload.get("pwd") != user.password:
        raise AccountServiceError(
            "Invalid password reset link.",
            code="token_invalid",
        )

    user.set_password(new_password)
    user.save(update_fields=["password", "updated_at"])
    from apps.moderation.audit import log_audit
    from apps.moderation.models import AuditLog

    log_audit(
        user=user,
        action=AuditLog.Action.PASSWORD_CHANGE,
        object_type="user",
        object_id=str(user.id),
    )
    return user
