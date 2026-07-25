"""Admin dashboard URL routes — mounted at /api/v1/admin/."""

from django.urls import path

from apps.admin_dashboard import views

app_name = "admin_dashboard"

urlpatterns = [
    path("me/", views.AdminMeView.as_view(), name="me"),
    path("roles/assign/", views.AdminAssignRoleView.as_view(), name="assign-role"),
    # Analytics
    path(
        "analytics/overview/",
        views.AnalyticsOverviewView.as_view(),
        name="analytics-overview",
    ),
    path(
        "analytics/trends/",
        views.AnalyticsTrendsView.as_view(),
        name="analytics-trends",
    ),
    path(
        "analytics/metrics/",
        views.AnalyticsMetricsView.as_view(),
        name="analytics-metrics",
    ),
    # Users
    path("users/", views.AdminUserListView.as_view(), name="users"),
    path(
        "users/<uuid:user_id>/", views.AdminUserDetailView.as_view(), name="user-detail"
    ),
    path(
        "users/<uuid:user_id>/suspend/",
        views.AdminUserSuspendView.as_view(),
        name="user-suspend",
    ),
    path(
        "users/<uuid:user_id>/unsuspend/",
        views.AdminUserUnsuspendView.as_view(),
        name="user-unsuspend",
    ),
    path(
        "users/<uuid:user_id>/deactivate/",
        views.AdminUserDeactivateView.as_view(),
        name="user-deactivate",
    ),
    path(
        "users/<uuid:user_id>/delete/",
        views.AdminUserDeleteView.as_view(),
        name="user-delete",
    ),
    # Content
    path("content/posts/", views.AdminPostListView.as_view(), name="posts"),
    path(
        "content/posts/<uuid:post_id>/",
        views.AdminPostDeleteView.as_view(),
        name="post-delete",
    ),
    path(
        "content/posts/<uuid:post_id>/restore/",
        views.AdminPostRestoreView.as_view(),
        name="post-restore",
    ),
    path("content/comments/", views.AdminCommentListView.as_view(), name="comments"),
    path(
        "content/comments/<uuid:comment_id>/",
        views.AdminCommentRemoveView.as_view(),
        name="comment-remove",
    ),
    path(
        "content/comments/<uuid:comment_id>/restore/",
        views.AdminCommentRestoreView.as_view(),
        name="comment-restore",
    ),
    # Reports
    path("reports/", views.AdminReportListView.as_view(), name="reports"),
    path(
        "reports/<uuid:report_id>/",
        views.AdminReportDetailView.as_view(),
        name="report-detail",
    ),
    # Moderation
    path(
        "moderation/history/",
        views.AdminModerationHistoryView.as_view(),
        name="moderation-history",
    ),
    path(
        "moderation/actions/",
        views.AdminModerationActionView.as_view(),
        name="moderation-actions",
    ),
    # Audit
    path("audit/", views.AdminAuditListView.as_view(), name="audit"),
    # Export
    path("export/", views.AdminExportView.as_view(), name="export"),
]
