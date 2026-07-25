"""Phone OTP storage and verification (Redis-backed)."""

from __future__ import annotations

import hashlib
import hmac
import json
import logging
import secrets
import time

from django.conf import settings
from django.core.cache import cache

from apps.accounts.services import AccountServiceError

logger = logging.getLogger(__name__)

OTP_LENGTH = 6
OTP_TTL_SECONDS = 10 * 60
RESEND_COOLDOWN_SECONDS = 2 * 60
MAX_VERIFY_ATTEMPTS = 5


def _otp_key(phone: str) -> str:
    return f"linkme:phone_otp:{phone}"


def _digest(phone: str, code: str) -> str:
    secret = (settings.SECRET_KEY or "linkme").encode()
    return hmac.new(secret, f"{phone}:{code}".encode(), hashlib.sha256).hexdigest()


def generate_otp_code() -> str:
    return f"{secrets.randbelow(10**OTP_LENGTH):0{OTP_LENGTH}d}"


def store_otp(*, phone: str, code: str) -> None:
    payload = {
        "digest": _digest(phone, code),
        "attempts": 0,
        "created_at": int(time.time()),
    }
    cache.set(_otp_key(phone), json.dumps(payload), timeout=OTP_TTL_SECONDS)


def get_resend_cooldown_remaining(phone: str) -> int:
    raw = cache.get(_otp_key(phone))
    if not raw:
        return 0
    try:
        data = json.loads(raw) if isinstance(raw, str) else raw
        created_at = int(data.get("created_at") or 0)
    except (TypeError, ValueError, json.JSONDecodeError):
        return 0
    elapsed = int(time.time()) - created_at
    remaining = RESEND_COOLDOWN_SECONDS - elapsed
    return max(0, remaining)


def assert_resend_allowed(phone: str) -> None:
    remaining = get_resend_cooldown_remaining(phone)
    if remaining > 0:
        raise AccountServiceError(
            f"Please wait {remaining} seconds before requesting a new code.",
            code="otp_resend_cooldown",
        )


def verify_otp(*, phone: str, code: str) -> None:
    raw = cache.get(_otp_key(phone))
    if not raw:
        raise AccountServiceError(
            "Invalid or expired verification code.",
            code="otp_invalid",
        )
    try:
        data = json.loads(raw) if isinstance(raw, str) else raw
    except (TypeError, ValueError, json.JSONDecodeError) as exc:
        cache.delete(_otp_key(phone))
        raise AccountServiceError(
            "Invalid or expired verification code.",
            code="otp_invalid",
        ) from exc

    attempts = int(data.get("attempts") or 0)
    if attempts >= MAX_VERIFY_ATTEMPTS:
        cache.delete(_otp_key(phone))
        raise AccountServiceError(
            "Too many incorrect attempts. Request a new code.",
            code="otp_locked",
        )

    expected = data.get("digest") or ""
    candidate = _digest(phone, (code or "").strip())
    if not hmac.compare_digest(expected, candidate):
        data["attempts"] = attempts + 1
        cache.set(_otp_key(phone), json.dumps(data), timeout=OTP_TTL_SECONDS)
        raise AccountServiceError(
            "Invalid or expired verification code.",
            code="otp_invalid",
        )

    cache.delete(_otp_key(phone))


def clear_otp(phone: str) -> None:
    cache.delete(_otp_key(phone))
