#!/usr/bin/env bash
# Encrypted off-host PostgreSQL backup.
# Requires: pg_dump, and `gpg` if ENCRYPT=1.
# Restores are performed by restore.sh. See docs/runbooks/BACKUP_RESTORE.md.
set -euo pipefail

cd "$(dirname "$0")/../.."
if [ -f infra/.env ]; then set -a; . infra/.env; set +a; fi

BACKUP_DIR="${BACKUP_DIR:-/backups}"
TIMESTAMP="$(date +%Y%m%d-%H%M%S)"
OUT="${BACKUP_DIR}/guill-${TIMESTAMP}.sql.gz"
mkdir -p "$BACKUP_DIR"

echo "Backing up ${POSTGRES_DB}@${POSTGRES_HOST:-postgres} -> ${OUT}"
PGPASSWORD="$POSTGRES_PASSWORD" pg_dump \
  -h "${POSTGRES_HOST:-postgres}" -U "${POSTGRES_USER:-app}" -d "${POSTGRES_DB:-guill}" \
  | gzip > "$OUT"

if [ "${ENCRYPT:-0}" = "1" ]; then
  gpg --batch --yes --symmetric --cipher-algo AES256 -o "${OUT}.gpg" "$OUT"
  rm -f "$OUT"
  echo "Encrypted backup written: ${OUT}.gpg"
else
  echo "Backup written: ${OUT}"
fi

# Retention: keep last 30 daily backups.
find "$BACKUP_DIR" -name 'guill-*.sql.gz*' -mtime +30 -delete
