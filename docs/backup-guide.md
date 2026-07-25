# Backup & Disaster Recovery

## Backup schedule

`scripts/backup/backup_postgres.sh` produces:

| Cadence | Retention |
| --- | --- |
| Daily | 7 |
| Weekly (Sunday) | 4 |
| Monthly (1st) | 12 |

Install cron on the DB host (or a bastion with network access):

```cron
0 2 * * * DATABASE_HOST=... DATABASE_PASSWORD=... \
  /opt/linkme/scripts/backup/backup_postgres.sh >> /var/log/linkme-backup.log 2>&1
```

Also back up:

- Object storage (S3 versioning + cross-region replication)
- `environment/production/.env` in a secrets manager (not disk)
- TLS certificates / DNS config

## Restore database

```bash
export DATABASE_HOST=... DATABASE_PASSWORD=...
./scripts/backup/restore_postgres.sh /var/backups/linkme/daily/linkme_2026-07-25.sql.gz
```

Then restart API / Celery so connections refresh.

## Disaster scenarios

### Database failure

1. Promote latest verified backup
2. Point PgBouncer at restored primary
3. Run `python manage.py migrate` if schema drifted
4. Verify `/api/readiness/`

### Object storage failure

1. Restore bucket from versioning / replica
2. Confirm `MEDIA_STORAGE_BUCKET` + CDN origin
3. Smoke-test avatar + post media URLs

### Application failure / bad deploy

1. Roll back to previous GHCR image tag (`IMAGE_TAG=<sha>`)
2. Recreate `backend`, `frontend`, `websocket`
3. If migrations were forward-only and irreversible, restore DB snapshot taken pre-deploy

### Redis failure

1. Restart Redis (AOF enabled in prod compose)
2. Expect temporary cache misses + WS reconnects
3. Celery will redeliver unacked tasks (`acks_late=True`)

### Complete region outage

1. Restore Postgres + object storage in secondary region
2. Update DNS / CDN origin
3. Bring up compose stack with staging→prod secrets
4. Invalidate CDN cache

## Verification

After any restore:

- [ ] `/api/health/` healthy
- [ ] Login works
- [ ] Recent posts visible
- [ ] Media URLs resolve
- [ ] Celery `inspect ping` returns workers
