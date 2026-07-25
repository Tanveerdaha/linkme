"""URL routes for the comments app."""

from django.urls import path

from apps.comments.views import CommentDetailView, CommentReplyView
from apps.reactions.views import CommentReactionView

app_name = "comments"

urlpatterns = [
    path("<uuid:comment_id>/", CommentDetailView.as_view(), name="detail"),
    path("<uuid:comment_id>/reply/", CommentReplyView.as_view(), name="reply"),
    path(
        "<uuid:comment_id>/reaction/",
        CommentReactionView.as_view(),
        name="reaction",
    ),
]
