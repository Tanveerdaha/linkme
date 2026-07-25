"""
WebSocket consumers for common/test endpoints.

Production consumers for messaging/notifications will live in their apps.
"""

from channels.generic.websocket import AsyncWebsocketConsumer


class TestConsumer(AsyncWebsocketConsumer):
    """Accepts connections at /ws/test/ for Channels smoke testing."""

    async def connect(self):
        await self.accept()
        await self.send(text_data="Connection accepted.")

    async def disconnect(self, close_code):
        pass

    async def receive(self, text_data=None, bytes_data=None):
        if text_data is not None:
            await self.send(text_data=f"echo: {text_data}")
