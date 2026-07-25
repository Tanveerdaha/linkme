"""Custom user model for LinkMe authentication."""

import uuid

from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin
from django.db import models
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

from apps.accounts.managers import UserManager
from apps.accounts.validators import USERNAME_MAX_LENGTH, validate_username


class User(AbstractBaseUser, PermissionsMixin):
    """
    Email-based user account.

    Authentication uses email (USERNAME_FIELD). Username is a unique public handle.
    New signups start inactive until email verification succeeds.
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    email = models.EmailField(
        _("email address"),
        unique=True,
        db_index=True,
        null=True,
        blank=True,
    )
    phone_number = models.CharField(
        _("phone number"),
        max_length=20,
        unique=True,
        null=True,
        blank=True,
        db_index=True,
        help_text=_("E.164 format, e.g. +923001234567"),
    )
    username = models.CharField(
        _("username"),
        max_length=USERNAME_MAX_LENGTH,
        unique=True,
        db_index=True,
        validators=[validate_username],
    )
    first_name = models.CharField(_("first name"), max_length=150, blank=True)
    last_name = models.CharField(_("last name"), max_length=150, blank=True)

    class AuthProvider(models.TextChoices):
        EMAIL = "email", _("Email")
        GOOGLE = "google", _("Google")
        PHONE = "phone", _("Phone")

    google_id = models.CharField(
        max_length=255,
        unique=True,
        null=True,
        blank=True,
        db_index=True,
    )
    auth_provider = models.CharField(
        max_length=20,
        choices=AuthProvider.choices,
        default=AuthProvider.EMAIL,
        db_index=True,
    )

    is_active = models.BooleanField(default=False)
    is_verified = models.BooleanField(default=False)
    is_staff = models.BooleanField(default=False)

    # Phase 8 — suspension
    is_suspended = models.BooleanField(default=False, db_index=True)
    suspended_until = models.DateTimeField(null=True, blank=True)
    suspension_reason = models.TextField(blank=True)

    # Phase 8 — soft delete
    is_deleted = models.BooleanField(default=False, db_index=True)
    deleted_at = models.DateTimeField(null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    objects = UserManager()

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["username"]

    class Meta:
        ordering = ["-created_at"]
        verbose_name = _("user")
        verbose_name_plural = _("users")
        indexes = [
            models.Index(fields=["is_deleted", "is_active"]),
            models.Index(fields=["is_suspended", "suspended_until"]),
        ]

    def clean(self):
        super().clean()
        if self.email:
            self.email = self.__class__.objects.normalize_email(self.email).lower()
        if self.username:
            self.username = validate_username(self.username)

    def save(self, *args, **kwargs):
        if self.email:
            self.email = self.email.strip().lower()
        else:
            self.email = None
        if self.username:
            self.username = self.username.strip().lower()
        if self.phone_number:
            self.phone_number = self.phone_number.strip()
        else:
            self.phone_number = None
        super().save(*args, **kwargs)

    def __str__(self) -> str:
        return self.username or self.email or self.phone_number or str(self.id)

    @property
    def full_name(self) -> str:
        name = f"{self.first_name} {self.last_name}".strip()
        return name or self.username

    def is_currently_suspended(self) -> bool:
        """Return True when suspension is active (indefinite or not yet expired)."""
        if not self.is_suspended:
            return False
        if self.suspended_until is None:
            return True
        return self.suspended_until > timezone.now()
