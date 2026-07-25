"""Account soft-delete, restore, and data export orchestration."""

from django.contrib.auth import get_user_model
from django.db import transaction
from django.utils import timezone
from rest_framework.exceptions import PermissionDenied, ValidationError
from rest_framework_simplejwt.token_blacklist.models import (
    BlacklistedToken,
    OutstandingToken,
)

from apps.moderation.audit import log_audit
from apps.moderation.models import AuditLog, DataExportRequest

User = get_user_model()


@transaction.atomic
def soft_delete_account(*, user) -> User:
    """Soft-delete the account. Does not hard-delete rows."""
    if getattr(user, "is_deleted", False):
        raise ValidationError({"detail": "Account is already deleted."})

    user.is_deleted = True
    user.deleted_at = timezone.now()
    user.is_active = False
    user.save(update_fields=["is_deleted", "deleted_at", "is_active", "updated_at"])

    # Invalidate outstanding refresh tokens.
    for token in OutstandingToken.objects.filter(user=user):
        BlacklistedToken.objects.get_or_create(token=token)

    log_audit(
        user=user,
        action=AuditLog.Action.ACCOUNT_DELETE,
        object_type="user",
        object_id=str(user.id),
    )
    return user


@transaction.atomic
def restore_account(*, user) -> User:
    """Restore a soft-deleted account within the retention window."""
    if not getattr(user, "is_deleted", False):
        raise ValidationError({"detail": "Account is not deleted."})

    # Optional retention: allow restore within 30 days.
    if user.deleted_at and (timezone.now() - user.deleted_at).days > 30:
        raise PermissionDenied("Account restore window has expired.")

    user.is_deleted = False
    user.deleted_at = None
    user.is_active = True
    user.save(update_fields=["is_deleted", "deleted_at", "is_active", "updated_at"])

    log_audit(
        user=user,
        action=AuditLog.Action.ACCOUNT_RESTORE,
        object_type="user",
        object_id=str(user.id),
    )
    return user


@transaction.atomic
def request_data_export(*, user) -> DataExportRequest:
    """Queue a data export job for the user."""
    pending = DataExportRequest.objects.filter(
        user=user,
        status__in=[
            DataExportRequest.Status.PENDING,
            DataExportRequest.Status.PROCESSING,
        ],
    ).exists()
    if pending:
        raise ValidationError({"detail": "An export request is already in progress."})

    export = DataExportRequest.objects.create(
        user=user,
        status=DataExportRequest.Status.PENDING,
    )
    log_audit(
        user=user,
        action=AuditLog.Action.DATA_EXPORT,
        object_type="export",
        object_id=str(export.id),
    )

    from apps.moderation.tasks import generate_export_file

    generate_export_file.delay(str(export.id))
    return export


def get_latest_export(*, user) -> DataExportRequest | None:
    return (
        DataExportRequest.objects.filter(user=user).order_by("-created_at").first()
    )
