#!/usr/bin/env bash
# Restore a PostgreSQL backup produced by backup.sh.
# Usage: RESTORE_FILE=/backups/guill-YYYYMMDD-HHMMSS.sql.gz ./restore.sh
set -euo pipefail

cd "$(dirname "$0")/../.."
if [ -f infra/.env ]; then set -a; . infra/.env; set +a; fi

RESTORE_FILE="${RESTORE_FILE:?Set RESTORE_FILE to the backup path}"
if [ ! -f "$RESTORE_FILE" ]; then echo "Missing $RESTORE_FILE"; exit 1; fi

TMP="$RESTORE_FILE"
if [[ "$RESTORE_FILE" == *.gpg ]]; then
  echo "Decrypting..."
  gpg --batch --yes --decrypt -o "${RESTORE_FILE%.gpg}" "$RESTORE_FILE"
  TMP="${RESTORE_FILE%.gpg}"
fi

echo "Restoring ${TMP} into ${POSTGRES_DB}@${POSTGRES_HOST:-postgres}"
if [[ "$TMP" == *.gz ]]; then
  zcat "$TMP"
else
  cat "$TMP"
fi | PGPASSWORD="$POSTGRES_PASSWORD" psql -h "${POSTGRES_HOST:-postgres}" -U "${POSTGRES_USER:-app}" -d "${POSTGRES_DB:-guill}"

echo "Restore complete."
