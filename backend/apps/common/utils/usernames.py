"""Username normalization helpers.

Canonical form is lowercase with only ``a-z``, ``0-9``, ``_``, and ``.``.
"""

from __future__ import annotations

import re

ALLOWED_USERNAME_CHARS = frozenset("abcdefghijklmnopqrstuvwxyz0123456789_.")
_INVALID_CHAR_RE = re.compile(r"[^a-z0-9._]")


def normalize_username(username: str | None) -> str:
    """
    Normalize a username for comparison and storage.

    Rules:
    - trim surrounding whitespace
    - lowercase
    - remove characters outside ``a-z``, ``0-9``, ``_``, ``.``
    """
    if username is None:
        return ""
    lowered = username.strip().lower()
    return _INVALID_CHAR_RE.sub("", lowered)


def username_had_invalid_characters(raw: str | None) -> bool:
    """Return True when normalizing removed characters (invalid input)."""
    if raw is None:
        return False
    stripped = raw.strip().lower()
    return stripped != normalize_username(raw)
