"""URL routes for the messaging app — mounted at /api/v1/messages/."""

from django.urls import path

from apps.messaging.views import (
    ConversationDetailView,
    ConversationListCreateView,
    ConversationMessagesView,
    ConversationMuteView,
    MessageDeleteView,
)

app_name = "messaging"

urlpatterns = [
    path(
        "conversations/",
        ConversationListCreateView.as_view(),
        name="conversation-list",
    ),
    path(
        "conversations/<uuid:conversation_id>/",
        ConversationDetailView.as_view(),
        name="conversation-detail",
    ),
    path(
        "conversations/<uuid:conversation_id>/mute/",
        ConversationMuteView.as_view(),
        name="conversation-mute",
    ),
    path(
        "conversations/<uuid:conversation_id>/messages/",
        ConversationMessagesView.as_view(),
        name="conversation-messages",
    ),
    path(
        "<uuid:message_id>/",
        MessageDeleteView.as_view(),
        name="message-delete",
    ),
]
