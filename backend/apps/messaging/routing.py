"""WebSocket URL routing for messaging."""

from django.urls import path

from apps.messaging.consumers import ChatConsumer

websocket_urlpatterns = [
    path("ws/chat/<uuid:conversation_id>/", ChatConsumer.as_asgi()),
]
