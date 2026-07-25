"""Custom permissions for moderation and staff tools."""

from rest_framework.permissions import BasePermission


class IsAuthenticatedVerified(BasePermission):
    """Require an authenticated, active, verified, non-deleted user."""

    def has_permission(self, request, view) -> bool:
        user = request.user
        if not (
            user
            and user.is_authenticated
            and getattr(user, "is_active", False)
            and getattr(user, "is_verified", False)
            and not getattr(user, "is_deleted", False)
        ):
            return False
        if hasattr(user, "is_currently_suspended") and user.is_currently_suspended():
            return False
        return True


class IsStaffModerator(BasePermission):
    """Staff-only access for moderation dashboard APIs."""

    def has_permission(self, request, view) -> bool:
        user = request.user
        return bool(
            user
            and user.is_authenticated
            and getattr(user, "is_staff", False)
            and getattr(user, "is_active", False)
            and not getattr(user, "is_deleted", False)
        )
