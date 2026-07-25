"""Private messaging models — direct conversations between connected users."""

import uuid

from django.conf import settings
from django.core.validators import FileExtensionValidator
from django.db import models
from django.utils.translation import gettext_lazy as _

from apps.messaging.validators import (
    MESSAGE_ALL_EXTENSIONS,
    validate_message_attachment,
)


def message_attachment_upload_to(instance, filename: str) -> str:
    ext = filename.rsplit(".", 1)[-1].lower() if "." in filename else "bin"
    return f"messages/{instance.conversation_id}/{uuid.uuid4().hex}.{ext}"


class Conversation(models.Model):
    """A private chat thread. Phase 6 supports DIRECT only; GROUP is reserved."""

    class ConversationType(models.TextChoices):
        DIRECT = "DIRECT", _("Direct")
        GROUP = "GROUP", _("Group")

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    conversation_type = models.CharField(
        max_length=16,
        choices=ConversationType.choices,
        default=ConversationType.DIRECT,
        db_index=True,
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True, db_index=True)
    last_message_at = models.DateTimeField(null=True, blank=True, db_index=True)

    class Meta:
        ordering = ["-last_message_at", "-updated_at"]
        indexes = [
            models.Index(fields=["-last_message_at"]),
            models.Index(fields=["-updated_at"]),
            models.Index(fields=["conversation_type", "-last_message_at"]),
        ]

    def __str__(self) -> str:
        return f"Conversation({self.id}, {self.conversation_type})"


class ConversationMember(models.Model):
    """Membership of a user in a conversation."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    conversation = models.ForeignKey(
        Conversation,
        on_delete=models.CASCADE,
        related_name="members",
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="conversation_memberships",
    )
    joined_at = models.DateTimeField(auto_now_add=True)
    last_read_at = models.DateTimeField(null=True, blank=True)
    is_muted = models.BooleanField(default=False)

    class Meta:
        ordering = ["joined_at"]
        constraints = [
            models.UniqueConstraint(
                fields=["conversation", "user"],
                name="unique_conversation_member",
            ),
        ]
        indexes = [
            models.Index(fields=["user", "conversation"]),
            models.Index(fields=["conversation", "last_read_at"]),
        ]

    def __str__(self) -> str:
        return f"Member({self.user_id} in {self.conversation_id})"


class Message(models.Model):
    """A message within a conversation. Soft-deleted via ``is_deleted``."""

    class MessageType(models.TextChoices):
        TEXT = "TEXT", _("Text")
        IMAGE = "IMAGE", _("Image")
        VIDEO = "VIDEO", _("Video")
        FILE = "FILE", _("File")
        VOICE = "VOICE", _("Voice")
        LINK = "LINK", _("Link")

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    conversation = models.ForeignKey(
        Conversation,
        on_delete=models.CASCADE,
        related_name="messages",
    )
    sender = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="sent_messages",
    )
    content = models.TextField(blank=True, max_length=5000)
    message_type = models.CharField(
        max_length=16,
        choices=MessageType.choices,
        default=MessageType.TEXT,
        db_index=True,
    )
    attachment = models.FileField(
        upload_to=message_attachment_upload_to,
        blank=True,
        null=True,
        validators=[
            FileExtensionValidator(allowed_extensions=MESSAGE_ALL_EXTENSIONS),
        ],
    )
    # Extra payload: link URL, file name, voice duration, etc.
    metadata = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_deleted = models.BooleanField(default=False, db_index=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["conversation", "-created_at"]),
            models.Index(fields=["sender", "-created_at"]),
            models.Index(fields=["conversation", "is_deleted", "-created_at"]),
        ]

    def __str__(self) -> str:
        return f"Message({self.id}, {self.message_type})"

    def clean(self):
        super().clean()
        if self.attachment and self.message_type in {
            self.MessageType.IMAGE,
            self.MessageType.VIDEO,
            self.MessageType.FILE,
            self.MessageType.VOICE,
        }:
            validate_message_attachment(self.attachment, self.message_type)


class MessageStatus(models.Model):
    """Delivery/read status of a message for a specific recipient."""

    class Status(models.TextChoices):
        SENT = "SENT", _("Sent")
        DELIVERED = "DELIVERED", _("Delivered")
        READ = "READ", _("Read")

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    message = models.ForeignKey(
        Message,
        on_delete=models.CASCADE,
        related_name="statuses",
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="message_statuses",
    )
    status = models.CharField(
        max_length=16,
        choices=Status.choices,
        default=Status.SENT,
        db_index=True,
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-updated_at"]
        constraints = [
            models.UniqueConstraint(
                fields=["message", "user"],
                name="unique_message_status_per_user",
            ),
        ]
        indexes = [
            models.Index(fields=["user", "status"]),
            models.Index(fields=["message", "status"]),
        ]

    def __str__(self) -> str:
        return f"MessageStatus({self.message_id} → {self.user_id}: {self.status})"
