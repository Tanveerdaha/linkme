"""Tests for authentication and account management."""

import pytest
from django.contrib.auth import get_user_model
from django.core import mail
from rest_framework import status
from rest_framework.test import APIClient
from rest_framework_simplejwt.tokens import RefreshToken

from apps.accounts.tokens import (
    make_email_verification_token,
    make_password_reset_token,
)

User = get_user_model()

SIGNUP_URL = "/api/v1/auth/signup/"
LOGIN_URL = "/api/v1/auth/login/"
LOGOUT_URL = "/api/v1/auth/logout/"
REFRESH_URL = "/api/v1/auth/token/refresh/"
PASSWORD_RESET_URL = "/api/v1/auth/password-reset/"
PASSWORD_RESET_CONFIRM_URL = "/api/v1/auth/password-reset-confirm/"


@pytest.fixture
def api_client():
    return APIClient()


@pytest.fixture
def user_payload():
    return {
        "email": "john@example.com",
        "username": "johnsmith",
        "password": "SecurePass123!",
        "first_name": "John",
        "last_name": "Smith",
    }


@pytest.fixture
def verified_user(user_payload, db):
    user = User.objects.create_user(
        email=user_payload["email"],
        username=user_payload["username"],
        password=user_payload["password"],
        first_name=user_payload["first_name"],
        last_name=user_payload["last_name"],
        is_active=True,
        is_verified=True,
    )
    return user


def test_signup_success(api_client, user_payload):
    response = api_client.post(SIGNUP_URL, user_payload, format="json")
    assert response.status_code == status.HTTP_201_CREATED
    assert response.data["email"] == user_payload["email"]
    assert "verify" in response.data["message"].lower()

    user = User.objects.get(email=user_payload["email"])
    assert user.is_active is False
    assert user.is_verified is False
    assert len(mail.outbox) == 1
    assert user_payload["email"] in mail.outbox[0].to


def test_signup_duplicate_email(api_client, verified_user, user_payload):
    payload = {**user_payload, "username": "anothername"}
    response = api_client.post(SIGNUP_URL, payload, format="json")
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response.data["code"] == "duplicate_email"


def test_signup_duplicate_username(api_client, verified_user, user_payload):
    payload = {**user_payload, "email": "other@example.com"}
    response = api_client.post(SIGNUP_URL, payload, format="json")
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response.data["code"] == "duplicate_username"


@pytest.mark.parametrize(
    "username",
    ["ab", "admin", "Support", "bad name!", "a" * 31],
)
def test_signup_invalid_username(api_client, user_payload, username):
    payload = {**user_payload, "username": username, "email": "unique@example.com"}
    response = api_client.post(SIGNUP_URL, payload, format="json")
    assert response.status_code == status.HTTP_400_BAD_REQUEST


def test_email_verification(api_client, user_payload):
    api_client.post(SIGNUP_URL, user_payload, format="json")
    user = User.objects.get(email=user_payload["email"])
    token = make_email_verification_token(user)

    response = api_client.get(f"/api/v1/auth/verify-email/{token}/")
    assert response.status_code == status.HTTP_200_OK

    user.refresh_from_db()
    assert user.is_active is True
    assert user.is_verified is True


def test_login_success(api_client, verified_user, user_payload):
    response = api_client.post(
        LOGIN_URL,
        {"login": user_payload["username"], "password": user_payload["password"]},
        format="json",
    )
    assert response.status_code == status.HTTP_200_OK
    assert "access" in response.data
    assert "refresh" in response.data
    assert response.data["user"]["username"] == user_payload["username"]


def test_login_with_email(api_client, verified_user, user_payload):
    response = api_client.post(
        LOGIN_URL,
        {"login": user_payload["email"], "password": user_payload["password"]},
        format="json",
    )
    assert response.status_code == status.HTTP_200_OK
    assert "access" in response.data


def test_login_invalid_password(api_client, verified_user, user_payload):
    response = api_client.post(
        LOGIN_URL,
        {"login": user_payload["username"], "password": "wrong-password"},
        format="json",
    )
    assert response.status_code == status.HTTP_401_UNAUTHORIZED


def test_login_unverified_rejected(api_client, user_payload):
    api_client.post(SIGNUP_URL, user_payload, format="json")
    response = api_client.post(
        LOGIN_URL,
        {"login": user_payload["username"], "password": user_payload["password"]},
        format="json",
    )
    assert response.status_code == status.HTTP_403_FORBIDDEN
    assert response.data["code"] == "unverified"


def test_logout_blacklists_refresh(api_client, verified_user):
    refresh = RefreshToken.for_user(verified_user)
    api_client.credentials(HTTP_AUTHORIZATION=f"Bearer {refresh.access_token}")
    response = api_client.post(LOGOUT_URL, {"refresh": str(refresh)}, format="json")
    assert response.status_code == status.HTTP_205_RESET_CONTENT

    refresh_response = api_client.post(
        REFRESH_URL, {"refresh": str(refresh)}, format="json"
    )
    assert refresh_response.status_code == status.HTTP_401_UNAUTHORIZED


def test_password_reset_flow(api_client, verified_user, user_payload):
    response = api_client.post(
        PASSWORD_RESET_URL, {"email": user_payload["email"]}, format="json"
    )
    assert response.status_code == status.HTTP_200_OK
    assert len(mail.outbox) == 1

    token = make_password_reset_token(verified_user)
    new_password = "NewSecurePass456!"
    confirm = api_client.post(
        PASSWORD_RESET_CONFIRM_URL,
        {"token": token, "password": new_password},
        format="json",
    )
    assert confirm.status_code == status.HTTP_200_OK

    login = api_client.post(
        LOGIN_URL,
        {"login": user_payload["username"], "password": new_password},
        format="json",
    )
    assert login.status_code == status.HTTP_200_OK
