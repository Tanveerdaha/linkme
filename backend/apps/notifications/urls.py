"""URL routes for notifications — mounted at /api/v1/notifications/."""

from django.urls import path

from apps.notifications.views import (
    MarkAllReadView,
    MarkNotificationReadView,
    NotificationDeleteView,
    NotificationListView,
    NotificationPreferencesView,
    UnreadCountView,
)

app_name = "notifications"

urlpatterns = [
    path("", NotificationListView.as_view(), name="list"),
    path("unread-count/", UnreadCountView.as_view(), name="unread-count"),
    path("read-all/", MarkAllReadView.as_view(), name="read-all"),
    path("preferences/", NotificationPreferencesView.as_view(), name="preferences"),
    path(
        "<uuid:notification_id>/read/",
        MarkNotificationReadView.as_view(),
        name="mark-read",
    ),
    path(
        "<uuid:notification_id>/",
        NotificationDeleteView.as_view(),
        name="delete",
    ),
]
