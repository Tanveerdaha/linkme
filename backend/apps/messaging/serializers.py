"""DRF serializers for messaging."""

import json

from rest_framework import serializers

from apps.messaging.models import Message
from apps.messaging.validators import (
    infer_message_type_from_file,
    validate_message_attachment,
)


class ParticipantSerializer(serializers.Serializer):
    username = serializers.CharField()
    name = serializers.CharField()
    avatar = serializers.CharField(allow_null=True)
    headline = serializers.CharField(allow_blank=True)
    is_online = serializers.BooleanField(required=False)


class ConversationListItemSerializer(serializers.Serializer):
    id = serializers.UUIDField()
    participant = ParticipantSerializer()
    last_message = serializers.CharField(allow_null=True, allow_blank=True)
    last_message_at = serializers.DateTimeField(allow_null=True)
    unread_count = serializers.IntegerField()
    is_muted = serializers.BooleanField(required=False)


class ConversationDetailSerializer(serializers.Serializer):
    id = serializers.UUIDField()
    participant = ParticipantSerializer()
    created_at = serializers.DateTimeField()
    is_muted = serializers.BooleanField(required=False)


class CreateConversationSerializer(serializers.Serializer):
    username = serializers.CharField(max_length=30)


class MessageSerializer(serializers.Serializer):
    id = serializers.UUIDField()
    sender = serializers.CharField()
    content = serializers.CharField(allow_blank=True)
    message_type = serializers.CharField()
    attachment = serializers.CharField(allow_null=True, required=False)
    metadata = serializers.DictField(required=False)
    created_at = serializers.DateTimeField()
    updated_at = serializers.DateTimeField(required=False)
    is_deleted = serializers.BooleanField()
    status = serializers.CharField(allow_null=True, required=False)


class SendMessageSerializer(serializers.Serializer):
    content = serializers.CharField(
        max_length=5000, required=False, allow_blank=True, default=""
    )
    attachment = serializers.FileField(required=False, allow_null=True)
    message_type = serializers.ChoiceField(
        choices=Message.MessageType.choices,
        required=False,
        allow_null=True,
    )
    metadata = serializers.JSONField(required=False, default=dict)

    def to_internal_value(self, data):
        # Multipart forms send metadata as a JSON string; QueryDict cannot
        # safely store a parsed dict, so normalize to a plain mapping first.
        if hasattr(data, "lists"):
            data = {key: data.get(key) for key in data.keys()}
        elif hasattr(data, "copy"):
            data = data.copy()
        else:
            data = dict(data)

        raw = data.get("metadata")
        if isinstance(raw, str):
            try:
                data["metadata"] = json.loads(raw or "{}")
            except json.JSONDecodeError as exc:
                raise serializers.ValidationError(
                    {"metadata": "Invalid JSON metadata."}
                ) from exc
        return super().to_internal_value(data)

    def validate(self, attrs):
        content = (attrs.get("content") or "").strip()
        attachment = attrs.get("attachment")
        message_type = (attrs.get("message_type") or "").upper() or None
        metadata = attrs.get("metadata") or {}
        if not isinstance(metadata, dict):
            raise serializers.ValidationError(
                {"metadata": "Metadata must be an object."}
            )

        if attachment is not None:
            resolved = message_type or infer_message_type_from_file(attachment)
            try:
                validate_message_attachment(attachment, resolved)
            except Exception as exc:
                from django.core.exceptions import (
                    ValidationError as DjangoValidationError,
                )

                if isinstance(exc, DjangoValidationError):
                    raise serializers.ValidationError(
                        {"attachment": list(exc.messages)}
                    ) from exc
                raise
            attrs["message_type"] = resolved
        elif message_type == Message.MessageType.LINK:
            url = (metadata.get("url") or content or "").strip()
            if not url:
                raise serializers.ValidationError(
                    {"metadata": "Provide a URL for link messages."}
                )
            attrs["message_type"] = Message.MessageType.LINK
            metadata = {**metadata, "url": url}
        else:
            if not content:
                raise serializers.ValidationError(
                    {"content": "Provide message content or an attachment."}
                )
            attrs["message_type"] = Message.MessageType.TEXT

        attrs["content"] = content
        attrs["metadata"] = metadata
        return attrs


class MuteConversationSerializer(serializers.Serializer):
    is_muted = serializers.BooleanField()
