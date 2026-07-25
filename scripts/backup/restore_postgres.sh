#!/usr/bin/env bash
# Restore PostgreSQL from a gzipped SQL dump.
# Usage: ./restore_postgres.sh /path/to/linkme_YYYY-MM-DD.sql.gz
set -euo pipefail

DUMP="${1:?Usage: $0 <backup.sql.gz>}"
DB_HOST="${DATABASE_HOST:-postgres}"
DB_PORT="${DATABASE_PORT:-5432}"
DB_NAME="${DATABASE_NAME:-linkme_db}"
DB_USER="${DATABASE_USER:-linkme}"
export PGPASSWORD="${DATABASE_PASSWORD:?DATABASE_PASSWORD required}"

echo "WARNING: This will drop and recreate ${DB_NAME} on ${DB_HOST}."
read -r -p "Type 'restore' to continue: " confirm
[[ "${confirm}" == "restore" ]] || { echo "Aborted."; exit 1; }

psql -h "${DB_HOST}" -p "${DB_PORT}" -U "${DB_USER}" -d postgres \
  -c "SELECT pg_terminate_backend(pid) FROM pg_stat_activity WHERE datname='${DB_NAME}' AND pid <> pg_backend_pid();" || true
psql -h "${DB_HOST}" -p "${DB_PORT}" -U "${DB_USER}" -d postgres \
  -c "DROP DATABASE IF EXISTS ${DB_NAME};"
psql -h "${DB_HOST}" -p "${DB_PORT}" -U "${DB_USER}" -d postgres \
  -c "CREATE DATABASE ${DB_NAME} OWNER ${DB_USER};"

gunzip -c "${DUMP}" | psql -h "${DB_HOST}" -p "${DB_PORT}" -U "${DB_USER}" -d "${DB_NAME}"
echo "Restore complete from ${DUMP}"
