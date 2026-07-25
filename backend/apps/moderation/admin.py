from django.contrib import admin

from apps.moderation.models import (
    AuditLog,
    BlockedUser,
    DataExportRequest,
    ModerationAction,
    Report,
)


@admin.register(BlockedUser)
class BlockedUserAdmin(admin.ModelAdmin):
    list_display = ("blocker", "blocked_user", "reason", "created_at")
    search_fields = ("blocker__username", "blocked_user__username")


@admin.register(Report)
class ReportAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "content_type_label",
        "reason",
        "status",
        "reporter",
        "reported_user",
        "created_at",
    )
    list_filter = ("status", "reason", "content_type_label")
    search_fields = ("reporter__username", "reported_user__username", "description")


@admin.register(ModerationAction)
class ModerationActionAdmin(admin.ModelAdmin):
    list_display = ("action", "target_type", "target_id", "admin", "created_at")
    list_filter = ("action",)


@admin.register(AuditLog)
class AuditLogAdmin(admin.ModelAdmin):
    list_display = ("action", "user", "object_type", "object_id", "created_at")
    list_filter = ("action",)
    readonly_fields = ("user", "action", "object_type", "object_id", "metadata", "created_at")


@admin.register(DataExportRequest)
class DataExportRequestAdmin(admin.ModelAdmin):
    list_display = ("user", "status", "created_at", "completed_at", "expires_at")
    list_filter = ("status",)
