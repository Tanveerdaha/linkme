"""Pagination helpers for profile discovery."""

from rest_framework.pagination import CursorPagination, PageNumberPagination


class UserSearchPagination(PageNumberPagination):
    page_size = 20
    page_size_query_param = "page_size"
    max_page_size = 50


class ProfileCursorPagination(CursorPagination):
    page_size = 20
    page_size_query_param = "page_size"
    max_page_size = 50
    ordering = ("-updated_at", "id")
    cursor_query_param = "cursor"
