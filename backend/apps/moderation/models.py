"""Trust & safety models: blocks, reports, moderation actions, audit logs."""

import uuid

from django.conf import settings
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import ValidationError
from django.db import models
from django.utils.translation import gettext_lazy as _


class BlockedUser(models.Model):
    """User A blocks User B — mutual interaction restrictions."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    blocker = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="blocks_initiated",
    )
    blocked_user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="blocks_received",
    )
    reason = models.CharField(max_length=255, blank=True)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        ordering = ["-created_at"]
        constraints = [
            models.UniqueConstraint(
                fields=["blocker", "blocked_user"],
                name="unique_block_pair",
            ),
            models.CheckConstraint(
                condition=~models.Q(blocker=models.F("blocked_user")),
                name="block_no_self",
            ),
        ]
        indexes = [
            models.Index(fields=["blocker", "-created_at"]),
            models.Index(fields=["blocked_user", "-created_at"]),
        ]

    def __str__(self) -> str:
        return f"Block({self.blocker_id} → {self.blocked_user_id})"

    def clean(self):
        super().clean()
        if self.blocker_id and self.blocked_user_id and self.blocker_id == self.blocked_user_id:
            raise ValidationError(_("You cannot block yourself."))


class Report(models.Model):
    """User-submitted report against a user or piece of content."""

    class ContentTypeChoice(models.TextChoices):
        USER = "USER", _("User")
        POST = "POST", _("Post")
        COMMENT = "COMMENT", _("Comment")
        MESSAGE = "MESSAGE", _("Message")

    class Reason(models.TextChoices):
        SPAM = "SPAM", _("Spam")
        HARASSMENT = "HARASSMENT", _("Harassment")
        HATE_SPEECH = "HATE_SPEECH", _("Hate speech")
        VIOLENCE = "VIOLENCE", _("Violence")
        NUDITY = "NUDITY", _("Nudity")
        FAKE_ACCOUNT = "FAKE_ACCOUNT", _("Fake account")
        OTHER = "OTHER", _("Other")

    class Status(models.TextChoices):
        PENDING = "PENDING", _("Pending")
        UNDER_REVIEW = "UNDER_REVIEW", _("Under review")
        RESOLVED = "RESOLVED", _("Resolved")
        REJECTED = "REJECTED", _("Rejected")

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    reporter = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="reports_filed",
    )
    reported_user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="reports_against",
    )
    content_type_label = models.CharField(
        max_length=16,
        choices=ContentTypeChoice.choices,
        db_index=True,
    )
    # Generic FK for polymorphic targets (post, comment, message, user).
    content_type = models.ForeignKey(
        ContentType,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
    )
    object_id = models.CharField(max_length=64, blank=True, db_index=True)
    content_object = GenericForeignKey("content_type", "object_id")

    reason = models.CharField(max_length=32, choices=Reason.choices, db_index=True)
    description = models.TextField(blank=True, max_length=2000)
    status = models.CharField(
        max_length=16,
        choices=Status.choices,
        default=Status.PENDING,
        db_index=True,
    )
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["status", "-created_at"]),
            models.Index(fields=["reporter", "-created_at"]),
            models.Index(fields=["content_type_label", "object_id"]),
        ]
        constraints = [
            models.UniqueConstraint(
                fields=["reporter", "content_type_label", "object_id", "reason"],
                condition=models.Q(status__in=["PENDING", "UNDER_REVIEW"]),
                name="unique_open_report",
            ),
        ]

    def __str__(self) -> str:
        return f"Report({self.content_type_label}:{self.object_id}, {self.status})"


class ModerationAction(models.Model):
    """Staff action taken against a user or content object."""

    class Action(models.TextChoices):
        WARNING = "WARNING", _("Warning")
        CONTENT_REMOVED = "CONTENT_REMOVED", _("Content removed")
        USER_SUSPENDED = "USER_SUSPENDED", _("User suspended")
        USER_BANNED = "USER_BANNED", _("User banned")

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    admin = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name="moderation_actions",
    )
    target_type = models.CharField(max_length=32, db_index=True)
    target_id = models.CharField(max_length=64, db_index=True)
    action = models.CharField(max_length=32, choices=Action.choices, db_index=True)
    reason = models.TextField(blank=True)
    report = models.ForeignKey(
        Report,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="actions",
    )
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["target_type", "target_id"]),
            models.Index(fields=["action", "-created_at"]),
        ]

    def __str__(self) -> str:
        return f"ModerationAction({self.action} on {self.target_type}:{self.target_id})"


class AuditLog(models.Model):
    """Immutable audit trail for security-sensitive events."""

    class Action(models.TextChoices):
        LOGIN = "LOGIN", _("Login")
        LOGOUT = "LOGOUT", _("Logout")
        PASSWORD_CHANGE = "PASSWORD_CHANGE", _("Password change")
        PROFILE_UPDATE = "PROFILE_UPDATE", _("Profile update")
        MODERATION_ACTION = "MODERATION_ACTION", _("Moderation action")
        ACCOUNT_DELETE = "ACCOUNT_DELETE", _("Account delete")
        ACCOUNT_RESTORE = "ACCOUNT_RESTORE", _("Account restore")
        REPORT_CREATED = "REPORT_CREATED", _("Report created")
        BLOCK_USER = "BLOCK_USER", _("Block user")
        UNBLOCK_USER = "UNBLOCK_USER", _("Unblock user")
        DATA_EXPORT = "DATA_EXPORT", _("Data export")
        PRIVACY_UPDATE = "PRIVACY_UPDATE", _("Privacy update")
        OTHER = "OTHER", _("Other")

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="audit_logs",
    )
    action = models.CharField(max_length=32, choices=Action.choices, db_index=True)
    object_type = models.CharField(max_length=64, blank=True)
    object_id = models.CharField(max_length=64, blank=True)
    metadata = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["user", "-created_at"]),
            models.Index(fields=["action", "-created_at"]),
        ]

    def __str__(self) -> str:
        return f"AuditLog({self.action}, {self.created_at})"


class DataExportRequest(models.Model):
    """Tracks async user data export jobs."""

    class Status(models.TextChoices):
        PENDING = "PENDING", _("Pending")
        PROCESSING = "PROCESSING", _("Processing")
        READY = "READY", _("Ready")
        FAILED = "FAILED", _("Failed")
        EXPIRED = "EXPIRED", _("Expired")

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="data_exports",
    )
    status = models.CharField(
        max_length=16,
        choices=Status.choices,
        default=Status.PENDING,
        db_index=True,
    )
    file = models.FileField(upload_to="exports/%Y/%m/", blank=True, null=True)
    error_message = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    expires_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self) -> str:
        return f"DataExportRequest({self.user_id}, {self.status})"
