# Architecture Decision Record — Phase 1 (Foundation)

## ADR-0001: Modular monolith, Flask + Expo, Postgres + Celery
Status: accepted (2026-08-26)

Context: The master prompt mandates a modular monolith with `services/api`
(Flask), `services/worker` (Celery), `apps/mobile` (Expo/React Native), and a
Postgres 17 + Redis + Celery stack. Python 3.14 is available and all core deps
installed cleanly, so we adopt 3.14 as required.

Decision:
- Flask application factory with blueprint boundaries; SQLAlchemy 2.x ORM;
  Alembic for migrations; psycopg 3 driver.
- Deterministic security applied server-side (headers, CORS, rate limit, JWT).
- WebAuthn passkeys via the `webauthn` library; challenge store pluggable
  (in-memory now, Redis later).
- All optional providers (Maps, AI, email) default to safe no-op/degraded modes
  so the core app never blocks on a missing credential.

Consequences: Larger initial surface, but matches spec and keeps providers
swappable. AI layer is provider-neutral (`none` default).

## ADR-0002: Invitation-only accounts with out-of-band first owner
Status: accepted

Context: No public signup. The first owner cannot be invited by another owner.
Decision: Provide a CLI `scripts/create_owner.py` that creates the owner account
and emits an invitation token. Subsequent accounts are created only via
owner-generated invitations. This is a reversible, documented bootstrap.

## ADR-0003: Refresh-token rotation with revocation
Status: accepted

Refresh tokens are opaque random strings; only a SHA-256 hash is stored in
`refresh_sessions`. Rotation revokes the prior token. Short-lived (15 min)
access JWTs are stateless. This satisfies "revocable sessions" and "rotating
refresh tokens".

## ADR-0004: SQLite for tests, Postgres for runtime
Status: accepted

Tests run against an in-memory SQLite database (StaticPool) so CI/dev need no
Postgres. Runtime uses Postgres 17. The ORM uses portable types; any
Postgres-specific SQL is confined to migrations.

## ADR-0005: AI provider = `none` by default, OpenAI-compatible plug
Status: accepted

Kilocode is a coding assistant, not a callable API; we expose an
OpenAI-compatible `AI_BASE_URL` so any compatible endpoint can be used. Default
`none`: the app fully functions without AI, and AI output is always
schema-validated and human-approved.
