"""Admin registration for media."""

from django.contrib import admin

from apps.media.models import PostMedia


@admin.register(PostMedia)
class PostMediaAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "post",
        "media_type",
        "processing_status",
        "order",
        "created_at",
    )
    list_filter = ("media_type", "processing_status")
    raw_id_fields = ("post",)
    readonly_fields = ("created_at",)
