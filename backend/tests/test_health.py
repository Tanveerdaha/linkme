"""
Health endpoint tests.
"""

import pytest
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient


@pytest.mark.django_db
def test_health_endpoint_returns_healthy(monkeypatch):
    client = APIClient()

    # Force dependency checks to succeed regardless of local infra.
    monkeypatch.setattr(
        "api.v1.health.HealthCheckView._check_database",
        staticmethod(lambda: True),
    )
    monkeypatch.setattr(
        "api.v1.health.HealthCheckView._check_redis",
        staticmethod(lambda: True),
    )
    monkeypatch.setattr("api.v1.health._check_celery", lambda: True)

    response = client.get(reverse("api-health"))

    assert response.status_code == status.HTTP_200_OK
    assert response.json() == {
        "status": "healthy",
        "database": True,
        "redis": True,
        "celery": True,
    }


@pytest.mark.django_db
def test_versioned_health_endpoint(monkeypatch):
    client = APIClient()
    monkeypatch.setattr(
        "api.v1.health.HealthCheckView._check_database",
        staticmethod(lambda: True),
    )
    monkeypatch.setattr(
        "api.v1.health.HealthCheckView._check_redis",
        staticmethod(lambda: True),
    )
    monkeypatch.setattr("api.v1.health._check_celery", lambda: True)

    response = client.get(reverse("health-check"))

    assert response.status_code == status.HTTP_200_OK
    body = response.json()
    assert body["status"] == "healthy"
    assert body["database"] is True
    assert body["redis"] is True
    assert body["celery"] is True


@pytest.mark.django_db
def test_liveness_endpoint():
    client = APIClient()
    response = client.get(reverse("api-liveness"))
    assert response.status_code == status.HTTP_200_OK
    assert response.json()["status"] == "alive"


@pytest.mark.django_db
def test_readiness_endpoint(monkeypatch):
    client = APIClient()
    monkeypatch.setattr("api.v1.health._check_database", lambda: True)
    monkeypatch.setattr("api.v1.health._check_redis", lambda: True)
    response = client.get(reverse("api-readiness"))
    assert response.status_code == status.HTTP_200_OK
    assert response.json()["status"] == "ready"
