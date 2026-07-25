"""
Custom permissions for the common app.

JWT authentication is configured globally; app-specific rules go here later.
"""

from rest_framework.permissions import BasePermission


class IsOwner(BasePermission):
    """Placeholder owner-check permission for future object-level auth."""

    def has_object_permission(self, request, view, obj) -> bool:
        owner = getattr(obj, "user", None) or getattr(obj, "owner", None)
        return bool(request.user and owner == request.user)
