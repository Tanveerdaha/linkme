"""WebSocket consumer for user notification feeds."""

import logging

from channels.db import database_sync_to_async
from channels.generic.websocket import AsyncJsonWebsocketConsumer
from django.contrib.auth.models import AnonymousUser

from apps.notifications.broadcast import notification_group

logger = logging.getLogger(__name__)


class NotificationConsumer(AsyncJsonWebsocketConsumer):
    """
    Personal notification stream.

    Endpoint: ``ws/notifications/?token=<jwt>``
    """

    group_name = None

    async def connect(self):
        user = self.scope.get("user")
        if (
            user is None
            or isinstance(user, AnonymousUser)
            or not getattr(user, "is_authenticated", False)
        ):
            await self.close(code=4001)
            return

        self.group_name = notification_group(user.id)
        await self.channel_layer.group_add(self.group_name, self.channel_name)
        await self.accept()

        count = await self._unread_count(user)
        await self.send_json({"type": "notification.unread_count", "count": count})

    async def disconnect(self, close_code):
        if self.group_name:
            await self.channel_layer.group_discard(
                self.group_name, self.channel_name
            )

    async def receive_json(self, content, **kwargs):
        user = self.scope.get("user")
        if not user or not getattr(user, "is_authenticated", False):
            return

        event_type = content.get("type")
        if event_type == "notification.read":
            note_id = content.get("id")
            if not note_id:
                return
            try:
                await self._mark_read(user, note_id)
                await self.send_json(
                    {"type": "notification.read", "id": str(note_id)}
                )
                count = await self._unread_count(user)
                await self.send_json(
                    {"type": "notification.unread_count", "count": count}
                )
            except Exception as exc:
                logger.exception("notification.read failed: %s", exc)
                await self.send_json(
                    {
                        "type": "error",
                        "detail": str(getattr(exc, "detail", None) or exc),
                    }
                )
        elif event_type == "notification.read_all":
            await self._mark_all_read(user)
            await self.send_json({"type": "notification.read_all"})
            await self.send_json({"type": "notification.unread_count", "count": 0})

    async def notification_message(self, event):
        await self.send_json(
            {
                "type": "notification.new",
                "notification": event["notification"],
            }
        )

    async def notification_unread_count(self, event):
        await self.send_json(
            {
                "type": "notification.unread_count",
                "count": event["count"],
            }
        )

    @database_sync_to_async
    def _unread_count(self, user) -> int:
        from apps.notifications import services

        return services.get_unread_count(user=user)

    @database_sync_to_async
    def _mark_read(self, user, note_id):
        from apps.notifications import services

        return services.mark_as_read(notification_id=note_id, user=user)

    @database_sync_to_async
    def _mark_all_read(self, user) -> int:
        from apps.notifications import services

        return services.mark_all_as_read(user=user)
