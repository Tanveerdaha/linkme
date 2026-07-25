"""Suggested users foundation (non-AI heuristics)."""

from django.db.models import Count, Q, QuerySet
from django.utils import timezone
from datetime import timedelta

from apps.posts.models import Post
from apps.profiles.models import Profile


def get_suggested_users(*, viewer=None, limit: int = 10) -> QuerySet:
    """
    Suggest public profiles based on:

    1. Recently active (recent posts)
    2. More complete profiles (avatar + headline)
    3. Popular creators (post count)

    Excludes the viewer. No AI / ML yet.
    """
    recent_cutoff = timezone.now() - timedelta(days=30)

    qs = (
        Profile.objects.select_related("user")
        .filter(
            user__is_active=True,
            user__is_verified=True,
            profile_visibility=Profile.Visibility.PUBLIC,
        )
        .annotate(
            recent_posts=Count(
                "user__posts",
                filter=Q(
                    user__posts__status=Post.Status.PUBLISHED,
                    user__posts__published_at__gte=recent_cutoff,
                ),
                distinct=True,
            ),
            total_posts=Count(
                "user__posts",
                filter=Q(user__posts__status=Post.Status.PUBLISHED),
                distinct=True,
            ),
        )
        .order_by("-recent_posts", "-total_posts", "-updated_at")
    )

    if viewer is not None and getattr(viewer, "is_authenticated", False):
        qs = qs.exclude(user_id=viewer.id)

    # Prefer profiles that look complete.
    qs = qs.filter(Q(avatar__isnull=False) | Q(headline__gt="") | Q(bio__gt=""))

    return qs[:limit]
