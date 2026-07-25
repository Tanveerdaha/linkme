"""Read-side selectors for admin dashboard."""

from datetime import timedelta

from django.contrib.auth import get_user_model
from django.db.models import Count, Q, QuerySet
from django.utils import timezone

from apps.admin_dashboard.filters import (
    filter_admin_comments,
    filter_admin_posts,
    filter_admin_reports,
    filter_admin_users,
    filter_audit_logs,
    filter_moderation_history,
)
from apps.comments.models import Comment
from apps.moderation.models import AuditLog, ModerationAction, Report
from apps.network.models import Connection
from apps.posts.models import Post

User = get_user_model()


def analytics_overview() -> dict:
    now = timezone.now()
    today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)

    total_users = User.objects.filter(is_deleted=False).count()
    active_today = (
        AuditLog.objects.filter(
            action=AuditLog.Action.LOGIN,
            created_at__gte=today_start,
        )
        .values("user_id")
        .distinct()
        .count()
    )

    posts = Post.objects.exclude(status=Post.Status.DELETED).count()
    comments = Comment.objects.filter(status=Comment.Status.ACTIVE).count()
    connections = Connection.objects.filter(status=Connection.Status.ACCEPTED).count()
    pending_reports = Report.objects.filter(
        status__in=[Report.Status.PENDING, Report.Status.UNDER_REVIEW]
    ).count()

    return {
        "users": {"total": total_users, "active_today": active_today},
        "content": {"posts": posts, "comments": comments},
        "network": {"connections": connections},
        "reports": {"pending": pending_reports},
    }


def analytics_trends(*, days: int = 14) -> dict:
    now = timezone.now()
    start = (now - timedelta(days=days - 1)).replace(
        hour=0, minute=0, second=0, microsecond=0
    )

    def _daily_counts(qs, field="created_at"):
        buckets = {
            (start + timedelta(days=i)).date().isoformat(): 0 for i in range(days)
        }
        for row in qs.filter(**{f"{field}__gte": start}).values_list(field, flat=True):
            key = row.date().isoformat()
            if key in buckets:
                buckets[key] += 1
        return [{"date": k, "count": v} for k, v in buckets.items()]

    return {
        "user_growth": _daily_counts(User.objects.all()),
        "content_growth": _daily_counts(
            Post.objects.exclude(status=Post.Status.DELETED)
        ),
        "reports_trend": _daily_counts(Report.objects.all()),
        "comments_trend": _daily_counts(
            Comment.objects.filter(status=Comment.Status.ACTIVE)
        ),
    }


def analytics_metrics() -> dict:
    now = timezone.now()
    today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    week_start = today_start - timedelta(days=7)

    return {
        "daily_active_users": AuditLog.objects.filter(
            action=AuditLog.Action.LOGIN, created_at__gte=today_start
        )
        .values("user_id")
        .distinct()
        .count(),
        "new_registrations": User.objects.filter(created_at__gte=today_start).count(),
        "posts_created": Post.objects.filter(created_at__gte=today_start)
        .exclude(status=Post.Status.DELETED)
        .count(),
        "comments": Comment.objects.filter(
            created_at__gte=today_start, status=Comment.Status.ACTIVE
        ).count(),
        "messages": _message_count_since(today_start),
        "reports": Report.objects.filter(created_at__gte=today_start).count(),
        "registrations_7d": User.objects.filter(created_at__gte=week_start).count(),
        "posts_7d": Post.objects.filter(created_at__gte=week_start)
        .exclude(status=Post.Status.DELETED)
        .count(),
    }


def _message_count_since(since):
    try:
        from apps.messaging.models import Message

        return Message.objects.filter(created_at__gte=since, is_deleted=False).count()
    except Exception:  # noqa: BLE001
        return 0


def list_users(*, params) -> QuerySet:
    qs = User.objects.select_related("profile", "admin_role").order_by("-created_at")
    return filter_admin_users(qs, params)


def get_user_detail(user_id):
    user = (
        User.objects.select_related("profile", "admin_role").filter(pk=user_id).first()
    )
    if user is None:
        return None

    posts_count = (
        Post.objects.filter(author=user).exclude(status=Post.Status.DELETED).count()
    )
    reports_against = Report.objects.filter(reported_user=user).count()
    connections = Connection.objects.filter(
        Q(sender=user) | Q(receiver=user),
        status=Connection.Status.ACCEPTED,
    ).count()
    moderation_history = list(
        ModerationAction.objects.filter(target_type="USER", target_id=str(user.id))
        .select_related("admin")
        .order_by("-created_at")[:20]
    )
    recent_activity = list(
        AuditLog.objects.filter(user=user).order_by("-created_at")[:20]
    )
    return {
        "user": user,
        "posts_count": posts_count,
        "reports_count": reports_against,
        "connections_count": connections,
        "moderation_history": moderation_history,
        "recent_activity": recent_activity,
    }


def list_posts(*, params):
    qs = Post.objects.select_related("author", "author__profile").order_by(
        "-created_at"
    )
    return filter_admin_posts(qs, params)


def list_comments(*, params):
    qs = Comment.objects.select_related("author", "author__profile", "post").order_by(
        "-created_at"
    )
    return filter_admin_comments(qs, params)


def list_reports(*, params):
    qs = Report.objects.select_related(
        "reporter", "reporter__profile", "reported_user", "reported_user__profile"
    ).order_by("-created_at")
    return filter_admin_reports(qs, params)


def list_moderation_history(*, params):
    qs = ModerationAction.objects.select_related("admin", "report").order_by(
        "-created_at"
    )
    return filter_moderation_history(qs, params)


def list_audit_logs(*, params):
    qs = AuditLog.objects.select_related("user").order_by("-created_at")
    return filter_audit_logs(qs, params)
