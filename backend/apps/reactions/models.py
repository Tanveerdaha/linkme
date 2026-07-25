"""Reactions (hearts) on posts and comments."""

import uuid

from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models
from django.db.models import Q
from django.utils.translation import gettext_lazy as _


class Reaction(models.Model):
    """A user's reaction to a post or comment. MVP supports HEART only."""

    class ReactionType(models.TextChoices):
        HEART = "HEART", _("Heart")
        # Future: LIKE, LOVE, CELEBRATE, SUPPORT, FUNNY

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="reactions",
    )
    post = models.ForeignKey(
        "posts.Post",
        on_delete=models.CASCADE,
        related_name="reactions",
        null=True,
        blank=True,
    )
    comment = models.ForeignKey(
        "comments.Comment",
        on_delete=models.CASCADE,
        related_name="reactions",
        null=True,
        blank=True,
    )
    reaction_type = models.CharField(
        max_length=32,
        choices=ReactionType.choices,
        default=ReactionType.HEART,
        db_index=True,
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]
        constraints = [
            models.CheckConstraint(
                condition=(
                    (Q(post__isnull=False) & Q(comment__isnull=True))
                    | (Q(post__isnull=True) & Q(comment__isnull=False))
                ),
                name="reaction_exactly_one_target",
            ),
            models.UniqueConstraint(
                fields=["user", "post"],
                condition=Q(post__isnull=False),
                name="unique_user_post_reaction",
            ),
            models.UniqueConstraint(
                fields=["user", "comment"],
                condition=Q(comment__isnull=False),
                name="unique_user_comment_reaction",
            ),
        ]
        indexes = [
            models.Index(fields=["post", "reaction_type"]),
            models.Index(fields=["comment", "reaction_type"]),
            models.Index(fields=["user", "created_at"]),
        ]

    def __str__(self) -> str:
        target = (
            f"post={self.post_id}" if self.post_id else f"comment={self.comment_id}"
        )
        return f"Reaction({self.reaction_type}, {target}, user={self.user_id})"

    def clean(self):
        super().clean()
        has_post = self.post_id is not None
        has_comment = self.comment_id is not None
        if has_post == has_comment:
            raise ValidationError(
                _("Reaction must target exactly one of post or comment.")
            )
        if self.reaction_type != self.ReactionType.HEART:
            raise ValidationError(
                {"reaction_type": _("Only HEART reactions are supported.")}
            )

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)
