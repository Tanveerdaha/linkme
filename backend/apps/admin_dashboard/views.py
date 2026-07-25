"""Admin dashboard API views."""

from drf_spectacular.utils import OpenApiParameter, extend_schema
from rest_framework import status
from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.admin_dashboard import selectors, services
from apps.admin_dashboard.models import AdminPermissionCode
from apps.admin_dashboard.permissions import HasAdminPermission, IsAdminUser
from apps.admin_dashboard.serializers import (
    AdminCommentSerializer,
    AdminExportSerializer,
    AdminPostSerializer,
    AdminReportSerializer,
    AdminUserDetailSerializer,
    AdminUserListSerializer,
    AssignRoleSerializer,
    AuditLogSerializer,
    ModerationActionReadSerializer,
    ReasonSerializer,
    SuspendUserSerializer,
    UpdateReportSerializer,
)
from apps.moderation import services as moderation_services
from apps.moderation.serializers import ModerationActionSerializer


class AdminPagination(PageNumberPagination):
    page_size = 25
    page_size_query_param = "page_size"
    max_page_size = 100


class AnalyticsOverviewView(APIView):
    permission_classes = [IsAdminUser, HasAdminPermission]
    required_admin_permissions = [
        AdminPermissionCode.VIEW_ANALYTICS,
        AdminPermissionCode.VIEW_DASHBOARD,
    ]

    @extend_schema(responses={200: dict}, tags=["admin"], summary="Analytics overview")
    def get(self, request):
        return Response(selectors.analytics_overview())


class AnalyticsTrendsView(APIView):
    permission_classes = [IsAdminUser, HasAdminPermission]
    required_admin_permission = AdminPermissionCode.VIEW_ANALYTICS

    @extend_schema(responses={200: dict}, tags=["admin"], summary="Analytics trends")
    def get(self, request):
        days = int(request.query_params.get("days", 14))
        days = max(1, min(days, 90))
        return Response(selectors.analytics_trends(days=days))


class AnalyticsMetricsView(APIView):
    permission_classes = [IsAdminUser, HasAdminPermission]
    required_admin_permission = AdminPermissionCode.VIEW_ANALYTICS

    @extend_schema(responses={200: dict}, tags=["admin"], summary="Daily metrics")
    def get(self, request):
        return Response(selectors.analytics_metrics())


class AdminUserListView(APIView):
    permission_classes = [IsAdminUser, HasAdminPermission]
    required_admin_permission = AdminPermissionCode.VIEW_USERS

    @extend_schema(
        parameters=[
            OpenApiParameter("search", str, required=False),
            OpenApiParameter("status", str, required=False),
            OpenApiParameter("verified", str, required=False),
            OpenApiParameter("suspended", str, required=False),
        ],
        responses={200: AdminUserListSerializer(many=True)},
        tags=["admin"],
        summary="List users",
    )
    def get(self, request):
        qs = selectors.list_users(params=request.query_params)
        paginator = AdminPagination()
        page = paginator.paginate_queryset(qs, request, view=self)
        data = AdminUserListSerializer(page, many=True, context={"request": request}).data
        return paginator.get_paginated_response(data)


class AdminUserDetailView(APIView):
    permission_classes = [IsAdminUser, HasAdminPermission]
    required_admin_permission = AdminPermissionCode.VIEW_USERS

    @extend_schema(responses={200: dict}, tags=["admin"], summary="User detail")
    def get(self, request, user_id):
        detail = selectors.get_user_detail(user_id)
        if detail is None:
            return Response({"detail": "User not found."}, status=404)
        return Response(AdminUserDetailSerializer(detail).data)


class AdminUserSuspendView(APIView):
    permission_classes = [IsAdminUser, HasAdminPermission]
    required_admin_permission = AdminPermissionCode.SUSPEND_USERS

    @extend_schema(request=SuspendUserSerializer, responses={200: dict}, tags=["admin"])
    def post(self, request, user_id):
        serializer = SuspendUserSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = services.suspend_user(
            actor=request.user, user_id=user_id, **serializer.validated_data
        )
        return Response(
            {
                "suspended": True,
                "username": user.username,
                "suspended_until": user.suspended_until,
            }
        )


class AdminUserUnsuspendView(APIView):
    permission_classes = [IsAdminUser, HasAdminPermission]
    required_admin_permission = AdminPermissionCode.SUSPEND_USERS

    @extend_schema(responses={200: dict}, tags=["admin"])
    def post(self, request, user_id):
        user = services.unsuspend_user(actor=request.user, user_id=user_id)
        return Response({"suspended": False, "username": user.username})


class AdminUserDeactivateView(APIView):
    permission_classes = [IsAdminUser, HasAdminPermission]
    required_admin_permission = AdminPermissionCode.MANAGE_USERS

    @extend_schema(request=ReasonSerializer, responses={200: dict}, tags=["admin"])
    def post(self, request, user_id):
        serializer = ReasonSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = services.deactivate_user(
            actor=request.user,
            user_id=user_id,
            reason=serializer.validated_data.get("reason", ""),
        )
        return Response({"deactivated": True, "username": user.username})


class AdminUserDeleteView(APIView):
    permission_classes = [IsAdminUser, HasAdminPermission]
    required_admin_permission = AdminPermissionCode.DELETE_USERS

    @extend_schema(request=ReasonSerializer, responses={200: dict}, tags=["admin"])
    def post(self, request, user_id):
        serializer = ReasonSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = services.soft_delete_user(
            actor=request.user,
            user_id=user_id,
            reason=serializer.validated_data.get("reason", ""),
        )
        return Response({"deleted": True, "username": user.username})


class AdminPostListView(APIView):
    permission_classes = [IsAdminUser, HasAdminPermission]
    required_admin_permission = AdminPermissionCode.VIEW_CONTENT

    @extend_schema(responses={200: AdminPostSerializer(many=True)}, tags=["admin"])
    def get(self, request):
        qs = selectors.list_posts(params=request.query_params)
        paginator = AdminPagination()
        page = paginator.paginate_queryset(qs, request, view=self)
        data = AdminPostSerializer(page, many=True).data
        return paginator.get_paginated_response(data)


class AdminPostDeleteView(APIView):
    permission_classes = [IsAdminUser, HasAdminPermission]
    required_admin_permission = AdminPermissionCode.REMOVE_CONTENT

    @extend_schema(request=ReasonSerializer, responses={200: dict}, tags=["admin"])
    def delete(self, request, post_id):
        serializer = ReasonSerializer(data=request.data or {})
        serializer.is_valid(raise_exception=True)
        post = services.remove_post(
            actor=request.user,
            post_id=post_id,
            reason=serializer.validated_data.get("reason", ""),
        )
        return Response({"removed": True, "id": str(post.id)})


class AdminPostRestoreView(APIView):
    permission_classes = [IsAdminUser, HasAdminPermission]
    required_admin_permission = AdminPermissionCode.RESTORE_CONTENT

    @extend_schema(responses={200: dict}, tags=["admin"])
    def post(self, request, post_id):
        post = services.restore_post(actor=request.user, post_id=post_id)
        return Response({"restored": True, "id": str(post.id)})


class AdminCommentListView(APIView):
    permission_classes = [IsAdminUser, HasAdminPermission]
    required_admin_permission = AdminPermissionCode.VIEW_CONTENT

    @extend_schema(responses={200: AdminCommentSerializer(many=True)}, tags=["admin"])
    def get(self, request):
        qs = selectors.list_comments(params=request.query_params)
        paginator = AdminPagination()
        page = paginator.paginate_queryset(qs, request, view=self)
        return paginator.get_paginated_response(
            AdminCommentSerializer(page, many=True).data
        )


class AdminCommentRemoveView(APIView):
    permission_classes = [IsAdminUser, HasAdminPermission]
    required_admin_permission = AdminPermissionCode.REMOVE_CONTENT

    @extend_schema(request=ReasonSerializer, responses={200: dict}, tags=["admin"])
    def delete(self, request, comment_id):
        serializer = ReasonSerializer(data=request.data or {})
        serializer.is_valid(raise_exception=True)
        comment = services.remove_comment(
            actor=request.user,
            comment_id=comment_id,
            reason=serializer.validated_data.get("reason", ""),
        )
        return Response({"removed": True, "id": str(comment.id)})


class AdminCommentRestoreView(APIView):
    permission_classes = [IsAdminUser, HasAdminPermission]
    required_admin_permission = AdminPermissionCode.RESTORE_CONTENT

    @extend_schema(responses={200: dict}, tags=["admin"])
    def post(self, request, comment_id):
        comment = services.restore_comment(actor=request.user, comment_id=comment_id)
        return Response({"restored": True, "id": str(comment.id)})


class AdminReportListView(APIView):
    permission_classes = [IsAdminUser, HasAdminPermission]
    required_admin_permission = AdminPermissionCode.VIEW_REPORTS

    @extend_schema(responses={200: AdminReportSerializer(many=True)}, tags=["admin"])
    def get(self, request):
        qs = selectors.list_reports(params=request.query_params)
        paginator = AdminPagination()
        page = paginator.paginate_queryset(qs, request, view=self)
        return paginator.get_paginated_response(
            AdminReportSerializer(page, many=True).data
        )


class AdminReportDetailView(APIView):
    permission_classes = [IsAdminUser, HasAdminPermission]
    required_admin_permission = AdminPermissionCode.VIEW_REPORTS

    @extend_schema(responses={200: dict}, tags=["admin"])
    def get(self, request, report_id):
        report = moderation_services.get_report(report_id=report_id)
        data = AdminReportSerializer(report).data
        previous = Report_related(report)
        data["previous_reports"] = AdminReportSerializer(previous, many=True).data
        data["actions"] = ModerationActionReadSerializer(
            report.actions.select_related("admin").all()[:20], many=True
        ).data
        return Response(data)

    @extend_schema(request=UpdateReportSerializer, responses={200: AdminReportSerializer}, tags=["admin"])
    def patch(self, request, report_id):
        serializer = UpdateReportSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        report = services.update_report(
            actor=request.user,
            report_id=report_id,
            status=serializer.validated_data["status"],
            note=serializer.validated_data.get("note", ""),
        )
        return Response(AdminReportSerializer(report).data)


def Report_related(report):
    from apps.moderation.models import Report

    if not report.reported_user_id:
        return Report.objects.none()
    return (
        Report.objects.filter(reported_user=report.reported_user)
        .exclude(pk=report.pk)
        .order_by("-created_at")[:10]
    )


class AdminModerationHistoryView(APIView):
    permission_classes = [IsAdminUser, HasAdminPermission]
    required_admin_permission = AdminPermissionCode.VIEW_MODERATION

    @extend_schema(
        responses={200: ModerationActionReadSerializer(many=True)}, tags=["admin"]
    )
    def get(self, request):
        qs = selectors.list_moderation_history(params=request.query_params)
        paginator = AdminPagination()
        page = paginator.paginate_queryset(qs, request, view=self)
        return paginator.get_paginated_response(
            ModerationActionReadSerializer(page, many=True).data
        )


class AdminModerationActionView(APIView):
    permission_classes = [IsAdminUser, HasAdminPermission]
    required_admin_permission = AdminPermissionCode.TAKE_MODERATION_ACTION

    @extend_schema(request=ModerationActionSerializer, responses={201: dict}, tags=["admin"])
    def post(self, request):
        serializer = ModerationActionSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        action = moderation_services.take_moderation_action(
            admin=request.user, **serializer.validated_data
        )
        return Response(
            ModerationActionReadSerializer(action).data,
            status=status.HTTP_201_CREATED,
        )


class AdminAuditListView(APIView):
    permission_classes = [IsAdminUser, HasAdminPermission]
    required_admin_permission = AdminPermissionCode.VIEW_AUDIT

    @extend_schema(responses={200: AuditLogSerializer(many=True)}, tags=["admin"])
    def get(self, request):
        qs = selectors.list_audit_logs(params=request.query_params)
        paginator = AdminPagination()
        page = paginator.paginate_queryset(qs, request, view=self)
        return paginator.get_paginated_response(
            AuditLogSerializer(page, many=True).data
        )


class AdminExportView(APIView):
    permission_classes = [IsAdminUser, HasAdminPermission]
    required_admin_permission = AdminPermissionCode.EXPORT_DATA

    @extend_schema(request=AdminExportSerializer, responses={202: dict}, tags=["admin"])
    def post(self, request):
        serializer = AdminExportSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        export = services.request_export(
            actor=request.user, **serializer.validated_data
        )
        return Response(
            {
                "id": str(export.id),
                "status": export.status,
                "export_type": export.export_type,
                "format": export.format,
            },
            status=status.HTTP_202_ACCEPTED,
        )

    @extend_schema(responses={200: dict}, tags=["admin"])
    def get(self, request):
        from apps.admin_dashboard.models import AdminExportRequest

        export_id = request.query_params.get("id")
        if export_id:
            export = AdminExportRequest.objects.filter(
                pk=export_id, requested_by=request.user
            ).first()
            if export is None:
                return Response({"detail": "Not found."}, status=404)
            url = None
            if export.file:
                url = request.build_absolute_uri(export.file.url)
            return Response(
                {
                    "id": str(export.id),
                    "status": export.status,
                    "download_url": url,
                    "error_message": export.error_message or None,
                }
            )
        latest = (
            AdminExportRequest.objects.filter(requested_by=request.user)
            .order_by("-created_at")[:10]
        )
        return Response(
            {
                "results": [
                    {
                        "id": str(e.id),
                        "status": e.status,
                        "export_type": e.export_type,
                        "format": e.format,
                        "created_at": e.created_at,
                    }
                    for e in latest
                ]
            }
        )


class AdminMeView(APIView):
    permission_classes = [IsAdminUser]

    @extend_schema(responses={200: dict}, tags=["admin"], summary="Current admin profile")
    def get(self, request):
        from apps.admin_dashboard.permissions import get_admin_role, user_has_admin_permission
        from apps.admin_dashboard.models import AdminPermissionCode, ROLE_DEFAULT_PERMISSIONS
        from apps.admin_dashboard.models import AdminRole

        role = get_admin_role(request.user)
        if role:
            permissions = role.permissions
            role_name = role.role
        elif request.user.is_superuser:
            permissions = list(AdminPermissionCode.ALL)
            role_name = "SUPER_ADMIN"
        else:
            permissions = list(ROLE_DEFAULT_PERMISSIONS.get(AdminRole.Role.MODERATOR, []))
            role_name = "MODERATOR"

        return Response(
            {
                "id": str(request.user.id),
                "username": request.user.username,
                "email": request.user.email,
                "role": role_name,
                "permissions": permissions,
                "is_superuser": request.user.is_superuser,
            }
        )


class AdminAssignRoleView(APIView):
    permission_classes = [IsAdminUser, HasAdminPermission]
    required_admin_permission = AdminPermissionCode.MANAGE_ADMINS

    @extend_schema(request=AssignRoleSerializer, responses={200: dict}, tags=["admin"])
    def post(self, request):
        serializer = AssignRoleSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        from django.contrib.auth import get_user_model

        User = get_user_model()
        user = User.objects.filter(pk=serializer.validated_data["user_id"]).first()
        if user is None:
            return Response({"detail": "User not found."}, status=404)
        role = services.ensure_admin_role(
            user=user,
            role=serializer.validated_data["role"],
            actor=request.user,
        )
        return Response(
            {"username": user.username, "role": role.role, "permissions": role.permissions}
        )
