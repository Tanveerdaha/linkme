"""URL routes for the feed app."""

from django.urls import path

from apps.feed.views import PublicFeedView, UserFeedView

app_name = "feed"

urlpatterns = [
    path("public/", PublicFeedView.as_view(), name="public"),
    path("", UserFeedView.as_view(), name="user"),
]
