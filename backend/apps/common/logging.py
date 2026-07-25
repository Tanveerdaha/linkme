"""Structured JSON logging helpers."""

from __future__ import annotations

import json
import logging
from datetime import datetime, timezone


class JSONFormatter(logging.Formatter):
    """Emit one JSON object per log line for collectors (ELK, Loki, CloudWatch)."""

    def format(self, record: logging.LogRecord) -> str:
        payload = {
            "time": datetime.now(timezone.utc).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "event": getattr(record, "event", record.name),
        }
        for key in (
            "user_id",
            "request_id",
            "path",
            "method",
            "status_code",
            "duration_ms",
            "ip",
            "extra",
        ):
            value = getattr(record, key, None)
            if value is not None:
                payload[key] = value

        if record.exc_info:
            payload["exc_info"] = self.formatException(record.exc_info)

        return json.dumps(payload, default=str)


def log_security_event(event: str, **kwargs) -> None:
    logger = logging.getLogger("linkme.security")
    logger.info(event, extra={"event": event, **kwargs})


def log_access_event(event: str, **kwargs) -> None:
    logger = logging.getLogger("linkme.access")
    logger.info(event, extra={"event": event, **kwargs})
