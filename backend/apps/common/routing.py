"""
WebSocket URL routing for the common app.

Included from config.asgi under the root WebSocket router.
"""

from django.urls import path

from apps.common.consumers import TestConsumer

websocket_urlpatterns = [
    path("ws/test/", TestConsumer.as_asgi()),
]
