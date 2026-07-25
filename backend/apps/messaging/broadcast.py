"""Channel-layer broadcast helpers for messaging."""

from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer

from apps.messaging.models import Message, MessageStatus


def serialize_message_for_ws(message: Message) -> dict:
    attachment = None
    if message.attachment and not message.is_deleted:
        attachment = message.attachment.url
    status_value = MessageStatus.Status.SENT
    statuses = list(message.statuses.all())
    if statuses:
        status_value = statuses[0].status
    return {
        "id": str(message.id),
        "conversation_id": str(message.conversation_id),
        "sender": message.sender.username,
        "content": "" if message.is_deleted else message.content,
        "message_type": message.message_type,
        "attachment": attachment,
        "metadata": {} if message.is_deleted else (message.metadata or {}),
        "created_at": message.created_at.isoformat(),
        "is_deleted": message.is_deleted,
        "status": status_value,
    }


def broadcast_message(message: Message) -> None:
    """Push a newly created message to the conversation WebSocket group."""
    channel_layer = get_channel_layer()
    if channel_layer is None:
        return
    group = f"chat_{message.conversation_id}"
    async_to_sync(channel_layer.group_send)(
        group,
        {
            "type": "chat.message",
            "message": serialize_message_for_ws(message),
        },
    )
