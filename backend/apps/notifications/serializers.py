"""DRF serializers for notifications."""

from rest_framework import serializers


class NotificationSenderSerializer(serializers.Serializer):
    username = serializers.CharField()
    name = serializers.CharField()
    avatar = serializers.CharField(allow_null=True)


class NotificationSerializer(serializers.Serializer):
    id = serializers.UUIDField()
    type = serializers.CharField()
    notification_type = serializers.CharField(required=False)
    sender = NotificationSenderSerializer(allow_null=True)
    message = serializers.CharField()
    object_type = serializers.CharField(allow_blank=True)
    object_id = serializers.CharField(allow_blank=True)
    is_read = serializers.BooleanField()
    created_at = serializers.DateTimeField()
    read_at = serializers.DateTimeField(allow_null=True, required=False)


class UnreadCountSerializer(serializers.Serializer):
    count = serializers.IntegerField()


class NotificationPreferenceSerializer(serializers.Serializer):
    post_reactions_enabled = serializers.BooleanField()
    comments_enabled = serializers.BooleanField()
    connection_enabled = serializers.BooleanField()
    messages_enabled = serializers.BooleanField()
