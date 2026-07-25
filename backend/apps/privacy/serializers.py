"""Privacy API serializers."""

from rest_framework import serializers

from apps.privacy.models import PrivacySetting


class PrivacySettingSerializer(serializers.ModelSerializer):
    class Meta:
        model = PrivacySetting
        fields = (
            "profile_visibility",
            "post_visibility",
            "connection_visibility",
            "message_permission",
            "created_at",
            "updated_at",
        )
        read_only_fields = ("created_at", "updated_at")


class PrivacySettingUpdateSerializer(serializers.Serializer):
    profile_visibility = serializers.ChoiceField(
        choices=PrivacySetting.ProfileVisibility.choices,
        required=False,
    )
    post_visibility = serializers.ChoiceField(
        choices=PrivacySetting.PostVisibility.choices,
        required=False,
    )
    connection_visibility = serializers.ChoiceField(
        choices=PrivacySetting.ConnectionVisibility.choices,
        required=False,
    )
    message_permission = serializers.ChoiceField(
        choices=PrivacySetting.MessagePermission.choices,
        required=False,
    )
