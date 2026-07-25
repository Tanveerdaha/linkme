"""API views for user profiles, search, and discovery."""

from drf_spectacular.utils import OpenApiParameter, extend_schema
from rest_framework import status
from rest_framework.parsers import FormParser, JSONParser, MultiPartParser
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.profiles import activity as activity_svc
from apps.profiles import media_gallery, recommendations
from apps.profiles import search as search_svc
from apps.profiles import services
from apps.profiles.pagination import UserSearchPagination
from apps.profiles.permissions import (
    CanViewProfileContent,
    IsAuthenticatedUser,
    IsOwner,
)
from apps.profiles.serializers import (
    ActivityItemSerializer,
    MeProfileSerializer,
    ProfileMediaGallerySerializer,
    ProfileUpdateSerializer,
    PublicProfileSerializer,
    SuggestedUserSerializer,
    UserSearchResultSerializer,
)


class MeProfileView(APIView):
    permission_classes = [IsAuthenticatedUser, IsOwner]
    parser_classes = [JSONParser, MultiPartParser, FormParser]

    def get_object(self):
        return services.get_profile_for_user(self.request.user)

    @extend_schema(
        responses={200: MeProfileSerializer},
        tags=["profile"],
        summary="Get the current user's profile (with completion + stats)",
    )
    def get(self, request):
        profile = self.get_object()
        self.check_object_permissions(request, profile)
        return Response(services.build_me_profile_payload(profile, request))

    @extend_schema(
        request=ProfileUpdateSerializer,
        responses={200: MeProfileSerializer},
        tags=["profile"],
        summary="Update the current user's profile",
    )
    def patch(self, request):
        profile = self.get_object()
        self.check_object_permissions(request, profile)

        serializer = ProfileUpdateSerializer(data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)

        data = {
            key: value
            for key, value in serializer.validated_data.items()
            if key not in {"avatar", "cover_image"}
        }
        files = {}
        if "avatar" in serializer.validated_data:
            files["avatar"] = serializer.validated_data["avatar"]
        if "cover_image" in serializer.validated_data:
            files["cover_image"] = serializer.validated_data["cover_image"]

        profile = services.update_own_profile(request.user, data=data, files=files)
        return Response(
            services.build_me_profile_payload(profile, request),
            status=status.HTTP_200_OK,
        )


class PublicProfileView(APIView):
    permission_classes = [AllowAny]

    @extend_schema(
        responses={200: PublicProfileSerializer},
        tags=["profile"],
        summary="Get a public profile by username",
    )
    def get(self, request, username: str):
        profile = services.get_public_profile(username, viewer=request.user)
        return Response(services.build_public_profile_payload(profile, request))


class ProfileMediaView(APIView):
    permission_classes = [AllowAny]

    @extend_schema(
        responses={200: ProfileMediaGallerySerializer},
        tags=["profile"],
        summary="Get a user's media gallery",
    )
    def get(self, request, username: str):
        profile = services.get_public_profile(username, viewer=request.user)
        if getattr(profile, "_limited_view", False):
            return Response({"images": [], "videos": []})
        gallery = media_gallery.get_profile_media(
            user=profile.user, viewer=request.user, request=request
        )
        return Response(gallery)


class ProfileActivityView(APIView):
    permission_classes = [AllowAny]

    @extend_schema(
        responses={200: ActivityItemSerializer(many=True)},
        tags=["profile"],
        summary="Get a user's activity timeline",
    )
    def get(self, request, username: str):
        profile = services.get_public_profile(username, viewer=request.user)
        if getattr(profile, "_limited_view", False):
            return Response([])
        items = activity_svc.get_user_activity(user=profile.user, viewer=request.user)
        return Response(ActivityItemSerializer(items, many=True).data)


class UserSearchView(APIView):
    permission_classes = [AllowAny]
    pagination_class = UserSearchPagination

    @extend_schema(
        parameters=[
            OpenApiParameter(name="q", type=str, location=OpenApiParameter.QUERY),
            OpenApiParameter(
                name="location",
                type=str,
                location=OpenApiParameter.QUERY,
                required=False,
            ),
            OpenApiParameter(
                name="interest",
                type=str,
                location=OpenApiParameter.QUERY,
                required=False,
            ),
            OpenApiParameter(
                name="page", type=int, location=OpenApiParameter.QUERY, required=False
            ),
            OpenApiParameter(
                name="page_size",
                type=int,
                location=OpenApiParameter.QUERY,
                required=False,
            ),
        ],
        responses={200: UserSearchResultSerializer(many=True)},
        tags=["search"],
        summary="Search users",
    )
    def get(self, request):
        q = request.query_params.get("q", "")
        location = request.query_params.get("location") or None
        interest = request.query_params.get("interest") or None
        qs = search_svc.search_users(
            q=q, location=location, interest=interest, viewer=request.user
        )
        paginator = self.pagination_class()
        page = paginator.paginate_queryset(qs, request, view=self)
        serializer = UserSearchResultSerializer(
            page, many=True, context={"request": request}
        )
        return paginator.get_paginated_response(serializer.data)


class UserSuggestionsView(APIView):
    permission_classes = [AllowAny]

    @extend_schema(
        responses={200: SuggestedUserSerializer(many=True)},
        tags=["search"],
        summary="Suggested users foundation",
    )
    def get(self, request):
        from apps.common.cache import cache_suggestions

        viewer_id = (
            request.user.id
            if getattr(request.user, "is_authenticated", False)
            else None
        )
        cached = cache_suggestions(viewer_id)
        if cached is not None:
            return Response(cached)

        qs = recommendations.get_suggested_users(viewer=request.user, limit=12)
        payload = SuggestedUserSerializer(
            qs, many=True, context={"request": request}
        ).data
        cache_suggestions(viewer_id, payload)
        return Response(payload)
