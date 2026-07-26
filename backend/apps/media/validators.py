"""Upload validators for post media with MIME / signature checks."""

from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _

IMAGE_EXTENSIONS = {"jpg", "jpeg", "png", "webp"}
VIDEO_EXTENSIONS = {"mp4", "webm", "mov"}

IMAGE_MIME_TYPES = {"image/jpeg", "image/png", "image/webp"}
VIDEO_MIME_TYPES = {"video/mp4", "video/webm", "video/quicktime"}

MAX_IMAGE_SIZE_BYTES = 10 * 1024 * 1024  # 10 MB
MAX_VIDEO_SIZE_BYTES = 200 * 1024 * 1024  # 200 MB

# Block obvious executable / script uploads even if renamed.
BLOCKED_EXTENSIONS = {
    "exe",
    "bat",
    "cmd",
    "com",
    "msi",
    "scr",
    "js",
    "jar",
    "sh",
    "php",
    "py",
    "rb",
    "pl",
    "html",
    "htm",
    "svg",
}

# Magic-byte signatures (file header sniffing).
_SIGNATURES = {
    "image/jpeg": (b"\xff\xd8\xff",),
    "image/png": (b"\x89PNG\r\n\x1a\n",),
    "image/webp": (b"RIFF",),  # RIFF....WEBP
    "video/mp4": (b"ftyp",),  # typically at offset 4
    "video/webm": (b"\x1a\x45\xdf\xa3",),
}


def _extension(filename: str) -> str:
    if not filename or "." not in filename:
        return ""
    return filename.rsplit(".", 1)[-1].lower().strip()


def _read_header(file_obj, length: int = 32) -> bytes:
    pos = None
    try:
        pos = file_obj.tell()
    except Exception:  # noqa: BLE001
        pos = None
    try:
        header = file_obj.read(length) or b""
    finally:
        try:
            if pos is not None:
                file_obj.seek(pos)
            else:
                file_obj.seek(0)
        except Exception:  # noqa: BLE001
            pass
    return header


def verify_file_signature(file_obj, expected_mime: str) -> None:
    """Reject uploads whose magic bytes do not match the claimed type."""
    header = _read_header(file_obj, 64)
    if not header:
        return  # empty / unreadable — size checks still apply

    if expected_mime == "image/jpeg":
        if not header.startswith(b"\xff\xd8\xff"):
            raise ValidationError(_("File content does not match a JPEG image."))
    elif expected_mime == "image/png":
        if not header.startswith(b"\x89PNG\r\n\x1a\n"):
            raise ValidationError(_("File content does not match a PNG image."))
    elif expected_mime == "image/webp":
        if not (header.startswith(b"RIFF") and b"WEBP" in header[:16]):
            raise ValidationError(_("File content does not match a WebP image."))
    elif expected_mime == "video/mp4":
        if b"ftyp" not in header[:32]:
            raise ValidationError(_("File content does not match an MP4 video."))
    elif expected_mime == "video/webm":
        if not header.startswith(b"\x1a\x45\xdf\xa3"):
            raise ValidationError(_("File content does not match a WebM video."))
    elif expected_mime == "video/quicktime":
        if b"ftyp" not in header[:32] and b"moov" not in header[:64]:
            raise ValidationError(_("File content does not match a QuickTime video."))


def detect_media_type(filename: str, content_type: str = "") -> str:
    """Return IMAGE or VIDEO based on extension / MIME, or raise ValidationError."""
    ext = _extension(filename)
    if ext in BLOCKED_EXTENSIONS:
        raise ValidationError(_("Executable or script uploads are not allowed."))

    ctype = (content_type or "").split(";")[0].strip().lower()

    if ext in IMAGE_EXTENSIONS or ctype in IMAGE_MIME_TYPES:
        if ext and ext not in IMAGE_EXTENSIONS:
            raise ValidationError(_("Allowed image types: jpg, jpeg, png, webp."))
        if ctype and ctype not in IMAGE_MIME_TYPES:
            raise ValidationError(_("Allowed image types: jpg, jpeg, png, webp."))
        return "IMAGE"

    if ext in VIDEO_EXTENSIONS or ctype in VIDEO_MIME_TYPES:
        if ext and ext not in VIDEO_EXTENSIONS:
            raise ValidationError(_("Allowed video types: mp4, webm, mov."))
        if ctype and ctype not in VIDEO_MIME_TYPES:
            raise ValidationError(_("Allowed video types: mp4, webm, mov."))
        return "VIDEO"

    raise ValidationError(
        _(
            "Unsupported file type. Upload an image (jpg, png, webp) or video (mp4, webm, mov)."
        )
    )


def _expected_mime(filename: str, content_type: str, media_type: str) -> str:
    ctype = (content_type or "").split(";")[0].strip().lower()
    if ctype in IMAGE_MIME_TYPES or ctype in VIDEO_MIME_TYPES:
        return ctype
    ext = _extension(filename)
    mapping = {
        "jpg": "image/jpeg",
        "jpeg": "image/jpeg",
        "png": "image/png",
        "webp": "image/webp",
        "mp4": "video/mp4",
        "webm": "video/webm",
        "mov": "video/quicktime",
    }
    return mapping.get(ext, "image/jpeg" if media_type == "IMAGE" else "video/mp4")


def validate_media_file(file_obj) -> str:
    """
    Validate an uploaded file and return media type ("IMAGE" | "VIDEO").

    Checks extension, MIME type, magic-byte signature, and size limits.
    """
    filename = getattr(file_obj, "name", "") or ""
    content_type = getattr(file_obj, "content_type", "") or ""
    size = getattr(file_obj, "size", None)

    media_type = detect_media_type(filename, content_type)
    expected = _expected_mime(filename, content_type, media_type)
    verify_file_signature(file_obj, expected)

    if size is None:
        return media_type

    if media_type == "IMAGE" and size > MAX_IMAGE_SIZE_BYTES:
        raise ValidationError(_("Image file size must not exceed 10 MB."))
    if media_type == "VIDEO" and size > MAX_VIDEO_SIZE_BYTES:
        raise ValidationError(_("Video file size must not exceed 200 MB."))

    return media_type
