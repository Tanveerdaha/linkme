"""Search URL routes."""

from django.urls import path

from apps.profiles.views import UserSearchView

urlpatterns = [
    path("users/", UserSearchView.as_view(), name="search-users"),
]
