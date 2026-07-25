"""Celery tasks for admin exports."""

import csv
import io
import json

from celery import shared_task
from django.core.files.base import ContentFile
from django.utils import timezone


@shared_task(name="admin_dashboard.generate_admin_export", queue="exports")
def generate_admin_export(export_id: str) -> str:
    from apps.admin_dashboard.models import AdminExportRequest
    from apps.admin_dashboard import selectors
    from apps.moderation.models import AuditLog, ModerationAction, Report
    from django.contrib.auth import get_user_model

    User = get_user_model()

    try:
        export = AdminExportRequest.objects.select_related("requested_by").get(
            pk=export_id
        )
    except AdminExportRequest.DoesNotExist:
        return "missing"

    export.status = AdminExportRequest.Status.PROCESSING
    export.save(update_fields=["status"])

    try:
        rows = _collect_rows(
            export, User, Report, ModerationAction, AuditLog, selectors
        )
        if export.format == AdminExportRequest.Format.JSON:
            payload = json.dumps(rows, indent=2, default=str).encode("utf-8")
            ext = "json"
        else:
            payload = _to_csv(rows)
            ext = "csv"

        filename = f"admin-{export.export_type.lower()}-{export.id}.{ext}"
        export.file.save(filename, ContentFile(payload), save=False)
        export.status = AdminExportRequest.Status.READY
        export.completed_at = timezone.now()
        export.error_message = ""
        export.save()
    except Exception as exc:  # noqa: BLE001
        export.status = AdminExportRequest.Status.FAILED
        export.error_message = str(exc)[:500]
        export.save(update_fields=["status", "error_message"])
        raise

    return str(export.id)


def _collect_rows(export, User, Report, ModerationAction, AuditLog, selectors):
    et = export.export_type
    if et == export.ExportType.USERS:
        qs = selectors.list_users(params=export.filters)
        return [
            {
                "id": str(u.id),
                "username": u.username,
                "email": u.email,
                "is_active": u.is_active,
                "is_verified": u.is_verified,
                "is_suspended": u.is_suspended,
                "created_at": u.created_at,
            }
            for u in qs.iterator()
        ]
    if et == export.ExportType.REPORTS:
        qs = selectors.list_reports(params=export.filters)
        return [
            {
                "id": str(r.id),
                "reason": r.reason,
                "status": r.status,
                "content_type": r.content_type_label,
                "reporter": r.reporter.username if r.reporter_id else "",
                "reported_user": r.reported_user.username if r.reported_user_id else "",
                "created_at": r.created_at,
            }
            for r in qs.iterator()
        ]
    if et == export.ExportType.MODERATION:
        qs = selectors.list_moderation_history(params=export.filters)
        return [
            {
                "id": str(m.id),
                "admin": m.admin.username if m.admin_id else "",
                "action": m.action,
                "target_type": m.target_type,
                "target_id": m.target_id,
                "reason": m.reason,
                "created_at": m.created_at,
            }
            for m in qs.iterator()
        ]
    if et == export.ExportType.AUDIT:
        qs = selectors.list_audit_logs(params=export.filters)
        return [
            {
                "id": str(a.id),
                "user": a.user.username if a.user_id else "",
                "action": a.action,
                "object_type": a.object_type,
                "object_id": a.object_id,
                "created_at": a.created_at,
            }
            for a in qs.iterator()
        ]
    # ACTIVITY — recent audit for all users
    qs = AuditLog.objects.select_related("user").order_by("-created_at")[:5000]
    return [
        {
            "user": a.user.username if a.user_id else "",
            "action": a.action,
            "object_type": a.object_type,
            "object_id": a.object_id,
            "created_at": a.created_at,
        }
        for a in qs
    ]


def _to_csv(rows: list[dict]) -> bytes:
    if not rows:
        return b""
    buffer = io.StringIO()
    writer = csv.DictWriter(buffer, fieldnames=list(rows[0].keys()))
    writer.writeheader()
    for row in rows:
        writer.writerow({k: ("" if v is None else v) for k, v in row.items()})
    return buffer.getvalue().encode("utf-8")
