"""Profile statistics helpers."""

from django.db.models import Count, Q

from apps.media.models import PostMedia
from apps.posts.models import Post
from apps.profiles.models import Profile


def get_profile_statistics(profile: Profile) -> dict:
    """
    Return engagement-style counts for a profile.

    ``profile_views`` is prepared for a future analytics phase (stored on Profile).
    """
    user_id = profile.user_id
    posts = Post.objects.filter(
        author_id=user_id,
        status=Post.Status.PUBLISHED,
    ).count()
    media = PostMedia.objects.filter(
        post__author_id=user_id,
        post__status=Post.Status.PUBLISHED,
    ).count()
    return {
        "posts": posts,
        "media": media,
        "profile_views": profile.profile_views,
    }


def annotate_profiles_with_stats(queryset):
    """Annotate Profile queryset with post_count and media_count."""
    return queryset.annotate(
        post_count=Count(
            "user__posts",
            filter=Q(user__posts__status=Post.Status.PUBLISHED),
            distinct=True,
        ),
        media_count=Count(
            "user__posts__media",
            filter=Q(user__posts__status=Post.Status.PUBLISHED),
            distinct=True,
        ),
    )
