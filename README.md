# LinkMe

Production-grade social networking platform (**Phase 10 — Performance, Scaling & Production Launch**).

## Project Overview

LinkMe is a modular monorepo for a scalable social platform.

| Phase | Focus |
| --- | --- |
| 0 | Infrastructure |
| 1 | Authentication & profiles |
| 2 | Posts, media, feed |
| 3 | Reactions & comments |
| 4 | Profile expansion & discovery |
| 5 | Network & connections |
| 6 | Messaging |
| 7 | Notifications |
| 8 | Safety, privacy & moderation |
| 9 | Admin dashboard |
| **10** | **Performance, scaling & production launch** |

## Architecture

| Layer | Stack |
| --- | --- |
| Edge | Nginx (TLS, compression, routing) |
| Frontend | Next.js (standalone), TypeScript, Tailwind |
| API | Django 5, DRF, Gunicorn, SimpleJWT |
| Realtime | Daphne + Channels + Redis |
| Workers | Celery (queued: default, media, notifications, exports, cleanup) |
| Data | PostgreSQL + PgBouncer |
| Cache | Redis |
| Media | S3-compatible object storage + CDN |
| Observability | Sentry, structured JSON logs, health probes |

See [docs/system-architecture.md](docs/system-architecture.md).

## Run locally (Docker)

### 1. Copy environment files

```bash
cp backend/.env.example backend/.env
cp frontend/.env.example frontend/.env.local
```

Edit `backend/.env` if you need custom secrets. Defaults work for local Docker.

### 2. Start the stack

```bash
docker compose up --build
```

Detached mode:

```bash
docker compose up --build -d
```

### 3. Open the app

| Service | URL |
| --- | --- |
| Frontend | http://localhost:8014 |
| API | http://localhost:8013/api/v1 |
| API health | http://localhost:8013/api/health/ |
| Readiness | http://localhost:8013/api/readiness/ |
| Liveness | http://localhost:8013/api/liveness/ |
| Swagger | http://localhost:8013/api/docs/ |
| PostgreSQL | localhost:5435 |
| Redis | localhost:6381 |

> **Port note:** API **8013** → 8000 (container), frontend **8014**, Postgres **5435** → 5432 (container), Redis **6381** → 6379 (container). Inside Compose, backend still reaches Postgres at `postgres:5432` and Redis at `redis:6379`.

### Useful commands

```bash
# Status
docker compose ps

# Logs (all / one service)
docker compose logs -f
docker compose logs -f backend
docker compose logs -f frontend
docker compose logs -f celery

# Restart a service
docker compose restart backend

# Stop
docker compose down

# Stop and remove volumes (wipes Postgres data)
docker compose down -v

# Rebuild after dependency changes
docker compose up --build -d
```

### Services started

| Service | Role |
| --- | --- |
| `postgres` | PostgreSQL 16 |
| `redis` | Cache, Celery broker, Channels |
| `backend` | Django API + WebSockets (Daphne) |
| `celery` | Background workers |
| `celery_beat` | Periodic tasks |
| `frontend` | Next.js app |

## Run without Docker (optional)

Requires local PostgreSQL + Redis, then:

```bash
# Backend
cd backend
cp .env.example .env
# Set DATABASE_HOST=localhost, DATABASE_PORT=5435, REDIS_URL=redis://localhost:6381/0
pip install -r requirements/dev.txt
python manage.py migrate
python manage.py runserver 0.0.0.0:8013
# or: daphne -b 0.0.0.0 -p 8013 config.asgi:application

# Celery (separate terminals) — required when NOTIFICATIONS_INLINE=false
# Notifications, media processing, and exports run on these queues.
celery -A config worker -Q default,media_processing,notifications,exports,cleanup --loglevel=info
celery -A config beat --loglevel=info

# Frontend
cd frontend
cp .env.example .env.local
npm ci
npm run dev
```

## Tests & lint

```bash
# Backend
cd backend
pip install -r requirements/dev.txt
pytest
black --check .
flake8 .

# Frontend
cd frontend
npm ci
npm run lint
npm run typecheck
npm run build
```

## Production

```bash
cp environment/production/.env.example environment/production/.env
# Fill secrets, then:
docker compose -f docker/docker-compose.prod.yml \
  --env-file environment/production/.env up -d --build
```

Docs:

- [Production deployment](docs/production-deployment.md)
- [Scaling](docs/scaling-guide.md)
- [Backups](docs/backup-guide.md)
- [Monitoring](docs/monitoring-guide.md)
- [Load testing](docs/load-testing-results.md)

## Phase 10 highlights

- Environment separation (`environment/{development,staging,production}`)
- Production Docker + Nginx + PgBouncer + multi-queue Celery
- Redis caching for profiles, feed, suggestions, notification counts
- Media pipeline (WebP / thumbnails / async processing) + S3/CDN ready
- Security hardening (SECURE_*, CSP, throttles, login lockout)
- Health / readiness / liveness probes
- Sentry + structured logging
- CI/CD (GitHub Actions) + Locust / k6 load tests
- Backup scripts with 7/4/12 retention
