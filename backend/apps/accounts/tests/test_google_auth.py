"""Google OAuth authentication tests."""

from unittest.mock import patch

import pytest
from django.contrib.auth import get_user_model
from rest_framework import status
from rest_framework.test import APIClient

from apps.accounts.google import GoogleIdentity
from apps.accounts.services import AccountServiceError

User = get_user_model()

GOOGLE_URL = "/api/v1/auth/google/"
LOGIN_URL = "/api/v1/auth/login/"


@pytest.fixture
def api_client():
    return APIClient()


def _identity(**overrides):
    data = {
        "google_id": "google-sub-123",
        "email": "azeem@gmail.com",
        "first_name": "Azeem",
        "last_name": "Amjad",
        "picture": "",
        "full_name": "Azeem Amjad",
    }
    data.update(overrides)
    return GoogleIdentity(**data)


@pytest.mark.django_db
def test_google_creates_new_user_via_code(api_client):
    with patch(
        "apps.accounts.google.exchange_authorization_code",
        return_value=_identity(),
    ):
        response = api_client.post(
            GOOGLE_URL,
            {"code": "fake-auth-code"},
            format="json",
        )

    assert response.status_code == status.HTTP_200_OK
    assert "access" in response.data
    assert "refresh" in response.data
    user = User.objects.get(email="azeem@gmail.com")
    assert user.google_id == "google-sub-123"
    assert user.auth_provider == User.AuthProvider.GOOGLE
    assert user.is_verified is True
    assert user.is_active is True
    assert user.username.startswith("azeem")
    assert not user.has_usable_password()


@pytest.mark.django_db
def test_google_links_existing_email_user(api_client):
    existing = User.objects.create_user(
        email="azeem@gmail.com",
        username="azeemlocal",
        password="SecurePass123!",
        is_active=True,
        is_verified=True,
        auth_provider=User.AuthProvider.EMAIL,
    )

    with patch(
        "apps.accounts.google.exchange_authorization_code",
        return_value=_identity(),
    ):
        response = api_client.post(
            GOOGLE_URL,
            {"code": "fake-auth-code"},
            format="json",
        )

    assert response.status_code == status.HTTP_200_OK
    existing.refresh_from_db()
    assert existing.google_id == "google-sub-123"
    assert existing.auth_provider == User.AuthProvider.EMAIL
    assert User.objects.filter(email="azeem@gmail.com").count() == 1
    assert response.data["user"]["username"] == "azeemlocal"


@pytest.mark.django_db
def test_google_invalid_code(api_client, settings):
    settings.GOOGLE_CLIENT_ID = "test-client-id.apps.googleusercontent.com"
    settings.GOOGLE_CLIENT_SECRET = "test-secret"
    settings.GOOGLE_REDIRECT_URI = "http://localhost:3000/auth/google/callback"
    with patch(
        "apps.accounts.google.exchange_authorization_code",
        side_effect=AccountServiceError(
            "Unable to continue with Google. Please try again.",
            code="invalid_google_token",
        ),
    ):
        response = api_client.post(
            GOOGLE_URL,
            {"code": "bad-code"},
            format="json",
        )

    assert response.status_code == status.HTTP_401_UNAUTHORIZED
    assert response.data["code"] == "invalid_google_token"


@pytest.mark.django_db
def test_email_password_login_still_works(api_client):
    User.objects.create_user(
        email="john@example.com",
        username="johnsmith",
        password="SecurePass123!",
        is_active=True,
        is_verified=True,
    )
    response = api_client.post(
        LOGIN_URL,
        {"login": "john@example.com", "password": "SecurePass123!"},
        format="json",
    )
    assert response.status_code == status.HTTP_200_OK
    assert "access" in response.data
