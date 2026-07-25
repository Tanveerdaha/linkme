"""Profile media gallery queries."""

from apps.media.models import PostMedia
from apps.posts.filters import filter_posts_for_viewer
from apps.posts.models import Post


def get_profile_media(*, user, viewer, request=None) -> dict:
    """
    Return published media for a user's posts, split into images and videos.

    Visibility is filtered for the viewer (public posts for guests/others).
    """
    posts_qs = Post.objects.filter(author=user)
    visible_posts = filter_posts_for_viewer(posts_qs, viewer).filter(
        status=Post.Status.PUBLISHED
    )
    media_qs = (
        PostMedia.objects.select_related("post")
        .filter(post__in=visible_posts)
        .order_by("-created_at")
    )

    def absolute(field_file):
        if not field_file:
            return None
        url = field_file.url
        if request is not None:
            return request.build_absolute_uri(url)
        return url

    images = []
    videos = []
    for item in media_qs:
        payload = {
            "id": str(item.id),
            "media_type": item.media_type,
            "url": absolute(item.file),
            "thumbnail_url": absolute(item.thumbnail),
            "post_id": str(item.post_id),
            "created_at": item.created_at,
            "width": item.width,
            "height": item.height,
            "duration": item.duration,
            "processing_status": item.processing_status,
        }
        if item.media_type == PostMedia.MediaType.IMAGE:
            images.append(payload)
        else:
            videos.append(payload)

    return {"images": images, "videos": videos}
