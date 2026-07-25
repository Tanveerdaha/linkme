"""API views for comments and replies."""

from django.shortcuts import get_object_or_404
from drf_spectacular.utils import OpenApiParameter, extend_schema, extend_schema_view
from rest_framework import status
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.comments import services
from apps.comments.models import Comment
from apps.comments.pagination import CommentCursorPagination
from apps.comments.permissions import CanComment, IsCommentOwner
from apps.comments.serializers import CommentSerializer, CommentWriteSerializer
from apps.moderation.throttling import CommentCreateThrottle


class PostCommentListCreateView(APIView):
    """
    GET  /api/v1/posts/{id}/comments/ — list comments (with nested replies)
    POST /api/v1/posts/{id}/comments/ — create top-level comment
    """

    pagination_class = CommentCursorPagination

    def get_permissions(self):
        if self.request.method == "POST":
            return [CanComment()]
        return [AllowAny()]

    def get_throttles(self):
        if self.request.method == "POST":
            return [CommentCreateThrottle()]
        return []

    @extend_schema(
        parameters=[
            OpenApiParameter(
                name="cursor",
                type=str,
                location=OpenApiParameter.QUERY,
                required=False,
            ),
        ],
        responses={200: CommentSerializer(many=True)},
        tags=["comments"],
        summary="List comments on a post",
    )
    def get(self, request, post_id):
        qs = services.list_post_comments(post_id=post_id, viewer=request.user)
        paginator = self.pagination_class()
        page = paginator.paginate_queryset(qs, request, view=self)
        serializer = CommentSerializer(page, many=True, context={"request": request})
        return paginator.get_paginated_response(serializer.data)

    @extend_schema(
        request=CommentWriteSerializer,
        responses={201: CommentSerializer},
        tags=["comments"],
        summary="Create a comment or reply on a post",
    )
    def post(self, request, post_id):
        serializer = CommentWriteSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        parent_id = serializer.validated_data.get("parent_comment_id")
        if parent_id:
            parent = services.get_active_comment(parent_id)
            if str(parent.post_id) != str(post_id):
                return Response(
                    {"detail": "Parent comment does not belong to this post."},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            reply = services.reply_to_comment(
                comment_id=parent_id,
                author=request.user,
                content=serializer.validated_data["content"],
            )
            return Response(
                CommentSerializer(reply, context={"request": request}).data,
                status=status.HTTP_201_CREATED,
            )
        comment = services.create_comment(
            post_id=post_id,
            author=request.user,
            content=serializer.validated_data["content"],
        )
        return Response(
            CommentSerializer(comment, context={"request": request}).data,
            status=status.HTTP_201_CREATED,
        )


@extend_schema_view(
    patch=extend_schema(
        request=CommentWriteSerializer,
        responses={200: CommentSerializer},
        tags=["comments"],
        summary="Update own comment",
    ),
    delete=extend_schema(
        responses={204: None},
        tags=["comments"],
        summary="Soft-delete own comment",
    ),
)
class CommentDetailView(APIView):
    """
    PATCH  /api/v1/comments/{id}/
    DELETE /api/v1/comments/{id}/
    """

    def get_permissions(self):
        return [CanComment(), IsCommentOwner()]

    def get_object(self, comment_id):
        return get_object_or_404(
            Comment.objects.select_related("author", "author__profile", "post"),
            pk=comment_id,
        )

    def patch(self, request, comment_id):
        comment = self.get_object(comment_id)
        if comment.status == Comment.Status.DELETED:
            return Response({"detail": "Not found."}, status=status.HTTP_404_NOT_FOUND)
        self.check_object_permissions(request, comment)
        serializer = CommentWriteSerializer(data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        comment = services.update_comment(
            comment=comment,
            actor=request.user,
            content=serializer.validated_data["content"],
        )
        return Response(CommentSerializer(comment, context={"request": request}).data)

    def delete(self, request, comment_id):
        comment = self.get_object(comment_id)
        if comment.status == Comment.Status.DELETED:
            return Response(status=status.HTTP_204_NO_CONTENT)
        self.check_object_permissions(request, comment)
        services.soft_delete_comment(comment=comment, actor=request.user)
        return Response(status=status.HTTP_204_NO_CONTENT)


class CommentReplyView(APIView):
    """POST /api/v1/comments/{id}/reply/"""

    def get_permissions(self):
        return [CanComment()]

    @extend_schema(
        request=CommentWriteSerializer,
        responses={201: CommentSerializer},
        tags=["comments"],
        summary="Reply to a top-level comment",
    )
    def post(self, request, comment_id):
        serializer = CommentWriteSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        reply = services.reply_to_comment(
            comment_id=comment_id,
            author=request.user,
            content=serializer.validated_data["content"],
        )
        return Response(
            CommentSerializer(reply, context={"request": request}).data,
            status=status.HTTP_201_CREATED,
        )
