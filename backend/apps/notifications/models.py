"""Notification persistence models."""

import uuid

from django.conf import settings
from django.db import models
from django.utils.translation import gettext_lazy as _


class Notification(models.Model):
    """A single in-app notification for a recipient."""

    class NotificationType(models.TextChoices):
        POST_REACTION = "POST_REACTION", _("Post reaction")
        POST_COMMENT = "POST_COMMENT", _("Post comment")
        COMMENT_REPLY = "COMMENT_REPLY", _("Comment reply")
        COMMENT_REACTION = "COMMENT_REACTION", _("Comment reaction")
        CONNECTION_REQUEST = "CONNECTION_REQUEST", _("Connection request")
        CONNECTION_ACCEPTED = "CONNECTION_ACCEPTED", _("Connection accepted")
        MESSAGE_RECEIVED = "MESSAGE_RECEIVED", _("Message received")
        ACCOUNT_EVENT = "ACCOUNT_EVENT", _("Account event")
        # Future-ready (not generated in Phase 7)
        MENTION = "MENTION", _("Mention")
        SHARE = "SHARE", _("Share")
        FOLLOW = "FOLLOW", _("Follow")

    class ObjectType(models.TextChoices):
        POST = "post", _("Post")
        COMMENT = "comment", _("Comment")
        CONNECTION = "connection", _("Connection")
        MESSAGE = "message", _("Message")
        CONVERSATION = "conversation", _("Conversation")
        USER = "user", _("User")
        ACCOUNT = "account", _("Account")

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    recipient = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="notifications",
    )
    sender = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="sent_notifications",
    )
    notification_type = models.CharField(
        max_length=32,
        choices=NotificationType.choices,
        db_index=True,
    )
    object_type = models.CharField(
        max_length=32,
        choices=ObjectType.choices,
        blank=True,
        default="",
    )
    object_id = models.CharField(max_length=128, blank=True, default="")
    message = models.CharField(max_length=500)
    is_read = models.BooleanField(default=False, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    read_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["recipient", "-created_at"]),
            models.Index(fields=["recipient", "is_read", "-created_at"]),
            models.Index(fields=["recipient", "notification_type"]),
            models.Index(fields=["object_type", "object_id"]),
        ]

    def __str__(self) -> str:
        return f"Notification({self.notification_type} → {self.recipient_id})"


class NotificationPreference(models.Model):
    """Per-user toggles for notification categories."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="notification_preferences",
    )
    post_reactions_enabled = models.BooleanField(default=True)
    comments_enabled = models.BooleanField(default=True)
    connection_enabled = models.BooleanField(default=True)
    messages_enabled = models.BooleanField(default=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name_plural = "notification preferences"

    def __str__(self) -> str:
        return f"NotificationPreference({self.user_id})"
