"""DRF serializers for posts and media."""

from rest_framework import serializers

from apps.media.models import PostMedia
from apps.posts.models import Post


class PostAuthorSerializer(serializers.Serializer):
    username = serializers.CharField(source="author.username", read_only=True)
    name = serializers.SerializerMethodField()
    avatar = serializers.SerializerMethodField()
    headline = serializers.SerializerMethodField()

    def get_name(self, obj: Post) -> str:
        return obj.author.full_name

    def get_avatar(self, obj: Post):
        profile = getattr(obj.author, "profile", None)
        avatar = getattr(profile, "avatar", None) if profile else None
        if not avatar:
            return None
        request = self.context.get("request")
        url = avatar.url
        if request is not None:
            return request.build_absolute_uri(url)
        return url

    def get_headline(self, obj: Post) -> str:
        profile = getattr(obj.author, "profile", None)
        headline = getattr(profile, "headline", "") if profile else ""
        return (headline or "").strip()


class PostMediaSerializer(serializers.ModelSerializer):
    url = serializers.SerializerMethodField()
    thumbnail_url = serializers.SerializerMethodField()

    class Meta:
        model = PostMedia
        fields = [
            "id",
            "media_type",
            "url",
            "thumbnail_url",
            "order",
            "processing_status",
            "width",
            "height",
            "duration",
            "file_size",
            "created_at",
        ]

    def _absolute(self, field_file):
        if not field_file:
            return None
        request = self.context.get("request")
        url = field_file.url
        if request is not None:
            return request.build_absolute_uri(url)
        return url

    def get_url(self, obj: PostMedia):
        return self._absolute(obj.file)

    def get_thumbnail_url(self, obj: PostMedia):
        return self._absolute(obj.thumbnail)


class PostSerializer(serializers.Serializer):
    id = serializers.UUIDField(read_only=True)
    author = serializers.SerializerMethodField()
    content = serializers.CharField(read_only=True)
    visibility = serializers.CharField(read_only=True)
    status = serializers.CharField(read_only=True)
    media = PostMediaSerializer(many=True, read_only=True)
    reaction_count = serializers.SerializerMethodField()
    comment_count = serializers.SerializerMethodField()
    user_reacted = serializers.SerializerMethodField()
    created_at = serializers.DateTimeField(read_only=True)
    updated_at = serializers.DateTimeField(read_only=True)
    published_at = serializers.DateTimeField(read_only=True)

    def get_author(self, obj: Post) -> dict:
        return PostAuthorSerializer(obj, context=self.context).data

    def get_reaction_count(self, obj: Post) -> int:
        return int(getattr(obj, "reaction_count", 0) or 0)

    def get_comment_count(self, obj: Post) -> int:
        return int(getattr(obj, "comment_count", 0) or 0)

    def get_user_reacted(self, obj: Post) -> bool:
        value = getattr(obj, "user_reacted", None)
        if value is None:
            return False
        return bool(value)


class PostShareSerializer(serializers.Serializer):
    url = serializers.URLField()
    title = serializers.CharField()


class PostCreateSerializer(serializers.Serializer):
    content = serializers.CharField(
        required=False,
        allow_blank=True,
        max_length=5000,
        default="",
    )
    visibility = serializers.ChoiceField(
        choices=[Post.Visibility.PUBLIC, Post.Visibility.PRIVATE],
        default=Post.Visibility.PUBLIC,
        required=False,
    )
    media = serializers.ListField(
        child=serializers.FileField(),
        required=False,
        allow_empty=True,
        max_length=10,
    )

    def to_internal_value(self, data):
        # Multipart QueryDict + TemporaryUploadedFile cannot be deep-copied.
        # Normalize into a plain dict for ListField(FileField).
        if hasattr(data, "getlist"):
            files = data.getlist("media") or data.getlist("media[]") or []
            files = [f for f in files if f]
            payload = {
                "content": data.get("content", ""),
                "visibility": data.get("visibility", Post.Visibility.PUBLIC),
            }
            if files:
                payload["media"] = files
            data = payload
        elif (
            isinstance(data, dict)
            and "media" in data
            and not isinstance(data.get("media"), (list, tuple))
        ):
            media = data.get("media")
            data = {**data, "media": [media] if media else []}
        return super().to_internal_value(data)


class PostUpdateSerializer(serializers.Serializer):
    content = serializers.CharField(
        required=False,
        allow_blank=True,
        max_length=5000,
    )
    visibility = serializers.ChoiceField(
        choices=[Post.Visibility.PUBLIC, Post.Visibility.PRIVATE],
        required=False,
    )
