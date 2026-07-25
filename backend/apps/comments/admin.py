"""Admin registration for comments."""

from django.contrib import admin

from apps.comments.models import Comment


@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
    list_display = ("id", "author", "post", "parent", "status", "created_at")
    list_filter = ("status", "created_at")
    search_fields = ("content", "author__username", "author__email")
    raw_id_fields = ("author", "post", "parent")
    readonly_fields = ("created_at", "updated_at")
