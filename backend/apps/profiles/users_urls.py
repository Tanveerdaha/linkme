"""User-related routes mounted under /api/v1/users/."""

from django.urls import path

from apps.accounts.username_views import CheckUsernameView
from apps.moderation.views import BlockedUsersListView, BlockUserView
from apps.profiles.views import UserSuggestionsView

urlpatterns = [
    path(
        "check-username/",
        CheckUsernameView.as_view(),
        name="check-username",
    ),
    path("suggestions/", UserSuggestionsView.as_view(), name="suggestions"),
    path("blocked/", BlockedUsersListView.as_view(), name="blocked-users"),
    path("<str:username>/block/", BlockUserView.as_view(), name="block-user"),
]
