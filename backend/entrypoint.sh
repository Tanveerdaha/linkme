#!/bin/sh
set -e

echo "Waiting for PostgreSQL at ${DATABASE_HOST}:${DATABASE_PORT:-5432}..."
python << 'PY'
import os
import time

import psycopg

host = os.environ.get("DATABASE_HOST", "postgres")
port = int(os.environ.get("DATABASE_PORT", "5432"))
user = os.environ.get("DATABASE_USER", "linkme")
password = os.environ.get("DATABASE_PASSWORD", "")
dbname = os.environ.get("DATABASE_NAME", "linkme_db")

for attempt in range(60):
    try:
        with psycopg.connect(
            host=host,
            port=port,
            user=user,
            password=password,
            dbname=dbname,
            connect_timeout=3,
        ):
            print("PostgreSQL is available.")
            break
    except Exception as exc:
        print(f"PostgreSQL not ready ({attempt + 1}/60): {exc}")
        time.sleep(2)
else:
    raise SystemExit("PostgreSQL did not become ready in time.")
PY

echo "Applying migrations..."
python manage.py migrate --noinput

# Static files only needed for the HTTP process.
case " $* " in
  *" daphne "*|*" gunicorn "*|*" runserver "*)
    echo "Collecting static files..."
    python manage.py collectstatic --noinput
    ;;
esac

exec "$@"
