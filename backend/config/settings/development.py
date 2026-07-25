"""Development settings — local Docker / laptop."""

from config.settings.base import *  # noqa: F401,F403

DEBUG = True
ENVIRONMENT = "development"

# Convenient defaults for local compose; still overridable via env.
CORS_ALLOW_ALL_ORIGINS = False

# Email to console during local development.
EMAIL_BACKEND = env(  # noqa: F405
    "EMAIL_BACKEND",
    default="django.core.mail.backends.console.EmailBackend",
)

# Optional query profiling — enable with ENABLE_SILK=True / ENABLE_DEBUG_TOOLBAR=True
if env.bool("ENABLE_DEBUG_TOOLBAR", default=False):  # noqa: F405
    INSTALLED_APPS = list(INSTALLED_APPS) + ["debug_toolbar"]  # noqa: F405
    MIDDLEWARE = [  # noqa: F405
        "debug_toolbar.middleware.DebugToolbarMiddleware",
        *MIDDLEWARE,  # noqa: F405
    ]
    INTERNAL_IPS = ["127.0.0.1", "localhost"]

if env.bool("ENABLE_SILK", default=False):  # noqa: F405
    INSTALLED_APPS = list(INSTALLED_APPS) + ["silk"]  # noqa: F405
    MIDDLEWARE = [  # noqa: F405
        "silk.middleware.SilkyMiddleware",
        *MIDDLEWARE,  # noqa: F405
    ]

# Deliver notifications in-process when no Celery worker is running locally.
# Set NOTIFICATIONS_INLINE=false to exercise the real notifications queue.
NOTIFICATIONS_INLINE = env.bool("NOTIFICATIONS_INLINE", default=True)  # noqa: F405
