"""Domain services for post and comment reactions."""

from django.db import IntegrityError, transaction
from django.db.models import Count, Q
from rest_framework.exceptions import NotFound, ValidationError

from apps.posts.models import Post
from apps.posts.services import get_visible_post
from apps.reactions.models import Reaction


def _active_comment_or_404(comment_id):
    from apps.comments.models import Comment

    try:
        comment = Comment.objects.select_related("post", "author").get(pk=comment_id)
    except Comment.DoesNotExist as exc:
        raise NotFound("Comment not found.") from exc
    if comment.status == Comment.Status.DELETED:
        raise NotFound("Comment not found.")
    return comment


def annotate_posts_with_engagement(queryset, viewer=None):
    """
    Annotate a Post queryset with reaction_count, comment_count, user_reacted.

    Avoids N+1 by using database aggregates.
    """
    qs = queryset.annotate(
        reaction_count=Count(
            "reactions",
            filter=Q(reactions__reaction_type=Reaction.ReactionType.HEART),
            distinct=True,
        ),
        comment_count=Count(
            "comments",
            filter=Q(comments__status="ACTIVE"),
            distinct=True,
        ),
    )
    if viewer is not None and getattr(viewer, "is_authenticated", False):
        qs = qs.annotate(
            user_reacted=Count(
                "reactions",
                filter=Q(
                    reactions__user=viewer,
                    reactions__reaction_type=Reaction.ReactionType.HEART,
                ),
                distinct=True,
            )
        )
    return qs


def annotate_comments_with_engagement(queryset, viewer=None):
    """Annotate Comment queryset with reaction_count and user_reacted."""
    qs = queryset.annotate(
        reaction_count=Count(
            "reactions",
            filter=Q(reactions__reaction_type=Reaction.ReactionType.HEART),
            distinct=True,
        ),
    )
    if viewer is not None and getattr(viewer, "is_authenticated", False):
        qs = qs.annotate(
            user_reacted=Count(
                "reactions",
                filter=Q(
                    reactions__user=viewer,
                    reactions__reaction_type=Reaction.ReactionType.HEART,
                ),
                distinct=True,
            )
        )
    return qs


def _post_reaction_count(post_id) -> int:
    return Reaction.objects.filter(
        post_id=post_id,
        reaction_type=Reaction.ReactionType.HEART,
    ).count()


def _comment_reaction_count(comment_id) -> int:
    return Reaction.objects.filter(
        comment_id=comment_id,
        reaction_type=Reaction.ReactionType.HEART,
    ).count()


@transaction.atomic
def add_post_reaction(
    *, post_id, user, reaction_type: str = Reaction.ReactionType.HEART
) -> dict:
    from apps.moderation.blocks import assert_not_blocked, assert_user_can_act

    assert_user_can_act(user)
    post = get_visible_post(post_id, user)
    assert_not_blocked(actor=user, target=post.author)
    if reaction_type != Reaction.ReactionType.HEART:
        raise ValidationError({"reaction_type": "Only HEART reactions are supported."})

    try:
        _reaction, created = Reaction.objects.get_or_create(
            user=user,
            post=post,
            defaults={"reaction_type": Reaction.ReactionType.HEART, "comment": None},
        )
    except IntegrityError as exc:
        raise ValidationError({"detail": "Could not add reaction."}) from exc

    if created:
        from apps.notifications.signals import notify_post_reaction

        notify_post_reaction(actor=user, post=post)

    return {
        "reacted": True,
        "reaction_type": Reaction.ReactionType.HEART,
        "count": _post_reaction_count(post.id),
    }


@transaction.atomic
def remove_post_reaction(*, post_id, user) -> dict:
    post = get_visible_post(post_id, user)
    Reaction.objects.filter(user=user, post=post).delete()
    return {
        "reacted": False,
        "count": _post_reaction_count(post.id),
    }


def get_post_reaction_summary(*, post_id, viewer) -> dict:
    post = get_visible_post(post_id, viewer)
    total = _post_reaction_count(post.id)
    return {"total": total, "heart": total}


@transaction.atomic
def add_comment_reaction(
    *, comment_id, user, reaction_type: str = Reaction.ReactionType.HEART
) -> dict:
    comment = _active_comment_or_404(comment_id)
    # Ensure the parent post is visible to the actor.
    get_visible_post(comment.post_id, user)

    if reaction_type != Reaction.ReactionType.HEART:
        raise ValidationError({"reaction_type": "Only HEART reactions are supported."})

    try:
        _reaction, created = Reaction.objects.get_or_create(
            user=user,
            comment=comment,
            defaults={"reaction_type": Reaction.ReactionType.HEART, "post": None},
        )
    except IntegrityError as exc:
        raise ValidationError({"detail": "Could not add reaction."}) from exc

    if created:
        from apps.notifications.signals import notify_comment_reaction

        notify_comment_reaction(actor=user, comment=comment)

    return {
        "reacted": True,
        "reaction_type": Reaction.ReactionType.HEART,
        "count": _comment_reaction_count(comment.id),
    }


@transaction.atomic
def remove_comment_reaction(*, comment_id, user) -> dict:
    comment = _active_comment_or_404(comment_id)
    get_visible_post(comment.post_id, user)
    Reaction.objects.filter(user=user, comment=comment).delete()
    return {
        "reacted": False,
        "count": _comment_reaction_count(comment.id),
    }
