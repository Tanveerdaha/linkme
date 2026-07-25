"""Domain services for comments and replies."""

from django.db import transaction
from django.db.models import Prefetch, Q
from rest_framework.exceptions import NotFound, PermissionDenied, ValidationError

from apps.comments.models import Comment
from apps.posts.models import Post
from apps.posts.services import get_visible_post
from apps.reactions.services import annotate_comments_with_engagement

MAX_COMMENT_LENGTH = 2000
DELETED_PLACEHOLDER = "[deleted]"


def _validate_content(content: str) -> str:
    text = (content or "").strip()
    if not text:
        raise ValidationError({"content": "Comment content is required."})
    if len(text) > MAX_COMMENT_LENGTH:
        raise ValidationError(
            {"content": f"Content must be at most {MAX_COMMENT_LENGTH} characters."}
        )
    return text


def get_active_comment(comment_id) -> Comment:
    try:
        comment = Comment.objects.select_related(
            "author", "author__profile", "post", "parent"
        ).get(pk=comment_id)
    except Comment.DoesNotExist as exc:
        raise NotFound("Comment not found.") from exc
    if comment.status == Comment.Status.DELETED:
        raise NotFound("Comment not found.")
    return comment


def list_post_comments(*, post_id, viewer):
    """
    Return top-level comments for a visible post, with active replies prefetched.

    Soft-deleted top-level comments that still have active replies are included
    so threads remain readable; content is masked in the serializer.
    """
    post = get_visible_post(post_id, viewer)

    reply_qs = annotate_comments_with_engagement(
        Comment.objects.select_related("author", "author__profile")
        .filter(status=Comment.Status.ACTIVE)
        .order_by("created_at"),
        viewer=viewer,
    )

    parents_with_replies = Comment.objects.filter(
        post=post,
        parent__isnull=True,
        status=Comment.Status.DELETED,
        replies__status=Comment.Status.ACTIVE,
    ).values_list("id", flat=True)

    qs = (
        Comment.objects.select_related("author", "author__profile")
        .filter(post=post, parent__isnull=True)
        .filter(Q(status=Comment.Status.ACTIVE) | Q(id__in=parents_with_replies))
        .prefetch_related(Prefetch("replies", queryset=reply_qs))
        .order_by("created_at")
    )
    return annotate_comments_with_engagement(qs, viewer=viewer)


@transaction.atomic
def create_comment(*, post_id, author, content: str) -> Comment:
    from apps.moderation.blocks import assert_not_blocked, assert_user_can_act

    assert_user_can_act(author)
    post = get_visible_post(post_id, author)
    if post.status != Post.Status.PUBLISHED and post.author_id != author.id:
        raise NotFound("Post not found.")

    assert_not_blocked(actor=author, target=post.author)

    text = _validate_content(content)
    comment = Comment(
        author=author,
        post=post,
        parent=None,
        content=text,
        status=Comment.Status.ACTIVE,
    )
    comment.save()
    result = annotate_comments_with_engagement(
        Comment.objects.select_related("author", "author__profile").filter(
            pk=comment.pk
        ),
        viewer=author,
    ).get()

    from apps.notifications.signals import notify_comment_on_post

    notify_comment_on_post(actor=author, post=post, comment=result)
    return result


@transaction.atomic
def reply_to_comment(*, comment_id, author, content: str) -> Comment:
    parent = get_active_comment(comment_id)
    if parent.parent_id is not None:
        raise ValidationError({"parent": "Replies to replies are not allowed."})

    post = get_visible_post(parent.post_id, author)
    text = _validate_content(content)

    reply = Comment(
        author=author,
        post=post,
        parent=parent,
        content=text,
        status=Comment.Status.ACTIVE,
    )
    reply.save()
    result = annotate_comments_with_engagement(
        Comment.objects.select_related("author", "author__profile").filter(pk=reply.pk),
        viewer=author,
    ).get()

    from apps.notifications.signals import notify_comment_reply

    notify_comment_reply(actor=author, parent_comment=parent, reply=result)
    return result


@transaction.atomic
def update_comment(*, comment: Comment, actor, content: str) -> Comment:
    if comment.author_id != actor.id:
        raise PermissionDenied("Only the author can update this comment.")
    if comment.status == Comment.Status.DELETED:
        raise NotFound("Comment not found.")

    text = _validate_content(content)
    comment.content = text
    comment.save(update_fields=["content", "updated_at"])
    return annotate_comments_with_engagement(
        Comment.objects.select_related("author", "author__profile").filter(
            pk=comment.pk
        ),
        viewer=actor,
    ).get()


@transaction.atomic
def soft_delete_comment(*, comment: Comment, actor) -> Comment:
    if comment.author_id != actor.id:
        raise PermissionDenied("Only the author can delete this comment.")
    if comment.status == Comment.Status.DELETED:
        return comment
    comment.status = Comment.Status.DELETED
    comment.save(update_fields=["status", "updated_at"])
    return comment
