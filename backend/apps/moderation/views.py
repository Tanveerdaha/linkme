"""API views for blocking, reporting, and staff moderation."""

from drf_spectacular.utils import extend_schema
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.moderation import services
from apps.moderation.permissions import IsAuthenticatedVerified, IsStaffModerator
from apps.moderation.serializers import (
    BlockedUserSerializer,
    BlockUserSerializer,
    CreateReportSerializer,
    ModerationActionReadSerializer,
    ModerationActionSerializer,
    ReportSerializer,
    UpdateReportStatusSerializer,
)
from apps.moderation.throttling import BlockActionThrottle, ReportCreateThrottle


class BlockUserView(APIView):
    permission_classes = [IsAuthenticatedVerified]
    throttle_classes = [BlockActionThrottle]

    @extend_schema(
        request=BlockUserSerializer,
        responses={200: dict},
        tags=["moderation"],
        summary="Block a user",
    )
    def post(self, request, username: str):
        serializer = BlockUserSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        services.block_user(
            blocker=request.user,
            username=username,
            reason=serializer.validated_data.get("reason", ""),
        )
        return Response({"blocked": True})

    @extend_schema(
        responses={204: None},
        tags=["moderation"],
        summary="Unblock a user",
    )
    def delete(self, request, username: str):
        services.unblock_user(blocker=request.user, username=username)
        return Response(status=status.HTTP_204_NO_CONTENT)


class BlockedUsersListView(APIView):
    permission_classes = [IsAuthenticatedVerified]

    @extend_schema(
        responses={200: BlockedUserSerializer(many=True)},
        tags=["moderation"],
        summary="List blocked users",
    )
    def get(self, request):
        qs = services.list_blocked_users(user=request.user)
        data = BlockedUserSerializer(qs, many=True, context={"request": request}).data
        return Response({"results": data})


class ReportCreateView(APIView):
    permission_classes = [IsAuthenticatedVerified]
    throttle_classes = [ReportCreateThrottle]

    @extend_schema(
        request=CreateReportSerializer,
        responses={201: ReportSerializer},
        tags=["moderation"],
        summary="Create a report",
    )
    def post(self, request):
        serializer = CreateReportSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        report = services.create_report(
            reporter=request.user, **serializer.validated_data
        )
        return Response(
            ReportSerializer(report).data,
            status=status.HTTP_201_CREATED,
        )


class MyReportsView(APIView):
    permission_classes = [IsAuthenticatedVerified]

    @extend_schema(
        responses={200: ReportSerializer(many=True)},
        tags=["moderation"],
        summary="List my reports",
    )
    def get(self, request):
        qs = services.list_my_reports(user=request.user)
        return Response({"results": ReportSerializer(qs, many=True).data})


class ModerationReportListView(APIView):
    permission_classes = [IsStaffModerator]

    @extend_schema(
        responses={200: ReportSerializer(many=True)},
        tags=["moderation"],
        summary="Staff: list reports",
    )
    def get(self, request):
        status_filter = request.query_params.get("status")
        qs = services.list_pending_reports(status=status_filter)
        return Response({"results": ReportSerializer(qs, many=True).data})


class ModerationReportDetailView(APIView):
    permission_classes = [IsStaffModerator]

    @extend_schema(
        responses={200: ReportSerializer},
        tags=["moderation"],
        summary="Staff: report detail",
    )
    def get(self, request, report_id):
        report = services.get_report(report_id=report_id)
        return Response(ReportSerializer(report).data)

    @extend_schema(
        request=UpdateReportStatusSerializer,
        responses={200: ReportSerializer},
        tags=["moderation"],
        summary="Staff: update report status",
    )
    def patch(self, request, report_id):
        serializer = UpdateReportStatusSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        report = services.update_report_status(
            report_id=report_id,
            actor=request.user,
            status=serializer.validated_data["status"],
        )
        return Response(ReportSerializer(report).data)


class ModerationActionCreateView(APIView):
    permission_classes = [IsStaffModerator]

    @extend_schema(
        request=ModerationActionSerializer,
        responses={201: ModerationActionReadSerializer},
        tags=["moderation"],
        summary="Staff: take moderation action",
    )
    def post(self, request):
        serializer = ModerationActionSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        action = services.take_moderation_action(
            admin=request.user, **serializer.validated_data
        )
        return Response(
            ModerationActionReadSerializer(action).data,
            status=status.HTTP_201_CREATED,
        )
