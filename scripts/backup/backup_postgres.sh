#!/usr/bin/env bash
# Daily PostgreSQL backup with retention:
#   7 daily · 4 weekly · 12 monthly
set -euo pipefail

BACKUP_ROOT="${BACKUP_ROOT:-/var/backups/linkme}"
RETENTION_DAILY="${RETENTION_DAILY:-7}"
RETENTION_WEEKLY="${RETENTION_WEEKLY:-4}"
RETENTION_MONTHLY="${RETENTION_MONTHLY:-12}"

DB_HOST="${DATABASE_HOST:-postgres}"
DB_PORT="${DATABASE_PORT:-5432}"
DB_NAME="${DATABASE_NAME:-linkme_db}"
DB_USER="${DATABASE_USER:-linkme}"
export PGPASSWORD="${DATABASE_PASSWORD:?DATABASE_PASSWORD required}"

DATE="$(date -u +%Y-%m-%d)"
DAY_OF_WEEK="$(date -u +%u)"   # 1=Monday … 7=Sunday
DAY_OF_MONTH="$(date -u +%d)"

mkdir -p "${BACKUP_ROOT}/daily" "${BACKUP_ROOT}/weekly" "${BACKUP_ROOT}/monthly"

FILE="${BACKUP_ROOT}/daily/linkme_${DATE}.sql.gz"
echo "Backing up ${DB_NAME} → ${FILE}"
pg_dump -h "${DB_HOST}" -p "${DB_PORT}" -U "${DB_USER}" -d "${DB_NAME}" \
  --format=plain --no-owner --no-acl | gzip -9 > "${FILE}"

# Weekly snapshot (Sunday)
if [[ "${DAY_OF_WEEK}" == "7" ]]; then
  cp "${FILE}" "${BACKUP_ROOT}/weekly/linkme_${DATE}.sql.gz"
fi

# Monthly snapshot (1st)
if [[ "${DAY_OF_MONTH}" == "01" ]]; then
  cp "${FILE}" "${BACKUP_ROOT}/monthly/linkme_${DATE}.sql.gz"
fi

# Retention cleanup
find "${BACKUP_ROOT}/daily" -type f -name '*.sql.gz' | sort -r | tail -n +$((RETENTION_DAILY + 1)) | xargs -r rm -f
find "${BACKUP_ROOT}/weekly" -type f -name '*.sql.gz' | sort -r | tail -n +$((RETENTION_WEEKLY + 1)) | xargs -r rm -f
find "${BACKUP_ROOT}/monthly" -type f -name '*.sql.gz' | sort -r | tail -n +$((RETENTION_MONTHLY + 1)) | xargs -r rm -f

# Metadata sidecar for restore tooling
cat > "${BACKUP_ROOT}/daily/linkme_${DATE}.meta.json" <<EOF
{
  "database": "${DB_NAME}",
  "created_at": "$(date -u +%Y-%m-%dT%H:%M:%SZ)",
  "host": "${DB_HOST}",
  "type": "postgresql"
}
EOF

echo "Backup complete."
