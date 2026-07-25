"""
Load environment-specific Django settings.

Set ENVIRONMENT (or DJANGO_ENV) to one of: development, staging, production.
Default: development.

Reads backend/.env early so ENVIRONMENT from the file is respected.
"""

import os
from pathlib import Path


def _load_env_file(path: Path) -> None:
    """Minimal KEY=VALUE loader (does not override existing os.environ)."""
    if not path.is_file():
        return
    try:
        for raw in path.read_text(encoding="utf-8").splitlines():
            line = raw.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, _, value = line.partition("=")
            key = key.strip()
            if not key or key in os.environ:
                continue
            value = value.strip().strip("'").strip('"')
            os.environ[key] = value
    except OSError:
        pass


_BASE_DIR = Path(__file__).resolve().parent.parent.parent
_load_env_file(_BASE_DIR / ".env")

_env = (
    (os.environ.get("ENVIRONMENT") or os.environ.get("DJANGO_ENV") or "development")
    .lower()
    .strip()
)

if _env in {"prod", "production"}:
    from config.settings.production import *  # noqa: F401,F403
elif _env in {"stage", "staging"}:
    from config.settings.staging import *  # noqa: F401,F403
else:
    from config.settings.development import *  # noqa: F401,F403
