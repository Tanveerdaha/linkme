"""Admin registration for messaging models."""

from django.contrib import admin

from apps.messaging.models import (
    Conversation,
    ConversationMember,
    Message,
    MessageStatus,
)


class ConversationMemberInline(admin.TabularInline):
    model = ConversationMember
    extra = 0
    raw_id_fields = ("user",)


@admin.register(Conversation)
class ConversationAdmin(admin.ModelAdmin):
    list_display = ("id", "conversation_type", "last_message_at", "created_at")
    list_filter = ("conversation_type",)
    search_fields = ("id",)
    inlines = [ConversationMemberInline]


@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "conversation",
        "sender",
        "message_type",
        "is_deleted",
        "created_at",
    )
    list_filter = ("message_type", "is_deleted")
    search_fields = ("id", "content", "sender__username")
    raw_id_fields = ("conversation", "sender")


@admin.register(MessageStatus)
class MessageStatusAdmin(admin.ModelAdmin):
    list_display = ("id", "message", "user", "status", "updated_at")
    list_filter = ("status",)
    raw_id_fields = ("message", "user")
