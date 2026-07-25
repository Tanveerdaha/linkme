from django.apps import AppConfig


class ProfilesConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.profiles"
    label = "profiles"
    verbose_name = "Profiles"

    def ready(self):
        # Register signal handlers.
        from apps.profiles import signals  # noqa: F401
