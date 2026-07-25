#!/usr/bin/env bash
# Production deploy helper (run on the production host).
set -euo pipefail
cd "$(dirname "$0")/.."
export IMAGE_TAG="${IMAGE_TAG:-latest}"
docker compose -f docker/docker-compose.prod.yml \
  --env-file environment/production/.env \
  pull || true
docker compose -f docker/docker-compose.prod.yml \
  --env-file environment/production/.env \
  up -d
echo "Production deploy complete (IMAGE_TAG=${IMAGE_TAG})"
