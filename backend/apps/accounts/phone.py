"""Phone number validation helpers (E.164)."""

from __future__ import annotations

import re

from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _

# E.164: + then country code and subscriber number (8–15 digits total after +).
E164_REGEX = re.compile(r"^\+[1-9]\d{7,14}$")


def normalize_phone_number(value: str | None) -> str:
    """Strip spaces/dashes/parentheses; keep leading + and digits."""
    if value is None:
        return ""
    raw = value.strip()
    if not raw:
        return ""
    # Allow local formatting then normalize.
    cleaned = re.sub(r"[\s\-().]", "", raw)
    if cleaned.startswith("00"):
        cleaned = f"+{cleaned[2:]}"
    if not cleaned.startswith("+") and cleaned.isdigit():
        # Assume missing + for convenience when user typed digits only with country code.
        cleaned = f"+{cleaned}"
    return cleaned


def validate_phone_number(value: str) -> str:
    """Validate and return normalized E.164 phone number."""
    phone = normalize_phone_number(value)
    if not phone:
        raise ValidationError(_("Phone number is required."), code="required")
    if not E164_REGEX.fullmatch(phone):
        raise ValidationError(
            _(
                "Enter a valid phone number in international format, "
                "including country code (e.g. +923001234567)."
            ),
            code="invalid_phone",
        )
    return phone
