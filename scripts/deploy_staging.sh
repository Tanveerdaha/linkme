#!/usr/bin/env bash
# Staging deploy helper (run on the staging host).
set -euo pipefail
cd "$(dirname "$0")/.."
export IMAGE_TAG="${IMAGE_TAG:-latest}"
docker compose -f docker/docker-compose.prod.yml \
  --env-file environment/staging/.env \
  pull || true
docker compose -f docker/docker-compose.prod.yml \
  --env-file environment/staging/.env \
  up -d --build
echo "Staging deploy complete (IMAGE_TAG=${IMAGE_TAG})"
