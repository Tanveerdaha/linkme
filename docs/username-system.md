# Username uniqueness system

LinkMe usernames are globally unique, case-insensitive public handles.

## Validation flow

```
User enters username
        ↓
Normalize (trim, lowercase, strip invalid chars for canonical form)
        ↓
Validate format (length, allowed charset, reserved names)
        ↓
Check Redis Bloom Filter (linkme:usernames)
        ↓
If possible match → check PostgreSQL
If no match → available
        ↓
On successful create / rename → save user → BF.ADD
```

## Bloom Filter purpose

The Redis Bloom filter is a **read-path speed optimization** for availability
checks. It answers “might this username already exist?” in O(1).

| Outcome | Meaning |
|---------|---------|
| `BF.EXISTS = 0` | Definitely free (no false negatives) |
| `BF.EXISTS = 1` | Maybe taken → confirm in PostgreSQL |

False positives are acceptable. False negatives must never happen, so after
every successful signup or username change we always `BF.ADD` the new handle.

## Database protection

PostgreSQL remains the source of truth:

- `User.username` has `unique=True`
- Application code lowercases before save
- Concurrent signups that race past the bloom/API check hit `IntegrityError`
  and are rejected as duplicate usernames

## API

`GET /api/v1/users/check-username/?username=<value>`

Available:

```json
{ "username": "azeemamjad", "available": true }
```

Taken:

```json
{
  "username": "azeemamjad",
  "available": false,
  "reason": "Username already exists"
}
```

Authenticated callers are excluded from conflicting with their own current
username (useful for profile rename).

## Configuration

| Variable | Purpose |
|----------|---------|
| `REDIS_URL` / `REDIS_HOST` / `REDIS_PORT` / `REDIS_PASSWORD` | Redis connection |
| `REDIS_BLOOM_ENABLED` | Enable Bloom (default `true`) |

Docker Compose uses `redis/redis-stack-server` so RedisBloom (`BF.*`) is available.

## Recovery / rebuild

If Redis data is lost or the filter drifts:

```bash
python manage.py rebuild_username_bloom
```

This deletes `linkme:usernames`, recreates the filter
(`error_rate=0.01`, `capacity=1_000_000`), and loads every username from
PostgreSQL.
