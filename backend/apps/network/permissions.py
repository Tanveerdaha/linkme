"""Permissions for the network app."""

from rest_framework.permissions import BasePermission

from apps.posts.permissions import IsAuthenticatedVerified


class IsNetworkUser(IsAuthenticatedVerified):
    """Authenticated, active, verified users may manage network actions."""


class IsConnectionReceiver(BasePermission):
    def has_object_permission(self, request, view, obj) -> bool:
        return bool(
            request.user
            and request.user.is_authenticated
            and obj.receiver_id == request.user.id
        )


class IsConnectionSender(BasePermission):
    def has_object_permission(self, request, view, obj) -> bool:
        return bool(
            request.user
            and request.user.is_authenticated
            and obj.sender_id == request.user.id
        )
