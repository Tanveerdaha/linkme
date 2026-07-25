"""DRF exception handler that preserves default behaviour and adds structure."""

from __future__ import annotations

import logging

from rest_framework.views import exception_handler

logger = logging.getLogger(__name__)


def structured_exception_handler(exc, context):
    response = exception_handler(exc, context)
    request = context.get("request")
    if response is not None and request is not None:
        logger.warning(
            "api_error",
            extra={
                "event": "api_error",
                "path": getattr(request, "path", ""),
                "method": getattr(request, "method", ""),
                "status_code": response.status_code,
                "user_id": str(getattr(getattr(request, "user", None), "id", "") or ""),
            },
        )
    elif response is None:
        logger.exception(
            "unhandled_exception",
            extra={"event": "unhandled_exception"},
            exc_info=exc,
        )
    return response
