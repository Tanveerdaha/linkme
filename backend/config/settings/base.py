"""
Django base settings for LinkMe.

Environment-specific modules (development / staging / production) import from here.
Secrets and connection strings come from environment variables.
"""

from datetime import timedelta
from pathlib import Path

import environ

BASE_DIR = Path(__file__).resolve().parent.parent.parent

env = environ.Env(
    DEBUG=(bool, False),
    ALLOWED_HOSTS=(list, ["localhost", "127.0.0.1"]),
    CORS_ALLOWED_ORIGINS=(list, ["http://localhost:3000"]),
    ENVIRONMENT=(str, "development"),
    USE_S3=(bool, False),
    SENTRY_DSN=(str, ""),
    REDIS_CACHE_URL=(str, ""),
    REDIS_CELERY_URL=(str, ""),
    REDIS_CHANNELS_URL=(str, ""),
    REDIS_BLOOM_ENABLED=(bool, True),
    REDIS_HOST=(str, ""),
    REDIS_PORT=(int, 6379),
    REDIS_PASSWORD=(str, ""),
)

# Load .env when present (local / docker compose bind mounts).
environ.Env.read_env(BASE_DIR / ".env")

SECRET_KEY = env("SECRET_KEY")
DEBUG = env("DEBUG")
ALLOWED_HOSTS = env("ALLOWED_HOSTS")
ENVIRONMENT = env("ENVIRONMENT")

DJANGO_APPS = [
    "daphne",
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "django.contrib.postgres",
]

THIRD_PARTY_APPS = [
    "rest_framework",
    "rest_framework_simplejwt",
    "rest_framework_simplejwt.token_blacklist",
    "drf_spectacular",
    "corsheaders",
    "channels",
]

LOCAL_APPS = [
    "apps.accounts",
    "apps.profiles",
    "apps.posts",
    "apps.comments",
    "apps.reactions",
    "apps.network",
    "apps.messaging",
    "apps.notifications",
    "apps.feed",
    "apps.media",
    "apps.moderation",
    "apps.privacy",
    "apps.admin_dashboard",
    "apps.common",
]

_APP_CONFIG_MAP = {
    "apps.profiles": "apps.profiles.apps.ProfilesConfig",
    "apps.notifications": "apps.notifications.apps.NotificationsConfig",
    "apps.privacy": "apps.privacy.apps.PrivacyConfig",
    "apps.moderation": "apps.moderation.apps.ModerationConfig",
    "apps.admin_dashboard": "apps.admin_dashboard.apps.AdminDashboardConfig",
}

INSTALLED_APPS = [
    _APP_CONFIG_MAP.get(app, app)
    for app in (DJANGO_APPS + THIRD_PARTY_APPS + LOCAL_APPS)
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "corsheaders.middleware.CorsMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    "apps.common.middleware.SecurityHeadersMiddleware",
    "apps.common.middleware.RequestLoggingMiddleware",
]

ROOT_URLCONF = "config.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "config.wsgi.application"
ASGI_APPLICATION = "config.asgi.application"

# ---------------------------------------------------------------------------
# Database — PostgreSQL (linkme_db); production routes via PgBouncer
# ---------------------------------------------------------------------------
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": env("DATABASE_NAME", default="linkme_db"),
        "USER": env("DATABASE_USER", default="linkme"),
        "PASSWORD": env("DATABASE_PASSWORD"),
        "HOST": env("DATABASE_HOST", default="localhost"),
        "PORT": env("DATABASE_PORT", default="5432"),
        # With PgBouncer (transaction pooling) keep CONN_MAX_AGE at 0.
        "CONN_MAX_AGE": env.int("DATABASE_CONN_MAX_AGE", default=60),
        "OPTIONS": {
            "connect_timeout": 10,
        },
    }
}

# ---------------------------------------------------------------------------
# Redis — prefer dedicated URLs; fall back to REDIS_URL for local/dev
# ---------------------------------------------------------------------------
REDIS_URL = env("REDIS_URL", default="redis://localhost:6379/0")
REDIS_CACHE_URL = env("REDIS_CACHE_URL") or REDIS_URL
REDIS_CELERY_URL = env("REDIS_CELERY_URL") or REDIS_URL
REDIS_CHANNELS_URL = env("REDIS_CHANNELS_URL") or REDIS_URL
REDIS_HOST = env("REDIS_HOST")
REDIS_PORT = env("REDIS_PORT")
REDIS_PASSWORD = env("REDIS_PASSWORD")
REDIS_BLOOM_ENABLED = env("REDIS_BLOOM_ENABLED")

CACHES = {
    "default": {
        "BACKEND": "django_redis.cache.RedisCache",
        "LOCATION": REDIS_CACHE_URL,
        "OPTIONS": {
            "CLIENT_CLASS": "django_redis.client.DefaultClient",
            "SOCKET_CONNECT_TIMEOUT": 5,
            "SOCKET_TIMEOUT": 5,
            "IGNORE_EXCEPTIONS": True,
        },
        "KEY_PREFIX": "linkme",
    }
}

CHANNEL_LAYERS = {
    "default": {
        "BACKEND": "channels_redis.core.RedisChannelLayer",
        "CONFIG": {
            "hosts": [REDIS_CHANNELS_URL],
            "capacity": 1500,
            "expiry": 60,
        },
    },
}

CELERY_BROKER_URL = REDIS_CELERY_URL
CELERY_RESULT_BACKEND = REDIS_CELERY_URL
CELERY_ACCEPT_CONTENT = ["json"]
CELERY_TASK_SERIALIZER = "json"
CELERY_RESULT_SERIALIZER = "json"
CELERY_TIMEZONE = "UTC"
CELERY_TASK_TRACK_STARTED = True
CELERY_TASK_TIME_LIMIT = 30 * 60
CELERY_TASK_SOFT_TIME_LIMIT = 25 * 60
CELERY_WORKER_PREFETCH_MULTIPLIER = 1
CELERY_TASK_ACKS_LATE = True
CELERY_TASK_REJECT_ON_WORKER_LOST = True
CELERY_TASK_DEFAULT_QUEUE = "default"
CELERY_TASK_ROUTES = {
    "media.*": {"queue": "media_processing"},
    "notifications.*": {"queue": "notifications"},
    "moderation.generate_export_file": {"queue": "exports"},
    "admin_dashboard.generate_admin_export": {"queue": "exports"},
    "moderation.cleanup_deleted_accounts": {"queue": "cleanup"},
    "common.cleanup_token_blacklist": {"queue": "cleanup"},
    "common.cleanup_expired_cache": {"queue": "cleanup"},
}
CELERY_BEAT_SCHEDULE = {
    "cleanup-deleted-accounts-daily": {
        "task": "moderation.cleanup_deleted_accounts",
        "schedule": timedelta(hours=24),
    },
    "cleanup-token-blacklist-hourly": {
        "task": "common.cleanup_token_blacklist",
        "schedule": timedelta(hours=1),
    },
}

# ---------------------------------------------------------------------------
# Custom user model
# ---------------------------------------------------------------------------
AUTH_USER_MODEL = "accounts.User"

AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {
        "NAME": "django.contrib.auth.password_validation.MinimumLengthValidator",
        "OPTIONS": {"min_length": 8},
    },
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

# Prefer dedicated JWT secret when provided; fall back to Django SECRET_KEY.
_JWT_SECRET = env("JWT_SECRET", default="") or SECRET_KEY

SIMPLE_JWT = {
    "ACCESS_TOKEN_LIFETIME": timedelta(
        minutes=env.int("JWT_ACCESS_MINUTES", default=15)
    ),
    "REFRESH_TOKEN_LIFETIME": timedelta(days=env.int("JWT_REFRESH_DAYS", default=7)),
    "ROTATE_REFRESH_TOKENS": True,
    "BLACKLIST_AFTER_ROTATION": True,
    "UPDATE_LAST_LOGIN": True,
    "ALGORITHM": "HS256",
    "SIGNING_KEY": _JWT_SECRET,
    "AUTH_HEADER_TYPES": ("Bearer",),
    "AUTH_HEADER_NAME": "HTTP_AUTHORIZATION",
    "USER_ID_FIELD": "id",
    "USER_ID_CLAIM": "user_id",
}

REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": (
        "rest_framework_simplejwt.authentication.JWTAuthentication",
    ),
    "DEFAULT_PERMISSION_CLASSES": (
        "rest_framework.permissions.IsAuthenticated",
    ),
    "DEFAULT_SCHEMA_CLASS": "drf_spectacular.openapi.AutoSchema",
    "DEFAULT_PAGINATION_CLASS": "rest_framework.pagination.PageNumberPagination",
    "PAGE_SIZE": 20,
    "DEFAULT_RENDERER_CLASSES": (
        "rest_framework.renderers.JSONRenderer",
    ),
    "DEFAULT_THROTTLE_CLASSES": (
        "rest_framework.throttling.AnonRateThrottle",
        "rest_framework.throttling.UserRateThrottle",
    ),
    "DEFAULT_THROTTLE_RATES": {
        "anon": "120/hour",
        "user": "2000/hour",
        "auth_signup": "10/hour",
        "auth_login": "30/hour",
        "auth_google": "30/hour",
        "auth_phone_send": "10/hour",
        "auth_phone_verify": "30/hour",
        "auth_password_reset": "5/hour",
        "posts_create": "60/hour",
        "feed_read": "300/hour",
        "media_upload": "30/hour",
        "connection_request": "30/hour",
        "comment_create": "60/min",
        "message_send": "60/min",
        "report_create": "20/hour",
        "block_action": "30/hour",
    },
    "EXCEPTION_HANDLER": "apps.common.exceptions.structured_exception_handler",
}

SPECTACULAR_SETTINGS = {
    "TITLE": "LinkMe API",
    "DESCRIPTION": "LinkMe social networking platform API",
    "VERSION": "1.0.0",
    "SERVE_INCLUDE_SCHEMA": False,
    "TAGS": [
        {"name": "auth", "description": "Registration, login, and password flows"},
        {"name": "profile", "description": "User profile management"},
        {"name": "posts", "description": "Create, read, update, and soft-delete posts"},
        {"name": "feed", "description": "Public and personalized feed endpoints"},
        {"name": "network", "description": "Connections and network discovery"},
        {"name": "search", "description": "User search and suggestions"},
        {"name": "comments", "description": "Comments and replies"},
        {"name": "reactions", "description": "Post and comment reactions"},
        {"name": "messages", "description": "Direct messaging between connections"},
        {"name": "notifications", "description": "In-app notifications and preferences"},
        {"name": "moderation", "description": "Reports, blocks, and staff moderation"},
        {"name": "privacy", "description": "Privacy and visibility settings"},
        {"name": "account", "description": "Account deletion, restore, and data export"},
        {"name": "admin", "description": "Admin dashboard operations and analytics"},
    ],
}

CORS_ALLOWED_ORIGINS = env("CORS_ALLOWED_ORIGINS")
CORS_ALLOW_CREDENTIALS = True

# ---------------------------------------------------------------------------
# Email
# ---------------------------------------------------------------------------
EMAIL_BACKEND = env(
    "EMAIL_BACKEND",
    default="django.core.mail.backends.console.EmailBackend",
)
EMAIL_HOST = env("EMAIL_HOST", default="localhost")
EMAIL_PORT = env.int("EMAIL_PORT", default=587)
EMAIL_HOST_USER = env("EMAIL_HOST_USER", default="")
# Strip spaces so Google App Passwords work whether pasted with or without spaces.
EMAIL_HOST_PASSWORD = env("EMAIL_HOST_PASSWORD", default="").replace(" ", "")
EMAIL_USE_TLS = env.bool("EMAIL_USE_TLS", default=True)
EMAIL_USE_SSL = env.bool("EMAIL_USE_SSL", default=False)
DEFAULT_FROM_EMAIL = env("DEFAULT_FROM_EMAIL", default="LinkMe <noreply@linkme.local>")

FRONTEND_URL = env("FRONTEND_URL", default="http://localhost:3000")

# Google OAuth (ID token verification). Leave empty until credentials are provisioned.
GOOGLE_CLIENT_ID = env("GOOGLE_CLIENT_ID", default="")
GOOGLE_CLIENT_SECRET = env("GOOGLE_CLIENT_SECRET", default="")
GOOGLE_REDIRECT_URI = env("GOOGLE_REDIRECT_URI", default="")

# WhatsApp / message-service OTP delivery
WHATSAPP_API_URL = env("WHATSAPP_API_URL", default="")
WHATSAPP_API_KEY = env("WHATSAPP_API_KEY", default="")
EMAIL_VERIFICATION_TOKEN_MAX_AGE = env.int(
    "EMAIL_VERIFICATION_TOKEN_MAX_AGE", default=60 * 60 * 48
)
PASSWORD_RESET_TOKEN_MAX_AGE = env.int(
    "PASSWORD_RESET_TOKEN_MAX_AGE", default=60 * 60
)

LANGUAGE_CODE = "en-us"
TIME_ZONE = "UTC"
USE_I18N = True
USE_TZ = True

STATIC_URL = "static/"
STATIC_ROOT = BASE_DIR / "staticfiles"

# ---------------------------------------------------------------------------
# Media / object storage (local FS by default; S3/R2/GCS via django-storages)
# ---------------------------------------------------------------------------
USE_S3 = env.bool("USE_S3", default=False)
AWS_ACCESS_KEY_ID = env("AWS_ACCESS_KEY_ID", default="")
AWS_SECRET_ACCESS_KEY = env("AWS_SECRET_ACCESS_KEY", default="")
AWS_STORAGE_BUCKET_NAME = env("MEDIA_STORAGE_BUCKET", default="")
AWS_S3_REGION_NAME = env("AWS_S3_REGION_NAME", default="us-east-1")
AWS_S3_ENDPOINT_URL = env("AWS_S3_ENDPOINT_URL", default="") or None
AWS_S3_CUSTOM_DOMAIN = env("AWS_S3_CUSTOM_DOMAIN", default="") or None
AWS_DEFAULT_ACL = None
AWS_QUERYSTRING_AUTH = env.bool("AWS_QUERYSTRING_AUTH", default=True)
AWS_S3_OBJECT_PARAMETERS = {
    "CacheControl": "max-age=31536000, public, immutable",
}
AWS_S3_FILE_OVERWRITE = False
AWS_S3_SIGNATURE_VERSION = "s3v4"

if USE_S3 and AWS_STORAGE_BUCKET_NAME:
    STORAGES = {
        "default": {
            "BACKEND": "storages.backends.s3boto3.S3Boto3Storage",
        },
        "staticfiles": {
            "BACKEND": "whitenoise.storage.CompressedManifestStaticFilesStorage",
        },
    }
    if AWS_S3_CUSTOM_DOMAIN:
        MEDIA_URL = f"https://{AWS_S3_CUSTOM_DOMAIN}/"
    else:
        MEDIA_URL = f"https://{AWS_STORAGE_BUCKET_NAME}.s3.amazonaws.com/"
else:
    STORAGES = {
        "default": {
            "BACKEND": "django.core.files.storage.FileSystemStorage",
        },
        "staticfiles": {
            "BACKEND": "whitenoise.storage.CompressedManifestStaticFilesStorage",
        },
    }
    MEDIA_URL = "/media/"

MEDIA_ROOT = BASE_DIR / "media"
# Spill large uploads (videos up to 200MB) to temp files; keep small images in memory.
FILE_UPLOAD_MAX_MEMORY_SIZE = 10 * 1024 * 1024
DATA_UPLOAD_MAX_MEMORY_SIZE = 12 * 1024 * 1024
# Absolute ceiling for a single request body (multipart posts with video).
DATA_UPLOAD_MAX_NUMBER_FIELDS = 100

# ---------------------------------------------------------------------------
# Cache TTLs (seconds)
# ---------------------------------------------------------------------------
CACHE_TTL_PROFILE = 60 * 30
CACHE_TTL_FEED = 60 * 5
CACHE_TTL_SUGGESTIONS = 60 * 10
CACHE_TTL_NOTIFICATION_COUNT = 60

# ---------------------------------------------------------------------------
# Auth security
# ---------------------------------------------------------------------------
LOGIN_MAX_ATTEMPTS = env.int("LOGIN_MAX_ATTEMPTS", default=10)
LOGIN_LOCKOUT_SECONDS = env.int("LOGIN_LOCKOUT_SECONDS", default=900)
LOGIN_ATTEMPT_WINDOW_SECONDS = env.int("LOGIN_ATTEMPT_WINDOW_SECONDS", default=900)

# ---------------------------------------------------------------------------
# Logging (structured JSON for production collectors)
# ---------------------------------------------------------------------------
LOG_LEVEL = env("LOG_LEVEL", default="INFO")
LOG_DIR = Path(env("LOG_DIR", default=str(BASE_DIR / "logs")))
try:
    LOG_DIR.mkdir(parents=True, exist_ok=True)
except OSError:
    # Fall back to /tmp when the configured log directory is not writable.
    LOG_DIR = Path("/tmp/linkme-logs")
    LOG_DIR.mkdir(parents=True, exist_ok=True)

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "json": {
            "()": "apps.common.logging.JSONFormatter",
        },
        "verbose": {
            "format": "[{asctime}] {levelname} {name} {message}",
            "style": "{",
        },
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "formatter": "json" if ENVIRONMENT != "development" else "verbose",
        },
        "application": {
            "class": "logging.handlers.RotatingFileHandler",
            "filename": str(LOG_DIR / "application.log"),
            "maxBytes": 10 * 1024 * 1024,
            "backupCount": 5,
            "formatter": "json",
        },
        "security": {
            "class": "logging.handlers.RotatingFileHandler",
            "filename": str(LOG_DIR / "security.log"),
            "maxBytes": 10 * 1024 * 1024,
            "backupCount": 5,
            "formatter": "json",
        },
        "celery": {
            "class": "logging.handlers.RotatingFileHandler",
            "filename": str(LOG_DIR / "celery.log"),
            "maxBytes": 10 * 1024 * 1024,
            "backupCount": 5,
            "formatter": "json",
        },
        "access": {
            "class": "logging.handlers.RotatingFileHandler",
            "filename": str(LOG_DIR / "access.log"),
            "maxBytes": 10 * 1024 * 1024,
            "backupCount": 5,
            "formatter": "json",
        },
    },
    "loggers": {
        "django": {
            "handlers": ["console", "application"],
            "level": LOG_LEVEL,
        },
        "django.request": {
            "handlers": ["console", "application"],
            "level": "WARNING",
            "propagate": False,
        },
        "django.security": {
            "handlers": ["console", "security"],
            "level": "INFO",
            "propagate": False,
        },
        "linkme.security": {
            "handlers": ["console", "security"],
            "level": "INFO",
            "propagate": False,
        },
        "linkme.access": {
            "handlers": ["access"],
            "level": "INFO",
            "propagate": False,
        },
        "celery": {
            "handlers": ["console", "celery"],
            "level": LOG_LEVEL,
            "propagate": False,
        },
        "apps": {
            "handlers": ["console", "application"],
            "level": LOG_LEVEL,
        },
    },
}

# ---------------------------------------------------------------------------
# Sentry (optional — enabled when SENTRY_DSN is set)
# ---------------------------------------------------------------------------
SENTRY_DSN = env("SENTRY_DSN")
SENTRY_TRACES_SAMPLE_RATE = env.float("SENTRY_TRACES_SAMPLE_RATE", default=0.1)
SENTRY_PROFILES_SAMPLE_RATE = env.float("SENTRY_PROFILES_SAMPLE_RATE", default=0.0)

if SENTRY_DSN:
    import sentry_sdk
    from sentry_sdk.integrations.celery import CeleryIntegration
    from sentry_sdk.integrations.django import DjangoIntegration
    from sentry_sdk.integrations.redis import RedisIntegration

    sentry_sdk.init(
        dsn=SENTRY_DSN,
        environment=ENVIRONMENT,
        integrations=[
            DjangoIntegration(),
            CeleryIntegration(),
            RedisIntegration(),
        ],
        traces_sample_rate=SENTRY_TRACES_SAMPLE_RATE,
        profiles_sample_rate=SENTRY_PROFILES_SAMPLE_RATE,
        send_default_pii=False,
    )

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"
