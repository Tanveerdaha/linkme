"""Username and related field validators for LinkMe accounts."""

import re

from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _

from apps.common.utils.usernames import (
    normalize_username,
    username_had_invalid_characters,
)

USERNAME_REGEX = re.compile(r"^[a-z0-9._]+$")
RESERVED_USERNAMES = frozenset(
    {
        "admin",
        "support",
        "linkme",
        "root",
        "official",
    }
)
USERNAME_MIN_LENGTH = 3
USERNAME_MAX_LENGTH = 30


def validate_username(value: str) -> str:
    """
    Validate and normalize a username.

    Rules:
    - 3–30 characters
    - lowercase letters, numbers, underscore, period only
    - not a reserved name
    """
    if value is None:
        raise ValidationError(_("Username is required."), code="required")

    if username_had_invalid_characters(value):
        raise ValidationError(
            _(
                "Username may only contain lowercase letters, numbers, "
                "underscores, and periods."
            ),
            code="invalid_characters",
        )

    username = normalize_username(value)

    if len(username) < USERNAME_MIN_LENGTH or len(username) > USERNAME_MAX_LENGTH:
        raise ValidationError(
            _("Username must be between %(min)d and %(max)d characters.")
            % {"min": USERNAME_MIN_LENGTH, "max": USERNAME_MAX_LENGTH},
            code="invalid_length",
        )

    if not USERNAME_REGEX.fullmatch(username):
        raise ValidationError(
            _(
                "Username may only contain lowercase letters, numbers, "
                "underscores, and periods."
            ),
            code="invalid_characters",
        )

    if username in RESERVED_USERNAMES:
        raise ValidationError(
            _("This username is reserved and cannot be used."),
            code="reserved",
        )

    return username
