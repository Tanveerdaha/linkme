"""Admin registration for notifications."""

from django.contrib import admin

from apps.notifications.models import Notification, NotificationPreference


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "recipient",
        "sender",
        "notification_type",
        "is_read",
        "created_at",
    )
    list_filter = ("notification_type", "is_read")
    search_fields = ("message", "recipient__username", "sender__username")
    raw_id_fields = ("recipient", "sender")


@admin.register(NotificationPreference)
class NotificationPreferenceAdmin(admin.ModelAdmin):
    list_display = (
        "user",
        "post_reactions_enabled",
        "comments_enabled",
        "connection_enabled",
        "messages_enabled",
    )
    raw_id_fields = ("user",)
