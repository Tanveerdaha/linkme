"""Account management views — delete, restore, data export."""

from drf_spectacular.utils import extend_schema
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.accounts import account_services
from apps.moderation.models import DataExportRequest
from apps.moderation.permissions import IsAuthenticatedVerified


class AccountDeleteView(APIView):
    permission_classes = [IsAuthenticatedVerified]

    @extend_schema(
        responses={200: dict},
        tags=["account"],
        summary="Soft-delete the authenticated account",
    )
    def delete(self, request):
        account_services.soft_delete_account(user=request.user)
        return Response(
            {
                "deleted": True,
                "message": (
                    "Your account has been scheduled for deletion. "
                    "You can restore it within 30 days."
                ),
            }
        )


class AccountRestoreView(APIView):
    """
    Restore a soft-deleted account.

    Requires authentication with a still-valid access token. Tokens are
    blacklisted on delete, so restore is typically staff-assisted or via
    a dedicated recovery flow; this endpoint supports in-session restore
    when the access token has not yet expired.
    """

    permission_classes = [IsAuthenticated]

    @extend_schema(
        responses={200: dict},
        tags=["account"],
        summary="Restore a soft-deleted account",
    )
    def post(self, request):
        user = request.user
        if not getattr(user, "is_deleted", False):
            return Response(
                {"detail": "Account is not deleted."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        account_services.restore_account(user=user)
        return Response({"restored": True})


class AccountExportView(APIView):
    permission_classes = [IsAuthenticatedVerified]

    @extend_schema(
        responses={202: dict},
        tags=["account"],
        summary="Request a data export ZIP",
    )
    def post(self, request):
        export = account_services.request_data_export(user=request.user)
        return Response(
            {
                "id": str(export.id),
                "status": export.status,
                "message": "Export queued. Poll GET /account/export/ for status.",
            },
            status=status.HTTP_202_ACCEPTED,
        )

    @extend_schema(
        responses={200: dict},
        tags=["account"],
        summary="Get latest data export status / download URL",
    )
    def get(self, request):
        export = account_services.get_latest_export(user=request.user)
        if export is None:
            return Response({"detail": "No export request found."}, status=404)

        download_url = None
        if export.status == DataExportRequest.Status.READY and export.file:
            download_url = request.build_absolute_uri(export.file.url)

        return Response(
            {
                "id": str(export.id),
                "status": export.status,
                "download_url": download_url,
                "created_at": export.created_at,
                "completed_at": export.completed_at,
                "expires_at": export.expires_at,
                "error_message": export.error_message or None,
            }
        )


class AccountStatusView(APIView):
    permission_classes = [IsAuthenticatedVerified]

    @extend_schema(
        responses={200: dict},
        tags=["account"],
        summary="Account safety status",
    )
    def get(self, request):
        user = request.user
        return Response(
            {
                "username": user.username,
                "email": user.email or "",
                "phone_number": getattr(user, "phone_number", None) or "",
                "is_active": user.is_active,
                "is_verified": user.is_verified,
                "is_suspended": user.is_currently_suspended(),
                "suspended_until": user.suspended_until,
                "suspension_reason": (
                    user.suspension_reason if user.is_suspended else ""
                ),
                "is_deleted": user.is_deleted,
                "is_staff": user.is_staff,
            }
        )
