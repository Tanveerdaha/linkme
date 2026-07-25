"""WebSocket consumers for real-time direct messaging."""

import logging

from channels.db import database_sync_to_async
from channels.generic.websocket import AsyncJsonWebsocketConsumer
from django.contrib.auth.models import AnonymousUser

from apps.messaging import presence, selectors, services
from apps.messaging.broadcast import serialize_message_for_ws
from apps.messaging.models import Message

logger = logging.getLogger(__name__)


class ChatConsumer(AsyncJsonWebsocketConsumer):
    """
    Real-time chat for a single conversation.

    Endpoint: ``ws/chat/{conversation_id}/?token=<jwt>``
    """

    conversation_id = None
    group_name = None

    async def connect(self):
        user = self.scope.get("user")
        self.conversation_id = self.scope["url_route"]["kwargs"].get("conversation_id")

        if (
            user is None
            or isinstance(user, AnonymousUser)
            or not getattr(user, "is_authenticated", False)
        ):
            await self.close(code=4001)
            return

        if not self.conversation_id:
            await self.close(code=4002)
            return

        is_member = await self._user_is_member(user.id, self.conversation_id)
        if not is_member:
            await self.close(code=4003)
            return

        self.group_name = f"chat_{self.conversation_id}"
        await self.channel_layer.group_add(self.group_name, self.channel_name)
        await self.accept()

        await database_sync_to_async(presence.set_online)(user.id)
        await database_sync_to_async(presence.set_viewing_conversation)(
            user.id, self.conversation_id
        )
        await self._broadcast_presence(online=True)

    async def disconnect(self, close_code):
        user = self.scope.get("user")
        if self.group_name:
            await self.channel_layer.group_discard(self.group_name, self.channel_name)
        if user and getattr(user, "is_authenticated", False):
            await database_sync_to_async(presence.clear_viewing_conversation)(user.id)
            await database_sync_to_async(presence.set_offline)(user.id)
            if self.group_name:
                await self._broadcast_presence(online=False)

    async def receive_json(self, content, **kwargs):
        user = self.scope.get("user")
        if not user or not getattr(user, "is_authenticated", False):
            return

        event_type = content.get("type")
        try:
            if event_type == "message.send":
                await self._handle_send(user, content)
            elif event_type == "typing.start":
                await self._handle_typing(user, True)
            elif event_type == "typing.stop":
                await self._handle_typing(user, False)
            elif event_type == "message.read":
                await self._handle_read(user, content)
            elif event_type == "presence.heartbeat":
                await database_sync_to_async(presence.heartbeat)(user.id)
            else:
                await self.send_json(
                    {"type": "error", "detail": f"Unknown event type: {event_type}"}
                )
        except Exception as exc:
            logger.exception("ChatConsumer error: %s", exc)
            await self.send_json(
                {"type": "error", "detail": str(getattr(exc, "detail", None) or exc)}
            )

    async def _handle_send(self, user, content):
        text = (content.get("content") or "").strip()
        if not text:
            await self.send_json(
                {"type": "error", "detail": "Message content is required."}
            )
            return

        try:
            message = await database_sync_to_async(services.send_message)(
                sender=user,
                conversation_id=self.conversation_id,
                content=text,
            )
        except Exception as exc:
            await self.send_json(
                {
                    "type": "error",
                    "detail": str(getattr(exc, "detail", None) or exc),
                }
            )
            return

        payload = await self._serialize_message(message)
        await self.channel_layer.group_send(
            self.group_name,
            {"type": "chat.message", "message": payload},
        )

    async def _handle_typing(self, user, typing: bool):
        await self.channel_layer.group_send(
            self.group_name,
            {
                "type": "chat.typing",
                "user": user.username,
                "typing": typing,
            },
        )

    async def _handle_read(self, user, content):
        message_id = content.get("message_id")
        if not message_id:
            # Mark whole conversation read.
            await database_sync_to_async(services.mark_conversation_read)(
                reader=user, conversation_id=self.conversation_id
            )
            await self.channel_layer.group_send(
                self.group_name,
                {
                    "type": "chat.read",
                    "message_id": None,
                    "reader": user.username,
                    "conversation_id": str(self.conversation_id),
                },
            )
            return

        try:
            await database_sync_to_async(services.mark_message_read)(
                reader=user, message_id=message_id
            )
        except Exception as exc:
            await self.send_json(
                {
                    "type": "error",
                    "detail": str(getattr(exc, "detail", None) or exc),
                }
            )
            return

        await self.channel_layer.group_send(
            self.group_name,
            {
                "type": "chat.read",
                "message_id": str(message_id),
                "reader": user.username,
                "conversation_id": str(self.conversation_id),
            },
        )

    async def _broadcast_presence(self, *, online: bool):
        user = self.scope.get("user")
        if not user or not self.group_name:
            return
        await self.channel_layer.group_send(
            self.group_name,
            {
                "type": "chat.presence",
                "user": user.username,
                "online": online,
            },
        )

    # --- channel layer event handlers ---

    async def chat_message(self, event):
        message = event["message"]
        await self.send_json({"type": "message.receive", "message": message})

        # Mark delivered for the recipient quietly; notify peers separately.
        user = self.scope.get("user")
        if user and message.get("sender") != user.username:
            status_obj = await database_sync_to_async(services.mark_message_delivered)(
                recipient=user, message_id=message["id"]
            )
            if status_obj is not None:
                await self.channel_layer.group_send(
                    self.group_name,
                    {
                        "type": "chat.delivered",
                        "message_id": str(message["id"]),
                        "user": user.username,
                    },
                )

    async def chat_typing(self, event):
        user = self.scope.get("user")
        if user and event.get("user") == user.username:
            return
        await self.send_json(
            {
                "type": "typing",
                "user": event["user"],
                "typing": event["typing"],
            }
        )

    async def chat_read(self, event):
        await self.send_json(
            {
                "type": "message.read",
                "message_id": event.get("message_id"),
                "reader": event.get("reader"),
                "conversation_id": event.get("conversation_id"),
            }
        )

    async def chat_delivered(self, event):
        await self.send_json(
            {
                "type": "message.delivered",
                "message_id": event.get("message_id"),
                "user": event.get("user"),
            }
        )

    async def chat_presence(self, event):
        user = self.scope.get("user")
        if user and event.get("user") == user.username:
            return
        await self.send_json(
            {
                "type": "presence",
                "user": event["user"],
                "online": event["online"],
            }
        )

    @database_sync_to_async
    def _user_is_member(self, user_id, conversation_id) -> bool:
        from django.contrib.auth import get_user_model

        User = get_user_model()
        try:
            user = User.objects.get(pk=user_id)
        except User.DoesNotExist:
            return False
        return selectors.user_is_member(conversation_id=conversation_id, user=user)

    @database_sync_to_async
    def _serialize_message(self, message: Message) -> dict:
        return serialize_message_for_ws(message)
