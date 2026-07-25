"""Feed ranking and query services."""

from django.db.models import Q, QuerySet

from apps.posts.models import Post
from apps.reactions.services import annotate_posts_with_engagement


def get_public_feed(viewer=None) -> QuerySet:
    """
    Public chronological feed for guests.

    Ranking foundation (Phase 2): newest published public posts first.
    Future phases may weight active authors / engagement.
    """
    qs = (
        Post.objects.select_related("author", "author__profile")
        .prefetch_related("media")
        .filter(
            status=Post.Status.PUBLISHED,
            visibility=Post.Visibility.PUBLIC,
        )
        .order_by("-published_at", "-id")
    )
    return annotate_posts_with_engagement(qs, viewer=viewer)


def get_user_feed(user) -> QuerySet:
    """
    Authenticated personal feed foundation.

    Phase 2: public posts + the viewer's own non-deleted posts.
    Later phases add connection-based content.
    """
    qs = (
        Post.objects.select_related("author", "author__profile")
        .prefetch_related("media")
        .filter(
            Q(
                status=Post.Status.PUBLISHED,
                visibility=Post.Visibility.PUBLIC,
            )
            | Q(author=user)
        )
        .exclude(status=Post.Status.DELETED)
        .order_by("-published_at", "-id")
    )
    return annotate_posts_with_engagement(qs, viewer=user)
