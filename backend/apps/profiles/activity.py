"""User activity timeline aggregation."""

from django.db.models import Q
from django.utils import timezone

from apps.comments.models import Comment
from apps.posts.models import Post
from apps.reactions.models import Reaction


ACTIVITY_LIMIT_DEFAULT = 30


def get_user_activity(*, user, viewer=None, limit: int = ACTIVITY_LIMIT_DEFAULT) -> list[dict]:
    """
    Build a merged activity feed for a user.

    Types: POST_CREATED, COMMENT_CREATED, REACTION_CREATED.
    Respects post visibility for non-owner viewers.
    """
    is_owner = bool(
        viewer
        and getattr(viewer, "is_authenticated", False)
        and viewer.id == user.id
    )

    posts_qs = Post.objects.filter(
        author=user,
        status=Post.Status.PUBLISHED,
    ).order_by("-published_at", "-created_at")
    if not is_owner:
        posts_qs = posts_qs.filter(visibility=Post.Visibility.PUBLIC)

    activities: list[dict] = []

    for post in posts_qs[:limit]:
        activities.append(
            {
                "type": "POST_CREATED",
                "content": (post.content or "")[:200],
                "created_at": post.published_at or post.created_at,
                "ref_id": str(post.id),
            }
        )

    comments_qs = (
        Comment.objects.select_related("post")
        .filter(author=user, status=Comment.Status.ACTIVE)
        .order_by("-created_at")
    )
    if not is_owner:
        comments_qs = comments_qs.filter(
            post__status=Post.Status.PUBLISHED,
            post__visibility=Post.Visibility.PUBLIC,
        )
    for comment in comments_qs[:limit]:
        activities.append(
            {
                "type": "COMMENT_CREATED",
                "content": (comment.content or "")[:200],
                "created_at": comment.created_at,
                "ref_id": str(comment.id),
                "post_id": str(comment.post_id),
            }
        )

    reactions_qs = (
        Reaction.objects.select_related("post", "comment")
        .filter(user=user)
        .order_by("-created_at")
    )
    if not is_owner:
        reactions_qs = reactions_qs.filter(
            Q(
                post__isnull=False,
                post__status=Post.Status.PUBLISHED,
                post__visibility=Post.Visibility.PUBLIC,
            )
            | Q(
                comment__isnull=False,
                comment__post__status=Post.Status.PUBLISHED,
                comment__post__visibility=Post.Visibility.PUBLIC,
            )
        )
    for reaction in reactions_qs[:limit]:
        target = "post" if reaction.post_id else "comment"
        activities.append(
            {
                "type": "REACTION_CREATED",
                "content": f"Reacted with {reaction.reaction_type} to a {target}",
                "created_at": reaction.created_at,
                "ref_id": str(reaction.id),
                "reaction_type": reaction.reaction_type,
            }
        )

    activities.sort(
        key=lambda item: item["created_at"] or timezone.now(),
        reverse=True,
    )
    return activities[:limit]
