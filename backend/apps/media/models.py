"""Media upload, storage, and processing models."""

import uuid

from django.core.validators import FileExtensionValidator
from django.db import models


def post_image_upload_to(instance, filename: str) -> str:
    ext = filename.rsplit(".", 1)[-1].lower()
    return f"posts/images/{instance.post_id}/{uuid.uuid4().hex}.{ext}"


def post_video_upload_to(instance, filename: str) -> str:
    ext = filename.rsplit(".", 1)[-1].lower()
    return f"posts/videos/{instance.post_id}/{uuid.uuid4().hex}.{ext}"


def post_thumbnail_upload_to(instance, filename: str) -> str:
    ext = filename.rsplit(".", 1)[-1].lower() if "." in filename else "jpg"
    return f"posts/thumbnails/{instance.post_id}/{uuid.uuid4().hex}.{ext}"


def post_media_upload_to(instance, filename: str) -> str:
    """Route uploads into images/ or videos/ based on media_type."""
    if instance.media_type == PostMedia.MediaType.VIDEO:
        return post_video_upload_to(instance, filename)
    return post_image_upload_to(instance, filename)


IMAGE_EXTENSIONS = ["jpg", "jpeg", "png", "webp"]
VIDEO_EXTENSIONS = ["mp4", "webm", "mov"]


class PostMedia(models.Model):
    """A media attachment belonging to a post."""

    class MediaType(models.TextChoices):
        IMAGE = "IMAGE", "Image"
        VIDEO = "VIDEO", "Video"

    class ProcessingStatus(models.TextChoices):
        PENDING = "PENDING", "Pending"
        PROCESSING = "PROCESSING", "Processing"
        READY = "READY", "Ready"
        FAILED = "FAILED", "Failed"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    post = models.ForeignKey(
        "posts.Post",
        on_delete=models.CASCADE,
        related_name="media",
    )
    file = models.FileField(
        upload_to=post_media_upload_to,
        validators=[
            FileExtensionValidator(
                allowed_extensions=IMAGE_EXTENSIONS + VIDEO_EXTENSIONS
            )
        ],
    )
    media_type = models.CharField(max_length=16, choices=MediaType.choices)
    thumbnail = models.ImageField(
        upload_to=post_thumbnail_upload_to,
        blank=True,
        null=True,
    )
    order = models.PositiveSmallIntegerField(default=0)
    processing_status = models.CharField(
        max_length=16,
        choices=ProcessingStatus.choices,
        default=ProcessingStatus.READY,
        db_index=True,
    )
    # Metadata populated on upload / async video processing.
    file_size = models.PositiveBigIntegerField(null=True, blank=True)
    width = models.PositiveIntegerField(null=True, blank=True)
    height = models.PositiveIntegerField(null=True, blank=True)
    duration = models.FloatField(null=True, blank=True)
    original_filename = models.CharField(max_length=255, blank=True)
    content_type = models.CharField(max_length=128, blank=True)
    error_message = models.CharField(max_length=500, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["order", "created_at"]
        verbose_name_plural = "post media"

    def __str__(self) -> str:
        return f"PostMedia({self.media_type}, {self.id})"
