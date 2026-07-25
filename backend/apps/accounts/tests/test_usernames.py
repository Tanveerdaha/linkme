"""Tests for username normalization, bloom filter, and availability API."""

import threading
from concurrent.futures import ThreadPoolExecutor

import pytest
from django.contrib.auth import get_user_model
from django.db import connection
from rest_framework import status
from rest_framework.test import APIClient

from apps.accounts.bloom import UsernameBloomFilter
from apps.accounts.services import AccountServiceError, register_user
from apps.accounts.username_service import check_username_availability
from apps.common.utils.usernames import normalize_username

User = get_user_model()

CHECK_URL = "/api/v1/users/check-username/"
SIGNUP_URL = "/api/v1/auth/signup/"
PROFILE_ME_URL = "/api/v1/profile/me/"


@pytest.fixture
def api_client():
    return APIClient()


@pytest.fixture
def bloom(settings):
    settings.REDIS_BLOOM_ENABLED = True
    filter_obj = UsernameBloomFilter()
    client = filter_obj._get_client()
    if client is None:
        pytest.skip("Redis unavailable")
    try:
        client.execute_command("BF.RESERVE", "linkme:usernames:probe", 0.01, 10)
        client.delete("linkme:usernames:probe")
    except Exception:
        pytest.skip("RedisBloom module unavailable")
    # Isolate tests on a dedicated key.
    filter_obj.FILTER_NAME = "linkme:usernames:test"
    try:
        client.delete(filter_obj.FILTER_NAME)
    except Exception:
        pass
    filter_obj._ensured = False
    return filter_obj


def test_normalize_username_strips_and_lowercases():
    assert normalize_username("  AzeemAmjad  ") == "azeemamjad"


def test_normalize_username_removes_invalid_characters():
    assert normalize_username("azeem@123") == "azeem123"
    assert normalize_username("azeem amjad") == "azeemamjad"


def test_duplicate_username_rejected(db):
    User.objects.create_user(
        email="a@example.com",
        username="azeemamjad",
        password="SecurePass123!",
        is_active=True,
        is_verified=True,
    )
    with pytest.raises(AccountServiceError) as exc:
        register_user(
            email="b@example.com",
            username="azeemamjad",
            password="SecurePass123!",
        )
    assert exc.value.code == "duplicate_username"


def test_case_insensitive_username_conflict(db):
    User.objects.create_user(
        email="a@example.com",
        username="azeemamjad",
        password="SecurePass123!",
        is_active=True,
        is_verified=True,
    )
    result = check_username_availability("AzeemAmjad")
    assert result["available"] is False
    assert result["username"] == "azeemamjad"


def test_bloom_add_and_exists(bloom):
    assert bloom.username_exists("newuserxyz") is False
    bloom.add_username("newuserxyz")
    assert bloom.username_exists("newuserxyz") is True


def test_signup_adds_username_to_bloom(api_client, bloom, monkeypatch):
    monkeypatch.setattr(
        "apps.accounts.services.get_username_bloom", lambda: bloom
    )
    payload = {
        "email": "bloomuser@example.com",
        "username": "bloomuser",
        "password": "SecurePass123!",
        "first_name": "Bloom",
        "last_name": "User",
    }
    response = api_client.post(SIGNUP_URL, payload, format="json")
    assert response.status_code == status.HTTP_201_CREATED
    assert User.objects.filter(username="bloomuser").exists()
    assert bloom.username_exists("bloomuser") is True


def test_check_username_available(api_client, db):
    response = api_client.get(CHECK_URL, {"username": "freshhandle"})
    assert response.status_code == status.HTTP_200_OK
    assert response.data["available"] is True
    assert response.data["username"] == "freshhandle"


def test_check_username_taken(api_client, db):
    User.objects.create_user(
        email="taken@example.com",
        username="takenname",
        password="SecurePass123!",
        is_active=True,
        is_verified=True,
    )
    response = api_client.get(CHECK_URL, {"username": "TakenName"})
    assert response.status_code == status.HTTP_200_OK
    assert response.data["available"] is False
    assert response.data["reason"] == "Username already exists"


def test_check_username_invalid(api_client):
    response = api_client.get(CHECK_URL, {"username": "bad name!"})
    assert response.status_code == status.HTTP_200_OK
    assert response.data["available"] is False


def test_profile_username_update(api_client, db):
    user = User.objects.create_user(
        email="owner@example.com",
        username="oldhandle",
        password="SecurePass123!",
        is_active=True,
        is_verified=True,
    )
    api_client.force_authenticate(user=user)
    response = api_client.patch(
        PROFILE_ME_URL, {"username": "NewHandle"}, format="json"
    )
    assert response.status_code == status.HTTP_200_OK
    user.refresh_from_db()
    assert user.username == "newhandle"


def test_profile_username_conflict(api_client, db):
    User.objects.create_user(
        email="other@example.com",
        username="claimed",
        password="SecurePass123!",
        is_active=True,
        is_verified=True,
    )
    user = User.objects.create_user(
        email="owner@example.com",
        username="oldhandle",
        password="SecurePass123!",
        is_active=True,
        is_verified=True,
    )
    api_client.force_authenticate(user=user)
    response = api_client.patch(
        PROFILE_ME_URL, {"username": "Claimed"}, format="json"
    )
    assert response.status_code == status.HTTP_400_BAD_REQUEST


def test_rebuild_username_bloom(bloom, db, monkeypatch):
    User.objects.create_user(
        email="rb@example.com",
        username="rebuildme",
        password="SecurePass123!",
        is_active=True,
        is_verified=True,
    )
    monkeypatch.setattr("apps.accounts.bloom.get_username_bloom", lambda: bloom)
    count = bloom.rebuild()
    assert count >= 1
    assert bloom.username_exists("rebuildme") is True


@pytest.mark.django_db(transaction=True)
def test_race_condition_only_one_succeeds():
    """Two concurrent registrations for the same username → one wins."""
    results = []
    barrier = threading.Barrier(2)

    def attempt(idx: int):
        connection.close()
        barrier.wait(timeout=5)
        try:
            register_user(
                email=f"race{idx}@example.com",
                username="racerhandle",
                password="SecurePass123!",
            )
            results.append("ok")
        except AccountServiceError as exc:
            results.append(exc.code)
        finally:
            connection.close()

    with ThreadPoolExecutor(max_workers=2) as pool:
        list(pool.map(attempt, (1, 2)))

    assert results.count("ok") == 1
    assert User.objects.filter(username="racerhandle").count() == 1
