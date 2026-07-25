"""Custom permissions for the accounts app."""

from rest_framework.permissions import BasePermission


class IsAuthenticatedUser(BasePermission):
    """Require a verified, active authenticated user."""

    def has_permission(self, request, view) -> bool:
        user = request.user
        return bool(
            user
            and user.is_authenticated
            and getattr(user, "is_active", False)
            and getattr(user, "is_verified", False)
        )


class IsOwner(BasePermission):
    """Object-level permission: only the owner may mutate the object."""

    def has_object_permission(self, request, view, obj) -> bool:
        owner = getattr(obj, "user", None) or getattr(obj, "owner", None)
        if owner is None and hasattr(obj, "id"):
            # Allow comparing User instances directly.
            owner = obj
        return bool(
            request.user and request.user.is_authenticated and owner == request.user
        )
