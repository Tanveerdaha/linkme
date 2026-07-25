"""Privacy permission helpers."""

from rest_framework.permissions import BasePermission


class IsAuthenticatedVerified(BasePermission):
    def has_permission(self, request, view) -> bool:
        user = request.user
        return bool(
            user
            and user.is_authenticated
            and getattr(user, "is_active", False)
            and getattr(user, "is_verified", False)
            and not getattr(user, "is_deleted", False)
        )
