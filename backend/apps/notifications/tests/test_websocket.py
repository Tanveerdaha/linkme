"""WebSocket notification consumer tests."""

import pytest
from channels.testing import WebsocketCommunicator
from django.contrib.auth import get_user_model
from rest_framework_simplejwt.tokens import AccessToken

from apps.notifications.models import Notification
from apps.notifications.tasks import process_notification_task
from config.asgi import application

User = get_user_model()

WS_HEADERS = [(b"origin", b"http://localhost:3000")]


@pytest.fixture
def channel_layers(settings):
    settings.CHANNEL_LAYERS = {
        "default": {"BACKEND": "channels.layers.InMemoryChannelLayer"}
    }
    settings.ALLOWED_HOSTS = ["localhost", "127.0.0.1", "testserver"]
    settings.CELERY_TASK_ALWAYS_EAGER = True


@pytest.fixture
def users(db):
    user_a = User.objects.create_user(
        email="n_ali@example.com",
        username="n_ali",
        password="SecurePass123!",
        first_name="Ali",
        last_name="N",
        is_active=True,
        is_verified=True,
    )
    user_b = User.objects.create_user(
        email="n_ahmed@example.com",
        username="n_ahmed",
        password="SecurePass123!",
        first_name="Ahmed",
        last_name="N",
        is_active=True,
        is_verified=True,
    )
    return user_a, user_b


def _token(user) -> str:
    return str(AccessToken.for_user(user))


def _communicator(path: str) -> WebsocketCommunicator:
    return WebsocketCommunicator(application, path, headers=WS_HEADERS)


async def _recv_of_type(communicator, expected_type: str, *, limit: int = 8):
    for _ in range(limit):
        event = await communicator.receive_json_from(timeout=2)
        if event.get("type") == expected_type:
            return event
    raise AssertionError(f"Did not receive event type={expected_type}")


@pytest.mark.asyncio
@pytest.mark.django_db(transaction=True)
async def test_ws_connection_accepted(channel_layers, users):
    user_a, _user_b = users
    communicator = _communicator(f"/ws/notifications/?token={_token(user_a)}")
    connected, _ = await communicator.connect()
    assert connected is True
    event = await _recv_of_type(communicator, "notification.unread_count")
    assert event["count"] == 0
    await communicator.disconnect()


@pytest.mark.asyncio
@pytest.mark.django_db(transaction=True)
async def test_ws_unauthorized_rejected(channel_layers, users):
    communicator = _communicator("/ws/notifications/")
    connected, _ = await communicator.connect()
    assert connected is False


@pytest.mark.asyncio
@pytest.mark.django_db(transaction=True)
async def test_ws_notification_delivered(channel_layers, users):
    from channels.db import database_sync_to_async

    user_a, user_b = users
    communicator = _communicator(f"/ws/notifications/?token={_token(user_a)}")
    assert (await communicator.connect())[0]
    await _recv_of_type(communicator, "notification.unread_count")

    note_id = await database_sync_to_async(process_notification_task)(
        recipient_id=str(user_a.id),
        sender_id=str(user_b.id),
        notification_type=Notification.NotificationType.POST_REACTION,
        message="Ahmed reacted ❤️ to your post",
        object_type="post",
        object_id="123",
    )
    assert note_id is not None

    event = await _recv_of_type(communicator, "notification.new")
    assert event["notification"]["message"] == "Ahmed reacted ❤️ to your post"
    assert event["notification"]["type"] == "POST_REACTION"

    count_event = await _recv_of_type(communicator, "notification.unread_count")
    assert count_event["count"] == 1

    await communicator.disconnect()
