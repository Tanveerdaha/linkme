"""Media optimization pipeline — images (WebP/thumbnails) and video processing."""

from __future__ import annotations

import io
import logging
from pathlib import Path

from django.core.files.base import ContentFile

logger = logging.getLogger(__name__)

# Max edge length for feed-ready images.
IMAGE_MAX_EDGE = 1920
THUMBNAIL_EDGE = 480
WEBP_QUALITY = 82
JPEG_QUALITY = 85


def optimize_image_file(uploaded_file) -> tuple[ContentFile, str, int, int]:
    """
    Resize, compress, and convert an uploaded image to WebP when possible.

    Returns (content_file, extension, width, height).
    Falls back to JPEG when WebP encoding is unavailable.
    """
    from PIL import Image, ImageOps

    uploaded_file.seek(0)
    with Image.open(uploaded_file) as img:
        img = ImageOps.exif_transpose(img)
        img = img.convert("RGB") if img.mode not in ("RGB", "RGBA") else img
        width, height = img.size
        max_edge = max(width, height)
        if max_edge > IMAGE_MAX_EDGE:
            scale = IMAGE_MAX_EDGE / max_edge
            img = img.resize(
                (max(1, int(width * scale)), max(1, int(height * scale))),
                Image.Resampling.LANCZOS,
            )
            width, height = img.size

        buffer = io.BytesIO()
        name = Path(getattr(uploaded_file, "name", "image.jpg")).stem or "image"
        try:
            save_kwargs = {"quality": WEBP_QUALITY, "method": 4}
            if img.mode == "RGBA":
                img.save(buffer, format="WEBP", **save_kwargs)
            else:
                img.convert("RGB").save(buffer, format="WEBP", **save_kwargs)
            ext = "webp"
            content_type = "image/webp"
        except Exception:
            buffer = io.BytesIO()
            img.convert("RGB").save(
                buffer, format="JPEG", quality=JPEG_QUALITY, optimize=True
            )
            ext = "jpg"
            content_type = "image/jpeg"

        buffer.seek(0)
        content = ContentFile(buffer.read(), name=f"{name}.{ext}")
        content.content_type = content_type  # type: ignore[attr-defined]
        return content, ext, width, height


def generate_image_thumbnail(source_file) -> tuple[ContentFile, int, int] | None:
    """Create a small JPEG thumbnail for gallery / feed previews."""
    from PIL import Image, ImageOps

    try:
        source_file.seek(0)
        with Image.open(source_file) as img:
            img = ImageOps.exif_transpose(img)
            img = img.convert("RGB")
            img.thumbnail((THUMBNAIL_EDGE, THUMBNAIL_EDGE), Image.Resampling.LANCZOS)
            width, height = img.size
            buffer = io.BytesIO()
            img.save(buffer, format="JPEG", quality=80, optimize=True)
            buffer.seek(0)
            return ContentFile(buffer.read(), name="thumb.jpg"), width, height
    except Exception:
        logger.exception("Failed to generate image thumbnail")
        return None


def build_cdn_cache_headers(*, private: bool = False) -> dict:
    """Cache-Control headers for CDN / object storage."""
    if private:
        return {"CacheControl": "private, max-age=3600"}
    return {"CacheControl": "public, max-age=31536000, immutable"}
