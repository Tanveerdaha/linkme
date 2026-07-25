"""DRF serializers for network connections."""

from rest_framework import serializers

from apps.network.models import Connection
from apps.profiles.models import Profile


class NetworkUserSerializer(serializers.Serializer):
    username = serializers.CharField(source="user.username", read_only=True)
    name = serializers.SerializerMethodField()
    avatar = serializers.ImageField(read_only=True)
    headline = serializers.CharField(read_only=True)

    def get_name(self, obj: Profile) -> str:
        return obj.user.full_name


class ConnectionStatusSerializer(serializers.Serializer):
    status = serializers.CharField()
    can_connect = serializers.BooleanField()
    connection_id = serializers.CharField(required=False, allow_null=True)
    is_self = serializers.BooleanField(required=False)


class ConnectionRequestCreateSerializer(serializers.Serializer):
    message = serializers.CharField(
        max_length=300, required=False, allow_blank=True, default=""
    )


class ConnectionListItemSerializer(serializers.Serializer):
    username = serializers.CharField()
    name = serializers.CharField()
    avatar = serializers.ImageField(allow_null=True)
    headline = serializers.CharField(allow_blank=True)
    connected_at = serializers.DateTimeField(allow_null=True)


class ConnectionRequestSerializer(serializers.Serializer):
    id = serializers.UUIDField()
    user = serializers.SerializerMethodField()
    message = serializers.CharField()
    created_at = serializers.DateTimeField()

    def get_user(self, obj: Connection) -> dict:
        # For received requests, show sender; for sent, show receiver.
        direction = self.context.get("direction", "received")
        person = obj.sender if direction == "received" else obj.receiver
        profile = getattr(person, "profile", None)
        request = self.context.get("request")
        avatar = None
        if profile and profile.avatar:
            url = profile.avatar.url
            avatar = request.build_absolute_uri(url) if request else url
        return {
            "username": person.username,
            "name": person.full_name,
            "avatar": avatar,
            "headline": getattr(profile, "headline", "") or "",
        }


class DiscoverUserSerializer(serializers.Serializer):
    username = serializers.CharField()
    name = serializers.CharField()
    avatar = serializers.ImageField(allow_null=True)
    headline = serializers.CharField(allow_blank=True)
    reason = serializers.CharField()


class MutualConnectionsSerializer(serializers.Serializer):
    count = serializers.IntegerField()
    users = NetworkUserSerializer(many=True)
