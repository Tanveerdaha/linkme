"""Cross-cutting HTTP middleware for production hardening and observability."""

from __future__ import annotations

import time
import uuid

from apps.common.logging import log_access_event


class SecurityHeadersMiddleware:
    """
    Add defense-in-depth response headers.

    Complements Django's SecurityMiddleware / SECURE_* settings.
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        response.setdefault("X-Content-Type-Options", "nosniff")
        response.setdefault("X-Frame-Options", "DENY")
        response.setdefault("Referrer-Policy", "same-origin")
        response.setdefault(
            "Permissions-Policy",
            "camera=(), microphone=(), geolocation=()",
        )
        # Baseline CSP — API returns JSON; tighten further at the CDN/WAF edge.
        if "Content-Security-Policy" not in response:
            response["Content-Security-Policy"] = (
                "default-src 'self'; "
                "img-src 'self' data: https: blob:; "
                "media-src 'self' https: blob:; "
                "script-src 'self'; "
                "style-src 'self' 'unsafe-inline'; "
                "connect-src 'self' https: wss:; "
                "frame-ancestors 'none'; "
                "base-uri 'self'; "
                "form-action 'self'"
            )
        return response


class RequestLoggingMiddleware:
    """Emit structured access logs with latency for every API request."""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        request_id = request.headers.get("X-Request-ID") or str(uuid.uuid4())
        request.request_id = request_id
        started = time.perf_counter()
        response = self.get_response(request)
        duration_ms = round((time.perf_counter() - started) * 1000, 2)
        response["X-Request-ID"] = request_id

        path = request.path
        if path.startswith("/api/"):
            user = getattr(request, "user", None)
            user_id = (
                str(user.id)
                if user is not None and getattr(user, "is_authenticated", False)
                else None
            )
            log_access_event(
                "http_request",
                request_id=request_id,
                method=request.method,
                path=path,
                status_code=response.status_code,
                duration_ms=duration_ms,
                user_id=user_id,
                ip=self._client_ip(request),
            )
        return response

    @staticmethod
    def _client_ip(request) -> str:
        forwarded = request.META.get("HTTP_X_FORWARDED_FOR")
        if forwarded:
            return forwarded.split(",")[0].strip()
        return request.META.get("REMOTE_ADDR", "")
