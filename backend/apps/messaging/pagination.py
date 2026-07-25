"""Pagination for messaging endpoints."""

from rest_framework.pagination import CursorPagination, PageNumberPagination


class ConversationPagination(PageNumberPagination):
    page_size = 20
    page_size_query_param = "page_size"
    max_page_size = 50


class MessageCursorPagination(CursorPagination):
    """Newest messages first; clients page backward through history."""

    page_size = 30
    page_size_query_param = "page_size"
    max_page_size = 100
    ordering = ("-created_at", "-id")
    cursor_query_param = "cursor"
