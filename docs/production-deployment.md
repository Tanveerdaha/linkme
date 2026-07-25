# Production Deployment Guide

## Server requirements

| Role | Minimum | Recommended (launch) |
| --- | --- | --- |
| App nodes (API + WS) | 2 vCPU / 4 GB | 4 vCPU / 8 GB × 2 |
| PostgreSQL | 2 vCPU / 4 GB / 50 GB SSD | 4 vCPU / 16 GB / 200 GB SSD |
| Redis | 1 vCPU / 1 GB | 2 vCPU / 4 GB |
| Object storage | S3 / R2 / GCS bucket | + CDN in front |
| Celery workers | 2 vCPU / 4 GB | Separate media + notification pools |

## Environments

Templates live under `environment/`:

- `environment/development/.env.example`
- `environment/staging/.env.example`
- `environment/production/.env.example`

```bash
cp environment/production/.env.example environment/production/.env
# Edit secrets, hosts, S3, Sentry
```

Never commit real `.env` files.

## Deploy with Docker Compose (single host / VM)

```bash
# From repo root
cp environment/production/.env.example environment/production/.env
# Fill DATABASE_PASSWORD, SECRET_KEY, JWT_SECRET, ALLOWED_HOSTS, etc.

docker compose -f docker/docker-compose.prod.yml \
  --env-file environment/production/.env \
  up -d --build
```

Services started:

- `nginx` — reverse proxy (HTTP profile by default; swap to `nginx.conf` for TLS)
- `frontend` — Next.js standalone
- `backend` — Gunicorn (`workers ≈ CPU×2+1` via `WEB_CONCURRENCY`)
- `websocket` — Daphne ASGI for `/ws/*`
- `celery_*` — queue-isolated workers + beat
- `postgres` + `pgbouncer` + `redis`

## TLS

1. Place certs in `docker/nginx/certs/fullchain.pem` and `privkey.pem`
2. Switch nginx volume mount to `nginx.conf` (HTTPS + redirect)
3. Set `SECURE_SSL_REDIRECT=True` and `CSRF_TRUSTED_ORIGINS`

## Object storage / CDN

```env
USE_S3=True
MEDIA_STORAGE_BUCKET=linkme-prod-media
AWS_ACCESS_KEY_ID=...
AWS_SECRET_ACCESS_KEY=...
AWS_S3_CUSTOM_DOMAIN=cdn.linkme.example
```

Images get long-lived `Cache-Control: max-age=31536000`. Private exports use signed URLs (`AWS_QUERYSTRING_AUTH=True`).

## Health probes

| Path | Purpose |
| --- | --- |
| `GET /api/liveness/` | Process up |
| `GET /api/readiness/` | DB + Redis |
| `GET /api/health/` | Full (includes Celery ping) |

Wire these into your load balancer / Kubernetes probes.

## Rollback

```bash
# Pin previous image tag and recreate
export IMAGE_TAG=<previous_sha>
docker compose -f docker/docker-compose.prod.yml up -d backend frontend websocket
```

Or redeploy the previous Git commit and rebuild.

## CI/CD

- PR → `.github/workflows/backend.yml` + `frontend.yml` (lint, test, build)
- `main` → `.github/workflows/deploy.yml` builds GHCR images and deploys staging when SSH secrets are set
- Production deploy is manual via `workflow_dispatch`

## Post-deploy checklist

- [ ] `/api/health/` returns healthy
- [ ] Login + feed load under 500ms p95
- [ ] WebSocket chat connects through `/ws/`
- [ ] Media upload lands in object storage
- [ ] Sentry receives a test error
- [ ] Nightly backup cron installed (`scripts/backup/backup_postgres.sh`)
