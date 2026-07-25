"""DRF serializers for moderation / safety APIs."""

from rest_framework import serializers

from apps.moderation.models import BlockedUser, ModerationAction, Report


class BlockUserSerializer(serializers.Serializer):
    reason = serializers.CharField(required=False, allow_blank=True, max_length=255)


class BlockedUserSerializer(serializers.ModelSerializer):
    username = serializers.CharField(source="blocked_user.username", read_only=True)
    avatar = serializers.SerializerMethodField()
    blocked_at = serializers.DateTimeField(source="created_at", read_only=True)

    class Meta:
        model = BlockedUser
        fields = ("username", "avatar", "blocked_at", "reason")

    def get_avatar(self, obj) -> str | None:
        profile = getattr(obj.blocked_user, "profile", None)
        if profile is None or not profile.avatar:
            return None
        request = self.context.get("request")
        url = profile.avatar.url
        if request is not None:
            return request.build_absolute_uri(url)
        return url


class CreateReportSerializer(serializers.Serializer):
    content_type = serializers.ChoiceField(choices=Report.ContentTypeChoice.choices)
    object_id = serializers.CharField(max_length=64)
    reason = serializers.ChoiceField(choices=Report.Reason.choices)
    description = serializers.CharField(
        required=False, allow_blank=True, max_length=2000
    )


class ReportSerializer(serializers.ModelSerializer):
    reported_username = serializers.SerializerMethodField()

    class Meta:
        model = Report
        fields = (
            "id",
            "content_type_label",
            "object_id",
            "reason",
            "description",
            "status",
            "reported_username",
            "created_at",
            "updated_at",
        )
        read_only_fields = fields

    def get_reported_username(self, obj) -> str | None:
        if obj.reported_user_id:
            return obj.reported_user.username
        return None


class UpdateReportStatusSerializer(serializers.Serializer):
    status = serializers.ChoiceField(choices=Report.Status.choices)


class ModerationActionSerializer(serializers.Serializer):
    target_type = serializers.CharField(max_length=32)
    target_id = serializers.CharField(max_length=64)
    action = serializers.ChoiceField(choices=ModerationAction.Action.choices)
    reason = serializers.CharField(required=False, allow_blank=True)
    report_id = serializers.UUIDField(required=False, allow_null=True)
    suspend_days = serializers.IntegerField(required=False, min_value=1, max_value=365)


class ModerationActionReadSerializer(serializers.ModelSerializer):
    admin_username = serializers.SerializerMethodField()

    class Meta:
        model = ModerationAction
        fields = (
            "id",
            "admin_username",
            "target_type",
            "target_id",
            "action",
            "reason",
            "report",
            "created_at",
        )
        read_only_fields = fields

    def get_admin_username(self, obj) -> str | None:
        return obj.admin.username if obj.admin_id else None
