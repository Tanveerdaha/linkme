"""
Redis caching helpers for hot read paths.

Keys:
  profile:{username}              — 30 minutes
  feed:user:{id}                  — 5 minutes (first page payload)
  feed:public                     — 5 minutes (first page payload)
  suggestions:{user_id|anon}      — 10 minutes
  notifications:{user_id}:unread  — 1 minute
"""

from __future__ import annotations

import logging
from typing import Any, Callable

from django.conf import settings
from django.core.cache import cache

logger = logging.getLogger(__name__)


def profile_key(username: str) -> str:
    return f"profile:{username.lower()}"


def feed_user_key(user_id) -> str:
    return f"feed:user:{user_id}"


def feed_public_key() -> str:
    return "feed:public"


def suggestions_key(user_id=None) -> str:
    return f"suggestions:{user_id or 'anon'}"


def notification_count_key(user_id) -> str:
    return f"notifications:{user_id}:unread"


def cache_get(key: str) -> Any | None:
    try:
        return cache.get(key)
    except Exception:
        logger.exception("cache get failed for %s", key)
        return None


def cache_set(key: str, value: Any, ttl: int) -> None:
    try:
        cache.set(key, value, timeout=ttl)
    except Exception:
        logger.exception("cache set failed for %s", key)


def cache_delete(*keys: str) -> None:
    try:
        cache.delete_many([k for k in keys if k])
    except Exception:
        logger.exception("cache delete failed for %s", keys)


def get_or_set(key: str, producer: Callable[[], Any], ttl: int) -> Any:
    """Return cached value or compute, store, and return it."""
    cached = cache_get(key)
    if cached is not None:
        return cached
    value = producer()
    cache_set(key, value, ttl)
    return value


def cache_user_profile(username: str, payload: dict | None = None) -> dict | None:
    """Get or set a serialized public profile payload."""
    key = profile_key(username)
    if payload is not None:
        cache_set(key, payload, settings.CACHE_TTL_PROFILE)
        return payload
    return cache_get(key)


def invalidate_user_profile(username: str) -> None:
    cache_delete(profile_key(username))


def cache_feed(user_id=None, payload: dict | None = None) -> dict | None:
    """Cache first-page feed payload for a user (or public feed when user_id is None)."""
    key = feed_user_key(user_id) if user_id is not None else feed_public_key()
    if payload is not None:
        cache_set(key, payload, settings.CACHE_TTL_FEED)
        return payload
    return cache_get(key)


def invalidate_feed(user_id=None) -> None:
    """Invalidate personal feed and the public feed (new posts affect both)."""
    keys = [feed_public_key()]
    if user_id is not None:
        keys.append(feed_user_key(user_id))
    cache_delete(*keys)


def invalidate_all_feeds_for_author(author_id) -> None:
    """
    On new post: drop author's feed + public feed.

    Per-follower fan-out invalidation is deferred; TTL covers stale windows.
    """
    cache_delete(feed_public_key(), feed_user_key(author_id))


def cache_suggestions(user_id=None, payload: list | None = None) -> list | None:
    key = suggestions_key(user_id)
    if payload is not None:
        cache_set(key, payload, settings.CACHE_TTL_SUGGESTIONS)
        return payload
    return cache_get(key)


def invalidate_suggestions(user_id=None) -> None:
    cache_delete(suggestions_key(user_id), suggestions_key(None))


def cache_notification_count(user_id, count: int | None = None) -> int | None:
    key = notification_count_key(user_id)
    if count is not None:
        cache_set(key, count, settings.CACHE_TTL_NOTIFICATION_COUNT)
        return count
    cached = cache_get(key)
    return int(cached) if cached is not None else None


def invalidate_notification_count(user_id) -> None:
    cache_delete(notification_count_key(user_id))


def bump_notification_count(user_id, delta: int = 1) -> None:
    """Best-effort in-place increment; falls back to invalidation."""
    key = notification_count_key(user_id)
    try:
        current = cache.get(key)
        if current is None:
            return
        cache.set(
            key,
            max(0, int(current) + delta),
            timeout=settings.CACHE_TTL_NOTIFICATION_COUNT,
        )
    except Exception:
        invalidate_notification_count(user_id)
