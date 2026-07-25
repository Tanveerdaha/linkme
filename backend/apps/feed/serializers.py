"""Feed serializers re-export post payloads for OpenAPI clarity."""

from apps.posts.serializers import PostSerializer

__all__ = ["PostSerializer"]
