"""Pagination for network list endpoints."""

from rest_framework.pagination import PageNumberPagination


class ConnectionPagination(PageNumberPagination):
    page_size = 20
    page_size_query_param = "page_size"
    max_page_size = 50
