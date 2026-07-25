"""
Celery tasks owned by the common app.

These are infrastructure/smoke tasks; domain work lives in other apps.
"""

from celery import shared_task


@shared_task(name="common.health_check_task")
def health_check_task() -> dict:
    """Lightweight worker smoke test used in Phase 0 validation."""
    return {"status": "ok", "service": "celery"}


@shared_task(name="common.cleanup_token_blacklist", queue="cleanup")
def cleanup_token_blacklist() -> dict:
    """Remove expired SimpleJWT blacklist rows."""
    from django.utils import timezone
    from rest_framework_simplejwt.token_blacklist.models import (
        BlacklistedToken,
        OutstandingToken,
    )

    now = timezone.now()
    expired_ids = list(
        OutstandingToken.objects.filter(expires_at__lt=now).values_list("id", flat=True)
    )
    blacklisted, _ = BlacklistedToken.objects.filter(token_id__in=expired_ids).delete()
    outstanding, _ = OutstandingToken.objects.filter(id__in=expired_ids).delete()
    return {"blacklisted_deleted": blacklisted, "outstanding_deleted": outstanding}


@shared_task(name="common.cleanup_expired_cache", queue="cleanup")
def cleanup_expired_cache() -> dict:
    """No-op placeholder — Redis handles TTL expiry; kept for beat visibility."""
    return {"status": "ok"}