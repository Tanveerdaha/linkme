"""Read helpers for moderation queries."""

from apps.moderation.models import AuditLog, BlockedUser, ModerationAction, Report


def open_reports():
    return Report.objects.filter(
        status__in=[Report.Status.PENDING, Report.Status.UNDER_REVIEW]
    ).select_related("reporter", "reported_user")


def recent_actions(*, limit: int = 50):
    return ModerationAction.objects.select_related("admin", "report").order_by(
        "-created_at"
    )[:limit]


def audit_for_user(user, *, limit: int = 100):
    return AuditLog.objects.filter(user=user).order_by("-created_at")[:limit]


def blocks_by(user):
    return BlockedUser.objects.filter(blocker=user).select_related(
        "blocked_user", "blocked_user__profile"
    )
