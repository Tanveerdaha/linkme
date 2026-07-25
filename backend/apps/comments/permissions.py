"""Permissions for the comments app."""

from rest_framework.permissions import SAFE_METHODS, BasePermission

from apps.posts.permissions import IsAuthenticatedVerified


class CanComment(IsAuthenticatedVerified):
    """Authenticated, verified users may create comments and replies."""


class IsCommentOwner(BasePermission):
    """Only the comment author may edit or soft-delete."""

    def has_object_permission(self, request, view, obj) -> bool:
        if request.method in SAFE_METHODS:
            return True
        return bool(
            request.user
            and request.user.is_authenticated
            and obj.author_id == request.user.id
        )
