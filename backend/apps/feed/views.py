"""API views for the feed app."""

from drf_spectacular.utils import OpenApiParameter, extend_schema
from rest_framework.permissions import AllowAny
from rest_framework.throttling import ScopedRateThrottle
from rest_framework.views import APIView

from apps.common.cache import cache_feed
from apps.feed import services
from apps.posts.pagination import PostCursorPagination
from apps.posts.permissions import IsAuthenticatedVerified
from apps.posts.serializers import PostSerializer


class PublicFeedView(APIView):
    """GET /api/v1/feed/public/ — guest-accessible public feed."""

    permission_classes = [AllowAny]
    pagination_class = PostCursorPagination
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = "feed_read"

    @extend_schema(
        parameters=[
            OpenApiParameter(
                name="cursor",
                type=str,
                location=OpenApiParameter.QUERY,
                required=False,
            ),
        ],
        responses={200: PostSerializer(many=True)},
        tags=["feed"],
        summary="Public feed (no auth required)",
    )
    def get(self, request):
        cursor = request.query_params.get("cursor")
        # Cache only the first page for anonymous visitors.
        use_cache = not cursor and not getattr(
            request.user, "is_authenticated", False
        )
        if use_cache:
            cached = cache_feed(None)
            if cached is not None:
                from rest_framework.response import Response

                return Response(cached)

        qs = services.get_public_feed(viewer=request.user)
        paginator = self.pagination_class()
        page = paginator.paginate_queryset(qs, request, view=self)
        serializer = PostSerializer(page, many=True, context={"request": request})
        response = paginator.get_paginated_response(serializer.data)
        if use_cache:
            cache_feed(None, response.data)
        return response


class UserFeedView(APIView):
    """GET /api/v1/feed/ — authenticated personal feed foundation."""

    permission_classes = [IsAuthenticatedVerified]
    pagination_class = PostCursorPagination
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = "feed_read"

    @extend_schema(
        parameters=[
            OpenApiParameter(
                name="cursor",
                type=str,
                location=OpenApiParameter.QUERY,
                required=False,
            ),
        ],
        responses={200: PostSerializer(many=True)},
        tags=["feed"],
        summary="Authenticated user feed foundation",
    )
    def get(self, request):
        cursor = request.query_params.get("cursor")
        use_cache = not cursor
        if use_cache:
            cached = cache_feed(request.user.id)
            if cached is not None:
                from rest_framework.response import Response

                return Response(cached)

        qs = services.get_user_feed(request.user)
        paginator = self.pagination_class()
        page = paginator.paginate_queryset(qs, request, view=self)
        serializer = PostSerializer(page, many=True, context={"request": request})
        response = paginator.get_paginated_response(serializer.data)
        if use_cache:
            cache_feed(request.user.id, response.data)
        return response
