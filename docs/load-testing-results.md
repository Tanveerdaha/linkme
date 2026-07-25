# Load testing results (baseline template)

Run against a staging stack before launch. Record numbers here.

## Environment under test

| Field | Value |
| --- | --- |
| Date | YYYY-MM-DD |
| Host | staging / local prod-compose |
| API replicas | |
| Celery workers | |
| DB | |
| Notes | |

## Feed browse (k6 / Locust)

| Metric | Target | Observed | Pass? |
| --- | --- | --- | --- |
| Avg latency | < 200ms | | |
| Feed p95 | < 500ms | | |
| Error rate | < 1% | | |
| Max VUs | 500 / 10k soak | | |

```bash
k6 run loadtests/k6/feed.js
locust -f loadtests/locust/locustfile.py --host https://staging... \
  --users 500 --spawn-rate 25 --run-time 5m --headless
```

## Messaging WebSockets

| Metric | Target | Observed | Pass? |
| --- | --- | --- | --- |
| Concurrent connections | 1000 | | |
| Delivery p95 | < 100ms | | |

```bash
LINKME_ACCESS_TOKEN=... CONVERSATION_ID=... k6 run loadtests/k6/websocket.js
```

## Upload load

| Metric | Target | Observed | Pass? |
| --- | --- | --- | --- |
| Successful posts/min | | | |
| Media queue lag | < 5 min | | |

```bash
LOCUST_ENABLE_UPLOADS=1 LINKME_ACCESS_TOKEN=... \
  locust -f loadtests/locust/locustfile.py --host ... --users 20 --run-time 5m --headless
```

## Sign-off

- [ ] Targets met or accepted with mitigation plan
- [ ] Bottlenecks documented (DB / Redis / Gunicorn / Celery)
- [ ] Scaling actions applied
