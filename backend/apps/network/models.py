"""Network connection models — LinkedIn-style mutual relationships."""

import uuid

from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models
from django.db.models import Q
from django.db.models.functions import Greatest, Least
from django.utils.translation import gettext_lazy as _


class Connection(models.Model):
    """
    A directed connection request that becomes mutual when ACCEPTED.

    Only one active relationship (PENDING / ACCEPTED / BLOCKED) may exist
    between a pair of users in either direction.
    """

    class Status(models.TextChoices):
        PENDING = "PENDING", _("Pending")
        ACCEPTED = "ACCEPTED", _("Accepted")
        REJECTED = "REJECTED", _("Rejected")
        CANCELLED = "CANCELLED", _("Cancelled")
        REMOVED = "REMOVED", _("Removed")
        BLOCKED = "BLOCKED", _("Blocked")

    ACTIVE_STATUSES = (Status.PENDING, Status.ACCEPTED, Status.BLOCKED)

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    sender = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="sent_connections",
    )
    receiver = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="received_connections",
    )
    status = models.CharField(
        max_length=16,
        choices=Status.choices,
        default=Status.PENDING,
        db_index=True,
    )
    message = models.CharField(max_length=300, blank=True)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)
    accepted_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["-updated_at"]
        indexes = [
            models.Index(fields=["sender", "status"]),
            models.Index(fields=["receiver", "status"]),
            models.Index(fields=["status", "-created_at"]),
            models.Index(fields=["sender", "receiver", "status"]),
        ]
        constraints = [
            models.CheckConstraint(
                condition=~Q(sender=models.F("receiver")),
                name="connection_no_self",
            ),
            models.UniqueConstraint(
                Least("sender", "receiver"),
                Greatest("sender", "receiver"),
                condition=Q(
                    status__in=["PENDING", "ACCEPTED", "BLOCKED"]
                ),
                name="unique_active_connection_pair",
            ),
        ]

    def __str__(self) -> str:
        return (
            f"Connection({self.sender_id} → {self.receiver_id}, {self.status})"
        )

    def clean(self):
        super().clean()
        if self.sender_id and self.receiver_id and self.sender_id == self.receiver_id:
            raise ValidationError(_("Cannot connect with yourself."))

    @property
    def is_active(self) -> bool:
        return self.status in self.ACTIVE_STATUSES
