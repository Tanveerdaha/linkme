"""
Redis Bloom Filter for fast username existence checks.

PostgreSQL UNIQUE remains the source of truth. The bloom filter is a
read-path optimization: false positives are OK; false negatives are not.
When Bloom is disabled or RedisBloom is unavailable, ``username_exists``
returns True so callers always fall back to the database.
"""

from __future__ import annotations

import logging
from typing import Iterable
from urllib.parse import urlparse

import redis
from django.conf import settings
from django.contrib.auth import get_user_model

logger = logging.getLogger(__name__)


class UsernameBloomFilter:
    FILTER_NAME = "linkme:usernames"
    ERROR_RATE = 0.01
    CAPACITY = 1_000_000

    def __init__(self, client: redis.Redis | None = None):
        self._client = client
        self._ensured = False

    @property
    def enabled(self) -> bool:
        return bool(getattr(settings, "REDIS_BLOOM_ENABLED", True))

    def _get_client(self) -> redis.Redis | None:
        if not self.enabled:
            return None
        if self._client is not None:
            return self._client
        try:
            self._client = _build_redis_client()
            return self._client
        except Exception:
            logger.exception("Unable to connect Redis for username bloom filter")
            return None

    def _ensure_filter(self, client: redis.Redis) -> bool:
        if self._ensured:
            return True
        try:
            # BF.RESERVE returns error if the key already exists — ignore that.
            client.execute_command(
                "BF.RESERVE",
                self.FILTER_NAME,
                self.ERROR_RATE,
                self.CAPACITY,
            )
        except redis.ResponseError as exc:
            message = str(exc).lower()
            if "item exists" in message or "exists" in message:
                pass
            elif "unknown command" in message or "bloom" in message:
                logger.warning(
                    "RedisBloom module unavailable; username checks will use DB only"
                )
                return False
            else:
                logger.warning("BF.RESERVE failed: %s", exc)
                return False
        except Exception:
            logger.exception("BF.RESERVE failed")
            return False
        self._ensured = True
        return True

    def add_username(self, username: str) -> bool:
        """Add a normalized username to the bloom filter."""
        if not username:
            return False
        client = self._get_client()
        if client is None:
            return False
        if not self._ensure_filter(client):
            return False
        try:
            client.execute_command("BF.ADD", self.FILTER_NAME, username)
            return True
        except Exception:
            logger.exception("BF.ADD failed for username=%s", username)
            return False

    def username_exists(self, username: str) -> bool:
        """
        Return whether the username *might* exist.

        True  → possible match → caller must check PostgreSQL.
        False → definite miss → username is available (no false negatives).
        """
        if not username:
            return False
        client = self._get_client()
        if client is None:
            # Safe fallback: force DB check.
            return True
        if not self._ensure_filter(client):
            return True
        try:
            result = client.execute_command("BF.EXISTS", self.FILTER_NAME, username)
            return bool(result)
        except Exception:
            logger.exception("BF.EXISTS failed for username=%s", username)
            return True

    def rebuild(self, usernames: Iterable[str] | None = None) -> int:
        """
        Drop and recreate the filter, then load usernames.

        Returns the number of usernames added.
        """
        client = self._get_client()
        if client is None:
            raise RuntimeError("Redis bloom filter is disabled or unavailable")

        try:
            client.delete(self.FILTER_NAME)
        except Exception:
            logger.exception("Failed deleting bloom key %s", self.FILTER_NAME)

        self._ensured = False
        if not self._ensure_filter(client):
            raise RuntimeError("Unable to reserve username bloom filter")

        if usernames is None:
            User = get_user_model()
            usernames = User.objects.values_list("username", flat=True).iterator(
                chunk_size=1000
            )

        count = 0
        pipe = client.pipeline(transaction=False)
        batch = 0
        for username in usernames:
            if not username:
                continue
            pipe.execute_command("BF.ADD", self.FILTER_NAME, username)
            count += 1
            batch += 1
            if batch >= 500:
                pipe.execute()
                pipe = client.pipeline(transaction=False)
                batch = 0
        if batch:
            pipe.execute()
        return count


_username_bloom: UsernameBloomFilter | None = None


def get_username_bloom() -> UsernameBloomFilter:
    global _username_bloom
    if _username_bloom is None:
        _username_bloom = UsernameBloomFilter()
    return _username_bloom


def _build_redis_client() -> redis.Redis:
    host = getattr(settings, "REDIS_HOST", "") or ""
    port = getattr(settings, "REDIS_PORT", None)
    password = getattr(settings, "REDIS_PASSWORD", None)
    url = getattr(settings, "REDIS_URL", "redis://localhost:6379/0")

    if host:
        return redis.Redis(
            host=host,
            port=int(port or 6379),
            password=password or None,
            db=_db_from_url(url),
            decode_responses=True,
            socket_connect_timeout=2,
            socket_timeout=2,
        )

    return redis.Redis.from_url(
        url,
        decode_responses=True,
        socket_connect_timeout=2,
        socket_timeout=2,
    )


def _db_from_url(url: str) -> int:
    try:
        path = urlparse(url).path or "/0"
        return int(path.lstrip("/") or "0")
    except (TypeError, ValueError):
        return 0
