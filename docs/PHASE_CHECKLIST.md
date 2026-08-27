# Phase checklist

## Phase 1 — Foundation and authentication
- [x] Monorepo structure (apps/services/packages/infra/docs)
- [x] Compose stack: api, worker, beat, postgres, redis, backup
- [x] Flask app factory + blueprints; config from env only
- [x] Secure headers, restricted CORS, rate limiting, health/readiness
- [x] SQLAlchemy 2.x models: User, PasskeyCredential, Invitation,
      RecoveryToken, RecoveryCode, RefreshSession, Trip, TripMembership, AuditEvent
- [x] Alembic initial migration
- [x] WebAuthn passkey register/authenticate (challenge store)
- [x] Invitation-only accounts + first-owner bootstrap script
- [x] Short-lived access JWT + rotating refresh tokens + revocation
- [x] Single-use recovery codes + recovery email flow
- [x] Audit logging foundation
- [x] Provider-status endpoint (no secret leakage)
- [X] Deterministic tests (config, crypto, headers, challenges, invitations,
      refresh rotation, recovery codes) — 16 passing
- [x] Expo mobile shell scaffold (bottom nav, config)
- [x] OpenAPI contract (packages/contracts)
- [x] Docs: SETUP, KEYS_GUIDE, ADR, runbook, threat model
- [x] CI workflow (lint + test)

### Phase 1 verification commands
```bash
cd services/api && pytest
docker compose -f infra/docker-compose.yml -f infra/docker-compose.override.yml up --build
curl localhost:8000/healthz
bash infra/scripts/migrate.sh
docker compose -f infra/docker-compose.yml exec api python scripts/create_owner.py --email owner@example.com --name Owner
```

## Phase 2 — Profiles and manual trips  (not started)
- [ ] Traveler, pet, vehicle, trailer, preference profiles + CRUD
- [ ] Trip, day, stop, lodging, meal, reservation, expense CRUD
- [ ] Role-based permissions in service layer
- [ ] Accessible Expo screens

## Phase 3 — Deterministic planning + Tennessee seed  (not started)
- [ ] Google routing/geocoding adapters, route legs, daily division
- [ ] Breaks, fuel calculations, warnings, alternatives
- [ ] Repeatable Tennessee-trip import fixture

## Phase 4 — Today mode + offline  (not started)
- [ ] Today dashboard, nav deep links, progress updates
- [ ] Offline cache, mutation outbox, sync, conflict resolution

## Phase 5 — Research providers + AI proposals  (not started)
- [ ] Places/meals/lodging/fuel/weather/road-condition adapters
- [ ] Provider provenance + staleness; schema-validated AI proposals + approval

## Phase 6 — Exports + hardening  (not started)
- [ ] PDF/DOCX/XLSX/CSV exports, optional Drive delivery
- [ ] Security review, a11y audit, backup restore test, ops docs
