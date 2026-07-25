"""
Locust load tests for LinkMe.

Targets (set LOCUST_HOST, default http://localhost:8000):
  - Public feed browse (anonymous)
  - Authenticated feed (optional LINKME_ACCESS_TOKEN)
  - Health probes

Example:
  locust -f loadtests/locust/locustfile.py --host http://localhost:8000 \
    --users 100 --spawn-rate 10 --run-time 2m --headless
"""

from __future__ import annotations

import os
import random

from locust import HttpUser, between, events, task


class FeedBrowser(HttpUser):
    """Simulate users browsing the public feed (high-volume read path)."""

    wait_time = between(0.5, 2.0)
    weight = 10

    @task(5)
    def public_feed(self):
        self.client.get("/api/v1/feed/public/", name="/api/v1/feed/public/")

    @task(1)
    def health(self):
        self.client.get("/api/health/", name="/api/health/")

    @task(1)
    def suggestions(self):
        self.client.get("/api/v1/users/suggestions/", name="/api/v1/users/suggestions/")


class AuthenticatedUser(HttpUser):
    """Authenticated feed / notifications (requires LINKME_ACCESS_TOKEN)."""

    wait_time = between(1.0, 3.0)
    weight = 3

    def on_start(self):
        self.token = os.environ.get("LINKME_ACCESS_TOKEN", "")
        self.headers = (
            {"Authorization": f"Bearer {self.token}"} if self.token else {}
        )

    @task(4)
    def user_feed(self):
        if not self.token:
            self.client.get("/api/v1/feed/public/", name="/api/v1/feed/public/ [fallback]")
            return
        self.client.get(
            "/api/v1/feed/",
            headers=self.headers,
            name="/api/v1/feed/",
        )

    @task(1)
    def unread_count(self):
        if not self.token:
            return
        self.client.get(
            "/api/v1/notifications/unread-count/",
            headers=self.headers,
            name="/api/v1/notifications/unread-count/",
        )


class UploadUser(HttpUser):
    """
    Light media upload pressure test.

    Disabled by default (weight 0) — set LOCUST_ENABLE_UPLOADS=1 and provide
    LINKME_ACCESS_TOKEN plus a small fixture at loadtests/fixtures/sample.jpg.
    """

    wait_time = between(5.0, 15.0)
    weight = 1 if os.environ.get("LOCUST_ENABLE_UPLOADS") == "1" else 0

    def on_start(self):
        self.token = os.environ.get("LINKME_ACCESS_TOKEN", "")
        self.fixture = os.environ.get(
            "LOCUST_UPLOAD_FIXTURE",
            "loadtests/fixtures/sample.jpg",
        )

    @task
    def create_text_post(self):
        if not self.token:
            return
        self.client.post(
            "/api/v1/posts/",
            headers={"Authorization": f"Bearer {self.token}"},
            data={
                "content": f"load-test-{random.randint(1, 1_000_000)}",
                "visibility": "PUBLIC",
            },
            name="/api/v1/posts/ [text]",
        )


@events.test_start.add_listener
def on_test_start(environment, **_kwargs):
    print(
        "LinkMe load test started. Targets: feed <500ms p95, API <200ms avg (goal)."
    )
