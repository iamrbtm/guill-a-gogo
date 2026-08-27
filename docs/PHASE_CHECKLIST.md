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

## Phase 2 — Profiles and manual trips  (DONE)
- [x] Models: TravelerProfile, Pet, Vehicle, Trailer, Preference (with medical privacy)
- [x] Itinerary models: TripDay, Stop, LodgingCandidate, MealPlan, Reservation, Expense, PlanningWarning
- [x] Trip<->profile links (travelers, pets, vehicle, trailer)
- [x] Service-layer permissions (owner/editor/traveler/viewer + profile sharing)
- [x] CRUD services + REST routes: trips, members, profiles, plan, expenses
- [x] Lodging "required accessibility / two-dog" never auto-confirmed (human confirmation only)
- [x] Deterministic vehicle-completeness blocking warning
- [x] Alembic migration upgrade/downgrade test (23 tests total passing)
- [x] Accessible Expo screens: API client (secure token store), Trips list/detail,
      Profiles list/create, Plan, More, New trip/stop forms (a11y primitives)

### Phase 2 verification commands
```bash
cd services/api && pytest            # 23 passing
# manual: create trip + traveler via API, assign, refresh warnings (blocking)
```

## Phase 3 — Deterministic planning + Tennessee seed  (DONE)
- [x] Routing provider interface (RoutingProvider) + MockRoutingProvider + GoogleRoutingProvider stub
- [x] Provider degrades gracefully (ProviderUnavailable -> manual entry; never invents distances)
- [x] Deterministic planner: daily division, wheel-turning vs break time, breaks every ~2h,
     fuel gallons/stops/cost from MPG + tank + price + reserve, warnings, single-leg overflow
- [x] Repeatable Tennessee seed (Mother/Jeremy/Nephew, 2 unnamed dogs, incomplete vehicle ->
     blocking warning, 8 required stops). Idempotent via deterministic UUIDs + CLI.
- [x] `/trips/<id>/plan` endpoint (Google when keyed; mock only under ALLOW_MOCK_PLANNING; else 503)
- [x] Tests: planner division/breaks/fuel, single-leg overflow, provider degradation, seed fixture, plan endpoint (29 total passing)

### Phase 3 verification commands
```bash
cd services/api && pytest
ALLOW_MOCK_PLANNING=1 python -m pytest tests/test_phase3.py
# end-to-end seed:
docker compose ... exec api python scripts/create_owner.py --email owner@example.com --name Owner
docker compose ... exec api python scripts/seed_tennessee.py --email owner@example.com
``` fixture

## Phase 4 — Today mode + offline  (not started)
- [ ] Today dashboard, nav deep links, progress updates
- [ ] Offline cache, mutation outbox, sync, conflict resolution

## Phase 5 — Research providers + AI proposals  (not started)
- [ ] Places/meals/lodging/fuel/weather/road-condition adapters
- [ ] Provider provenance + staleness; schema-validated AI proposals + approval

## Phase 6 — Exports + hardening  (not started)
- [ ] PDF/DOCX/XLSX/CSV exports, optional Drive delivery
- [ ] Security review, a11y audit, backup restore test, ops docs
