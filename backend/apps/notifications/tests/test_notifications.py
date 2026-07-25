"""Tests for notification creation and REST APIs."""

import pytest
from django.contrib.auth import get_user_model
from rest_framework import status
from rest_framework.test import APIClient
from rest_framework_simplejwt.tokens import RefreshToken

from apps.comments.models import Comment
from apps.comments.services import create_comment, reply_to_comment
from apps.messaging.models import Conversation, ConversationMember
from apps.messaging.services import send_message
from apps.network.models import Connection
from apps.network.services import accept_connection_request, send_connection_request
from apps.notifications.models import Notification, NotificationPreference
from apps.posts.models import Post
from apps.reactions.services import add_comment_reaction, add_post_reaction

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
def post(user_a):
    return Post.objects.create(
        author=user_a,
        content="Hello world",
        status=Post.Status.PUBLISHED,
        visibility=Post.Visibility.PUBLIC,
    )


def _auth(client, user):
    token = RefreshToken.for_user(user)
    client.credentials(HTTP_AUTHORIZATION=f"Bearer {token.access_token}")
    return client


def test_post_reaction_creates_notification(user_a, user_b, post):
    add_post_reaction(post_id=post.id, user=user_b)
    assert Notification.objects.filter(
        recipient=user_a,
        sender=user_b,
        notification_type=Notification.NotificationType.POST_REACTION,
    ).exists()


def test_self_reaction_no_notification(user_a, post):
    add_post_reaction(post_id=post.id, user=user_a)
    assert not Notification.objects.filter(recipient=user_a).exists()


def test_comment_creates_notification(user_a, user_b, post):
    create_comment(post_id=post.id, author=user_b, content="Nice post")
    assert Notification.objects.filter(
        recipient=user_a,
        notification_type=Notification.NotificationType.POST_COMMENT,
    ).exists()


def test_reply_creates_notification(user_a, user_b, post):
    parent = create_comment(post_id=post.id, author=user_a, content="Root")
    Notification.objects.all().delete()
    reply_to_comment(comment_id=parent.id, author=user_b, content="Reply")
    assert Notification.objects.filter(
        recipient=user_a,
        notification_type=Notification.NotificationType.COMMENT_REPLY,
    ).exists()


def test_comment_reaction_creates_notification(user_a, user_b, post):
    comment = create_comment(post_id=post.id, author=user_a, content="Mine")
    Notification.objects.all().delete()
    add_comment_reaction(comment_id=comment.id, user=user_b)
    assert Notification.objects.filter(
        recipient=user_a,
        notification_type=Notification.NotificationType.COMMENT_REACTION,
    ).exists()


def test_connection_request_creates_notification(user_a, user_b):
    send_connection_request(sender=user_a, username="ahmed")
    assert Notification.objects.filter(
        recipient=user_b,
        notification_type=Notification.NotificationType.CONNECTION_REQUEST,
    ).exists()


def test_connection_accepted_creates_notification(user_a, user_b):
    conn = Connection.objects.create(
        sender=user_a, receiver=user_b, status=Connection.Status.PENDING
    )
    accept_connection_request(connection_id=conn.id, actor=user_b)
    assert Notification.objects.filter(
        recipient=user_a,
        notification_type=Notification.NotificationType.CONNECTION_ACCEPTED,
    ).exists()


def test_message_creates_notification(user_a, user_b):
    Connection.objects.create(
        sender=user_a, receiver=user_b, status=Connection.Status.ACCEPTED
    )
    conversation = Conversation.objects.create(
        conversation_type=Conversation.ConversationType.DIRECT
    )
    ConversationMember.objects.create(conversation=conversation, user=user_a)
    ConversationMember.objects.create(conversation=conversation, user=user_b)
    send_message(
        sender=user_a, conversation_id=conversation.id, content="Hello"
    )
    assert Notification.objects.filter(
        recipient=user_b,
        notification_type=Notification.NotificationType.MESSAGE_RECEIVED,
    ).exists()


def test_message_skipped_when_viewing(user_a, user_b):
    from apps.messaging import presence

    Connection.objects.create(
        sender=user_a, receiver=user_b, status=Connection.Status.ACCEPTED
    )
    conversation = Conversation.objects.create(
        conversation_type=Conversation.ConversationType.DIRECT
    )
    ConversationMember.objects.create(conversation=conversation, user=user_a)
    ConversationMember.objects.create(conversation=conversation, user=user_b)
    presence.set_viewing_conversation(user_b.id, conversation.id)
    send_message(
        sender=user_a, conversation_id=conversation.id, content="Seen"
    )
    assert not Notification.objects.filter(
        notification_type=Notification.NotificationType.MESSAGE_RECEIVED
    ).exists()


def test_get_notifications(api_client, user_a, user_b, post):
    add_post_reaction(post_id=post.id, user=user_b)
    _auth(api_client, user_a)
    response = api_client.get("/api/v1/notifications/")
    assert response.status_code == status.HTTP_200_OK
    assert len(response.data["results"]) == 1
    assert response.data["results"][0]["type"] == "POST_REACTION"


def test_unread_count(api_client, user_a, user_b, post):
    add_post_reaction(post_id=post.id, user=user_b)
    _auth(api_client, user_a)
    response = api_client.get("/api/v1/notifications/unread-count/")
    assert response.status_code == status.HTTP_200_OK
    assert response.data["count"] == 1


def test_mark_read(api_client, user_a, user_b, post):
    add_post_reaction(post_id=post.id, user=user_b)
    note = Notification.objects.get(recipient=user_a)
    _auth(api_client, user_a)
    response = api_client.patch(f"/api/v1/notifications/{note.id}/read/")
    assert response.status_code == status.HTTP_200_OK
    assert response.data["is_read"] is True
    note.refresh_from_db()
    assert note.is_read is True
    assert note.read_at is not None


def test_mark_all_read(api_client, user_a, user_b, post):
    add_post_reaction(post_id=post.id, user=user_b)
    create_comment(post_id=post.id, author=user_b, content="Hi")
    _auth(api_client, user_a)
    response = api_client.post("/api/v1/notifications/read-all/")
    assert response.status_code == status.HTTP_200_OK
    assert response.data["count"] == 0
    assert Notification.objects.filter(recipient=user_a, is_read=False).count() == 0


def test_delete_notification(api_client, user_a, user_b, post):
    add_post_reaction(post_id=post.id, user=user_b)
    note = Notification.objects.get(recipient=user_a)
    _auth(api_client, user_a)
    response = api_client.delete(f"/api/v1/notifications/{note.id}/")
    assert response.status_code == status.HTTP_204_NO_CONTENT
    assert not Notification.objects.filter(pk=note.id).exists()


def test_cannot_delete_others_notification(api_client, user_a, user_b, post):
    add_post_reaction(post_id=post.id, user=user_b)
    note = Notification.objects.get(recipient=user_a)
    _auth(api_client, user_b)
    response = api_client.delete(f"/api/v1/notifications/{note.id}/")
    assert response.status_code == status.HTTP_403_FORBIDDEN


def test_preferences(api_client, user_a, user_b, post):
    _auth(api_client, user_a)
    response = api_client.patch(
        "/api/v1/notifications/preferences/",
        {"post_reactions_enabled": False},
        format="json",
    )
    assert response.status_code == status.HTTP_200_OK
    assert response.data["post_reactions_enabled"] is False

    add_post_reaction(post_id=post.id, user=user_b)
    assert not Notification.objects.filter(
        recipient=user_a,
        notification_type=Notification.NotificationType.POST_REACTION,
    ).exists()
