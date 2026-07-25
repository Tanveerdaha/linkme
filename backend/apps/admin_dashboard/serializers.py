"""Serializers for admin dashboard APIs."""

from rest_framework import serializers

from apps.admin_dashboard.models import AdminExportRequest, AdminRole
from apps.comments.models import Comment
from apps.moderation.models import AuditLog, ModerationAction, Report
from apps.posts.models import Post


class AdminUserListSerializer(serializers.Serializer):
    id = serializers.UUIDField()
    username = serializers.CharField()
    email = serializers.EmailField()
    status = serializers.SerializerMethodField()
    is_verified = serializers.BooleanField()
    is_staff = serializers.BooleanField()
    created_at = serializers.DateTimeField()
    avatar = serializers.SerializerMethodField()

    def get_status(self, obj) -> str:
        if getattr(obj, "is_deleted", False):
            return "DELETED"
        if getattr(obj, "is_suspended", False) and (
            not hasattr(obj, "is_currently_suspended") or obj.is_currently_suspended()
        ):
            return "SUSPENDED"
        if not obj.is_active:
            return "INACTIVE"
        return "ACTIVE"

    def get_avatar(self, obj) -> str | None:
        profile = getattr(obj, "profile", None)
        if profile is None or not profile.avatar:
            return None
        request = self.context.get("request")
        url = profile.avatar.url
        return request.build_absolute_uri(url) if request else url


class AdminUserDetailSerializer(serializers.Serializer):
    id = serializers.UUIDField()
    username = serializers.CharField()
    email = serializers.EmailField()
    first_name = serializers.CharField()
    last_name = serializers.CharField()
    status = serializers.SerializerMethodField()
    is_verified = serializers.BooleanField()
    is_staff = serializers.BooleanField()
    is_suspended = serializers.BooleanField()
    suspended_until = serializers.DateTimeField(allow_null=True)
    suspension_reason = serializers.CharField()
    is_deleted = serializers.BooleanField()
    created_at = serializers.DateTimeField()
    admin_role = serializers.SerializerMethodField()
    posts_count = serializers.IntegerField()
    reports_count = serializers.IntegerField()
    connections_count = serializers.IntegerField()
    profile = serializers.SerializerMethodField()
    moderation_history = serializers.SerializerMethodField()
    recent_activity = serializers.SerializerMethodField()

    def get_status(self, obj) -> str:
        user = obj["user"]
        if user.is_deleted:
            return "DELETED"
        if user.is_currently_suspended():
            return "SUSPENDED"
        if not user.is_active:
            return "INACTIVE"
        return "ACTIVE"

    def get_admin_role(self, obj) -> dict | None:
        role = getattr(obj["user"], "admin_role", None)
        if role is None:
            return None
        return {"role": role.role, "permissions": role.permissions}

    def get_profile(self, obj) -> dict:
        user = obj["user"]
        profile = getattr(user, "profile", None)
        if profile is None:
            return {}
        return {
            "headline": profile.headline,
            "bio": profile.bio,
            "location": profile.location,
        }

    def get_moderation_history(self, obj) -> list:
        return ModerationActionReadSerializer(obj["moderation_history"], many=True).data

    def get_recent_activity(self, obj) -> list:
        return AuditLogSerializer(obj["recent_activity"], many=True).data

    def to_representation(self, instance):
        user = instance["user"]
        data = {
            "id": user.id,
            "username": user.username,
            "email": user.email,
            "first_name": user.first_name,
            "last_name": user.last_name,
            "is_verified": user.is_verified,
            "is_staff": user.is_staff,
            "is_suspended": user.is_suspended,
            "suspended_until": user.suspended_until,
            "suspension_reason": user.suspension_reason,
            "is_deleted": user.is_deleted,
            "created_at": user.created_at,
            "posts_count": instance["posts_count"],
            "reports_count": instance["reports_count"],
            "connections_count": instance["connections_count"],
        }
        # Use serializer fields for computed ones
        proxy = type("Proxy", (), data)()
        # Manual build
        result = dict(data)
        result["id"] = str(user.id)
        result["status"] = self.get_status(instance)
        result["admin_role"] = self.get_admin_role(instance)
        result["profile"] = self.get_profile(instance)
        result["moderation_history"] = self.get_moderation_history(instance)
        result["recent_activity"] = self.get_recent_activity(instance)
        return result


class SuspendUserSerializer(serializers.Serializer):
    reason = serializers.CharField(required=False, allow_blank=True, max_length=1000)
    duration = serializers.ChoiceField(
        choices=[
            "1_day",
            "3_days",
            "7_days",
            "14_days",
            "30_days",
            "permanent",
        ],
        default="7_days",
    )


class AdminPostSerializer(serializers.ModelSerializer):
    author = serializers.CharField(source="author.username", read_only=True)
    reports = serializers.SerializerMethodField()

    class Meta:
        model = Post
        fields = (
            "id",
            "author",
            "content",
            "visibility",
            "status",
            "reports",
            "created_at",
            "published_at",
        )

    def get_reports(self, obj) -> int:
        return Report.objects.filter(
            content_type_label=Report.ContentTypeChoice.POST,
            object_id=str(obj.id),
        ).count()


class AdminCommentSerializer(serializers.ModelSerializer):
    author = serializers.CharField(source="author.username", read_only=True)
    post_id = serializers.UUIDField(source="post.id", read_only=True)

    class Meta:
        model = Comment
        fields = (
            "id",
            "author",
            "post_id",
            "content",
            "status",
            "created_at",
        )


class AdminReportSerializer(serializers.ModelSerializer):
    reporter = serializers.CharField(source="reporter.username", read_only=True)
    target = serializers.SerializerMethodField()
    reported_user = serializers.SerializerMethodField()

    class Meta:
        model = Report
        fields = (
            "id",
            "reporter",
            "reason",
            "target",
            "reported_user",
            "content_type_label",
            "object_id",
            "description",
            "status",
            "created_at",
            "updated_at",
        )

    def get_target(self, obj) -> str:
        return f"{obj.content_type_label}:{obj.object_id}"

    def get_reported_user(self, obj) -> str | None:
        return obj.reported_user.username if obj.reported_user_id else None


class UpdateReportSerializer(serializers.Serializer):
    status = serializers.CharField()
    note = serializers.CharField(required=False, allow_blank=True)


class ModerationActionReadSerializer(serializers.ModelSerializer):
    admin = serializers.SerializerMethodField()
    date = serializers.DateTimeField(source="created_at", read_only=True)

    class Meta:
        model = ModerationAction
        fields = (
            "id",
            "admin",
            "action",
            "reason",
            "target_type",
            "target_id",
            "date",
            "created_at",
        )

    def get_admin(self, obj) -> str:
        return obj.admin.username if obj.admin_id else ""


class AuditLogSerializer(serializers.ModelSerializer):
    user = serializers.SerializerMethodField()
    object = serializers.SerializerMethodField()
    time = serializers.DateTimeField(source="created_at", read_only=True)

    class Meta:
        model = AuditLog
        fields = (
            "id",
            "user",
            "action",
            "object_type",
            "object_id",
            "object",
            "metadata",
            "time",
            "created_at",
        )

    def get_user(self, obj) -> str:
        return obj.user.username if obj.user_id else ""

    def get_object(self, obj) -> str:
        return obj.object_id or ""


class AdminExportSerializer(serializers.Serializer):
    export_type = serializers.ChoiceField(choices=AdminExportRequest.ExportType.choices)
    format = serializers.ChoiceField(
        choices=AdminExportRequest.Format.choices, default="CSV"
    )
    filters = serializers.DictField(required=False)


class AdminRoleSerializer(serializers.ModelSerializer):
    username = serializers.CharField(source="user.username", read_only=True)

    class Meta:
        model = AdminRole
        fields = ("id", "username", "role", "permissions", "created_at", "updated_at")


class AssignRoleSerializer(serializers.Serializer):
    user_id = serializers.UUIDField()
    role = serializers.ChoiceField(choices=AdminRole.Role.choices)


class ReasonSerializer(serializers.Serializer):
    reason = serializers.CharField(required=False, allow_blank=True, max_length=1000)
