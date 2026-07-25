"""Validators for messaging media uploads."""

from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _

MESSAGE_IMAGE_EXTENSIONS = ["jpg", "jpeg", "png", "webp"]
MESSAGE_VIDEO_EXTENSIONS = ["mp4", "webm", "mov"]
MESSAGE_FILE_EXTENSIONS = ["pdf", "doc", "docx"]
MESSAGE_VOICE_EXTENSIONS = ["webm", "mp4", "m4a", "ogg", "mp3"]

MESSAGE_ALL_EXTENSIONS = sorted(
    set(
        MESSAGE_IMAGE_EXTENSIONS
        + MESSAGE_VIDEO_EXTENSIONS
        + MESSAGE_FILE_EXTENSIONS
        + MESSAGE_VOICE_EXTENSIONS
    )
)

MESSAGE_IMAGE_MIME_TYPES = {
    "image/jpeg",
    "image/jpg",
    "image/png",
    "image/webp",
}
MESSAGE_VIDEO_MIME_TYPES = {
    "video/mp4",
    "video/webm",
    "video/quicktime",
}
MESSAGE_FILE_MIME_TYPES = {
    "application/pdf",
    "application/msword",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
}
MESSAGE_VOICE_MIME_TYPES = {
    "audio/webm",
    "audio/mp4",
    "audio/mpeg",
    "audio/ogg",
    "audio/x-m4a",
    "video/webm",  # browsers often record MediaRecorder as video/webm
}

MAX_IMAGE_BYTES = 10 * 1024 * 1024  # 10 MB
MAX_VIDEO_BYTES = 100 * 1024 * 1024  # 100 MB
MAX_FILE_BYTES = 25 * 1024 * 1024  # 25 MB
MAX_VOICE_BYTES = 10 * 1024 * 1024  # 10 MB

# Backwards-compatible aliases
MAX_MESSAGE_ATTACHMENT_BYTES = MAX_IMAGE_BYTES

TYPE_LIMITS = {
    "IMAGE": (MAX_IMAGE_BYTES, MESSAGE_IMAGE_EXTENSIONS, MESSAGE_IMAGE_MIME_TYPES),
    "VIDEO": (MAX_VIDEO_BYTES, MESSAGE_VIDEO_EXTENSIONS, MESSAGE_VIDEO_MIME_TYPES),
    "FILE": (MAX_FILE_BYTES, MESSAGE_FILE_EXTENSIONS, MESSAGE_FILE_MIME_TYPES),
    "VOICE": (MAX_VOICE_BYTES, MESSAGE_VOICE_EXTENSIONS, MESSAGE_VOICE_MIME_TYPES),
}


def _file_ext(file_obj) -> str:
    name = getattr(file_obj, "name", "") or ""
    if "." not in name:
        return ""
    return name.rsplit(".", 1)[-1].lower()


def validate_message_attachment(file_obj, message_type: str = "IMAGE") -> None:
    """Validate attachment size/MIME/extension for the given message type."""
    resolved = (message_type or "IMAGE").upper()
    if resolved not in TYPE_LIMITS:
        raise ValidationError(
            _("Unsupported attachment message type."),
            code="invalid_message_type",
        )

    max_bytes, extensions, mime_types = TYPE_LIMITS[resolved]
    size = getattr(file_obj, "size", None)
    if size is not None and size > max_bytes:
        mb = max_bytes // (1024 * 1024)
        raise ValidationError(
            _("Attachment must not exceed %(mb)s MB.") % {"mb": mb},
            code="file_too_large",
        )

    content_type = getattr(file_obj, "content_type", None)
    if content_type and content_type not in mime_types:
        raise ValidationError(
            _("File type is not allowed for %(kind)s messages.")
            % {"kind": resolved.lower()},
            code="invalid_mime_type",
        )

    ext = _file_ext(file_obj)
    if ext and ext not in extensions:
        raise ValidationError(
            _("Invalid file extension. Allowed: %(exts)s.")
            % {"exts": ", ".join(extensions)},
            code="invalid_extension",
        )


def infer_message_type_from_file(file_obj) -> str:
    """Best-effort type inference from extension/MIME."""
    ext = _file_ext(file_obj)
    content_type = (getattr(file_obj, "content_type", None) or "").lower()

    if ext in MESSAGE_IMAGE_EXTENSIONS or content_type in MESSAGE_IMAGE_MIME_TYPES:
        return "IMAGE"
    if ext in MESSAGE_VIDEO_EXTENSIONS or content_type in MESSAGE_VIDEO_MIME_TYPES:
        return "VIDEO"
    if ext in MESSAGE_FILE_EXTENSIONS or content_type in MESSAGE_FILE_MIME_TYPES:
        return "FILE"
    if ext in MESSAGE_VOICE_EXTENSIONS or content_type in MESSAGE_VOICE_MIME_TYPES:
        return "VOICE"
    return "FILE"
