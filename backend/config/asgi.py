"""
ASGI config for LinkMe.

Combines HTTP (Django) and WebSocket (Channels) protocols so a single
Daphne/Uvicorn process can serve both.
"""

import os

from channels.routing import ProtocolTypeRouter, URLRouter
from channels.security.websocket import AllowedHostsOriginValidator
from django.core.asgi import get_asgi_application

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")

django_asgi_app = get_asgi_application()

# Import after Django setup so app registry is ready.
from apps.common.routing import websocket_urlpatterns as common_ws  # noqa: E402
from apps.messaging.middleware import JWTAuthMiddlewareStack  # noqa: E402
from apps.messaging.routing import websocket_urlpatterns as messaging_ws  # noqa: E402
from apps.notifications.routing import (  # noqa: E402
    websocket_urlpatterns as notifications_ws,
)

websocket_urlpatterns = notifications_ws + messaging_ws + common_ws

application = ProtocolTypeRouter(
    {
        "http": django_asgi_app,
        "websocket": AllowedHostsOriginValidator(
            JWTAuthMiddlewareStack(URLRouter(websocket_urlpatterns))
        ),
    }
)
