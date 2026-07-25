"""API views for reactions on posts and comments."""

from drf_spectacular.utils import extend_schema
from rest_framework import status
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.reactions import services
from apps.reactions.permissions import CanReact
from apps.reactions.serializers import (
    ReactionResultSerializer,
    ReactionSummarySerializer,
    ReactionToggleSerializer,
)


class PostReactionView(APIView):
    """
    POST   /api/v1/posts/{id}/reaction/ — add HEART
    DELETE /api/v1/posts/{id}/reaction/ — remove reaction
    """

    def get_permissions(self):
        return [CanReact()]

    @extend_schema(
        request=ReactionToggleSerializer,
        responses={200: ReactionResultSerializer},
        tags=["reactions"],
        summary="Add heart reaction to a post",
    )
    def post(self, request, post_id):
        serializer = ReactionToggleSerializer(data=request.data or {})
        serializer.is_valid(raise_exception=True)
        result = services.add_post_reaction(
            post_id=post_id,
            user=request.user,
            reaction_type=serializer.validated_data.get("reaction_type", "HEART"),
        )
        return Response(result, status=status.HTTP_200_OK)

    @extend_schema(
        responses={200: ReactionResultSerializer},
        tags=["reactions"],
        summary="Remove reaction from a post",
    )
    def delete(self, request, post_id):
        result = services.remove_post_reaction(post_id=post_id, user=request.user)
        return Response(result, status=status.HTTP_200_OK)


class PostReactionSummaryView(APIView):
    """GET /api/v1/posts/{id}/reactions/"""

    permission_classes = [AllowAny]

    @extend_schema(
        responses={200: ReactionSummarySerializer},
        tags=["reactions"],
        summary="Get reaction summary for a post",
    )
    def get(self, request, post_id):
        result = services.get_post_reaction_summary(
            post_id=post_id, viewer=request.user
        )
        return Response(result)


class CommentReactionView(APIView):
    """
    POST   /api/v1/comments/{id}/reaction/ — add HEART
    DELETE /api/v1/comments/{id}/reaction/ — remove reaction
    """

    def get_permissions(self):
        return [CanReact()]

    @extend_schema(
        request=ReactionToggleSerializer,
        responses={200: ReactionResultSerializer},
        tags=["reactions"],
        summary="Add heart reaction to a comment",
    )
    def post(self, request, comment_id):
        serializer = ReactionToggleSerializer(data=request.data or {})
        serializer.is_valid(raise_exception=True)
        result = services.add_comment_reaction(
            comment_id=comment_id,
            user=request.user,
            reaction_type=serializer.validated_data.get("reaction_type", "HEART"),
        )
        return Response(result, status=status.HTTP_200_OK)

    @extend_schema(
        responses={200: ReactionResultSerializer},
        tags=["reactions"],
        summary="Remove reaction from a comment",
    )
    def delete(self, request, comment_id):
        result = services.remove_comment_reaction(
            comment_id=comment_id, user=request.user
        )
        return Response(result, status=status.HTTP_200_OK)
