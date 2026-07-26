"""Celery tasks for async media processing."""

from celery import shared_task


@shared_task(
    name="media.process_video",
    bind=True,
    max_retries=3,
    default_retry_delay=30,
    queue="media_processing",
)
def process_video_task(self, media_id: str) -> dict:
    """
    Process an uploaded video asynchronously.

    Flow: upload → PostMedia(PENDING) → this task → thumbnail + metadata → READY.
    """
    from apps.media.services import process_video

    result = process_video(media_id)
    if result.get("status") == "failed" and self.request.retries < self.max_retries:
        raise self.retry(exc=RuntimeError(result.get("error") or "processing failed"))
    return result


@shared_task(
    name="media.process_image",
    bind=True,
    max_retries=2,
    default_retry_delay=15,
    queue="media_processing",
)
def process_image_task(self, media_id: str) -> dict:
    """Generate thumbnails / finalize image metadata off the request path."""
    from apps.media.models import PostMedia
    from apps.media.services import _populate_image_metadata

    try:
        media = PostMedia.objects.get(pk=media_id)
    except PostMedia.DoesNotExist:
        return {"status": "missing", "media_id": media_id}

    if media.media_type != PostMedia.MediaType.IMAGE:
        return {"status": "skipped", "reason": "not_image"}

    try:
        _populate_image_metadata(media)
        return {"status": "ready", "media_id": media_id}
    except Exception as exc:
        if self.request.retries < self.max_retries:
            raise self.retry(exc=exc)
        media.processing_status = PostMedia.ProcessingStatus.FAILED
        media.error_message = str(exc)[:500]
        media.save(update_fields=["processing_status", "error_message"])
        return {"status": "failed", "media_id": media_id, "error": str(exc)}
