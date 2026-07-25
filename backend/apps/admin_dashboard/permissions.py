"""Admin dashboard permission classes."""

from rest_framework.permissions import BasePermission

from apps.admin_dashboard.models import (
    AdminPermissionCode,
    AdminRole,
    ROLE_DEFAULT_PERMISSIONS,
)


def user_is_admin(user) -> bool:
    if not user or not getattr(user, "is_authenticated", False):
        return False
    if not getattr(user, "is_active", False):
        return False
    if getattr(user, "is_deleted", False):
        return False
    if hasattr(user, "is_currently_suspended") and user.is_currently_suspended():
        return False
    # Superusers and staff with an AdminRole (or legacy is_staff) may access.
    if getattr(user, "is_superuser", False):
        return True
    if getattr(user, "is_staff", False):
        return True
    return AdminRole.objects.filter(user=user).exists()


def get_admin_role(user) -> AdminRole | None:
    if not user or not getattr(user, "is_authenticated", False):
        return None
    try:
        return user.admin_role
    except AdminRole.DoesNotExist:
        return None
    except Exception:  # noqa: BLE001
        return AdminRole.objects.filter(user=user).first()


def user_has_admin_permission(user, code: str) -> bool:
    if not user_is_admin(user):
        return False
    if getattr(user, "is_superuser", False):
        return True

    role = get_admin_role(user)
    if role is not None:
        return role.has_permission(code)

    # Legacy staff without AdminRole: grant moderator defaults.
    if getattr(user, "is_staff", False):
        return code in ROLE_DEFAULT_PERMISSIONS.get(AdminRole.Role.MODERATOR, [])
    return False


class IsAdminUser(BasePermission):
    """Require an authenticated admin (staff / AdminRole / superuser)."""

    message = "Admin access required."

    def has_permission(self, request, view) -> bool:
        return user_is_admin(request.user)


class HasAdminPermission(BasePermission):
    """
    Require a specific admin permission code.

    Set ``required_admin_permission`` on the view, or
    ``required_admin_permissions`` (any of).
    """

    message = "You do not have permission to perform this admin action."

    def has_permission(self, request, view) -> bool:
        if not user_is_admin(request.user):
            return False

        codes = getattr(view, "required_admin_permissions", None)
        if codes:
            return any(user_has_admin_permission(request.user, c) for c in codes)

        code = getattr(view, "required_admin_permission", None)
        if code is None:
            # Fall back to dashboard view permission.
            code = AdminPermissionCode.VIEW_DASHBOARD
        return user_has_admin_permission(request.user, code)
