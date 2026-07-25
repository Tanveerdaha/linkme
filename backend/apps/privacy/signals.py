"""Create PrivacySetting when a new user is created."""

from django.conf import settings
from django.db.models.signals import post_save
from django.dispatch import receiver

from apps.privacy.models import PrivacySetting


@receiver(post_save, sender=settings.AUTH_USER_MODEL)
def ensure_privacy_settings(sender, instance, created, **kwargs):
    if created:
        PrivacySetting.objects.get_or_create(user=instance)
