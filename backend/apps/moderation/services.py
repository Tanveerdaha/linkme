"""Domain services for blocking, reporting, and staff moderation."""

from datetime import timedelta

from django.contrib.auth import get_user_model
from django.contrib.contenttypes.models import ContentType
from django.db import IntegrityError, transaction
from django.db.models import Q
from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework.exceptions import NotFound, PermissionDenied, ValidationError

from apps.moderation.audit import log_audit
from apps.moderation.blocks import assert_user_can_act
from apps.moderation.models import AuditLog, BlockedUser, ModerationAction, Report

User = get_user_model()


def _get_active_user(username: str):
    return get_object_or_404(
        User.objects.select_related("profile"),
        username__iexact=username,
        is_active=True,
        is_verified=True,
        is_deleted=False,
    )


@transaction.atomic
def block_user(*, blocker, username: str, reason: str = "") -> BlockedUser:
    assert_user_can_act(blocker)
    if blocker.username.lower() == username.lower():
        raise ValidationError({"detail": "You cannot block yourself."})

    target = _get_active_user(username)
    if BlockedUser.objects.filter(blocker=blocker, blocked_user=target).exists():
        raise ValidationError({"detail": "User is already blocked."})

    block = BlockedUser.objects.create(
        blocker=blocker,
        blocked_user=target,
        reason=(reason or "").strip()[:255],
    )

    # Cancel any active connection between the pair.
    from apps.network.models import Connection

    Connection.objects.filter(
        Q(sender=blocker, receiver=target) | Q(sender=target, receiver=blocker),
        status__in=Connection.ACTIVE_STATUSES,
    ).update(status=Connection.Status.BLOCKED, updated_at=timezone.now())

    log_audit(
        user=blocker,
        action=AuditLog.Action.BLOCK_USER,
        object_type="user",
        object_id=str(target.id),
        metadata={"username": target.username, "reason": block.reason},
    )
    return block


@transaction.atomic
def unblock_user(*, blocker, username: str) -> None:
    assert_user_can_act(blocker)
    target = get_object_or_404(User, username__iexact=username)
    deleted, _ = BlockedUser.objects.filter(
        blocker=blocker, blocked_user=target
    ).delete()
    if not deleted:
        raise NotFound("Block not found.")

    from apps.network.models import Connection

    Connection.objects.filter(
        Q(sender=blocker, receiver=target) | Q(sender=target, receiver=blocker),
        status=Connection.Status.BLOCKED,
    ).update(status=Connection.Status.REMOVED, updated_at=timezone.now())

    log_audit(
        user=blocker,
        action=AuditLog.Action.UNBLOCK_USER,
        object_type="user",
        object_id=str(target.id),
        metadata={"username": target.username},
    )


def list_blocked_users(*, user):
    return (
        BlockedUser.objects.filter(blocker=user)
        .select_related("blocked_user", "blocked_user__profile")
        .order_by("-created_at")
    )


def _resolve_report_target(*, content_type: str, object_id: str):
    """Return (reported_user, content_type_obj or None, object_id)."""
    label = content_type.upper()
    oid = str(object_id).strip()
    if not oid:
        raise ValidationError({"object_id": "object_id is required."})

    if label == Report.ContentTypeChoice.USER:
        # Accept user UUID or username.
        import uuid as uuid_lib

        user = None
        try:
            uuid_lib.UUID(str(oid))
            user = User.objects.filter(pk=oid).first()
        except (ValueError, TypeError):
            user = None
        if user is None:
            user = get_object_or_404(User, username__iexact=oid)
        return user, ContentType.objects.get_for_model(User), str(user.id)

    if label == Report.ContentTypeChoice.POST:
        from apps.posts.models import Post

        post = get_object_or_404(Post, pk=oid)
        return post.author, ContentType.objects.get_for_model(Post), str(post.id)

    if label == Report.ContentTypeChoice.COMMENT:
        from apps.comments.models import Comment

        comment = get_object_or_404(Comment, pk=oid)
        return comment.author, ContentType.objects.get_for_model(Comment), str(comment.id)

    if label == Report.ContentTypeChoice.MESSAGE:
        from apps.messaging.models import Message

        message = get_object_or_404(Message, pk=oid)
        return message.sender, ContentType.objects.get_for_model(Message), str(message.id)

    raise ValidationError({"content_type": "Unsupported content type."})


@transaction.atomic
def create_report(
    *,
    reporter,
    content_type: str,
    object_id: str,
    reason: str,
    description: str = "",
) -> Report:
    assert_user_can_act(reporter)

    if reason not in Report.Reason.values:
        raise ValidationError({"reason": "Invalid report reason."})

    reported_user, ct, oid = _resolve_report_target(
        content_type=content_type, object_id=object_id
    )
    if reported_user and reported_user.id == reporter.id:
        raise ValidationError({"detail": "You cannot report yourself."})

    try:
        report = Report.objects.create(
            reporter=reporter,
            reported_user=reported_user,
            content_type_label=content_type.upper(),
            content_type=ct,
            object_id=oid,
            reason=reason,
            description=(description or "").strip()[:2000],
            status=Report.Status.PENDING,
        )
    except IntegrityError as exc:
        raise ValidationError(
            {"detail": "You already have an open report for this content."}
        ) from exc

    log_audit(
        user=reporter,
        action=AuditLog.Action.REPORT_CREATED,
        object_type=content_type.upper(),
        object_id=oid,
        metadata={"reason": reason, "report_id": str(report.id)},
    )

    from apps.moderation.tasks import process_report

    process_report.delay(str(report.id))
    return report


def list_my_reports(*, user):
    return (
        Report.objects.filter(reporter=user)
        .select_related("reported_user", "reported_user__profile")
        .order_by("-created_at")
    )


def list_pending_reports(*, status: str | None = None):
    qs = Report.objects.select_related(
        "reporter", "reporter__profile", "reported_user", "reported_user__profile"
    )
    if status:
        qs = qs.filter(status=status)
    else:
        qs = qs.filter(
            status__in=[Report.Status.PENDING, Report.Status.UNDER_REVIEW]
        )
    return qs.order_by("created_at")


def get_report(*, report_id) -> Report:
    report = (
        Report.objects.select_related(
            "reporter", "reporter__profile", "reported_user", "reported_user__profile"
        )
        .filter(pk=report_id)
        .first()
    )
    if report is None:
        raise NotFound("Report not found.")
    return report


@transaction.atomic
def update_report_status(*, report_id, actor, status: str) -> Report:
    if not actor.is_staff:
        raise PermissionDenied("Staff access required.")
    report = get_report(report_id=report_id)
    if status not in Report.Status.values:
        raise ValidationError({"status": "Invalid status."})
    report.status = status
    report.save(update_fields=["status", "updated_at"])
    return report


@transaction.atomic
def take_moderation_action(
    *,
    admin,
    target_type: str,
    target_id: str,
    action: str,
    reason: str = "",
    report_id=None,
    suspend_days: int | None = None,
) -> ModerationAction:
    if not admin.is_staff:
        raise PermissionDenied("Staff access required.")
    if action not in ModerationAction.Action.values:
        raise ValidationError({"action": "Invalid moderation action."})

    report = None
    if report_id:
        report = get_report(report_id=report_id)

    if action == ModerationAction.Action.CONTENT_REMOVED:
        _remove_content(target_type=target_type, target_id=target_id)
    elif action in (
        ModerationAction.Action.USER_SUSPENDED,
        ModerationAction.Action.USER_BANNED,
    ):
        _suspend_or_ban_user(
            target_id=target_id,
            action=action,
            reason=reason,
            suspend_days=suspend_days,
        )

    mod = ModerationAction.objects.create(
        admin=admin,
        target_type=target_type.upper(),
        target_id=str(target_id),
        action=action,
        reason=(reason or "").strip(),
        report=report,
    )

    if report and report.status in (Report.Status.PENDING, Report.Status.UNDER_REVIEW):
        report.status = Report.Status.RESOLVED
        report.save(update_fields=["status", "updated_at"])

    log_audit(
        user=admin,
        action=AuditLog.Action.MODERATION_ACTION,
        object_type=target_type,
        object_id=str(target_id),
        metadata={"action": action, "reason": reason, "moderation_id": str(mod.id)},
    )
    return mod


def _remove_content(*, target_type: str, target_id: str) -> None:
    label = target_type.upper()
    if label == "POST":
        from apps.posts.models import Post

        post = get_object_or_404(Post, pk=target_id)
        post.status = Post.Status.DELETED
        post.save(update_fields=["status", "updated_at"])
    elif label == "COMMENT":
        from apps.comments.models import Comment

        comment = get_object_or_404(Comment, pk=target_id)
        comment.status = Comment.Status.DELETED
        comment.save(update_fields=["status", "updated_at"])
    elif label == "MESSAGE":
        from apps.messaging.models import Message

        message = get_object_or_404(Message, pk=target_id)
        message.is_deleted = True
        message.save(update_fields=["is_deleted", "updated_at"])
    else:
        raise ValidationError({"target_type": "Cannot remove this target type."})


def _suspend_or_ban_user(*, target_id, action: str, reason: str, suspend_days: int | None):
    user = get_object_or_404(User, pk=target_id)
    user.is_suspended = True
    user.suspension_reason = (reason or "").strip()
    if action == ModerationAction.Action.USER_BANNED:
        user.suspended_until = None
        user.is_active = False
    else:
        days = suspend_days or 7
        user.suspended_until = timezone.now() + timedelta(days=days)
    user.save(
        update_fields=[
            "is_suspended",
            "suspended_until",
            "suspension_reason",
            "is_active",
            "updated_at",
        ]
    )
