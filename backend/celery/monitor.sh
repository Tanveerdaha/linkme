#!/usr/bin/env sh
# Print Celery worker / queue stats for ops monitoring.
set -e
celery -A config inspect ping || true
celery -A config inspect active || true
celery -A config inspect stats || true
