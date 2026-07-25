"""Celery tasks for asynchronous notification processing."""

from celery import shared_task


@shared_task(name="notifications.process_notification", queue="notifications")
def process_notification_task(
    *,
    recipient_id: str,
    sender_id: str | None = None,
    notification_type: str,
    message: str,
    object_type: str = "",
    object_id: str = "",
) -> str | None:
    """
    Persist a notification and push it over WebSockets.

    Returns the notification id as a string, or None when suppressed.
    """
    from django.contrib.auth import get_user_model

    from apps.notifications import services
    from apps.notifications.broadcast import (
        broadcast_notification,
        broadcast_unread_count,
    )

    User = get_user_model()
    try:
        recipient = User.objects.get(pk=recipient_id)
    except User.DoesNotExist:
        return None

    sender = None
    if sender_id:
        sender = User.objects.filter(pk=sender_id).first()

    note = services.create_notification(
        recipient=recipient,
        sender=sender,
        notification_type=notification_type,
        message=message,
        object_type=object_type,
        object_id=object_id,
    )
    if note is None:
        return None

    broadcast_notification(note)
    count = services.get_unread_count(user=recipient)
    broadcast_unread_count(user_id=recipient.id, count=count)
    return str(note.id)


def enqueue_notification(
    *,
    recipient,
    sender=None,
    notification_type: str,
    message: str | None = None,
    object_type: str = "",
    object_id: str = "",
) -> None:
    """
    Queue notification creation on Celery.

    In development, ``NOTIFICATIONS_INLINE=true`` (default) delivers in-process
    so ``runserver`` works without a Celery worker. Tests use
    ``CELERY_TASK_ALWAYS_EAGER``.
    """
    from django.conf import settings
    from django.db import transaction

    from apps.notifications import services

    if recipient is None:
        return
    if sender is not None and sender.id == recipient.id:
        return

    text = message or services.build_message(
        notification_type=notification_type, sender=sender
    )
    kwargs = {
        "recipient_id": str(recipient.id),
        "sender_id": str(sender.id) if sender else None,
        "notification_type": notification_type,
        "message": text,
        "object_type": object_type,
        "object_id": str(object_id) if object_id else "",
    }

    inline = getattr(settings, "NOTIFICATIONS_INLINE", False) or getattr(
        settings, "CELERY_TASK_ALWAYS_EAGER", False
    )

    def _queue() -> None:
        try:
            process_notification_task.delay(**kwargs)
        except Exception:
            process_notification_task(**kwargs)

    if inline:
        # Sync path for local/dev and tests (visible in the same DB transaction).
        process_notification_task(**kwargs)
    else:
        # Production: enqueue only after the surrounding transaction commits.
        transaction.on_commit(_queue)
