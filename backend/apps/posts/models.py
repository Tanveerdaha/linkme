"""User-generated posts and content."""

import uuid

from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models
from django.utils import timezone
from django.utils.translation import gettext_lazy as _


class Post(models.Model):
    """A user post with optional media attachments."""

    class Visibility(models.TextChoices):
        PUBLIC = "PUBLIC", _("Public")
        CONNECTIONS_ONLY = "CONNECTIONS_ONLY", _("Connections only")
        PRIVATE = "PRIVATE", _("Private")

    class Status(models.TextChoices):
        DRAFT = "DRAFT", _("Draft")
        PUBLISHED = "PUBLISHED", _("Published")
        DELETED = "DELETED", _("Deleted")

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="posts",
    )
    content = models.TextField(blank=True, max_length=5000)
    visibility = models.CharField(
        max_length=32,
        choices=Visibility.choices,
        default=Visibility.PUBLIC,
        db_index=True,
    )
    status = models.CharField(
        max_length=32,
        choices=Status.choices,
        default=Status.PUBLISHED,
        db_index=True,
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    published_at = models.DateTimeField(null=True, blank=True, db_index=True)

    class Meta:
        ordering = ["-published_at", "-created_at"]
        indexes = [
            models.Index(fields=["status", "visibility", "-published_at"]),
            models.Index(fields=["author", "status", "-published_at"]),
            models.Index(fields=["created_at"]),
            models.Index(fields=["author", "status"]),
        ]

    def __str__(self) -> str:
        return f"Post({self.id}, @{self.author.username})"

    def clean(self):
        super().clean()
        content = (self.content or "").strip()
        if len(content) > 5000:
            raise ValidationError({"content": _("Content must be at most 5000 characters.")})

    def save(self, *args, **kwargs):
        if self.content:
            self.content = self.content.strip()
        if (
            self.status == self.Status.PUBLISHED
            and self.published_at is None
        ):
            self.published_at = timezone.now()
        super().save(*args, **kwargs)

    @property
    def is_public(self) -> bool:
        return (
            self.status == self.Status.PUBLISHED
            and self.visibility == self.Visibility.PUBLIC
        )
