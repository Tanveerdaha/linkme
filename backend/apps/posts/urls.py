"""URL routes for the posts app."""

from django.urls import path

from apps.comments.views import PostCommentListCreateView
from apps.posts.views import PostDetailView, PostListCreateView, PostShareView
from apps.reactions.views import PostReactionSummaryView, PostReactionView

app_name = "posts"

urlpatterns = [
    path("", PostListCreateView.as_view(), name="list-create"),
    path("<uuid:post_id>/", PostDetailView.as_view(), name="detail"),
    path(
        "<uuid:post_id>/reaction/",
        PostReactionView.as_view(),
        name="reaction",
    ),
    path(
        "<uuid:post_id>/reactions/",
        PostReactionSummaryView.as_view(),
        name="reactions-summary",
    ),
    path(
        "<uuid:post_id>/comments/",
        PostCommentListCreateView.as_view(),
        name="comments",
    ),
    path("<uuid:post_id>/share/", PostShareView.as_view(), name="share"),
]
