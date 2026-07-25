# LinkMe System Architecture

## Overview

LinkMe is a production-oriented social platform:

- **Frontend**: Next.js (App Router, standalone output)
- **API**: Django 5 + DRF + SimpleJWT
- **Realtime**: Django Channels + Daphne + Redis channel layer
- **Async**: Celery with isolated queues
- **Data**: PostgreSQL via PgBouncer
- **Cache / broker**: Redis (separate logical DBs in production)
- **Media**: Local FS (dev) or S3-compatible object storage + CDN
- **Edge**: Nginx (TLS, compression, routing, rate limits)

## Component diagram

```
                         Users
                           │
                     CDN / WAF
                           │
                        Nginx
              ┌────────────┼────────────┐
              │            │            │
           Next.js     Gunicorn      Daphne
           (SSR/UI)     (HTTP API)    (WebSockets)
              │            │            │
              │            ├──── Redis (cache / Channels / Celery)
              │            │
              │         PgBouncer
              │            │
              │        PostgreSQL
              │
         Object Storage ←── Celery media workers
```

## Database architecture

Core indexed domains (already present from earlier phases):

- Users: `username`, `email`, suspension / deletion flags
- Posts: `(status, visibility, -published_at)`, `(author, status, -published_at)`
- Comments: `(post, status, created_at)`
- Messages: `(conversation, -created_at)`
- Notifications: `(recipient, is_read, -created_at)`
- Connections: `(sender|receiver, status)`

Connection pooling: application → **PgBouncer (transaction)** → PostgreSQL (`CONN_MAX_AGE=0`).

## Cache strategy

Implemented in `apps/common/cache.py`:

- Profile payloads (30m)
- Feed first page (5m)
- Suggestions (10m)
- Unread notification counts (1m)

Invalidation hooks on profile update, post create, and notification mutations.

## Real-time architecture

```
Client ──WSS──▶ Nginx ──▶ Daphne workers
                              │
                         Redis Pub/Sub
                              │
                    other Daphne workers / Celery
```

Presence keys and chat fan-out use the Redis channel layer. Scale WS horizontally by adding Daphne replicas.

## Media pipeline

```
Upload → validate → store (S3/images|videos|thumbnails)
      → Celery queue: media_processing
      → Images: resize + WebP + thumbnail
      → Videos: ffprobe + thumbnail (+ optional ladder)
      → CDN Cache-Control: max-age=31536000
```

## Deployment architecture

See `docker/docker-compose.prod.yml` and `docs/production-deployment.md`.

Environments:

- **development** — compose at repo root, Daphne + bind mounts
- **staging** — prod-like compose, separate DB/bucket/secrets
- **production** — hardened settings, TLS, Sentry, backups

## Security layers

1. TLS at nginx
2. Django `SECURE_*` + HSTS in staging/production
3. Security headers middleware + CSP baseline
4. DRF anon/user throttles + scoped endpoint throttles
5. Login lockout + suspicious IP detection
6. JWT short access TTL + refresh rotation + blacklist cleanup beat task
7. Upload validation + media processing sandbox (worker queue)

## Related docs

- [Production deployment](production-deployment.md)
- [Scaling](scaling-guide.md)
- [Backups](backup-guide.md)
- [Monitoring](monitoring-guide.md)
