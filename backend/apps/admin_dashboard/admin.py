from django.contrib import admin

from apps.admin_dashboard.models import AdminExportRequest, AdminRole


@admin.register(AdminRole)
class AdminRoleAdmin(admin.ModelAdmin):
    list_display = ("user", "role", "created_at")
    list_filter = ("role",)
    search_fields = ("user__username", "user__email")
    raw_id_fields = ("user",)


@admin.register(AdminExportRequest)
class AdminExportRequestAdmin(admin.ModelAdmin):
    list_display = ("export_type", "format", "status", "requested_by", "created_at")
    list_filter = ("status", "export_type", "format")
