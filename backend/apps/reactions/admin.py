"""Admin registration for reactions."""

from django.contrib import admin

from apps.reactions.models import Reaction


@admin.register(Reaction)
class ReactionAdmin(admin.ModelAdmin):
    list_display = ("id", "user", "reaction_type", "post", "comment", "created_at")
    list_filter = ("reaction_type", "created_at")
    search_fields = ("user__username", "user__email")
    raw_id_fields = ("user", "post", "comment")
    readonly_fields = ("created_at", "updated_at")
