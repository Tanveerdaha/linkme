"""Domain services for admin operations."""

from datetime import timedelta

from django.contrib.auth import get_user_model
from django.db import transaction
from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework.exceptions import NotFound, PermissionDenied, ValidationError

from apps.admin_dashboard.models import (
    AdminExportRequest,
    AdminPermissionCode,
    AdminRole,
    ROLE_DEFAULT_PERMISSIONS,
)
from apps.admin_dashboard.permissions import user_has_admin_permission
from apps.comments.models import Comment
from apps.moderation.audit import log_audit
from apps.moderation.models import AuditLog, ModerationAction, Report
from apps.moderation import services as moderation_services
from apps.posts.models import Post

User = get_user_model()

DURATION_MAP = {
    "1_day": 1,
    "3_days": 3,
    "7_days": 7,
    "14_days": 14,
    "30_days": 30,
    "permanent": None,
}


def ensure_admin_role(*, user, role: str, actor=None) -> AdminRole:
    """Create or update AdminRole. Requires MANAGE_ADMINS unless bootstrapping self as superuser."""
    if role not in AdminRole.Role.values:
        raise ValidationError({"role": "Invalid admin role."})

    if actor is not None and not user_has_admin_permission(
        actor, AdminPermissionCode.MANAGE_ADMINS
    ):
        if not getattr(actor, "is_superuser", False):
            raise PermissionDenied("Cannot manage admin roles.")

    user.is_staff = True
    user.save(update_fields=["is_staff", "updated_at"])

    admin_role, _ = AdminRole.objects.update_or_create(
        user=user,
        defaults={
            "role": role,
            "permissions": list(ROLE_DEFAULT_PERMISSIONS.get(role, [])),
        },
    )
    if actor is not None:
        log_audit(
            user=actor,
            action=AuditLog.Action.OTHER,
            object_type="admin_role",
            object_id=str(admin_role.id),
            metadata={"role": role, "target_user": user.username},
        )
    return admin_role


@transaction.atomic
def suspend_user(*, actor, user_id, reason: str = "", duration: str = "7_days") -> User:
    if not user_has_admin_permission(actor, AdminPermissionCode.SUSPEND_USERS):
        raise PermissionDenied("Missing SUSPEND_USERS permission.")

    user = get_object_or_404(User, pk=user_id)
    if user.is_superuser and not actor.is_superuser:
        raise PermissionDenied("Cannot suspend a superuser.")

    days = DURATION_MAP.get(duration, 7)
    user.is_suspended = True
    user.suspension_reason = (reason or "").strip()
    user.suspended_until = (
        None if days is None else timezone.now() + timedelta(days=days)
    )
    user.save(
        update_fields=[
            "is_suspended",
            "suspension_reason",
            "suspended_until",
            "updated_at",
        ]
    )

    ModerationAction.objects.create(
        admin=actor,
        target_type="USER",
        target_id=str(user.id),
        action=ModerationAction.Action.USER_SUSPENDED,
        reason=user.suspension_reason,
    )
    log_audit(
        user=actor,
        action=AuditLog.Action.MODERATION_ACTION,
        object_type="user",
        object_id=str(user.id),
        metadata={
            "action": "SUSPEND",
            "reason": reason,
            "duration": duration,
            "username": user.username,
        },
    )
    return user


@transaction.atomic
def unsuspend_user(*, actor, user_id) -> User:
    if not user_has_admin_permission(actor, AdminPermissionCode.SUSPEND_USERS):
        raise PermissionDenied("Missing SUSPEND_USERS permission.")

    user = get_object_or_404(User, pk=user_id)
    user.is_suspended = False
    user.suspended_until = None
    user.suspension_reason = ""
    user.save(
        update_fields=[
            "is_suspended",
            "suspended_until",
            "suspension_reason",
            "updated_at",
        ]
    )
    log_audit(
        user=actor,
        action=AuditLog.Action.MODERATION_ACTION,
        object_type="user",
        object_id=str(user.id),
        metadata={"action": "UNSUSPEND", "username": user.username},
    )
    return user


@transaction.atomic
def deactivate_user(*, actor, user_id, reason: str = "") -> User:
    if not user_has_admin_permission(actor, AdminPermissionCode.MANAGE_USERS):
        raise PermissionDenied("Missing MANAGE_USERS permission.")

    user = get_object_or_404(User, pk=user_id)
    if user.is_superuser and not actor.is_superuser:
        raise PermissionDenied("Cannot deactivate a superuser.")

    user.is_active = False
    user.save(update_fields=["is_active", "updated_at"])
    log_audit(
        user=actor,
        action=AuditLog.Action.OTHER,
        object_type="user",
        object_id=str(user.id),
        metadata={"action": "DEACTIVATE", "reason": reason, "username": user.username},
    )
    return user


@transaction.atomic
def soft_delete_user(*, actor, user_id, reason: str = "") -> User:
    if not user_has_admin_permission(actor, AdminPermissionCode.DELETE_USERS):
        raise PermissionDenied("Missing DELETE_USERS permission.")

    user = get_object_or_404(User, pk=user_id)
    if user.is_superuser and not actor.is_superuser:
        raise PermissionDenied("Cannot delete a superuser.")

    from apps.accounts.account_services import soft_delete_account

    soft_delete_account(user=user)
    log_audit(
        user=actor,
        action=AuditLog.Action.ACCOUNT_DELETE,
        object_type="user",
        object_id=str(user.id),
        metadata={
            "action": "ADMIN_DELETE",
            "reason": reason,
            "username": user.username,
        },
    )
    return user


@transaction.atomic
def remove_post(*, actor, post_id, reason: str = "") -> Post:
    if not user_has_admin_permission(actor, AdminPermissionCode.REMOVE_CONTENT):
        raise PermissionDenied("Missing REMOVE_CONTENT permission.")

    post = get_object_or_404(Post, pk=post_id)
    post.status = Post.Status.DELETED
    post.save(update_fields=["status", "updated_at"])

    ModerationAction.objects.create(
        admin=actor,
        target_type="POST",
        target_id=str(post.id),
        action=ModerationAction.Action.CONTENT_REMOVED,
        reason=(reason or "").strip(),
    )
    log_audit(
        user=actor,
        action=AuditLog.Action.MODERATION_ACTION,
        object_type="post",
        object_id=str(post.id),
        metadata={"action": "CONTENT_REMOVED", "reason": reason},
    )
    return post


@transaction.atomic
def restore_post(*, actor, post_id) -> Post:
    if not user_has_admin_permission(actor, AdminPermissionCode.RESTORE_CONTENT):
        raise PermissionDenied("Missing RESTORE_CONTENT permission.")

    post = get_object_or_404(Post, pk=post_id)
    post.status = Post.Status.PUBLISHED
    post.save(update_fields=["status", "updated_at"])
    log_audit(
        user=actor,
        action=AuditLog.Action.MODERATION_ACTION,
        object_type="post",
        object_id=str(post.id),
        metadata={"action": "CONTENT_RESTORED"},
    )
    return post


@transaction.atomic
def remove_comment(*, actor, comment_id, reason: str = "") -> Comment:
    if not user_has_admin_permission(actor, AdminPermissionCode.REMOVE_CONTENT):
        raise PermissionDenied("Missing REMOVE_CONTENT permission.")

    comment = get_object_or_404(Comment, pk=comment_id)
    comment.status = Comment.Status.DELETED
    comment.save(update_fields=["status", "updated_at"])

    ModerationAction.objects.create(
        admin=actor,
        target_type="COMMENT",
        target_id=str(comment.id),
        action=ModerationAction.Action.CONTENT_REMOVED,
        reason=(reason or "").strip(),
    )
    log_audit(
        user=actor,
        action=AuditLog.Action.MODERATION_ACTION,
        object_type="comment",
        object_id=str(comment.id),
        metadata={"action": "CONTENT_REMOVED", "reason": reason},
    )
    return comment


@transaction.atomic
def restore_comment(*, actor, comment_id) -> Comment:
    if not user_has_admin_permission(actor, AdminPermissionCode.RESTORE_CONTENT):
        raise PermissionDenied("Missing RESTORE_CONTENT permission.")

    comment = get_object_or_404(Comment, pk=comment_id)
    comment.status = Comment.Status.ACTIVE
    comment.save(update_fields=["status", "updated_at"])
    log_audit(
        user=actor,
        action=AuditLog.Action.MODERATION_ACTION,
        object_type="comment",
        object_id=str(comment.id),
        metadata={"action": "CONTENT_RESTORED"},
    )
    return comment


@transaction.atomic
def update_report(*, actor, report_id, status: str, note: str = "") -> Report:
    if not user_has_admin_permission(actor, AdminPermissionCode.MANAGE_REPORTS):
        raise PermissionDenied("Missing MANAGE_REPORTS permission.")

    # Map friendly action names to statuses.
    status_map = {
        "ASSIGN": Report.Status.UNDER_REVIEW,
        "APPROVE": Report.Status.RESOLVED,
        "RESOLVE": Report.Status.RESOLVED,
        "REJECT": Report.Status.REJECTED,
    }
    resolved = status_map.get(status.upper(), status.upper())
    report = moderation_services.update_report_status(
        report_id=report_id, actor=actor, status=resolved
    )
    log_audit(
        user=actor,
        action=AuditLog.Action.MODERATION_ACTION,
        object_type="report",
        object_id=str(report.id),
        metadata={"status": resolved, "note": note},
    )
    return report


@transaction.atomic
def request_export(
    *, actor, export_type: str, format: str = "CSV", filters: dict | None = None
):
    if not user_has_admin_permission(actor, AdminPermissionCode.EXPORT_DATA):
        raise PermissionDenied("Missing EXPORT_DATA permission.")

    if export_type not in AdminExportRequest.ExportType.values:
        raise ValidationError({"export_type": "Invalid export type."})
    if format not in AdminExportRequest.Format.values:
        raise ValidationError({"format": "Invalid format."})

    export = AdminExportRequest.objects.create(
        requested_by=actor,
        export_type=export_type,
        format=format,
        filters=filters or {},
        status=AdminExportRequest.Status.PENDING,
    )
    log_audit(
        user=actor,
        action=AuditLog.Action.DATA_EXPORT,
        object_type="admin_export",
        object_id=str(export.id),
        metadata={"export_type": export_type, "format": format},
    )

    from apps.admin_dashboard.tasks import generate_admin_export

    generate_admin_export.delay(str(export.id))
    return export
