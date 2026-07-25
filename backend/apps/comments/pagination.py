"""Cursor pagination for comment lists."""

from rest_framework.pagination import CursorPagination


class CommentCursorPagination(CursorPagination):
    """Oldest comments first within a post thread; PAGE_SIZE = 20."""

    page_size = 20
    page_size_query_param = "page_size"
    max_page_size = 50
    ordering = ("created_at", "id")
    cursor_query_param = "cursor"
