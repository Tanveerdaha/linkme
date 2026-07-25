"""DRF serializers for profiles."""

from rest_framework import serializers

from apps.profiles.models import Profile
from apps.profiles.validators import MAX_IMAGE_SIZE_BYTES


class InterestsField(serializers.ListField):
    child = serializers.CharField(max_length=50)

    def __init__(self, **kwargs):
        kwargs.setdefault("max_length", 20)
        kwargs.setdefault("allow_empty", True)
        super().__init__(**kwargs)


class ImageUploadField(serializers.ImageField):
    def to_internal_value(self, data):
        file_obj = super().to_internal_value(data)
        if file_obj.size > MAX_IMAGE_SIZE_BYTES:
            raise serializers.ValidationError("Image file size must not exceed 5 MB.")
        content_type = getattr(data, "content_type", "") or ""
        allowed = {"image/jpeg", "image/png", "image/webp"}
        if content_type and content_type not in allowed:
            raise serializers.ValidationError(
                "Allowed image types: jpg, jpeg, png, webp."
            )
        return file_obj


class ProfileStatisticsSerializer(serializers.Serializer):
    posts = serializers.IntegerField()
    media = serializers.IntegerField()
    profile_views = serializers.IntegerField(required=False)


class ProfileCompletionSerializer(serializers.Serializer):
    percentage = serializers.IntegerField()
    missing = serializers.ListField(child=serializers.CharField())


class MeProfileSerializer(serializers.Serializer):
    id = serializers.UUIDField(source="user.id", read_only=True)
    username = serializers.CharField(source="user.username", read_only=True)
    email = serializers.EmailField(source="user.email", read_only=True, allow_null=True)
    phone_number = serializers.CharField(
        source="user.phone_number",
        read_only=True,
        allow_null=True,
        allow_blank=True,
        required=False,
    )
    first_name = serializers.CharField(source="user.first_name", read_only=True)
    last_name = serializers.CharField(source="user.last_name", read_only=True)
    name = serializers.SerializerMethodField()
    avatar = serializers.ImageField(read_only=True)
    cover_image = serializers.ImageField(read_only=True)
    bio = serializers.CharField(read_only=True)
    headline = serializers.CharField(read_only=True)
    location = serializers.CharField(read_only=True)
    website = serializers.URLField(read_only=True)
    interests = InterestsField(read_only=True)
    pronouns = serializers.CharField(read_only=True)
    birth_date = serializers.DateField(read_only=True, allow_null=True)
    social_links = serializers.JSONField(read_only=True)
    profile_visibility = serializers.CharField(read_only=True)
    connection_visibility = serializers.CharField(read_only=True)
    created_at = serializers.DateTimeField(read_only=True)

    def get_name(self, obj: Profile) -> str:
        return obj.user.full_name


class ProfileUpdateSerializer(serializers.Serializer):
    username = serializers.CharField(min_length=3, max_length=30, required=False)
    first_name = serializers.CharField(max_length=150, required=False, allow_blank=True)
    last_name = serializers.CharField(max_length=150, required=False, allow_blank=True)
    bio = serializers.CharField(max_length=2000, required=False, allow_blank=True)
    headline = serializers.CharField(max_length=200, required=False, allow_blank=True)
    location = serializers.CharField(max_length=120, required=False, allow_blank=True)
    website = serializers.URLField(max_length=300, required=False, allow_blank=True)
    interests = serializers.JSONField(required=False)
    pronouns = serializers.CharField(max_length=50, required=False, allow_blank=True)
    birth_date = serializers.DateField(required=False, allow_null=True)
    social_links = serializers.JSONField(required=False)
    profile_visibility = serializers.ChoiceField(
        choices=Profile.Visibility.choices,
        required=False,
    )
    connection_visibility = serializers.ChoiceField(
        choices=Profile.ConnectionVisibility.choices,
        required=False,
    )
    avatar = ImageUploadField(required=False, allow_null=True)
    cover_image = ImageUploadField(required=False, allow_null=True)

    def validate_username(self, value):
        from apps.accounts.validators import validate_username

        return validate_username(value)

    def validate_interests(self, value):
        if value is None:
            return []
        if isinstance(value, str):
            value = [part.strip() for part in value.split(",") if part.strip()]
        if not isinstance(value, list):
            raise serializers.ValidationError("Interests must be a list of strings.")
        cleaned = []
        for item in value:
            if not isinstance(item, str):
                raise serializers.ValidationError("Each interest must be a string.")
            item = item.strip()
            if not item:
                continue
            if len(item) > 50:
                raise serializers.ValidationError(
                    "Each interest must be at most 50 characters."
                )
            cleaned.append(item)
        if len(cleaned) > 20:
            raise serializers.ValidationError("At most 20 interests are allowed.")
        return cleaned

    def validate_social_links(self, value):
        if value is None:
            return {}
        if not isinstance(value, dict):
            raise serializers.ValidationError("social_links must be an object.")
        cleaned = {}
        for key, url in value.items():
            if not isinstance(key, str) or not isinstance(url, str):
                raise serializers.ValidationError(
                    "social_links keys and values must be strings."
                )
            key = key.strip()[:40]
            url = url.strip()[:300]
            if key and url:
                cleaned[key] = url
        if len(cleaned) > 10:
            raise serializers.ValidationError("At most 10 social links are allowed.")
        return cleaned


class PublicProfileSerializer(serializers.Serializer):
    id = serializers.UUIDField(source="user.id", read_only=True)
    username = serializers.CharField(source="user.username", read_only=True)
    name = serializers.SerializerMethodField()
    avatar = serializers.ImageField(read_only=True)
    cover_image = serializers.ImageField(read_only=True)
    bio = serializers.CharField(read_only=True)
    headline = serializers.CharField(read_only=True)
    location = serializers.CharField(read_only=True)
    website = serializers.URLField(read_only=True)
    interests = InterestsField(read_only=True)
    pronouns = serializers.CharField(read_only=True)
    social_links = serializers.JSONField(read_only=True)
    joined_date = serializers.DateTimeField(source="user.created_at", read_only=True)

    def get_name(self, obj: Profile) -> str:
        return obj.user.full_name


class UserSearchResultSerializer(serializers.Serializer):
    username = serializers.CharField(source="user.username", read_only=True)
    name = serializers.SerializerMethodField()
    avatar = serializers.ImageField(read_only=True)
    headline = serializers.CharField(read_only=True)
    location = serializers.CharField(read_only=True)

    def get_name(self, obj: Profile) -> str:
        return obj.user.full_name


class SuggestedUserSerializer(serializers.Serializer):
    username = serializers.CharField(source="user.username", read_only=True)
    name = serializers.SerializerMethodField()
    avatar = serializers.ImageField(read_only=True)
    headline = serializers.CharField(read_only=True)

    def get_name(self, obj: Profile) -> str:
        return obj.user.full_name


class ActivityItemSerializer(serializers.Serializer):
    type = serializers.CharField()
    content = serializers.CharField()
    created_at = serializers.DateTimeField()
    ref_id = serializers.CharField(required=False)
    post_id = serializers.CharField(required=False)
    reaction_type = serializers.CharField(required=False)


class MediaItemSerializer(serializers.Serializer):
    id = serializers.CharField()
    media_type = serializers.CharField()
    url = serializers.CharField(allow_null=True)
    thumbnail_url = serializers.CharField(allow_null=True, required=False)
    post_id = serializers.CharField()
    created_at = serializers.DateTimeField()
    width = serializers.IntegerField(allow_null=True)
    height = serializers.IntegerField(allow_null=True)
    duration = serializers.FloatField(allow_null=True, required=False)
    processing_status = serializers.CharField()


class ProfileMediaGallerySerializer(serializers.Serializer):
    images = MediaItemSerializer(many=True)
    videos = MediaItemSerializer(many=True)
