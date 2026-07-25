"""DRF serializers for comments."""

from rest_framework import serializers

from apps.comments.models import Comment
from apps.comments.services import DELETED_PLACEHOLDER


class CommentAuthorSerializer(serializers.Serializer):
    username = serializers.CharField(source="author.username", read_only=True)
    name = serializers.SerializerMethodField()
    avatar = serializers.SerializerMethodField()

    def get_name(self, obj: Comment) -> str:
        return obj.author.full_name

    def get_avatar(self, obj: Comment):
        profile = getattr(obj.author, "profile", None)
        avatar = getattr(profile, "avatar", None) if profile else None
        if not avatar:
            return None
        request = self.context.get("request")
        url = avatar.url
        if request is not None:
            return request.build_absolute_uri(url)
        return url


class CommentWriteSerializer(serializers.Serializer):
    content = serializers.CharField(max_length=2000, allow_blank=False)
    parent_comment_id = serializers.UUIDField(required=False, allow_null=True)


class CommentSerializer(serializers.Serializer):
    id = serializers.UUIDField(read_only=True)
    author = serializers.SerializerMethodField()
    content = serializers.SerializerMethodField()
    status = serializers.CharField(read_only=True)
    parent = serializers.UUIDField(source="parent_id", read_only=True, allow_null=True)
    reaction_count = serializers.SerializerMethodField()
    user_reacted = serializers.SerializerMethodField()
    replies = serializers.SerializerMethodField()
    created_at = serializers.DateTimeField(read_only=True)
    updated_at = serializers.DateTimeField(read_only=True)

    def get_author(self, obj: Comment) -> dict:
        return CommentAuthorSerializer(obj, context=self.context).data

    def get_content(self, obj: Comment) -> str:
        if obj.status == Comment.Status.DELETED:
            return DELETED_PLACEHOLDER
        return obj.content

    def get_reaction_count(self, obj: Comment) -> int:
        return int(getattr(obj, "reaction_count", 0) or 0)

    def get_user_reacted(self, obj: Comment) -> bool:
        value = getattr(obj, "user_reacted", None)
        if value is None:
            return False
        return bool(value)

    def get_replies(self, obj: Comment) -> list:
        # Only top-level comments expose nested replies (one level).
        if obj.parent_id is not None:
            return []
        replies = getattr(obj, "_prefetched_objects_cache", {}).get("replies")
        if replies is None:
            replies = obj.replies.filter(status=Comment.Status.ACTIVE).order_by(
                "created_at"
            )
        return CommentSerializer(replies, many=True, context=self.context).data
