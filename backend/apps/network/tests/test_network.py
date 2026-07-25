"""Tests for LinkedIn-style network connections."""

import pytest
from django.contrib.auth import get_user_model
from rest_framework import status
from rest_framework.test import APIClient
from rest_framework_simplejwt.tokens import RefreshToken

from apps.network.models import Connection
from apps.profiles.models import Profile

User = get_user_model()


@pytest.fixture
def api_client():
    return APIClient()


@pytest.fixture
def user_a(db):
    return User.objects.create_user(
        email="ali@example.com",
        username="ali",
        password="SecurePass123!",
        first_name="Ali",
        last_name="Khan",
        is_active=True,
        is_verified=True,
    )


@pytest.fixture
def user_b(db):
    return User.objects.create_user(
        email="ahmed@example.com",
        username="ahmed",
        password="SecurePass123!",
        first_name="Ahmed",
        last_name="Ali",
        is_active=True,
        is_verified=True,
    )


@pytest.fixture
def user_c(db):
    return User.objects.create_user(
        email="john@example.com",
        username="john",
        password="SecurePass123!",
        first_name="John",
        last_name="Doe",
        is_active=True,
        is_verified=True,
    )


def _auth(client, user):
    token = RefreshToken.for_user(user)
    client.credentials(HTTP_AUTHORIZATION=f"Bearer {token.access_token}")
    return client


def test_send_request(api_client, user_a, user_b):
    _auth(api_client, user_a)
    response = api_client.post("/api/v1/network/request/ahmed/", {"message": "Hi"})
    assert response.status_code == status.HTTP_201_CREATED
    assert response.data["status"] == "REQUEST_SENT"
    assert Connection.objects.filter(
        sender=user_a, receiver=user_b, status=Connection.Status.PENDING
    ).exists()


def test_duplicate_request_blocked(api_client, user_a, user_b):
    _auth(api_client, user_a)
    api_client.post("/api/v1/network/request/ahmed/")
    # Reverse direction also blocked.
    _auth(api_client, user_b)
    response = api_client.post("/api/v1/network/request/ali/")
    assert response.status_code == status.HTTP_400_BAD_REQUEST


def test_cannot_request_yourself(api_client, user_a):
    _auth(api_client, user_a)
    response = api_client.post("/api/v1/network/request/ali/")
    assert response.status_code == status.HTTP_400_BAD_REQUEST


def test_accept_request(api_client, user_a, user_b):
    conn = Connection.objects.create(
        sender=user_a, receiver=user_b, status=Connection.Status.PENDING
    )
    _auth(api_client, user_b)
    response = api_client.post(f"/api/v1/network/request/{conn.id}/accept/")
    assert response.status_code == status.HTTP_200_OK
    assert response.data["status"] == "CONNECTED"
    conn.refresh_from_db()
    assert conn.status == Connection.Status.ACCEPTED
    assert conn.accepted_at is not None


def test_reject_request(api_client, user_a, user_b):
    conn = Connection.objects.create(
        sender=user_a, receiver=user_b, status=Connection.Status.PENDING
    )
    _auth(api_client, user_b)
    response = api_client.post(f"/api/v1/network/request/{conn.id}/reject/")
    assert response.status_code == status.HTTP_200_OK
    conn.refresh_from_db()
    assert conn.status == Connection.Status.REJECTED


def test_cancel_request(api_client, user_a, user_b):
    conn = Connection.objects.create(
        sender=user_a, receiver=user_b, status=Connection.Status.PENDING
    )
    _auth(api_client, user_a)
    response = api_client.delete(f"/api/v1/network/request/{conn.id}/")
    assert response.status_code == status.HTTP_200_OK
    conn.refresh_from_db()
    assert conn.status == Connection.Status.CANCELLED


def test_sender_cannot_accept(api_client, user_a, user_b):
    conn = Connection.objects.create(
        sender=user_a, receiver=user_b, status=Connection.Status.PENDING
    )
    _auth(api_client, user_a)
    response = api_client.post(f"/api/v1/network/request/{conn.id}/accept/")
    assert response.status_code == status.HTTP_403_FORBIDDEN


def test_connection_appears_after_acceptance(api_client, user_a, user_b):
    conn = Connection.objects.create(
        sender=user_a, receiver=user_b, status=Connection.Status.PENDING
    )
    _auth(api_client, user_b)
    api_client.post(f"/api/v1/network/request/{conn.id}/accept/")

    _auth(api_client, user_a)
    list_a = api_client.get("/api/v1/network/connections/")
    assert list_a.status_code == status.HTTP_200_OK
    assert list_a.data["count"] == 1
    assert list_a.data["results"][0]["username"] == "ahmed"

    _auth(api_client, user_b)
    list_b = api_client.get("/api/v1/network/connections/")
    assert list_b.data["count"] == 1
    assert list_b.data["results"][0]["username"] == "ali"


def test_remove_connection(api_client, user_a, user_b):
    Connection.objects.create(
        sender=user_a,
        receiver=user_b,
        status=Connection.Status.ACCEPTED,
    )
    _auth(api_client, user_a)
    response = api_client.delete("/api/v1/network/connections/ahmed/")
    assert response.status_code == status.HTTP_200_OK
    assert response.data["status"] == "NONE"
    assert not Connection.objects.filter(status=Connection.Status.ACCEPTED).exists()


def test_status_endpoint(api_client, user_a, user_b):
    _auth(api_client, user_a)
    none = api_client.get("/api/v1/network/status/ahmed/")
    assert none.data["status"] == "NONE"
    assert none.data["can_connect"] is True

    api_client.post("/api/v1/network/request/ahmed/")
    sent = api_client.get("/api/v1/network/status/ahmed/")
    assert sent.data["status"] == "REQUEST_SENT"

    _auth(api_client, user_b)
    received = api_client.get("/api/v1/network/status/ali/")
    assert received.data["status"] == "REQUEST_RECEIVED"


def test_received_and_sent_lists(api_client, user_a, user_b):
    Connection.objects.create(
        sender=user_a, receiver=user_b, status=Connection.Status.PENDING
    )
    _auth(api_client, user_b)
    received = api_client.get("/api/v1/network/requests/received/")
    assert len(received.data) == 1
    assert received.data[0]["user"]["username"] == "ali"

    _auth(api_client, user_a)
    sent = api_client.get("/api/v1/network/requests/sent/")
    assert len(sent.data) == 1
    assert sent.data[0]["user"]["username"] == "ahmed"


def test_mutual_connections(api_client, user_a, user_b, user_c):
    Connection.objects.create(
        sender=user_a, receiver=user_c, status=Connection.Status.ACCEPTED
    )
    Connection.objects.create(
        sender=user_b, receiver=user_c, status=Connection.Status.ACCEPTED
    )
    _auth(api_client, user_a)
    response = api_client.get("/api/v1/network/mutual/ahmed/")
    assert response.status_code == status.HTTP_200_OK
    assert response.data["count"] == 1
    assert response.data["users"][0]["username"] == "john"


def test_discover_suggestions(api_client, user_a, user_b):
    user_b.profile.headline = "Engineer"
    user_b.profile.bio = "Building things"
    user_b.profile.save()
    _auth(api_client, user_a)
    response = api_client.get("/api/v1/network/discover/")
    assert response.status_code == status.HTTP_200_OK
    usernames = [u["username"] for u in response.data]
    assert "ahmed" in usernames
    assert "ali" not in usernames


def test_connection_privacy_private(api_client, user_a, user_b):
    Connection.objects.create(
        sender=user_a, receiver=user_b, status=Connection.Status.ACCEPTED
    )
    user_a.profile.connection_visibility = Profile.ConnectionVisibility.PRIVATE
    user_a.profile.save()

    _auth(api_client, user_b)
    response = api_client.get("/api/v1/network/connections/?username=ali")
    assert response.status_code == status.HTTP_403_FORBIDDEN


def test_connection_privacy_owner_can_view(api_client, user_a, user_b):
    Connection.objects.create(
        sender=user_a, receiver=user_b, status=Connection.Status.ACCEPTED
    )
    user_a.profile.connection_visibility = Profile.ConnectionVisibility.PRIVATE
    user_a.profile.save()

    _auth(api_client, user_a)
    response = api_client.get("/api/v1/network/connections/?username=ali")
    assert response.status_code == status.HTTP_200_OK
    assert response.data["count"] == 1


def test_network_summary(api_client, user_a, user_b):
    Connection.objects.create(
        sender=user_b, receiver=user_a, status=Connection.Status.PENDING
    )
    _auth(api_client, user_a)
    response = api_client.get("/api/v1/network/")
    assert response.status_code == status.HTTP_200_OK
    assert response.data["requests_received"] == 1
