"""
Login attempt tracking and suspicious login detection.

Uses Redis cache counters keyed by IP + identifier. Does not persist PII.
"""

from __future__ import annotations

from django.conf import settings
from django.core.cache import cache

from apps.common.logging import log_security_event


def _attempt_key(*, ip: str, identifier: str) -> str:
    return f"login:attempts:{ip}:{identifier.lower()}"


def _lock_key(*, ip: str, identifier: str) -> str:
    return f"login:lock:{ip}:{identifier.lower()}"


def is_login_locked(*, ip: str, identifier: str) -> bool:
    return bool(cache.get(_lock_key(ip=ip, identifier=identifier)))


def record_failed_login(*, ip: str, identifier: str) -> int:
    """Increment failure counter; lock out when threshold exceeded."""
    key = _attempt_key(ip=ip, identifier=identifier)
    window = settings.LOGIN_ATTEMPT_WINDOW_SECONDS
    try:
        count = cache.incr(key)
    except ValueError:
        cache.set(key, 1, timeout=window)
        count = 1

    max_attempts = settings.LOGIN_MAX_ATTEMPTS
    if count >= max_attempts:
        cache.set(
            _lock_key(ip=ip, identifier=identifier),
            True,
            timeout=settings.LOGIN_LOCKOUT_SECONDS,
        )
        log_security_event(
            "login_lockout",
            ip=ip,
            extra={"identifier": identifier[:64], "attempts": count},
        )
    else:
        log_security_event(
            "login_failed",
            ip=ip,
            extra={"identifier": identifier[:64], "attempts": count},
        )
    return count


def clear_login_attempts(*, ip: str, identifier: str) -> None:
    cache.delete_many(
        [
            _attempt_key(ip=ip, identifier=identifier),
            _lock_key(ip=ip, identifier=identifier),
        ]
    )


def detect_suspicious_login(*, user, ip: str, user_agent: str = "") -> bool:
    """
    Flag logins from a new IP when the user already has a remembered IP.

    Stores last-known IP in cache; returns True when IP changed.
    """
    key = f"login:last_ip:{user.id}"
    previous = cache.get(key)
    cache.set(key, ip, timeout=60 * 60 * 24 * 30)
    if previous and previous != ip:
        log_security_event(
            "suspicious_login",
            user_id=str(user.id),
            ip=ip,
            extra={"previous_ip": previous, "user_agent": user_agent[:200]},
        )
        return True
    log_security_event(
        "user_login",
        user_id=str(user.id),
        ip=ip,
        extra={"user_agent": user_agent[:200]},
    )
    return False
