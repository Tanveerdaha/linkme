"""Privacy settings API views."""

from drf_spectacular.utils import extend_schema
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.moderation.permissions import IsAuthenticatedVerified
from apps.privacy import services
from apps.privacy.serializers import (
    PrivacySettingSerializer,
    PrivacySettingUpdateSerializer,
)


class PrivacySettingsView(APIView):
    permission_classes = [IsAuthenticatedVerified]

    @extend_schema(
        responses={200: PrivacySettingSerializer},
        tags=["privacy"],
        summary="Get privacy settings",
    )
    def get(self, request):
        settings_obj = services.get_or_create_privacy_settings(request.user)
        return Response(PrivacySettingSerializer(settings_obj).data)

    @extend_schema(
        request=PrivacySettingUpdateSerializer,
        responses={200: PrivacySettingSerializer},
        tags=["privacy"],
        summary="Update privacy settings",
    )
    def patch(self, request):
        serializer = PrivacySettingUpdateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        settings_obj = services.update_privacy_settings(
            request.user, data=serializer.validated_data
        )
        return Response(PrivacySettingSerializer(settings_obj).data)
