"""Query helpers / filters for posts."""

from django.db.models import Q, QuerySet

from apps.moderation.blocks import blocked_user_ids_for
from apps.network.models import Connection
from apps.posts.models import Post


def filter_posts_for_viewer(queryset: QuerySet, viewer) -> QuerySet:
    """
    Restrict a post queryset to what `viewer` is allowed to see.

    Guests: public published posts only.
    Authenticated: public published + connections-only (if connected) + own posts.
    Excludes blocked users and deleted authors.
    """
    base = queryset.exclude(status=Post.Status.DELETED).exclude(author__is_deleted=True)

    if viewer is None or not getattr(viewer, "is_authenticated", False):
        return base.filter(
            status=Post.Status.PUBLISHED,
            visibility=Post.Visibility.PUBLIC,
        )

    blocked_ids = blocked_user_ids_for(viewer)
    if blocked_ids:
        base = base.exclude(author_id__in=blocked_ids)

    connected_ids = list(
        Connection.objects.filter(
            Q(sender=viewer) | Q(receiver=viewer),
            status=Connection.Status.ACCEPTED,
        ).values_list("sender_id", "receiver_id")
    )
    peer_ids = set()
    for sender_id, receiver_id in connected_ids:
        peer_ids.add(sender_id if sender_id != viewer.id else receiver_id)

    return base.filter(
        Q(
            status=Post.Status.PUBLISHED,
            visibility=Post.Visibility.PUBLIC,
        )
        | Q(
            status=Post.Status.PUBLISHED,
            visibility=Post.Visibility.CONNECTIONS_ONLY,
            author_id__in=peer_ids,
        )
        | Q(author=viewer)
    )
