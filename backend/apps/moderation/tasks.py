"""Celery tasks for moderation, cleanup, and data export."""

from celery import shared_task


@shared_task(name="moderation.process_report")
def process_report(report_id: str) -> str:
    """
    Lightweight report intake: mark UNDER_REVIEW for staff queue.

    AI / automated scoring belongs in a future phase.
    """
    from apps.moderation.models import Report

    try:
        report = Report.objects.get(pk=report_id)
    except Report.DoesNotExist:
        return "missing"

    if report.status == Report.Status.PENDING:
        report.status = Report.Status.UNDER_REVIEW
        report.save(update_fields=["status", "updated_at"])
    return str(report.id)


@shared_task(name="moderation.generate_export_file", queue="exports")
def generate_export_file(export_id: str) -> str:
    """Generate a ZIP data export for a DataExportRequest."""
    from apps.accounts.export import generate_and_store_export
    from apps.moderation.models import DataExportRequest

    try:
        export = DataExportRequest.objects.select_related("user").get(pk=export_id)
    except DataExportRequest.DoesNotExist:
        return "missing"

    generate_and_store_export(export)
    return str(export.id)


@shared_task(name="moderation.cleanup_deleted_accounts", queue="cleanup")
def cleanup_deleted_accounts(retention_days: int = 30) -> int:
    """
    Anonymize accounts soft-deleted past the retention window.

    Does not hard-delete rows; clears PII and marks content anonymized.
    """
    from datetime import timedelta

    from django.contrib.auth import get_user_model
    from django.db import transaction
    from django.utils import timezone

    User = get_user_model()
    cutoff = timezone.now() - timedelta(days=retention_days)
    qs = User.objects.filter(is_deleted=True, deleted_at__lt=cutoff)
    count = 0

    for user in qs.iterator():
        with transaction.atomic():
            anon = f"deleted_{str(user.id).replace('-', '')[:12]}"
            user.email = f"{anon}@deleted.local"
            user.username = anon[:30]
            user.first_name = ""
            user.last_name = ""
            user.is_active = False
            user.save(
                update_fields=[
                    "email",
                    "username",
                    "first_name",
                    "last_name",
                    "is_active",
                    "updated_at",
                ]
            )
            profile = getattr(user, "profile", None)
            if profile is not None:
                profile.bio = ""
                profile.headline = ""
                profile.location = ""
                profile.website = ""
                profile.interests = []
                profile.social_links = {}
                if profile.avatar:
                    profile.avatar.delete(save=False)
                    profile.avatar = None
                if profile.cover_image:
                    profile.cover_image.delete(save=False)
                    profile.cover_image = None
                profile.save()
            count += 1
    return count
