"""API views for posts."""

from django.shortcuts import get_object_or_404
from drf_spectacular.utils import OpenApiParameter, extend_schema, extend_schema_view
from rest_framework import status
from rest_framework.parsers import FormParser, JSONParser, MultiPartParser
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.throttling import ScopedRateThrottle
from rest_framework.views import APIView

from apps.posts import services
from apps.posts.models import Post
from apps.posts.pagination import PostCursorPagination
from apps.posts.permissions import (
    CanViewPost,
    IsAuthenticatedVerified,
    IsPostOwner,
)
from apps.posts.serializers import (
    PostCreateSerializer,
    PostSerializer,
    PostShareSerializer,
    PostUpdateSerializer,
)
from apps.posts.share import get_post_share_payload
from apps.reactions.services import annotate_posts_with_engagement


class PostListCreateView(APIView):
    """
    GET  /api/v1/posts/?username= — list an author's visible posts
    POST /api/v1/posts/ — create a post (multipart)
    """

    parser_classes = [MultiPartParser, FormParser, JSONParser]
    pagination_class = PostCursorPagination

    def get_permissions(self):
        if self.request.method == "POST":
            return [IsAuthenticatedVerified()]
        return [AllowAny()]

    def get_throttles(self):
        if self.request.method == "POST":
            return [ScopedRateThrottle()]
        return [ScopedRateThrottle()]

    @property
    def throttle_scope(self):
        if self.request.method == "POST":
            return "posts_create"
        return "feed_read"

    @extend_schema(
        parameters=[
            OpenApiParameter(
                name="username",
                type=str,
                location=OpenApiParameter.QUERY,
                required=False,
                description="Filter posts by author username",
            ),
            OpenApiParameter(
                name="cursor",
                type=str,
                location=OpenApiParameter.QUERY,
                required=False,
            ),
        ],
        responses={200: PostSerializer(many=True)},
        tags=["posts"],
        summary="List posts (optionally by username)",
    )
    def get(self, request):
        username = request.query_params.get("username")
        if username:
            qs = services.list_author_posts(username=username, viewer=request.user)
        else:
            from apps.feed.services import get_public_feed

            qs = get_public_feed(viewer=request.user)

        paginator = self.pagination_class()
        page = paginator.paginate_queryset(qs, request, view=self)
        serializer = PostSerializer(page, many=True, context={"request": request})
        return paginator.get_paginated_response(serializer.data)

    @extend_schema(
        request=PostCreateSerializer,
        responses={201: PostSerializer},
        tags=["posts"],
        summary="Create a post with optional media",
    )
    def post(self, request):
        serializer = PostCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        post = services.create_post(
            author=request.user,
            content=data.get("content", ""),
            visibility=data.get("visibility", Post.Visibility.PUBLIC),
            media_files=data.get("media") or [],
        )
        from apps.common.cache import invalidate_all_feeds_for_author

        invalidate_all_feeds_for_author(request.user.id)
        post = annotate_posts_with_engagement(
            Post.objects.filter(pk=post.pk), viewer=request.user
        ).get()
        return Response(
            PostSerializer(post, context={"request": request}).data,
            status=status.HTTP_201_CREATED,
        )


@extend_schema_view(
    get=extend_schema(
        responses={200: PostSerializer},
        tags=["posts"],
        summary="Retrieve a post",
    ),
    patch=extend_schema(
        request=PostUpdateSerializer,
        responses={200: PostSerializer},
        tags=["posts"],
        summary="Update own post",
    ),
    delete=extend_schema(
        responses={204: None},
        tags=["posts"],
        summary="Soft-delete own post",
    ),
)
class PostDetailView(APIView):
    parser_classes = [JSONParser, FormParser, MultiPartParser]

    def get_permissions(self):
        if self.request.method in ("PATCH", "DELETE"):
            return [IsAuthenticatedVerified(), IsPostOwner()]
        return [AllowAny(), CanViewPost()]

    def get_object(self, request, post_id):
        return services.get_visible_post(post_id, request.user)

    def get(self, request, post_id):
        post = self.get_object(request, post_id)
        self.check_object_permissions(request, post)
        post = annotate_posts_with_engagement(
            Post.objects.filter(pk=post.pk), viewer=request.user
        ).get()
        return Response(PostSerializer(post, context={"request": request}).data)

    def patch(self, request, post_id):
        post = get_object_or_404(
            Post.objects.select_related("author", "author__profile").prefetch_related("media"),
            pk=post_id,
        )
        if post.status == Post.Status.DELETED:
            return Response(
                {"detail": "Not found."}, status=status.HTTP_404_NOT_FOUND
            )
        self.check_object_permissions(request, post)

        serializer = PostUpdateSerializer(data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        post = services.update_post(
            post=post, actor=request.user, data=serializer.validated_data
        )
        post = annotate_posts_with_engagement(
            Post.objects.filter(pk=post.pk), viewer=request.user
        ).get()
        return Response(PostSerializer(post, context={"request": request}).data)

    def delete(self, request, post_id):
        post = get_object_or_404(
            Post.objects.select_related("author"),
            pk=post_id,
        )
        if post.status == Post.Status.DELETED:
            return Response(status=status.HTTP_204_NO_CONTENT)
        self.check_object_permissions(request, post)
        services.soft_delete_post(post=post, actor=request.user)
        return Response(status=status.HTTP_204_NO_CONTENT)


class PostShareView(APIView):
    """GET /api/v1/posts/{id}/share/ — public share URL foundation."""

    permission_classes = [AllowAny]

    @extend_schema(
        responses={200: PostShareSerializer},
        tags=["posts"],
        summary="Get shareable link for a post",
    )
    def get(self, request, post_id):
        payload = get_post_share_payload(post_id=post_id, viewer=request.user)
        return Response(payload)
