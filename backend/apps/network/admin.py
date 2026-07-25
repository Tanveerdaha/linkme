"""Admin registration for network connections."""

from django.contrib import admin

from apps.network.models import Connection


@admin.register(Connection)
class ConnectionAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "sender",
        "receiver",
        "status",
        "created_at",
        "accepted_at",
    )
    list_filter = ("status", "created_at")
    search_fields = (
        "sender__username",
        "receiver__username",
        "sender__email",
        "receiver__email",
    )
    raw_id_fields = ("sender", "receiver")
    readonly_fields = ("created_at", "updated_at", "accepted_at")
