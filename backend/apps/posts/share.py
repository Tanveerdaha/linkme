"""Share-link helpers for posts."""

from django.conf import settings

from apps.posts.models import Post
from apps.posts.services import get_visible_post


def get_post_share_payload(*, post_id, viewer) -> dict:
    """Return a public share URL and title for a visible post."""
    post = get_visible_post(post_id, viewer)
    frontend = settings.FRONTEND_URL.rstrip("/")
    url = f"{frontend}/post/{post.id}"
    content = (post.content or "").strip()
    if content:
        title = content[:80] + ("…" if len(content) > 80 else "")
    else:
        title = f"Post by @{post.author.username}"
    return {"url": url, "title": title}
