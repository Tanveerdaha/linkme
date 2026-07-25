# Monitoring Guide

## Application errors — Sentry

```env
SENTRY_DSN=https://...@o....ingest.sentry.io/...
SENTRY_TRACES_SAMPLE_RATE=0.1
ENVIRONMENT=production
```

Tracks Django exceptions, Celery failures, and Redis integration issues. PII is disabled (`send_default_pii=False`).

## Structured logs

JSON lines under `LOG_DIR` (default `/app/logs`):

| File | Contents |
| --- | --- |
| `application.log` | App / Django |
| `security.log` | Login failures, lockouts, suspicious IP |
| `celery.log` | Worker activity |
| `access.log` | API request latency (`duration_ms`) |

Ship to Loki / CloudWatch / ELK via a node agent. Nginx emits JSON access logs as well.

## Health endpoints

| Probe | Path | Checks |
| --- | --- | --- |
| Liveness | `/api/liveness/` | Process |
| Readiness | `/api/readiness/` | Postgres + Redis |
| Health | `/api/health/` | + Celery ping |

## Infrastructure metrics (suggested)

| Component | Signals |
| --- | --- |
| CPU / Memory / Disk | Node exporter / cloud monitors |
| PostgreSQL | Connections, slow queries, replication lag |
| Redis | Memory, hit rate, evictions |
| Celery | Queue depth, task runtime, retries |
| Nginx | 5xx rate, upstream latency |

## Celery inspection

```bash
./backend/celery/monitor.sh
# or
celery -A config inspect active
celery -A config inspect stats
```

## Alert ideas

- `/api/readiness/` ≠ 200 for > 2 minutes
- Feed p95 > 500ms for 10 minutes
- Celery `media_processing` depth > 100
- Login lockout burst (security.log)
- Disk usage > 80% on Postgres volume
- Sentry error spike > 3× baseline

## Performance budgets

| Path | Budget |
| --- | --- |
| API average | < 200ms |
| Feed | < 500ms |
| Profile | < 300ms |
| WebSocket delivery | < 100ms |
| Slow query | < 100ms |
