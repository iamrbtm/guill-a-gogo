# Release checklist

## Pre-release
- [ ] All tests pass: `cd services/api && pytest` (44 passing as of Phase 6).
- [ ] Lint/typecheck: `ruff check app`, `mypy` (when configured), `tsc --noEmit` for mobile.
- [ ] Production build: `docker compose -f infra/docker-compose.yml up --build` starts cleanly.
- [ ] Migrations run on a fresh DB: `bash infra/scripts/migrate.sh`.
- [ ] Secrets generated: `JWT_SECRET`, `POSTGRES_PASSWORD`, `RP_ID`, `RP_ORIGIN` set for production hostname.
- [ ] Reverse proxy configured; API joins `EXTERNAL_NETWORK`; Postgres/Redis publish no host ports.
- [ ] Backup scheduled: `infra/scripts/backup.sh` (encrypted, off-host) + restore tested via `infra/scripts/restore.sh`.
- [ ] Google Cloud APIs enabled + key restricted + billing alerts set (if using Maps/routing).
- [ ] EAS development/production build created for passkey support (Expo Go insufficient).
- [ ] Invitation-only bootstrap: first owner created via `scripts/create_owner.py`.

## Release
- [ ] Tag the release in Git.
- [ ] Deploy Compose stack behind the reverse proxy.
- [ ] Run smoke tests against production: `/healthz`, `/readyz`, create trip, seed Tennessee, export CSV.
- [ ] Verify HTTPS + secure headers (CSP, HSTS, nosniff).
- [ ] Confirm audit logging active for invitations, approvals, destructive actions.

## Post-release
- [ ] Monitor provider-health endpoint (`/api/v1/provider-status`).
- [ ] Verify backup retention and off-host copy.
- [ ] Schedule dependency + secret scanning in CI.
- [ ] Conduct accessibility screen-reader pass (iOS VoiceOver / Android TalkBack).
