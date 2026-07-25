"""URL routes for moderation and reporting."""

from django.urls import path

from apps.moderation.views import (
    ModerationActionCreateView,
    ModerationReportDetailView,
    ModerationReportListView,
    MyReportsView,
    ReportCreateView,
)

app_name = "moderation"

urlpatterns = [
    path("", ReportCreateView.as_view(), name="report-create"),
    path("my/", MyReportsView.as_view(), name="my-reports"),
    path(
        "admin/reports/",
        ModerationReportListView.as_view(),
        name="admin-reports",
    ),
    path(
        "admin/reports/<uuid:report_id>/",
        ModerationReportDetailView.as_view(),
        name="admin-report-detail",
    ),
    path(
        "admin/actions/",
        ModerationActionCreateView.as_view(),
        name="admin-actions",
    ),
]
