"""Custom permissions for the posts app."""

from rest_framework.permissions import SAFE_METHODS, BasePermission

from apps.posts.models import Post


class IsAuthenticatedVerified(BasePermission):
    """Require an authenticated, active, verified, non-suspended user."""

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


class IsPostOwner(BasePermission):
    """Only the post author may mutate the object."""

    def has_object_permission(self, request, view, obj) -> bool:
        if request.method in SAFE_METHODS:
            return True
        return bool(
            request.user
            and request.user.is_authenticated
            and obj.author_id == request.user.id
        )


class CanViewPost(BasePermission):
    """
    Visibility rules:

    - Soft-deleted posts are hidden from everyone (except staff later).
    - PUBLIC published posts: anyone (including guests) unless blocked.
    - CONNECTIONS_ONLY: accepted connections.
    - PRIVATE: owner only.
    """

    def has_object_permission(self, request, view, obj: Post) -> bool:
        from apps.privacy.services import can_view_post

        return can_view_post(post=obj, viewer=request.user)
