"""URL routes for profile endpoints."""

from django.urls import path

from apps.profiles.views import (
    MeProfileView,
    ProfileActivityView,
    ProfileMediaView,
    PublicProfileView,
)

app_name = "profiles"

urlpatterns = [
    path("me/", MeProfileView.as_view(), name="me"),
    path("<str:username>/media/", ProfileMediaView.as_view(), name="media"),
    path("<str:username>/activity/", ProfileActivityView.as_view(), name="activity"),
    path("<str:username>/", PublicProfileView.as_view(), name="public"),
]
