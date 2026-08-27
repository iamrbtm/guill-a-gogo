# Backup & restore runbook

Postgres is the system of record. Backups are produced by
`infra/scripts/backup.sh` and restored by `infra/scripts/restore.sh`. Redis
(caches/queues) is not backed up; it is repopulated from providers/DB.

## Backup (automated)
Schedule via cron or the `backup` container's entrypoint:
```bash
# encrypted, off-host recommended:
ENCRYPT=1 BACKUP_DIR=/backups ./infra/scripts/backup.sh
```
- Output: `/backups/guill-YYYYMMDD-HHMMSS.sql.gz` (or `.gz.gpg` if `ENCRYPT=1`).
- Retention: 30 daily backups kept by the script.
- For off-host: push `/backups` to object storage (e.g. `rclone`/`aws s3 cp`)
  from a separate job. Document the off-host target; do not store keys in repo.

## Restore (tested procedure)
1. Stop writers (or pause the API) to avoid partial restores:
   `docker compose -f infra/docker-compose.yml stop api worker beat`
2. Pick the backup: `RESTORE_FILE=/backups/guill-....sql.gz`
3. Run: `./infra/scripts/restore.sh` (set `ENCRYPT=1` not needed; the script
   auto-detects `.gpg` and decrypts).
4. Restart: `docker compose -f infra/docker-compose.yml start api worker beat`
5. Verify: `docker compose ... exec api python -c "from app import create_app; create_app()" `
   and spot-check a row count.

## Rollback of migrations
- Alembic `downgrade` is supported for the initial migration (drops all tables).
- Never run destructive migrations automatically in production without a backup
  taken immediately before (the migration script assumes a fresh backup exists).
