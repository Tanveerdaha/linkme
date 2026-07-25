"""Permissions for the messaging app."""

from rest_framework.permissions import BasePermission

from apps.posts.permissions import IsAuthenticatedVerified


class IsMessagingUser(IsAuthenticatedVerified):
    """Authenticated, active, verified users may use messaging."""


class IsConversationMember(BasePermission):
    """Object permission: user must be a conversation member."""

    def has_object_permission(self, request, view, obj) -> bool:
        user = request.user
        if not user or not user.is_authenticated:
            return False
        # Conversation instance
        if hasattr(obj, "members"):
            return obj.members.filter(user=user).exists()
        # Message instance
        if hasattr(obj, "conversation_id"):
            return obj.conversation.members.filter(user=user).exists()
        return False


class IsMessageSender(BasePermission):
    def has_object_permission(self, request, view, obj) -> bool:
        return bool(
            request.user
            and request.user.is_authenticated
            and getattr(obj, "sender_id", None) == request.user.id
        )
