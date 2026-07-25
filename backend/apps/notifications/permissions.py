"""Permissions for the notifications app."""

from rest_framework.permissions import BasePermission

from apps.posts.permissions import IsAuthenticatedVerified


class IsNotificationsUser(IsAuthenticatedVerified):
    """Authenticated, active, verified users may manage notifications."""


class IsNotificationRecipient(BasePermission):
    def has_object_permission(self, request, view, obj) -> bool:
        return bool(
            request.user
            and request.user.is_authenticated
            and getattr(obj, "recipient_id", None) == request.user.id
        )
