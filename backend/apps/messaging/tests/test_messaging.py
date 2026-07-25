"""Tests for conversation and message REST APIs."""

import pytest
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from rest_framework import status
from rest_framework.test import APIClient
from rest_framework_simplejwt.tokens import RefreshToken

from apps.messaging.models import Conversation, ConversationMember, Message, MessageStatus
from apps.network.models import Connection

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


@pytest.fixture
def connected(user_a, user_b):
    return Connection.objects.create(
        sender=user_a,
        receiver=user_b,
        status=Connection.Status.ACCEPTED,
    )


def _auth(client, user):
    token = RefreshToken.for_user(user)
    client.credentials(HTTP_AUTHORIZATION=f"Bearer {token.access_token}")
    return client


def test_create_conversation(api_client, user_a, user_b, connected):
    _auth(api_client, user_a)
    response = api_client.post(
        "/api/v1/messages/conversations/", {"username": "ahmed"}
    )
    assert response.status_code == status.HTTP_201_CREATED
    assert response.data["participant"]["username"] == "ahmed"
    assert Conversation.objects.count() == 1
    assert ConversationMember.objects.count() == 2


def test_existing_conversation_returned(api_client, user_a, user_b, connected):
    _auth(api_client, user_a)
    first = api_client.post(
        "/api/v1/messages/conversations/", {"username": "ahmed"}
    )
    second = api_client.post(
        "/api/v1/messages/conversations/", {"username": "ahmed"}
    )
    assert first.status_code == status.HTTP_201_CREATED
    assert second.status_code == status.HTTP_200_OK
    assert first.data["id"] == second.data["id"]
    assert Conversation.objects.count() == 1


def test_non_connected_users_blocked(api_client, user_a, user_c):
    _auth(api_client, user_a)
    response = api_client.post(
        "/api/v1/messages/conversations/", {"username": "john"}
    )
    assert response.status_code == status.HTTP_403_FORBIDDEN
    assert Conversation.objects.count() == 0


def test_pending_connection_blocked(api_client, user_a, user_b):
    Connection.objects.create(
        sender=user_a, receiver=user_b, status=Connection.Status.PENDING
    )
    _auth(api_client, user_a)
    response = api_client.post(
        "/api/v1/messages/conversations/", {"username": "ahmed"}
    )
    assert response.status_code == status.HTTP_403_FORBIDDEN


def test_conversation_permissions(api_client, user_a, user_b, user_c, connected):
    _auth(api_client, user_a)
    created = api_client.post(
        "/api/v1/messages/conversations/", {"username": "ahmed"}
    )
    conv_id = created.data["id"]

    _auth(api_client, user_c)
    detail = api_client.get(f"/api/v1/messages/conversations/{conv_id}/")
    assert detail.status_code == status.HTTP_404_NOT_FOUND


def test_send_message(api_client, user_a, user_b, connected):
    _auth(api_client, user_a)
    conv = api_client.post(
        "/api/v1/messages/conversations/", {"username": "ahmed"}
    ).data
    response = api_client.post(
        f"/api/v1/messages/conversations/{conv['id']}/messages/",
        {"content": "Hello!"},
    )
    assert response.status_code == status.HTTP_201_CREATED
    assert response.data["content"] == "Hello!"
    assert response.data["sender"] == "ali"
    assert Message.objects.count() == 1
    assert MessageStatus.objects.filter(
        status=MessageStatus.Status.SENT
    ).exists()


def test_cannot_send_without_connection(api_client, user_a, user_b, connected):
    _auth(api_client, user_a)
    conv = api_client.post(
        "/api/v1/messages/conversations/", {"username": "ahmed"}
    ).data
    # Remove connection
    Connection.objects.filter(
        sender=user_a, receiver=user_b
    ).update(status=Connection.Status.REMOVED)

    response = api_client.post(
        f"/api/v1/messages/conversations/{conv['id']}/messages/",
        {"content": "Still here?"},
    )
    assert response.status_code == status.HTTP_403_FORBIDDEN


def test_delete_own_message(api_client, user_a, user_b, connected):
    _auth(api_client, user_a)
    conv = api_client.post(
        "/api/v1/messages/conversations/", {"username": "ahmed"}
    ).data
    msg = api_client.post(
        f"/api/v1/messages/conversations/{conv['id']}/messages/",
        {"content": "Delete me"},
    ).data
    response = api_client.delete(f"/api/v1/messages/{msg['id']}/")
    assert response.status_code == status.HTTP_204_NO_CONTENT
    message = Message.objects.get(pk=msg["id"])
    assert message.is_deleted is True


def test_cannot_delete_others_message(api_client, user_a, user_b, connected):
    _auth(api_client, user_a)
    conv = api_client.post(
        "/api/v1/messages/conversations/", {"username": "ahmed"}
    ).data
    msg = api_client.post(
        f"/api/v1/messages/conversations/{conv['id']}/messages/",
        {"content": "Mine"},
    ).data

    _auth(api_client, user_b)
    response = api_client.delete(f"/api/v1/messages/{msg['id']}/")
    assert response.status_code == status.HTTP_403_FORBIDDEN
    assert Message.objects.get(pk=msg["id"]).is_deleted is False


def test_message_history(api_client, user_a, user_b, connected):
    _auth(api_client, user_a)
    conv = api_client.post(
        "/api/v1/messages/conversations/", {"username": "ahmed"}
    ).data
    for i in range(3):
        api_client.post(
            f"/api/v1/messages/conversations/{conv['id']}/messages/",
            {"content": f"msg {i}"},
        )
    response = api_client.get(
        f"/api/v1/messages/conversations/{conv['id']}/messages/"
    )
    assert response.status_code == status.HTTP_200_OK
    assert len(response.data["results"]) == 3


def test_list_conversations_unread(api_client, user_a, user_b, connected):
    _auth(api_client, user_a)
    conv = api_client.post(
        "/api/v1/messages/conversations/", {"username": "ahmed"}
    ).data
    api_client.post(
        f"/api/v1/messages/conversations/{conv['id']}/messages/",
        {"content": "Hi"},
    )

    _auth(api_client, user_b)
    response = api_client.get("/api/v1/messages/conversations/")
    assert response.status_code == status.HTTP_200_OK
    assert response.data["results"][0]["unread_count"] == 1
    assert response.data["results"][0]["last_message"] == "Hi"


def test_send_image_attachment(api_client, user_a, user_b, connected):
    _auth(api_client, user_a)
    conv = api_client.post(
        "/api/v1/messages/conversations/", {"username": "ahmed"}
    ).data
    # Minimal valid 1x1 PNG
    png = (
        b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01"
        b"\x00\x00\x00\x01\x08\x02\x00\x00\x00\x90wS\xde\x00\x00"
        b"\x00\x0cIDATx\x9cc\xf8\x0f\x00\x00\x01\x01\x00\x05\x18"
        b"\xd8N\x00\x00\x00\x00IEND\xaeB`\x82"
    )
    upload = SimpleUploadedFile("photo.png", png, content_type="image/png")
    response = api_client.post(
        f"/api/v1/messages/conversations/{conv['id']}/messages/",
        {"content": "", "attachment": upload},
        format="multipart",
    )
    assert response.status_code == status.HTTP_201_CREATED
    assert response.data["message_type"] == "IMAGE"
    assert response.data["attachment"] is not None
    assert "metadata" in response.data


def test_send_link_message(api_client, user_a, user_b, connected):
    _auth(api_client, user_a)
    conv = api_client.post(
        "/api/v1/messages/conversations/", {"username": "ahmed"}
    ).data
    response = api_client.post(
        f"/api/v1/messages/conversations/{conv['id']}/messages/",
        {
            "message_type": "LINK",
            "metadata": {"url": "https://example.com/page"},
            "content": "",
        },
        format="json",
    )
    assert response.status_code == status.HTTP_201_CREATED
    assert response.data["message_type"] == "LINK"
    assert response.data["metadata"]["url"] == "https://example.com/page"


def test_send_voice_message(api_client, user_a, user_b, connected):
    _auth(api_client, user_a)
    conv = api_client.post(
        "/api/v1/messages/conversations/", {"username": "ahmed"}
    ).data
    upload = SimpleUploadedFile(
        "voice.webm", b"fake-audio-bytes", content_type="audio/webm"
    )
    response = api_client.post(
        f"/api/v1/messages/conversations/{conv['id']}/messages/",
        {
            "message_type": "VOICE",
            "attachment": upload,
            "metadata": '{"duration_seconds": 12}',
        },
        format="multipart",
    )
    assert response.status_code == status.HTTP_201_CREATED, response.data
    assert response.data["message_type"] == "VOICE"
    assert response.data["attachment"] is not None
    assert response.data["metadata"]["duration_seconds"] == 12


def test_send_file_message(api_client, user_a, user_b, connected):
    _auth(api_client, user_a)
    conv = api_client.post(
        "/api/v1/messages/conversations/", {"username": "ahmed"}
    ).data
    upload = SimpleUploadedFile(
        "doc.pdf", b"%PDF-1.4 fake", content_type="application/pdf"
    )
    response = api_client.post(
        f"/api/v1/messages/conversations/{conv['id']}/messages/",
        {"message_type": "FILE", "attachment": upload},
        format="multipart",
    )
    assert response.status_code == status.HTTP_201_CREATED
    assert response.data["message_type"] == "FILE"
    assert response.data["attachment"] is not None
