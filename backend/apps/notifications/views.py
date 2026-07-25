"""API views for notifications."""

from drf_spectacular.utils import OpenApiParameter, extend_schema
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.notifications import services
from apps.notifications.broadcast import serialize_notification
from apps.notifications.models import Notification
from apps.notifications.pagination import NotificationPagination
from apps.notifications.permissions import IsNotificationsUser
from apps.notifications.preferences import get_or_create_preferences, update_preferences
from apps.notifications.serializers import (
    NotificationPreferenceSerializer,
    NotificationSerializer,
    UnreadCountSerializer,
)


class NotificationListView(APIView):
    """GET /api/v1/notifications/"""

    permission_classes = [IsNotificationsUser]
    pagination_class = NotificationPagination

    @extend_schema(
        parameters=[
            OpenApiParameter(
                name="page",
                type=int,
                location=OpenApiParameter.QUERY,
                required=False,
            ),
            OpenApiParameter(
                name="unread",
                type=bool,
                location=OpenApiParameter.QUERY,
                required=False,
                description="If true, return only unread notifications",
            ),
        ],
        responses={200: NotificationSerializer(many=True)},
        tags=["notifications"],
        summary="List notifications",
    )
    def get(self, request):
        qs = (
            Notification.objects.filter(recipient=request.user)
            .select_related("sender", "sender__profile")
            .order_by("-created_at")
        )
        unread = request.query_params.get("unread")
        if unread is not None and str(unread).lower() in {"1", "true", "yes"}:
            qs = qs.filter(is_read=False)

        paginator = self.pagination_class()
        page = paginator.paginate_queryset(qs, request, view=self)
        results = [
            serialize_notification(n, request=request) for n in page
        ]
        return paginator.get_paginated_response(results)


class UnreadCountView(APIView):
    """GET /api/v1/notifications/unread-count/"""

    permission_classes = [IsNotificationsUser]

    @extend_schema(
        responses={200: UnreadCountSerializer},
        tags=["notifications"],
        summary="Unread notification count",
    )
    def get(self, request):
        return Response({"count": services.get_unread_count(user=request.user)})


class MarkNotificationReadView(APIView):
    """PATCH /api/v1/notifications/{id}/read/"""

    permission_classes = [IsNotificationsUser]

    @extend_schema(
        responses={200: NotificationSerializer},
        tags=["notifications"],
        summary="Mark a notification as read",
    )
    def patch(self, request, notification_id):
        note = services.mark_as_read(
            notification_id=notification_id, user=request.user
        )
        note = (
            Notification.objects.select_related("sender", "sender__profile")
            .get(pk=note.pk)
        )
        return Response(serialize_notification(note, request=request))


class MarkAllReadView(APIView):
    """POST /api/v1/notifications/read-all/"""

    permission_classes = [IsNotificationsUser]

    @extend_schema(
        responses={200: UnreadCountSerializer},
        tags=["notifications"],
        summary="Mark all notifications as read",
    )
    def post(self, request):
        services.mark_all_as_read(user=request.user)
        return Response({"count": 0})


class NotificationDeleteView(APIView):
    """DELETE /api/v1/notifications/{id}/"""

    permission_classes = [IsNotificationsUser]

    @extend_schema(
        responses={204: None},
        tags=["notifications"],
        summary="Delete a notification",
    )
    def delete(self, request, notification_id):
        services.delete_notification(
            notification_id=notification_id, user=request.user
        )
        return Response(status=status.HTTP_204_NO_CONTENT)


class NotificationPreferencesView(APIView):
    """GET/PATCH /api/v1/notifications/preferences/"""

    permission_classes = [IsNotificationsUser]

    @extend_schema(
        responses={200: NotificationPreferenceSerializer},
        tags=["notifications"],
        summary="Get notification preferences",
    )
    def get(self, request):
        prefs = get_or_create_preferences(user=request.user)
        return Response(
            {
                "post_reactions_enabled": prefs.post_reactions_enabled,
                "comments_enabled": prefs.comments_enabled,
                "connection_enabled": prefs.connection_enabled,
                "messages_enabled": prefs.messages_enabled,
            }
        )

    @extend_schema(
        request=NotificationPreferenceSerializer,
        responses={200: NotificationPreferenceSerializer},
        tags=["notifications"],
        summary="Update notification preferences",
    )
    def patch(self, request):
        serializer = NotificationPreferenceSerializer(
            data=request.data, partial=True
        )
        serializer.is_valid(raise_exception=True)
        prefs = update_preferences(user=request.user, **serializer.validated_data)
        return Response(
            {
                "post_reactions_enabled": prefs.post_reactions_enabled,
                "comments_enabled": prefs.comments_enabled,
                "connection_enabled": prefs.connection_enabled,
                "messages_enabled": prefs.messages_enabled,
            }
        )
