"""Custom permissions for the profiles app."""

from rest_framework.permissions import SAFE_METHODS, BasePermission

from apps.profiles.models import Profile


class IsAuthenticatedUser(BasePermission):
    """Require an authenticated, active, verified user."""

    def has_permission(self, request, view) -> bool:
        user = request.user
        return bool(
            user
            and user.is_authenticated
            and getattr(user, "is_active", False)
            and getattr(user, "is_verified", False)
        )


class IsOwner(BasePermission):
    """Only the profile owner may update; anyone can read (when allowed by view)."""

    def has_object_permission(self, request, view, obj) -> bool:
        if request.method in SAFE_METHODS:
            return True
        owner = getattr(obj, "user", None)
        return bool(
            request.user
            and request.user.is_authenticated
            and owner == request.user
        )


class CanViewProfileContent(BasePermission):
    """
    Full profile content is visible when PUBLIC, or when the viewer is the owner.
    Private profiles expose limited identity only (handled in services/serializers).
    """

    def has_object_permission(self, request, view, obj: Profile) -> bool:
        if obj.profile_visibility == Profile.Visibility.PUBLIC:
            return True
        return bool(
            request.user
            and request.user.is_authenticated
            and obj.user_id == request.user.id
        )
