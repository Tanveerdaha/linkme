"""Domain services for notifications."""

from django.contrib.auth import get_user_model
from django.db import transaction
from django.utils import timezone
from rest_framework.exceptions import NotFound, PermissionDenied

from apps.notifications.models import Notification
from apps.notifications.preferences import is_type_enabled, update_preferences

User = get_user_model()


def _display_name(user) -> str:
    name = getattr(user, "full_name", None) or ""
    name = name.strip() if isinstance(name, str) else ""
    return name or user.username


@transaction.atomic
def create_notification(
    *,
    recipient,
    sender=None,
    notification_type: str,
    message: str,
    object_type: str = "",
    object_id: str = "",
    skip_preference_check: bool = False,
) -> Notification | None:
    """
    Persist a notification for ``recipient``.

    Returns ``None`` when suppressed (self-notify or preferences).
    """
    if recipient is None:
        return None
    if sender is not None and sender.id == recipient.id:
        return None

    # Suppress notifications across block relationships.
    if sender is not None:
        from apps.moderation.blocks import is_blocked

        if is_blocked(user_a=sender, user_b=recipient):
            return None

    if getattr(recipient, "is_deleted", False):
        return None

    if not skip_preference_check and not is_type_enabled(
        user=recipient, notification_type=notification_type
    ):
        return None

    text = (message or "").strip()[:500]
    if not text:
        return None

    note = Notification.objects.create(
        recipient=recipient,
        sender=sender,
        notification_type=notification_type,
        object_type=object_type or "",
        object_id=str(object_id) if object_id else "",
        message=text,
    )
    from apps.common.cache import bump_notification_count, invalidate_notification_count

    try:
        bump_notification_count(recipient.id, 1)
    except Exception:
        invalidate_notification_count(recipient.id)
    return note


def create_bulk_notifications(*, items: list[dict]) -> list[Notification]:
    """Create many notifications. Each item uses ``create_notification`` kwargs."""
    created = []
    for item in items:
        note = create_notification(**item)
        if note is not None:
            created.append(note)
    return created


@transaction.atomic
def mark_as_read(*, notification_id, user) -> Notification:
    note = (
        Notification.objects.select_related("sender", "sender__profile")
        .filter(pk=notification_id)
        .first()
    )
    if note is None:
        raise NotFound("Notification not found.")
    if note.recipient_id != user.id:
        raise PermissionDenied("You can only update your own notifications.")
    if not note.is_read:
        note.is_read = True
        note.read_at = timezone.now()
        note.save(update_fields=["is_read", "read_at"])
        from apps.common.cache import invalidate_notification_count

        invalidate_notification_count(user.id)
    return note


@transaction.atomic
def mark_all_as_read(*, user) -> int:
    now = timezone.now()
    updated = Notification.objects.filter(recipient=user, is_read=False).update(
        is_read=True, read_at=now
    )
    if updated:
        from apps.common.cache import cache_notification_count

        cache_notification_count(user.id, 0)
    return updated


def get_unread_count(*, user) -> int:
    from apps.common.cache import cache_notification_count

    cached = cache_notification_count(user.id)
    if cached is not None:
        return cached
    count = Notification.objects.filter(recipient=user, is_read=False).count()
    cache_notification_count(user.id, count)
    return count


@transaction.atomic
def delete_notification(*, notification_id, user) -> None:
    note = Notification.objects.filter(pk=notification_id).first()
    if note is None:
        raise NotFound("Notification not found.")
    if note.recipient_id != user.id:
        raise PermissionDenied("You can only delete your own notifications.")
    was_unread = not note.is_read
    note.delete()
    if was_unread:
        from apps.common.cache import invalidate_notification_count

        invalidate_notification_count(user.id)


def build_message(*, notification_type: str, sender) -> str:
    name = _display_name(sender) if sender else "Someone"
    templates = {
        Notification.NotificationType.POST_REACTION: f"{name} reacted ❤️ to your post",
        Notification.NotificationType.POST_COMMENT: f"{name} commented on your post",
        Notification.NotificationType.COMMENT_REPLY: f"{name} replied to your comment",
        Notification.NotificationType.COMMENT_REACTION: f"{name} reacted ❤️ to your comment",
        Notification.NotificationType.CONNECTION_REQUEST: f"{name} sent you a connection request",
        Notification.NotificationType.CONNECTION_ACCEPTED: f"{name} accepted your connection request",
        Notification.NotificationType.MESSAGE_RECEIVED: f"{name} sent you a message",
        Notification.NotificationType.ACCOUNT_EVENT: "Important account update",
    }
    return templates.get(notification_type, f"{name} sent you a notification")


# Re-export preference update for views.
update_user_preferences = update_preferences
