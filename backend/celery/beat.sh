#!/usr/bin/env sh
# Start Celery beat scheduler.
set -e
exec celery -A config beat --loglevel="${CELERY_LOG_LEVEL:-info}" --scheduler celery.beat:PersistentScheduler
