"""Media attachment and video processing services."""

from __future__ import annotations

import json
import logging
import subprocess
import tempfile
from pathlib import Path

from django.core.files import File
from django.db import transaction
from rest_framework.exceptions import ValidationError

from apps.media.models import PostMedia
from apps.media.validators import validate_media_file

logger = logging.getLogger(__name__)


def attach_media_files(post, files) -> list[PostMedia]:
    """Validate and attach uploaded files to a post; enqueue video processing."""
    created: list[PostMedia] = []

    for index, uploaded in enumerate(files):
        try:
            media_type = validate_media_file(uploaded)
        except Exception as exc:
            message = getattr(exc, "messages", None)
            if message:
                raise ValidationError({"media": list(message)}) from exc
            detail = getattr(exc, "detail", None)
            if detail is not None:
                raise ValidationError({"media": detail}) from exc
            raise ValidationError({"media": [str(exc)]}) from exc

        processing = (
            PostMedia.ProcessingStatus.PENDING
            if media_type == PostMedia.MediaType.VIDEO
            else PostMedia.ProcessingStatus.PENDING
        )

        media = PostMedia(
            post=post,
            media_type=media_type,
            order=index,
            processing_status=processing,
            file_size=getattr(uploaded, "size", None),
            original_filename=getattr(uploaded, "name", "") or "",
            content_type=getattr(uploaded, "content_type", "") or "",
        )

        if media_type == PostMedia.MediaType.IMAGE:
            try:
                from apps.common.media_pipeline import optimize_image_file

                optimized, _ext, width, height = optimize_image_file(uploaded)
                media.file = optimized
                media.width = width
                media.height = height
                media.content_type = (
                    getattr(optimized, "content_type", "") or media.content_type
                )
                media.file_size = optimized.size
            except Exception:
                logger.exception("Image optimization failed; storing original")
                uploaded.seek(0)
                media.file = uploaded
        else:
            media.file = uploaded

        media.save()

        if media_type == PostMedia.MediaType.IMAGE:
            from apps.media.tasks import process_image_task

            transaction.on_commit(
                lambda media_id=str(media.id): process_image_task.delay(media_id)
            )
        else:
            from apps.media.tasks import process_video_task

            transaction.on_commit(
                lambda media_id=str(media.id): process_video_task.delay(media_id)
            )

        created.append(media)

    return created


def _populate_image_metadata(media: PostMedia) -> None:
    """Best-effort width/height + thumbnail using the media pipeline."""
    try:
        from apps.common.media_pipeline import generate_image_thumbnail

        media.file.open("rb")
        if not media.width or not media.height:
            from PIL import Image

            with Image.open(media.file) as img:
                media.width, media.height = img.size
            media.file.seek(0)

        thumb = generate_image_thumbnail(media.file)
        media.file.close()
        if thumb is not None:
            content, _tw, _th = thumb
            media.thumbnail.save(f"{media.id}_thumb.jpg", content, save=False)

        media.processing_status = PostMedia.ProcessingStatus.READY
        media.save(
            update_fields=[
                "width",
                "height",
                "thumbnail",
                "processing_status",
            ]
        )
    except Exception:
        logger.exception("Failed to finalize image metadata for %s", media.id)
        media.processing_status = PostMedia.ProcessingStatus.READY
        media.save(update_fields=["processing_status"])


def process_video(media_id: str) -> dict:
    """
    Validate video, generate a thumbnail with FFmpeg, and store metadata.

    Designed to run inside a Celery worker — do not block API requests.
    """
    try:
        media = PostMedia.objects.select_related("post").get(pk=media_id)
    except PostMedia.DoesNotExist:
        return {"status": "missing", "media_id": media_id}

    if media.media_type != PostMedia.MediaType.VIDEO:
        return {"status": "skipped", "reason": "not_video"}

    media.processing_status = PostMedia.ProcessingStatus.PROCESSING
    media.error_message = ""
    media.save(update_fields=["processing_status", "error_message"])

    try:
        with media.file.open("rb") as src, tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            ext = Path(media.original_filename or media.file.name).suffix or ".mp4"
            video_path = tmp_path / f"source{ext}"
            thumb_path = tmp_path / "thumb.jpg"

            with open(video_path, "wb") as out:
                for chunk in src.chunks():
                    out.write(chunk)

            duration, width, height = _probe_video(video_path)
            _extract_thumbnail(video_path, thumb_path)

            if thumb_path.exists() and thumb_path.stat().st_size > 0:
                with open(thumb_path, "rb") as thumb_file:
                    media.thumbnail.save(
                        f"{media.id}.jpg",
                        File(thumb_file),
                        save=False,
                    )

            media.duration = duration
            media.width = width
            media.height = height
            media.processing_status = PostMedia.ProcessingStatus.READY
            media.save(
                update_fields=[
                    "thumbnail",
                    "duration",
                    "width",
                    "height",
                    "processing_status",
                    "error_message",
                ]
            )

        return {
            "status": "ready",
            "media_id": media_id,
            "duration": duration,
            "width": width,
            "height": height,
        }
    except Exception as exc:
        logger.exception("Video processing failed for %s", media_id)
        media.processing_status = PostMedia.ProcessingStatus.FAILED
        media.error_message = str(exc)[:500]
        media.save(update_fields=["processing_status", "error_message"])
        return {"status": "failed", "media_id": media_id, "error": str(exc)}


def _probe_video(video_path: Path) -> tuple[float | None, int | None, int | None]:
    """Return (duration, width, height) using ffprobe."""
    try:
        result = subprocess.run(
            [
                "ffprobe",
                "-v",
                "error",
                "-select_streams",
                "v:0",
                "-show_entries",
                "stream=width,height:format=duration",
                "-of",
                "json",
                str(video_path),
            ],
            check=True,
            capture_output=True,
            text=True,
            timeout=60,
        )
        payload = json.loads(result.stdout or "{}")
        streams = payload.get("streams") or [{}]
        fmt = payload.get("format") or {}
        width = streams[0].get("width")
        height = streams[0].get("height")
        duration_raw = fmt.get("duration")
        duration = float(duration_raw) if duration_raw is not None else None
        return duration, width, height
    except FileNotFoundError:
        logger.warning("ffprobe not installed; skipping video probe")
        return None, None, None
    except Exception:
        logger.exception("ffprobe failed for %s", video_path)
        return None, None, None


def _extract_thumbnail(video_path: Path, thumb_path: Path) -> None:
    """Generate a JPEG thumbnail with ffmpeg."""
    try:
        subprocess.run(
            [
                "ffmpeg",
                "-y",
                "-ss",
                "1",
                "-i",
                str(video_path),
                "-frames:v",
                "1",
                "-q:v",
                "2",
                str(thumb_path),
            ],
            check=True,
            capture_output=True,
            timeout=120,
        )
    except FileNotFoundError as exc:
        logger.warning("ffmpeg not installed; cannot generate video thumbnail")
        raise RuntimeError(
            "FFmpeg is required for video thumbnail generation."
        ) from exc
    except subprocess.CalledProcessError:
        subprocess.run(
            [
                "ffmpeg",
                "-y",
                "-i",
                str(video_path),
                "-frames:v",
                "1",
                "-q:v",
                "2",
                str(thumb_path),
            ],
            check=True,
            capture_output=True,
            timeout=120,
        )
