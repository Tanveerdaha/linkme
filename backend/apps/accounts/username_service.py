"""Username availability checks (Bloom + PostgreSQL)."""

from __future__ import annotations

from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError

from apps.accounts.bloom import get_username_bloom
from apps.accounts.validators import validate_username
from apps.common.utils.usernames import normalize_username

User = get_user_model()


def check_username_availability(
    raw_username: str,
    *,
    exclude_user_id=None,
) -> dict:
    """
    Check whether a username can be claimed.

    Flow:
      normalize → bloom (maybe) → PostgreSQL (definitive when bloom says maybe)
    """
    normalized = normalize_username(raw_username)

    try:
        username = validate_username(raw_username)
    except ValidationError as exc:
        message = "; ".join(exc.messages) if hasattr(exc, "messages") else str(exc)
        return {
            "username": normalized or (raw_username or "").strip().lower(),
            "available": False,
            "reason": message,
        }

    bloom = get_username_bloom()
    maybe_taken = bloom.username_exists(username)

    if maybe_taken:
        qs = User.objects.filter(username=username)
        if exclude_user_id is not None:
            qs = qs.exclude(pk=exclude_user_id)
        if qs.exists():
            return {
                "username": username,
                "available": False,
                "reason": "Username already exists",
            }

    return {"username": username, "available": True}


def assert_username_available(raw_username: str, *, exclude_user_id=None) -> str:
    """Validate and ensure username is free; return normalized username."""
    result = check_username_availability(raw_username, exclude_user_id=exclude_user_id)
    if not result["available"]:
        from apps.accounts.services import AccountServiceError

        raise AccountServiceError(
            result.get("reason") or "Username already exists",
            code=(
                "duplicate_username"
                if "already exists" in (result.get("reason") or "").lower()
                else "invalid_username"
            ),
        )
    return result["username"]
