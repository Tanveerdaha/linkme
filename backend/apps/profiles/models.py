"""User profile models."""

import uuid

from django.conf import settings
from django.core.validators import FileExtensionValidator
from django.db import models

from apps.profiles.validators import validate_image_size


def avatar_upload_to(instance, filename: str) -> str:
    ext = filename.rsplit(".", 1)[-1].lower()
    return f"profiles/avatars/{instance.user_id}/{uuid.uuid4().hex}.{ext}"


def cover_upload_to(instance, filename: str) -> str:
    ext = filename.rsplit(".", 1)[-1].lower()
    return f"profiles/covers/{instance.user_id}/{uuid.uuid4().hex}.{ext}"


IMAGE_EXTENSIONS = ["jpg", "jpeg", "png", "webp"]


class Profile(models.Model):
    """One-to-one public profile for a LinkMe user."""

    class Visibility(models.TextChoices):
        PUBLIC = "PUBLIC", "Public"
        PRIVATE = "PRIVATE", "Private"

    class ConnectionVisibility(models.TextChoices):
        PUBLIC = "PUBLIC", "Public"
        PRIVATE = "PRIVATE", "Private"
        CONNECTIONS_ONLY = "CONNECTIONS_ONLY", "Connections only"

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="profile",
    )
    avatar = models.ImageField(
        upload_to=avatar_upload_to,
        blank=True,
        null=True,
        validators=[
            FileExtensionValidator(allowed_extensions=IMAGE_EXTENSIONS),
            validate_image_size,
        ],
    )
    cover_image = models.ImageField(
        upload_to=cover_upload_to,
        blank=True,
        null=True,
        validators=[
            FileExtensionValidator(allowed_extensions=IMAGE_EXTENSIONS),
            validate_image_size,
        ],
    )
    bio = models.TextField(blank=True, max_length=2000)
    headline = models.CharField(blank=True, max_length=200)
    location = models.CharField(blank=True, max_length=120)
    website = models.URLField(blank=True, max_length=300)
    interests = models.JSONField(default=list, blank=True)
    pronouns = models.CharField(blank=True, max_length=50)
    birth_date = models.DateField(null=True, blank=True)
    social_links = models.JSONField(default=dict, blank=True)
    profile_visibility = models.CharField(
        max_length=16,
        choices=Visibility.choices,
        default=Visibility.PUBLIC,
        db_index=True,
    )
    connection_visibility = models.CharField(
        max_length=32,
        choices=ConnectionVisibility.choices,
        default=ConnectionVisibility.PUBLIC,
        db_index=True,
        help_text="Who can see this user's connections list.",
    )
    # Foundation for future analytics; incremented in a later phase.
    profile_views = models.PositiveIntegerField(default=0)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["profile_visibility", "-updated_at"]),
            models.Index(fields=["location"]),
        ]

    def __str__(self) -> str:
        return f"Profile({self.user.username})"

    @property
    def is_public(self) -> bool:
        return self.profile_visibility == self.Visibility.PUBLIC


class ProfileSection(models.Model):
    """
    Modular profile sections.

    MVP types: ABOUT, INTERESTS, ACTIVITY, MEDIA.
    Future: EXPERIENCE, EDUCATION, PROJECTS.
    """

    class SectionType(models.TextChoices):
        ABOUT = "ABOUT", "About"
        INTERESTS = "INTERESTS", "Interests"
        ACTIVITY = "ACTIVITY", "Activity"
        MEDIA = "MEDIA", "Media"
        EXPERIENCE = "EXPERIENCE", "Experience"
        EDUCATION = "EDUCATION", "Education"
        PROJECTS = "PROJECTS", "Projects"

    class Visibility(models.TextChoices):
        PUBLIC = "PUBLIC", "Public"
        PRIVATE = "PRIVATE", "Private"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    profile = models.ForeignKey(
        Profile,
        on_delete=models.CASCADE,
        related_name="sections",
    )
    section_type = models.CharField(max_length=32, choices=SectionType.choices)
    content = models.JSONField(default=dict, blank=True)
    order = models.PositiveSmallIntegerField(default=0)
    visibility = models.CharField(
        max_length=16,
        choices=Visibility.choices,
        default=Visibility.PUBLIC,
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["order", "created_at"]
        constraints = [
            models.UniqueConstraint(
                fields=["profile", "section_type"],
                name="unique_profile_section_type",
            ),
        ]
        indexes = [
            models.Index(fields=["profile", "order"]),
        ]

    def __str__(self) -> str:
        return f"ProfileSection({self.section_type}, profile={self.profile_id})"
