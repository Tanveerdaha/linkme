"""JWT authentication middleware for WebSocket connections."""

from urllib.parse import parse_qs

from channels.db import database_sync_to_async
from channels.middleware import BaseMiddleware
from django.contrib.auth import get_user_model
from django.contrib.auth.models import AnonymousUser
from rest_framework_simplejwt.exceptions import InvalidToken, TokenError
from rest_framework_simplejwt.tokens import AccessToken

User = get_user_model()


@database_sync_to_async
def _get_user(user_id):
    try:
        return User.objects.get(
            id=user_id, is_active=True, is_verified=True
        )
    except User.DoesNotExist:
        return AnonymousUser()


class JWTAuthMiddleware(BaseMiddleware):
    """
    Authenticate WebSocket connections via JWT.

    Token sources (first match wins):
    1. Query string ``?token=<access>``
    2. ``Authorization: Bearer <access>`` header
    """

    async def __call__(self, scope, receive, send):
        scope = dict(scope)
        scope["user"] = AnonymousUser()

        token = self._extract_token(scope)
        if token:
            user_id = self._user_id_from_token(token)
            if user_id:
                scope["user"] = await _get_user(user_id)

        return await super().__call__(scope, receive, send)

    def _extract_token(self, scope) -> str | None:
        query_string = scope.get("query_string", b"").decode()
        params = parse_qs(query_string)
        if "token" in params and params["token"]:
            return params["token"][0]

        headers = dict(scope.get("headers") or [])
        auth = headers.get(b"authorization", b"").decode()
        if auth.lower().startswith("bearer "):
            return auth.split(" ", 1)[1].strip()
        return None

    def _user_id_from_token(self, raw_token: str):
        try:
            token = AccessToken(raw_token)
            return token.get("user_id")
        except (InvalidToken, TokenError, KeyError):
            return None


def JWTAuthMiddlewareStack(inner):
    return JWTAuthMiddleware(inner)
