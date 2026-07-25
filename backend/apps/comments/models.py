"""Comments and one-level replies on posts."""

import uuid

from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models
from django.utils.translation import gettext_lazy as _


class Comment(models.Model):
    """A comment or reply on a post. Soft-deleted via status."""

    class Status(models.TextChoices):
        ACTIVE = "ACTIVE", _("Active")
        DELETED = "DELETED", _("Deleted")

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="comments",
    )
    post = models.ForeignKey(
        "posts.Post",
        on_delete=models.CASCADE,
        related_name="comments",
    )
    parent = models.ForeignKey(
        "self",
        on_delete=models.CASCADE,
        related_name="replies",
        null=True,
        blank=True,
    )
    content = models.TextField(max_length=2000)
    status = models.CharField(
        max_length=32,
        choices=Status.choices,
        default=Status.ACTIVE,
        db_index=True,
    )
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["created_at"]
        indexes = [
            models.Index(fields=["post", "parent", "created_at"]),
            models.Index(fields=["post", "status", "created_at"]),
            models.Index(fields=["author", "created_at"]),
        ]

    def __str__(self) -> str:
        return f"Comment({self.id}, post={self.post_id})"

    @property
    def is_reply(self) -> bool:
        return self.parent_id is not None

    @property
    def is_active(self) -> bool:
        return self.status == self.Status.ACTIVE

    def clean(self):
        super().clean()
        content = (self.content or "").strip()
        if not content:
            raise ValidationError({"content": _("Comment content is required.")})
        if len(content) > 2000:
            raise ValidationError(
                {"content": _("Content must be at most 2000 characters.")}
            )

        if self.parent_id:
            parent = self.parent
            if parent is None:
                parent = (
                    Comment.objects.filter(pk=self.parent_id)
                    .only("id", "post_id", "parent_id", "status")
                    .first()
                )
            if parent is None:
                raise ValidationError({"parent": _("Parent comment not found.")})
            if parent.parent_id is not None:
                raise ValidationError(
                    {"parent": _("Replies to replies are not allowed.")}
                )
            if parent.post_id != self.post_id:
                raise ValidationError(
                    {"parent": _("Reply must belong to the same post.")}
                )

    def save(self, *args, **kwargs):
        if self.content:
            self.content = self.content.strip()
        self.full_clean()
        super().save(*args, **kwargs)
