"""Domain services for creating and mutating posts."""

from django.db import transaction
from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework.exceptions import NotFound, PermissionDenied, ValidationError

from apps.media.services import attach_media_files
from apps.moderation.blocks import assert_user_can_act
from apps.posts.filters import filter_posts_for_viewer
from apps.posts.models import Post
from apps.privacy.services import can_view_post

PHASE2_VISIBILITIES = {
    Post.Visibility.PUBLIC,
    Post.Visibility.PRIVATE,
    Post.Visibility.CONNECTIONS_ONLY,
}
MAX_MEDIA_PER_POST = 10


def get_visible_post(post_id, viewer) -> Post:
    post = get_object_or_404(
        Post.objects.select_related("author", "author__profile").prefetch_related(
            "media"
        ),
        pk=post_id,
    )
    if not can_view_post(post=post, viewer=viewer):
        raise NotFound("Post not found.")
    return post


def list_author_posts(*, username: str, viewer):
    """Return visible posts authored by `username`."""
    from apps.reactions.services import annotate_posts_with_engagement

    qs = (
        Post.objects.select_related("author", "author__profile")
        .prefetch_related("media")
        .filter(author__username__iexact=username, author__is_deleted=False)
    )
    qs = filter_posts_for_viewer(qs, viewer).order_by("-published_at", "-id")
    return annotate_posts_with_engagement(qs, viewer=viewer)


@transaction.atomic
def create_post(
    *,
    author,
    content: str = "",
    visibility: str = Post.Visibility.PUBLIC,
    media_files=None,
) -> Post:
    """Create a published post with optional media attachments."""
    assert_user_can_act(author)
    media_files = list(media_files or [])
    content = (content or "").strip()

    if visibility not in PHASE2_VISIBILITIES:
        raise ValidationError(
            {"visibility": ("Supported values: PUBLIC, PRIVATE, CONNECTIONS_ONLY.")}
        )

    if not content and not media_files:
        raise ValidationError(
            {"content": "Provide text content or at least one media file."}
        )

    if len(content) > 5000:
        raise ValidationError({"content": "Content must be at most 5000 characters."})

    if len(media_files) > MAX_MEDIA_PER_POST:
        raise ValidationError(
            {"media": f"At most {MAX_MEDIA_PER_POST} media files are allowed."}
        )

    post = Post.objects.create(
        author=author,
        content=content,
        visibility=visibility,
        status=Post.Status.PUBLISHED,
        published_at=timezone.now(),
    )

    if media_files:
        attach_media_files(post, media_files)

    return (
        Post.objects.select_related("author", "author__profile")
        .prefetch_related("media")
        .get(pk=post.pk)
    )


@transaction.atomic
def update_post(*, post: Post, actor, data: dict) -> Post:
    if post.author_id != actor.id:
        raise PermissionDenied("Only the author can update this post.")
    if post.status == Post.Status.DELETED:
        raise ValidationError({"detail": "Cannot update a deleted post."})

    fields = []
    if "content" in data:
        content = (data["content"] or "").strip()
        if len(content) > 5000:
            raise ValidationError(
                {"content": "Content must be at most 5000 characters."}
            )
        # Content may become empty only if media remains.
        if not content and not post.media.exists():
            raise ValidationError(
                {"content": "Provide text content or at least one media file."}
            )
        post.content = content
        fields.append("content")

    if "visibility" in data:
        visibility = data["visibility"]
        if visibility not in PHASE2_VISIBILITIES:
            raise ValidationError(
                {"visibility": ("Only PUBLIC and PRIVATE are supported in this phase.")}
            )
        post.visibility = visibility
        fields.append("visibility")

    if fields:
        fields.append("updated_at")
        post.save(update_fields=fields)

    return (
        Post.objects.select_related("author", "author__profile")
        .prefetch_related("media")
        .get(pk=post.pk)
    )


@transaction.atomic
def soft_delete_post(*, post: Post, actor) -> Post:
    if post.author_id != actor.id:
        raise PermissionDenied("Only the author can delete this post.")
    if post.status == Post.Status.DELETED:
        return post
    post.status = Post.Status.DELETED
    post.save(update_fields=["status", "updated_at"])
    return post
