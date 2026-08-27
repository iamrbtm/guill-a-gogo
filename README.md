# Guill-a-Gogo — Accessible, Pet-Friendly Road Trip Planner

A private, invitation-only, multi-trip planning app for a family traveling with
mobility limitations, sensory considerations, pets, and a trailer. Built per the
master prompt (`docs/OpenCode_Accessible_Road_Trip_Planner_Master_Prompt.md`).

## Status
**Phase 1 (Foundation & authentication) — in progress / functionally complete.**
See `docs/PHASE_CHECKLIST.md` for per-phase status and verification commands.

## Architecture (modular monolith)
```
apps/mobile/      Expo / React Native / TypeScript client
services/api/     Flask REST API (app factory, blueprints, SQLAlchemy 2.x, Alembic)
services/worker/  Celery worker + beat (background & scheduled jobs)
packages/contracts/ Generated TypeScript API contracts (OpenAPI source)
infra/            Docker Compose, Dockerfile, .env.example, backup/restore scripts
docs/             Setup, keys guide, ADR, threat model, phase checklist, runbooks
```
- PostgreSQL 17 + Redis 7 via Compose. Postgres/Redis publish **no host ports**
  in production; only the API joins the existing external reverse-proxy network.
- Auth: passkeys (WebAuthn), short-lived access JWTs, rotating/revocable refresh
  tokens, single-use recovery codes, audit logging.
- Optional providers (Google Maps, AI, email) default to safe no-op/degraded
  modes so the core app never blocks on a missing credential.
- AI layer is provider-neutral and defaults to `none`.

## Quick start
See `docs/SETUP.md`. In short:
```bash
cp infra/.env.example infra/.env   # fill secrets
docker compose -f infra/docker-compose.yml -f infra/docker-compose.override.yml up --build
bash infra/scripts/migrate.sh
docker compose -f infra/docker-compose.yml exec api python scripts/create_owner.py --email owner@example.com --name Owner
```

## Getting keys (Google Maps, domain/passkeys, AI, email)
See **`docs/KEYS_GUIDE.md`** — step-by-step, with the note that the app runs
fully without any of them. (Kilocode is a coding assistant, not a callable API;
point `AI_BASE_URL` at any OpenAI-compatible endpoint if you enable AI.)

## Tests
```bash
cd services/api && pytest   # 16 passing (SQLite-backed)
```
CI: `.github/workflows/ci.yml` runs lint + tests (API) and typecheck (mobile).

## Docs index
- `docs/SETUP.md` — dev & prod setup
- `docs/KEYS_GUIDE.md` — obtaining every external key
- `docs/adr/0001-phase1-foundation.md` — architecture decisions
- `docs/THREAT_MODEL.md` — security threat model
- `docs/PHASE_CHECKLIST.md` — phase progress + verification commands
- `infra/runbooks/BACKUP_RESTORE.md` — backup/restore
