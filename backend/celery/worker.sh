#!/usr/bin/env sh
# Start a default-queue Celery worker.
set -e
exec celery -A config worker -Q default --loglevel="${CELERY_LOG_LEVEL:-info}" --concurrency="${CELERY_CONCURRENCY:-4}"
