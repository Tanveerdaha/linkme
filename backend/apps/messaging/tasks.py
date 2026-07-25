"""Celery tasks for messaging (presence cleanup hooks)."""

from apps.messaging import presence
from celery import shared_task


@shared_task(name="messaging.refresh_presence")
def refresh_presence_task(user_id: str) -> bool:
    """Extend online TTL — used if clients miss a heartbeat window."""
    presence.heartbeat(user_id)
    return True


@shared_task(name="messaging.clear_presence")
def clear_presence_task(user_id: str) -> bool:
    presence.set_offline(user_id)
    return True
