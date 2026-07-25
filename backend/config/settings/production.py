"""Production settings — strict security and operational defaults."""

from config.settings.base import *  # noqa: F401,F403

DEBUG = False
ENVIRONMENT = "production"

if SECRET_KEY.startswith("change-me") or len(SECRET_KEY) < 40:  # noqa: F405
    raise RuntimeError(
        "Production SECRET_KEY must be a strong random value (40+ chars)."
    )

SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
SECURE_SSL_REDIRECT = env.bool("SECURE_SSL_REDIRECT", default=True)  # noqa: F405
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
SECURE_HSTS_SECONDS = env.int("SECURE_HSTS_SECONDS", default=31536000)  # noqa: F405
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True
SECURE_CONTENT_TYPE_NOSNIFF = True
SECURE_BROWSER_XSS_FILTER = True
X_FRAME_OPTIONS = "DENY"
SESSION_COOKIE_HTTPONLY = True
CSRF_COOKIE_HTTPONLY = True
SECURE_REFERRER_POLICY = "same-origin"

CSRF_TRUSTED_ORIGINS = env.list(  # noqa: F405
    "CSRF_TRUSTED_ORIGINS",
    default=[],
)

# Transaction pooling via PgBouncer — do not hold server-side connections.
DATABASES["default"]["CONN_MAX_AGE"] = env.int(  # noqa: F405
    "DATABASE_CONN_MAX_AGE", default=0
)

# Shorter JWT access window in production (override via env if needed).
SIMPLE_JWT["ACCESS_TOKEN_LIFETIME"] = timedelta(  # noqa: F405
    minutes=env.int("JWT_ACCESS_MINUTES", default=10)  # noqa: F405
)

# Never expose browsable API / schema publicly without auth in prod.
SPECTACULAR_SETTINGS = {  # noqa: F405
    **SPECTACULAR_SETTINGS,  # noqa: F405
    "SERVE_PERMISSIONS": ["rest_framework.permissions.IsAdminUser"],
}
