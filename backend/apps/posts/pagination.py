"""Cursor pagination for posts and feeds."""

from rest_framework.pagination import CursorPagination


class PostCursorPagination(CursorPagination):
    """Newest published posts first; PAGE_SIZE = 20."""

    page_size = 20
    page_size_query_param = "page_size"
    max_page_size = 50
    ordering = ("-published_at", "-id")
    cursor_query_param = "cursor"
