"""Privacy settings for platform visibility and interaction controls."""

import uuid

from django.conf import settings
from django.db import models
from django.utils.translation import gettext_lazy as _


class PrivacySetting(models.Model):
    """Per-user privacy preferences (source of truth for Phase 8)."""

    class ProfileVisibility(models.TextChoices):
        PUBLIC = "PUBLIC", _("Public")
        PRIVATE = "PRIVATE", _("Private")

    class PostVisibility(models.TextChoices):
        PUBLIC = "PUBLIC", _("Public")
        CONNECTIONS_ONLY = "CONNECTIONS_ONLY", _("Connections only")
        PRIVATE = "PRIVATE", _("Private")

    class ConnectionVisibility(models.TextChoices):
        PUBLIC = "PUBLIC", _("Public")
        CONNECTIONS_ONLY = "CONNECTIONS_ONLY", _("Connections only")
        PRIVATE = "PRIVATE", _("Private")

    class MessagePermission(models.TextChoices):
        CONNECTIONS_ONLY = "CONNECTIONS_ONLY", _("Connections only")
        NOBODY = "NOBODY", _("Nobody")

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="privacy_settings",
    )
    profile_visibility = models.CharField(
        max_length=16,
        choices=ProfileVisibility.choices,
        default=ProfileVisibility.PUBLIC,
        db_index=True,
    )
    post_visibility = models.CharField(
        max_length=32,
        choices=PostVisibility.choices,
        default=PostVisibility.PUBLIC,
    )
    connection_visibility = models.CharField(
        max_length=32,
        choices=ConnectionVisibility.choices,
        default=ConnectionVisibility.PUBLIC,
        db_index=True,
    )
    message_permission = models.CharField(
        max_length=32,
        choices=MessagePermission.choices,
        default=MessagePermission.CONNECTIONS_ONLY,
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-updated_at"]
        verbose_name = _("privacy setting")
        verbose_name_plural = _("privacy settings")

    def __str__(self) -> str:
        return f"PrivacySetting({self.user_id})"
