"""API views for LinkedIn-style network connections."""

from django.contrib.auth import get_user_model
from django.shortcuts import get_object_or_404
from drf_spectacular.utils import OpenApiParameter, extend_schema
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.network import recommendations, selectors, services
from apps.network.pagination import ConnectionPagination
from apps.network.permissions import IsNetworkUser
from apps.network.serializers import (
    ConnectionListItemSerializer,
    ConnectionRequestCreateSerializer,
    ConnectionRequestSerializer,
    ConnectionStatusSerializer,
    DiscoverUserSerializer,
    MutualConnectionsSerializer,
    NetworkUserSerializer,
)
from apps.network.throttling import ConnectionRequestThrottle
from apps.profiles.models import Profile
from apps.profiles.services import get_profile_for_user

User = get_user_model()


def _serialize_connection_partner(connection, viewer, request) -> dict:
    partner = selectors.connection_partner(connection, viewer)
    profile = getattr(partner, "profile", None)
    avatar = None
    if profile and profile.avatar:
        url = profile.avatar.url
        avatar = request.build_absolute_uri(url) if request else url
    return {
        "username": partner.username,
        "name": partner.full_name,
        "avatar": avatar,
        "headline": getattr(profile, "headline", "") or "",
        "connected_at": connection.accepted_at,
    }


class ConnectionStatusView(APIView):
    """GET /api/v1/network/status/{username}/"""

    permission_classes = [IsNetworkUser]

    @extend_schema(
        responses={200: ConnectionStatusSerializer},
        tags=["network"],
        summary="Get connection status with a user",
    )
    def get(self, request, username: str):
        payload = services.get_connection_status(viewer=request.user, username=username)
        return Response(payload)


class SendConnectionRequestView(APIView):
    """POST /api/v1/network/request/{username}/"""

    permission_classes = [IsNetworkUser]
    throttle_classes = [ConnectionRequestThrottle]

    @extend_schema(
        request=ConnectionRequestCreateSerializer,
        responses={201: ConnectionStatusSerializer},
        tags=["network"],
        summary="Send a connection request",
    )
    def post(self, request, username: str):
        serializer = ConnectionRequestCreateSerializer(data=request.data or {})
        serializer.is_valid(raise_exception=True)
        services.send_connection_request(
            sender=request.user,
            username=username,
            message=serializer.validated_data.get("message", ""),
        )
        return Response(
            {"status": "REQUEST_SENT", "can_connect": False},
            status=status.HTTP_201_CREATED,
        )


class AcceptConnectionRequestView(APIView):
    """POST /api/v1/network/request/{id}/accept/"""

    permission_classes = [IsNetworkUser]

    @extend_schema(
        responses={200: ConnectionStatusSerializer},
        tags=["network"],
        summary="Accept a connection request",
    )
    def post(self, request, request_id):
        services.accept_connection_request(connection_id=request_id, actor=request.user)
        return Response({"status": "CONNECTED", "can_connect": False})


class RejectConnectionRequestView(APIView):
    """POST /api/v1/network/request/{id}/reject/"""

    permission_classes = [IsNetworkUser]

    @extend_schema(
        responses={200: ConnectionStatusSerializer},
        tags=["network"],
        summary="Reject a connection request",
    )
    def post(self, request, request_id):
        services.reject_connection_request(connection_id=request_id, actor=request.user)
        return Response({"status": "NONE", "can_connect": True})


class CancelConnectionRequestView(APIView):
    """DELETE /api/v1/network/request/{id}/"""

    permission_classes = [IsNetworkUser]

    @extend_schema(
        responses={200: ConnectionStatusSerializer},
        tags=["network"],
        summary="Cancel a sent connection request",
    )
    def delete(self, request, request_id):
        services.cancel_connection_request(connection_id=request_id, actor=request.user)
        return Response({"status": "NONE", "can_connect": True})


class ConnectionListView(APIView):
    """GET /api/v1/network/connections/"""

    permission_classes = [IsNetworkUser]
    pagination_class = ConnectionPagination

    @extend_schema(
        parameters=[
            OpenApiParameter(name="search", type=str, required=False),
            OpenApiParameter(name="page", type=int, required=False),
            OpenApiParameter(name="username", type=str, required=False),
        ],
        responses={200: ConnectionListItemSerializer(many=True)},
        tags=["network"],
        summary="List connections (own or another user if visibility allows)",
    )
    def get(self, request):
        username = request.query_params.get("username")
        if username:
            owner = get_object_or_404(
                User.objects.select_related("profile"),
                username__iexact=username,
                is_active=True,
                is_verified=True,
            )
            profile = get_profile_for_user(owner)
            if not selectors.can_view_connections_list(
                owner_profile=profile, viewer=request.user
            ):
                return Response(
                    {"detail": "Connections are private."},
                    status=status.HTTP_403_FORBIDDEN,
                )
            user = owner
        else:
            user = request.user

        qs = selectors.get_accepted_connections(user=user)
        search = request.query_params.get("search")
        qs = selectors.filter_connections_by_search(qs, search or "")

        paginator = self.pagination_class()
        page = paginator.paginate_queryset(qs, request, view=self)
        results = [_serialize_connection_partner(conn, user, request) for conn in page]
        return paginator.get_paginated_response(results)


class RemoveConnectionView(APIView):
    """DELETE /api/v1/network/connections/{username}/"""

    permission_classes = [IsNetworkUser]

    @extend_schema(
        responses={200: ConnectionStatusSerializer},
        tags=["network"],
        summary="Remove an accepted connection",
    )
    def delete(self, request, username: str):
        services.remove_connection(actor=request.user, username=username)
        return Response({"status": "NONE", "can_connect": True})


class ReceivedRequestsView(APIView):
    """GET /api/v1/network/requests/received/"""

    permission_classes = [IsNetworkUser]

    @extend_schema(
        responses={200: ConnectionRequestSerializer(many=True)},
        tags=["network"],
        summary="List incoming connection requests",
    )
    def get(self, request):
        qs = selectors.get_received_requests(user=request.user)
        return Response(
            ConnectionRequestSerializer(
                qs, many=True, context={"request": request, "direction": "received"}
            ).data
        )


class SentRequestsView(APIView):
    """GET /api/v1/network/requests/sent/"""

    permission_classes = [IsNetworkUser]

    @extend_schema(
        responses={200: ConnectionRequestSerializer(many=True)},
        tags=["network"],
        summary="List sent connection requests",
    )
    def get(self, request):
        qs = selectors.get_sent_requests(user=request.user)
        return Response(
            ConnectionRequestSerializer(
                qs, many=True, context={"request": request, "direction": "sent"}
            ).data
        )


class DiscoverView(APIView):
    """GET /api/v1/network/discover/"""

    permission_classes = [IsNetworkUser]

    @extend_schema(
        responses={200: DiscoverUserSerializer(many=True)},
        tags=["network"],
        summary="Discover people to connect with",
    )
    def get(self, request):
        suggestions = recommendations.get_network_suggestions(
            viewer=request.user, limit=20
        )
        payload = []
        for item in suggestions:
            profile: Profile = item["profile"]
            avatar = None
            if profile.avatar:
                avatar = request.build_absolute_uri(profile.avatar.url)
            payload.append(
                {
                    "username": profile.user.username,
                    "name": profile.user.full_name,
                    "avatar": avatar,
                    "headline": profile.headline or "",
                    "reason": item["reason"],
                }
            )
        return Response(payload)


class MutualConnectionsView(APIView):
    """GET /api/v1/network/mutual/{username}/"""

    permission_classes = [IsNetworkUser]

    @extend_schema(
        responses={200: MutualConnectionsSerializer},
        tags=["network"],
        summary="Get mutual connections with a user",
    )
    def get(self, request, username: str):
        other = get_object_or_404(
            User.objects.select_related("profile"),
            username__iexact=username,
            is_active=True,
            is_verified=True,
        )
        profiles = selectors.get_mutual_connections(user1=request.user, user2=other)
        return Response(
            {
                "count": len(profiles),
                "users": NetworkUserSerializer(
                    profiles, many=True, context={"request": request}
                ).data,
            }
        )


class NetworkSummaryView(APIView):
    """GET /api/v1/network/ — dashboard counts."""

    permission_classes = [IsNetworkUser]

    @extend_schema(tags=["network"], summary="Network dashboard summary")
    def get(self, request):
        connections = selectors.get_accepted_connections(user=request.user).count()
        received = selectors.get_received_requests(user=request.user).count()
        sent = selectors.get_sent_requests(user=request.user).count()
        suggestions = len(
            recommendations.get_network_suggestions(viewer=request.user, limit=20)
        )
        return Response(
            {
                "connections": connections,
                "requests_received": received,
                "requests_sent": sent,
                "suggestions": suggestions,
            }
        )
