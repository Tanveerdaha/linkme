"""URL routes for the network app."""

from django.urls import path

from apps.network.views import (
    AcceptConnectionRequestView,
    CancelConnectionRequestView,
    ConnectionListView,
    ConnectionStatusView,
    DiscoverView,
    MutualConnectionsView,
    NetworkSummaryView,
    ReceivedRequestsView,
    RejectConnectionRequestView,
    RemoveConnectionView,
    SendConnectionRequestView,
    SentRequestsView,
)

app_name = "network"

urlpatterns = [
    path("", NetworkSummaryView.as_view(), name="summary"),
    path("discover/", DiscoverView.as_view(), name="discover"),
    path("connections/", ConnectionListView.as_view(), name="connections"),
    path(
        "connections/<str:username>/",
        RemoveConnectionView.as_view(),
        name="remove-connection",
    ),
    path(
        "requests/received/",
        ReceivedRequestsView.as_view(),
        name="requests-received",
    ),
    path("requests/sent/", SentRequestsView.as_view(), name="requests-sent"),
    # UUID routes before username catch-all.
    path(
        "request/<uuid:request_id>/accept/",
        AcceptConnectionRequestView.as_view(),
        name="accept-request",
    ),
    path(
        "request/<uuid:request_id>/reject/",
        RejectConnectionRequestView.as_view(),
        name="reject-request",
    ),
    path(
        "request/<uuid:request_id>/",
        CancelConnectionRequestView.as_view(),
        name="cancel-request",
    ),
    path(
        "request/<str:username>/",
        SendConnectionRequestView.as_view(),
        name="send-request",
    ),
    path(
        "status/<str:username>/",
        ConnectionStatusView.as_view(),
        name="status",
    ),
    path(
        "mutual/<str:username>/",
        MutualConnectionsView.as_view(),
        name="mutual",
    ),
]
