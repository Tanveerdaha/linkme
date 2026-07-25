"""API v1 URL configuration."""

from django.urls import include, path

from api.v1.health import HealthCheckView, LivenessView, ReadinessView

urlpatterns = [
    path("health/", HealthCheckView.as_view(), name="health-check"),
    path("readiness/", ReadinessView.as_view(), name="v1-readiness"),
    path("liveness/", LivenessView.as_view(), name="v1-liveness"),
    path("auth/", include("apps.accounts.urls")),
    path("account/", include("apps.accounts.account_urls")),
    path("profile/", include("apps.profiles.urls")),
    path("posts/", include("apps.posts.urls")),
    path("comments/", include("apps.comments.urls")),
    path("feed/", include("apps.feed.urls")),
    path("search/", include("apps.profiles.search_urls")),
    path("users/", include("apps.profiles.users_urls")),
    path("network/", include("apps.network.urls")),
    path("messages/", include("apps.messaging.urls")),
    path("notifications/", include("apps.notifications.urls")),
    path("reports/", include("apps.moderation.urls")),
    path("privacy/", include("apps.privacy.urls")),
    path("admin/", include("apps.admin_dashboard.urls")),
]
