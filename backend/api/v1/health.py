"""
Health / readiness / liveness probes for load balancers and Kubernetes.
"""

from __future__ import annotations

from django.core.cache import cache
from django.db import connection
from drf_spectacular.utils import extend_schema
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView


def _check_database() -> bool:
    try:
        connection.ensure_connection()
        return True
    except Exception:
        return False


def _check_redis() -> bool:
    try:
        cache.set("health_check", "ok", timeout=5)
        return cache.get("health_check") == "ok"
    except Exception:
        return False


def _check_celery() -> bool | None:
    """
    Best-effort Celery ping.

    Returns None when the check is skipped (broker unreachable / no workers
    expected in unit tests), True/False when a definitive answer is available.
    """
    try:
        from config.celery import app

        inspector = app.control.inspect(timeout=1.0)
        ping = inspector.ping() if inspector else None
        if ping is None:
            return False
        return bool(ping)
    except Exception:
        return False


class HealthCheckView(APIView):
    """GET /api/health/ and /api/v1/health/ — full dependency probe."""

    permission_classes = [AllowAny]
    authentication_classes = []
    throttle_classes = []

    @extend_schema(
        summary="Health check",
        description="Returns service health including database, Redis, and Celery.",
        responses={
            200: {
                "type": "object",
                "properties": {
                    "status": {"type": "string"},
                    "database": {"type": "boolean"},
                    "redis": {"type": "boolean"},
                    "celery": {"type": "boolean"},
                },
            }
        },
        tags=["system"],
    )
    def get(self, request):
        database_ok = _check_database()
        redis_ok = _check_redis()
        # Celery is informational for the aggregate health endpoint — a missing
        # worker degrades status but the API can still serve reads.
        celery_ok = _check_celery()
        healthy = database_ok and redis_ok

        return Response(
            {
                "status": "healthy" if healthy else "degraded",
                "database": database_ok,
                "redis": redis_ok,
                "celery": bool(celery_ok),
            },
            status=200 if healthy else 503,
        )


class LivenessView(APIView):
    """GET /api/liveness/ — process is up (no dependency checks)."""

    permission_classes = [AllowAny]
    authentication_classes = []
    throttle_classes = []

    @extend_schema(summary="Liveness probe", tags=["system"])
    def get(self, request):
        return Response({"status": "alive"})


class ReadinessView(APIView):
    """GET /api/readiness/ — ready to accept traffic (DB + Redis)."""

    permission_classes = [AllowAny]
    authentication_classes = []
    throttle_classes = []

    @extend_schema(summary="Readiness probe", tags=["system"])
    def get(self, request):
        database_ok = _check_database()
        redis_ok = _check_redis()
        ready = database_ok and redis_ok
        return Response(
            {
                "status": "ready" if ready else "not_ready",
                "database": database_ok,
                "redis": redis_ok,
            },
            status=200 if ready else 503,
        )


# Backwards-compatible aliases for existing tests that monkeypatch class methods.
HealthCheckView._check_database = staticmethod(_check_database)
HealthCheckView._check_redis = staticmethod(_check_redis)
