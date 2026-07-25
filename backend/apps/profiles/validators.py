"""Validators for profile media uploads."""

from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _

from apps.media.validators import verify_file_signature

MAX_IMAGE_SIZE_BYTES = 5 * 1024 * 1024  # 5 MB
ALLOWED_IMAGE_EXTENSIONS = {"jpg", "jpeg", "png", "webp"}
ALLOWED_IMAGE_MIMES = {"image/jpeg", "image/png", "image/webp"}


def validate_image_size(file_obj) -> None:
    """Reject uploaded images larger than 5 MB and verify type/signature."""
    filename = getattr(file_obj, "name", "") or ""
    content_type = (getattr(file_obj, "content_type", "") or "").split(";")[0].strip().lower()
    size = getattr(file_obj, "size", None)

    ext = filename.rsplit(".", 1)[-1].lower() if "." in filename else ""
    if ext and ext not in ALLOWED_IMAGE_EXTENSIONS:
        raise ValidationError(
            _("Allowed image types: jpg, jpeg, png, webp."),
            code="invalid_extension",
        )
    if content_type and content_type not in ALLOWED_IMAGE_MIMES:
        raise ValidationError(
            _("Allowed image types: jpg, jpeg, png, webp."),
            code="invalid_mime",
        )

    expected = content_type or {
        "jpg": "image/jpeg",
        "jpeg": "image/jpeg",
        "png": "image/png",
        "webp": "image/webp",
    }.get(ext, "image/jpeg")
    verify_file_signature(file_obj, expected)

    if size is not None and size > MAX_IMAGE_SIZE_BYTES:
        raise ValidationError(
            _("Image file size must not exceed 5 MB."),
            code="file_too_large",
        )
