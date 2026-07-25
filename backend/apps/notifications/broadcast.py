"""Channel-layer broadcast for real-time notifications."""

from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer

from apps.notifications.models import Notification


def notification_group(user_id) -> str:
    return f"notifications_{user_id}"


def serialize_notification(notification: Notification, *, request=None) -> dict:
    sender_payload = None
    if notification.sender_id:
        sender = notification.sender
        profile = getattr(sender, "profile", None)
        avatar = None
        if profile and profile.avatar:
            url = profile.avatar.url
            avatar = request.build_absolute_uri(url) if request else url
        sender_payload = {
            "username": sender.username,
            "name": sender.full_name or sender.username,
            "avatar": avatar,
        }
    return {
        "id": str(notification.id),
        "type": notification.notification_type,
        "notification_type": notification.notification_type,
        "sender": sender_payload,
        "message": notification.message,
        "object_type": notification.object_type,
        "object_id": notification.object_id,
        "is_read": notification.is_read,
        "created_at": notification.created_at.isoformat(),
        "read_at": notification.read_at.isoformat() if notification.read_at else None,
    }


def broadcast_notification(notification: Notification) -> None:
    channel_layer = get_channel_layer()
    if channel_layer is None:
        return
    # Ensure sender/profile are loaded for serialization.
    if notification.sender_id and not hasattr(notification, "_state"):
        pass
    note = (
        Notification.objects.select_related("sender", "sender__profile")
        .filter(pk=notification.pk)
        .first()
    )
    if note is None:
        return
    async_to_sync(channel_layer.group_send)(
        notification_group(note.recipient_id),
        {
            "type": "notification.message",
            "notification": serialize_notification(note),
        },
    )


def broadcast_unread_count(*, user_id, count: int) -> None:
    channel_layer = get_channel_layer()
    if channel_layer is None:
        return
    async_to_sync(channel_layer.group_send)(
        notification_group(user_id),
        {
            "type": "notification.unread_count",
            "count": count,
        },
    )
