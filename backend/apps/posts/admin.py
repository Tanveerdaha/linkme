"""Admin registration for posts."""

from django.contrib import admin

from apps.posts.models import Post


@admin.register(Post)
class PostAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "author",
        "visibility",
        "status",
        "published_at",
        "created_at",
    )
    list_filter = ("visibility", "status")
    search_fields = ("content", "author__username", "author__email")
    raw_id_fields = ("author",)
    readonly_fields = ("created_at", "updated_at", "published_at")
