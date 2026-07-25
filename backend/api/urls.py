"""Top-level API URL router."""

from django.urls import include, path

from api.v1.health import HealthCheckView, LivenessView, ReadinessView

urlpatterns = [
    # Unversioned probes used by compose / load balancers / Kubernetes.
    path("health/", HealthCheckView.as_view(), name="api-health"),
    path("readiness/", ReadinessView.as_view(), name="api-readiness"),
    path("liveness/", LivenessView.as_view(), name="api-liveness"),
    path("v1/", include("api.v1.urls")),
]
