"""Username availability API views."""

from drf_spectacular.utils import OpenApiParameter, extend_schema
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.accounts.username_service import check_username_availability


class CheckUsernameView(APIView):
    """GET /api/v1/users/check-username/?username=..."""

    permission_classes = [AllowAny]
    throttle_classes = []

    @extend_schema(
        parameters=[
            OpenApiParameter(
                name="username",
                type=str,
                location=OpenApiParameter.QUERY,
                required=True,
                description="Username to check for availability",
            ),
        ],
        responses={
            200: {
                "type": "object",
                "properties": {
                    "username": {"type": "string"},
                    "available": {"type": "boolean"},
                    "reason": {"type": "string"},
                },
            }
        },
        tags=["users"],
        summary="Check whether a username is available",
    )
    def get(self, request):
        raw = request.query_params.get("username", "")
        exclude_user_id = None
        user = getattr(request, "user", None)
        if user is not None and getattr(user, "is_authenticated", False):
            exclude_user_id = user.pk
        result = check_username_availability(raw, exclude_user_id=exclude_user_id)
        return Response(result)
