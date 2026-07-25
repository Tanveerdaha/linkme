"""Tests for Redis cache helpers."""

import pytest
from django.core.cache import cache

from apps.common import cache as app_cache


@pytest.mark.django_db
def test_profile_cache_roundtrip():
    cache.clear()
    payload = {"username": "alice", "headline": "Hello"}
    app_cache.cache_user_profile("alice", payload)
    assert app_cache.cache_user_profile("alice") == payload
    app_cache.invalidate_user_profile("alice")
    assert app_cache.cache_user_profile("alice") is None


@pytest.mark.django_db
def test_notification_count_cache():
    cache.clear()
    app_cache.cache_notification_count(42, 3)
    assert app_cache.cache_notification_count(42) == 3
    app_cache.bump_notification_count(42, 1)
    assert app_cache.cache_notification_count(42) == 4
    app_cache.invalidate_notification_count(42)
    assert app_cache.cache_notification_count(42) is None
