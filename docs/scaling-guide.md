# Scaling Guide

## Horizontal scaling

```
Users → CDN/WAF → Load balancer → nginx
                                    ├─ Next.js (N replicas)
                                    ├─ Gunicorn API (N replicas)
                                    └─ Daphne WS (N replicas)
                                         │
                              Redis pub/sub channel layer
```

- **API**: scale Gunicorn replicas behind nginx/`least_conn`
- **WebSockets**: scale Daphne workers; Channels Redis layer fans out events
- **Celery**: scale per queue (`media_processing`, `notifications`, `default`)
- **Postgres**: keep a single primary; add read replicas later for feed fan-out
- **PgBouncer**: raise `default_pool_size` before adding more API replicas

## Feed performance

1. Cursor pagination only (`PostCursorPagination`) — never OFFSET
2. `select_related("author", "author__profile")` + `prefetch_related("media")`
3. Engagement annotations on the queryset (no N+1)
4. Redis first-page cache: `feed:user:{id}` / `feed:public` (TTL 5 min)
5. Invalidate author + public feed on new posts

## Cache map

| Key | TTL | Invalidate |
| --- | --- | --- |
| `profile:{username}` | 30m | Profile update |
| `feed:user:{id}` | 5m | New post / TTL |
| `feed:public` | 5m | New post / TTL |
| `suggestions:{id}` | 10m | TTL |
| `notifications:{id}:unread` | 1m | Create / read / delete |

## Celery queues

| Queue | Workload | Suggested concurrency |
| --- | --- | --- |
| `default` | Misc | 4 |
| `media_processing` | FFmpeg / Pillow | 2 (CPU heavy) |
| `notifications` | Fan-out + WS push | 4–8 |
| `exports` | ZIP generation | 1–2 |
| `cleanup` | Retention / JWT blacklist | 1 |

## Media pipeline

```
Upload → validate → store original (S3)
      → Celery media_processing
      → WebP + thumbnail (images) / FFmpeg thumb (videos)
      → CDN Cache-Control: max-age=31536000
```

## Performance targets

| Surface | Target |
| --- | --- |
| API average | < 200ms |
| Feed p95 | < 500ms |
| Profile | < 300ms |
| WS delivery | < 100ms |
| Slow SQL | < 100ms |

## Load testing

```bash
# Locust
pip install -r loadtests/requirements.txt
locust -f loadtests/locust/locustfile.py --host http://localhost:8000 \
  --users 200 --spawn-rate 20 --run-time 3m --headless

# k6 feed
k6 run loadtests/k6/feed.js

# k6 websockets
LINKME_ACCESS_TOKEN=... CONVERSATION_ID=... k6 run loadtests/k6/websocket.js
```

## When to shard

Consider sharding / CQRS when:

- Feed QPS exceeds ~2k sustained on a single primary
- Notification fan-out exceeds Celery pool capacity for >15 min
- Media processing backlog regularly exceeds 5 minutes
