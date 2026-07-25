"""Admin role and permission assignments for the LinkMe admin dashboard."""

import uuid

from django.conf import settings
from django.db import models
from django.utils.translation import gettext_lazy as _


class AdminPermissionCode:
    """Canonical permission strings stored on AdminRole.permissions."""

    VIEW_DASHBOARD = "VIEW_DASHBOARD"
    VIEW_USERS = "VIEW_USERS"
    MANAGE_USERS = "MANAGE_USERS"
    SUSPEND_USERS = "SUSPEND_USERS"
    DELETE_USERS = "DELETE_USERS"
    VIEW_CONTENT = "VIEW_CONTENT"
    REMOVE_CONTENT = "REMOVE_CONTENT"
    RESTORE_CONTENT = "RESTORE_CONTENT"
    VIEW_REPORTS = "VIEW_REPORTS"
    MANAGE_REPORTS = "MANAGE_REPORTS"
    VIEW_MODERATION = "VIEW_MODERATION"
    TAKE_MODERATION_ACTION = "TAKE_MODERATION_ACTION"
    VIEW_ANALYTICS = "VIEW_ANALYTICS"
    VIEW_AUDIT = "VIEW_AUDIT"
    EXPORT_DATA = "EXPORT_DATA"
    MANAGE_ADMINS = "MANAGE_ADMINS"

    ALL = [
        VIEW_DASHBOARD,
        VIEW_USERS,
        MANAGE_USERS,
        SUSPEND_USERS,
        DELETE_USERS,
        VIEW_CONTENT,
        REMOVE_CONTENT,
        RESTORE_CONTENT,
        VIEW_REPORTS,
        MANAGE_REPORTS,
        VIEW_MODERATION,
        TAKE_MODERATION_ACTION,
        VIEW_ANALYTICS,
        VIEW_AUDIT,
        EXPORT_DATA,
        MANAGE_ADMINS,
    ]


ROLE_DEFAULT_PERMISSIONS = {
    "SUPER_ADMIN": list(AdminPermissionCode.ALL),
    "MODERATOR": [
        AdminPermissionCode.VIEW_DASHBOARD,
        AdminPermissionCode.VIEW_USERS,
        AdminPermissionCode.SUSPEND_USERS,
        AdminPermissionCode.VIEW_CONTENT,
        AdminPermissionCode.REMOVE_CONTENT,
        AdminPermissionCode.RESTORE_CONTENT,
        AdminPermissionCode.VIEW_REPORTS,
        AdminPermissionCode.MANAGE_REPORTS,
        AdminPermissionCode.VIEW_MODERATION,
        AdminPermissionCode.TAKE_MODERATION_ACTION,
        AdminPermissionCode.VIEW_AUDIT,
    ],
    "SUPPORT_ADMIN": [
        AdminPermissionCode.VIEW_DASHBOARD,
        AdminPermissionCode.VIEW_USERS,
        AdminPermissionCode.MANAGE_USERS,
        AdminPermissionCode.SUSPEND_USERS,
        AdminPermissionCode.VIEW_CONTENT,
        AdminPermissionCode.VIEW_REPORTS,
        AdminPermissionCode.VIEW_MODERATION,
        AdminPermissionCode.VIEW_AUDIT,
    ],
    "ANALYST": [
        AdminPermissionCode.VIEW_DASHBOARD,
        AdminPermissionCode.VIEW_USERS,
        AdminPermissionCode.VIEW_CONTENT,
        AdminPermissionCode.VIEW_REPORTS,
        AdminPermissionCode.VIEW_ANALYTICS,
        AdminPermissionCode.VIEW_AUDIT,
        AdminPermissionCode.EXPORT_DATA,
    ],
}


class AdminRole(models.Model):
    """Assigns an admin role and permission set to a staff user."""

    class Role(models.TextChoices):
        SUPER_ADMIN = "SUPER_ADMIN", _("Super admin")
        MODERATOR = "MODERATOR", _("Moderator")
        SUPPORT_ADMIN = "SUPPORT_ADMIN", _("Support admin")
        ANALYST = "ANALYST", _("Analyst")

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="admin_role",
    )
    role = models.CharField(max_length=32, choices=Role.choices, db_index=True)
    permissions = models.JSONField(default=list, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["role", "-created_at"]),
        ]

    def __str__(self) -> str:
        return f"AdminRole({self.user_id}, {self.role})"

    def save(self, *args, **kwargs):
        if not self.permissions:
            self.permissions = list(ROLE_DEFAULT_PERMISSIONS.get(self.role, []))
        super().save(*args, **kwargs)

    def has_permission(self, code: str) -> bool:
        if self.role == self.Role.SUPER_ADMIN:
            return True
        return code in (self.permissions or [])


class AdminExportRequest(models.Model):
    """Tracks async admin CSV/JSON export jobs."""

    class ExportType(models.TextChoices):
        USERS = "USERS", _("Users")
        REPORTS = "REPORTS", _("Reports")
        MODERATION = "MODERATION", _("Moderation history")
        AUDIT = "AUDIT", _("Audit logs")
        ACTIVITY = "ACTIVITY", _("User activity")

    class Format(models.TextChoices):
        CSV = "CSV", _("CSV")
        JSON = "JSON", _("JSON")

    class Status(models.TextChoices):
        PENDING = "PENDING", _("Pending")
        PROCESSING = "PROCESSING", _("Processing")
        READY = "READY", _("Ready")
        FAILED = "FAILED", _("Failed")

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    requested_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="admin_exports",
    )
    export_type = models.CharField(max_length=32, choices=ExportType.choices)
    format = models.CharField(max_length=8, choices=Format.choices, default=Format.CSV)
    status = models.CharField(
        max_length=16,
        choices=Status.choices,
        default=Status.PENDING,
        db_index=True,
    )
    file = models.FileField(upload_to="admin_exports/%Y/%m/", blank=True, null=True)
    filters = models.JSONField(default=dict, blank=True)
    error_message = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self) -> str:
        return f"AdminExport({self.export_type}, {self.status})"
