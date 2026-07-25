"""Query helpers and filters for admin list endpoints."""

from django.contrib.auth import get_user_model
from django.db.models import Count, Q, QuerySet
from django.utils.dateparse import parse_date

from apps.comments.models import Comment
from apps.moderation.models import Report
from apps.posts.models import Post

User = get_user_model()


def filter_admin_users(queryset: QuerySet, params) -> QuerySet:
    search = (params.get("search") or "").strip()
    if search:
        queryset = queryset.filter(
            Q(username__icontains=search)
            | Q(email__icontains=search)
            | Q(first_name__icontains=search)
            | Q(last_name__icontains=search)
        )

    status = (params.get("status") or "").upper()
    if status == "ACTIVE":
        queryset = queryset.filter(is_active=True, is_deleted=False, is_suspended=False)
    elif status == "SUSPENDED":
        queryset = queryset.filter(is_suspended=True, is_deleted=False)
    elif status == "DELETED":
        queryset = queryset.filter(is_deleted=True)
    elif status == "INACTIVE":
        queryset = queryset.filter(is_active=False, is_deleted=False)

    verified = params.get("verified")
    if verified in ("true", "1", "yes"):
        queryset = queryset.filter(is_verified=True)
    elif verified in ("false", "0", "no"):
        queryset = queryset.filter(is_verified=False)

    suspended = params.get("suspended")
    if suspended in ("true", "1", "yes"):
        queryset = queryset.filter(is_suspended=True)
    elif suspended in ("false", "0", "no"):
        queryset = queryset.filter(is_suspended=False)

    created = params.get("created_date") or params.get("created_after")
    if created:
        day = parse_date(created)
        if day:
            queryset = queryset.filter(created_at__date__gte=day)

    created_before = params.get("created_before")
    if created_before:
        day = parse_date(created_before)
        if day:
            queryset = queryset.filter(created_at__date__lte=day)

    return queryset


def filter_admin_posts(queryset: QuerySet, params) -> QuerySet:
    search = (params.get("search") or "").strip()
    if search:
        queryset = queryset.filter(
            Q(content__icontains=search) | Q(author__username__icontains=search)
        )

    filt = (params.get("filter") or params.get("status") or "").lower()
    if filt == "deleted":
        queryset = queryset.filter(status=Post.Status.DELETED)
    elif filt == "reported":
        reported_ids = Report.objects.filter(
            content_type_label=Report.ContentTypeChoice.POST,
            status__in=[Report.Status.PENDING, Report.Status.UNDER_REVIEW],
        ).values_list("object_id", flat=True)
        queryset = queryset.filter(id__in=list(reported_ids))
    elif filt == "popular":
        queryset = queryset.annotate(
            _reaction_count=Count("reactions", distinct=True)
        ).order_by("-_reaction_count", "-created_at")
    elif filt == "recent":
        queryset = queryset.order_by("-created_at")
    else:
        queryset = queryset.exclude(status=Post.Status.DELETED)

    return queryset


def filter_admin_comments(queryset: QuerySet, params) -> QuerySet:
    search = (params.get("search") or "").strip()
    if search:
        queryset = queryset.filter(
            Q(content__icontains=search) | Q(author__username__icontains=search)
        )
    status = (params.get("status") or "").upper()
    if status == "DELETED":
        queryset = queryset.filter(status=Comment.Status.DELETED)
    elif status == "ACTIVE":
        queryset = queryset.filter(status=Comment.Status.ACTIVE)
    return queryset


def filter_admin_reports(queryset: QuerySet, params) -> QuerySet:
    status = (params.get("status") or "").upper()
    if status:
        queryset = queryset.filter(status=status)

    reason = (params.get("reason") or "").upper()
    if reason:
        queryset = queryset.filter(reason=reason)

    content_type = (params.get("content_type") or "").upper()
    if content_type:
        queryset = queryset.filter(content_type_label=content_type)

    date = params.get("date") or params.get("created_after")
    if date:
        day = parse_date(date)
        if day:
            queryset = queryset.filter(created_at__date__gte=day)

    search = (params.get("search") or "").strip()
    if search:
        queryset = queryset.filter(
            Q(reporter__username__icontains=search)
            | Q(reported_user__username__icontains=search)
            | Q(description__icontains=search)
        )
    return queryset


def filter_audit_logs(queryset: QuerySet, params) -> QuerySet:
    action = (params.get("action") or "").upper()
    if action:
        queryset = queryset.filter(action=action)

    object_type = (params.get("object_type") or "").strip()
    if object_type:
        queryset = queryset.filter(object_type__iexact=object_type)

    username = (params.get("user") or params.get("username") or "").strip()
    if username:
        queryset = queryset.filter(user__username__iexact=username)

    date = params.get("date") or params.get("created_after")
    if date:
        day = parse_date(date)
        if day:
            queryset = queryset.filter(created_at__date__gte=day)

    return queryset


def filter_moderation_history(queryset: QuerySet, params) -> QuerySet:
    action = (params.get("action") or "").upper()
    if action:
        queryset = queryset.filter(action=action)
    admin = (params.get("admin") or "").strip()
    if admin:
        queryset = queryset.filter(admin__username__iexact=admin)
    return queryset
