"""Video optimization helpers (multi-resolution + thumbnail via FFmpeg)."""

from __future__ import annotations

import logging
import subprocess
from pathlib import Path

logger = logging.getLogger(__name__)

# Target ladder for progressive delivery (height, video bitrate).
VIDEO_LADDER = (
    (720, "2500k"),
    (480, "1200k"),
    (360, "800k"),
)


def extract_thumbnail(
    video_path: Path, thumb_path: Path, *, seek_seconds: float = 1.0
) -> None:
    """Generate a JPEG thumbnail from a video file."""
    try:
        subprocess.run(
            [
                "ffmpeg",
                "-y",
                "-ss",
                str(seek_seconds),
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


def transcode_resolution(
    video_path: Path,
    output_path: Path,
    *,
    height: int,
    bitrate: str,
) -> bool:
    """
    Produce a single ladder rung. Returns False when FFmpeg is unavailable.
    Non-fatal — original upload remains the source of truth.
    """
    try:
        subprocess.run(
            [
                "ffmpeg",
                "-y",
                "-i",
                str(video_path),
                "-vf",
                f"scale=-2:{height}",
                "-c:v",
                "libx264",
                "-b:v",
                bitrate,
                "-c:a",
                "aac",
                "-b:a",
                "128k",
                "-movflags",
                "+faststart",
                str(output_path),
            ],
            check=True,
            capture_output=True,
            timeout=600,
        )
        return output_path.exists() and output_path.stat().st_size > 0
    except FileNotFoundError:
        logger.warning("ffmpeg not installed; skipping transcode to %sp", height)
        return False
    except Exception:
        logger.exception("Failed to transcode video to %sp", height)
        return False
