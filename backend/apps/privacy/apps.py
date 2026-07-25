from django.apps import AppConfig


class PrivacyConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.privacy"
    label = "privacy"
    verbose_name = "Privacy"

    def ready(self):
        # noqa: F401 — register signal handlers
        from apps.privacy import signals  # noqa: F401
