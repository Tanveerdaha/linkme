"""WebSocket chat consumer tests."""

import pytest
from channels.db import database_sync_to_async
from channels.testing import WebsocketCommunicator
from django.contrib.auth import get_user_model
from rest_framework_simplejwt.tokens import AccessToken

from apps.messaging.models import (
    Conversation,
    ConversationMember,
    Message,
    MessageStatus,
)
from apps.network.models import Connection
from config.asgi import application

User = get_user_model()

WS_HEADERS = [(b"origin", b"http://localhost:3000")]


@pytest.fixture
def channel_layers(settings):
    settings.CHANNEL_LAYERS = {
        "default": {"BACKEND": "channels.layers.InMemoryChannelLayer"}
    }
    settings.ALLOWED_HOSTS = ["localhost", "127.0.0.1", "testserver"]


@pytest.fixture
def users(db):
    user_a = User.objects.create_user(
        email="ws_ali@example.com",
        username="ws_ali",
        password="SecurePass123!",
        first_name="Ali",
        last_name="WS",
        is_active=True,
        is_verified=True,
    )
    user_b = User.objects.create_user(
        email="ws_ahmed@example.com",
        username="ws_ahmed",
        password="SecurePass123!",
        first_name="Ahmed",
        last_name="WS",
        is_active=True,
        is_verified=True,
    )
    Connection.objects.create(
        sender=user_a,
        receiver=user_b,
        status=Connection.Status.ACCEPTED,
    )
    conversation = Conversation.objects.create(
        conversation_type=Conversation.ConversationType.DIRECT,
    )
    ConversationMember.objects.create(conversation=conversation, user=user_a)
    ConversationMember.objects.create(conversation=conversation, user=user_b)
    return user_a, user_b, conversation


def _token(user) -> str:
    return str(AccessToken.for_user(user))


def _communicator(path: str) -> WebsocketCommunicator:
    return WebsocketCommunicator(application, path, headers=WS_HEADERS)


async def _recv_of_type(communicator, expected_type: str, *, limit: int = 8):
    """Receive events until one matches ``expected_type``."""
    for _ in range(limit):
        event = await communicator.receive_json_from(timeout=2)
        if event.get("type") == expected_type:
            return event
    raise AssertionError(f"Did not receive event type={expected_type}")


@pytest.mark.asyncio
@pytest.mark.django_db(transaction=True)
async def test_ws_connection_accepted(channel_layers, users):
    user_a, _user_b, conversation = users
    token = _token(user_a)
    communicator = _communicator(f"/ws/chat/{conversation.id}/?token={token}")
    connected, _ = await communicator.connect()
    assert connected is True
    await communicator.disconnect()


@pytest.mark.asyncio
@pytest.mark.django_db(transaction=True)
async def test_ws_rejects_non_member(channel_layers, users):
    _user_a, _user_b, conversation = users
    stranger = await database_sync_to_async(User.objects.create_user)(
        email="stranger@example.com",
        username="stranger",
        password="SecurePass123!",
        is_active=True,
        is_verified=True,
    )
    token = _token(stranger)
    communicator = _communicator(f"/ws/chat/{conversation.id}/?token={token}")
    connected, _ = await communicator.connect()
    assert connected is False


@pytest.mark.asyncio
@pytest.mark.django_db(transaction=True)
async def test_ws_message_broadcast(channel_layers, users):
    user_a, user_b, conversation = users
    comm_a = _communicator(f"/ws/chat/{conversation.id}/?token={_token(user_a)}")
    comm_b = _communicator(f"/ws/chat/{conversation.id}/?token={_token(user_b)}")
    assert (await comm_a.connect())[0]
    assert (await comm_b.connect())[0]

    # A receives B's presence after B connects.
    await _recv_of_type(comm_a, "presence")

    await comm_a.send_json_to({"type": "message.send", "content": "Hello WS"})
    event_a = await _recv_of_type(comm_a, "message.receive")
    event_b = await _recv_of_type(comm_b, "message.receive")
    assert event_a["message"]["content"] == "Hello WS"
    assert event_b["message"]["content"] == "Hello WS"

    count = await database_sync_to_async(Message.objects.count)()
    assert count == 1

    await comm_a.disconnect()
    await comm_b.disconnect()


@pytest.mark.asyncio
@pytest.mark.django_db(transaction=True)
async def test_ws_typing_event(channel_layers, users):
    user_a, user_b, conversation = users
    comm_a = _communicator(f"/ws/chat/{conversation.id}/?token={_token(user_a)}")
    comm_b = _communicator(f"/ws/chat/{conversation.id}/?token={_token(user_b)}")
    assert (await comm_a.connect())[0]
    assert (await comm_b.connect())[0]
    await _recv_of_type(comm_a, "presence")

    await comm_a.send_json_to({"type": "typing.start"})
    event = await _recv_of_type(comm_b, "typing")
    assert event["user"] == "ws_ali"
    assert event["typing"] is True

    await comm_a.disconnect()
    await comm_b.disconnect()


@pytest.mark.asyncio
@pytest.mark.django_db(transaction=True)
async def test_ws_read_receipt(channel_layers, users):
    user_a, user_b, conversation = users

    message = await database_sync_to_async(Message.objects.create)(
        conversation=conversation,
        sender=user_a,
        content="Read me",
        message_type=Message.MessageType.TEXT,
    )
    await database_sync_to_async(MessageStatus.objects.create)(
        message=message,
        user=user_b,
        status=MessageStatus.Status.SENT,
    )

    comm_a = _communicator(f"/ws/chat/{conversation.id}/?token={_token(user_a)}")
    comm_b = _communicator(f"/ws/chat/{conversation.id}/?token={_token(user_b)}")
    assert (await comm_a.connect())[0]
    assert (await comm_b.connect())[0]
    await _recv_of_type(comm_a, "presence")

    await comm_b.send_json_to({"type": "message.read", "message_id": str(message.id)})
    event = await _recv_of_type(comm_a, "message.read")
    assert event["message_id"] == str(message.id)

    status_obj = await database_sync_to_async(MessageStatus.objects.get)(
        message=message, user=user_b
    )
    assert status_obj.status == MessageStatus.Status.READ

    await comm_a.disconnect()
    await comm_b.disconnect()
