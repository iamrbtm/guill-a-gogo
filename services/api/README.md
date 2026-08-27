# Guill-a-Gogo API (Flask)

Phase 1 foundation: application factory, configuration, security middleware,
account/access domain models, Alembic migration, and WebAuthn-based
authentication (invitation-only accounts, passkeys, refresh-token rotation,
recovery codes, audit logging).

## Run (local venv)
```bash
python -m venv .venv && . .venv/bin/activate
pip install -e ".[dev]"
export DATABASE_URL="sqlite://"   # or postgresql+psycopg://...
python -m flask --app app run
pytest
```

## Endpoints (v1)
- `GET  /api/v1/health`, `GET /healthz`, `GET /readyz`
- `GET  /api/v1/provider-status` — provider config, no secrets
- `POST /api/v1/invitations` — owner creates invitation (auth required)
- `GET  /api/v1/invitations/<token>` — invitation details
- `POST /api/v1/auth/register/options` + `/auth/register` — WebAuthn registration
- `POST /api/v1/auth/login/options` + `/auth/login` — WebAuthn login
- `POST /api/v1/auth/refresh`, `/auth/logout`
- `POST /api/v1/auth/recovery/request`, `/auth/recovery-code`

## Notes
- All secrets come from the environment (see `infra/.env.example`).
- The OpenAPI source lives in `packages/contracts/openapi.yaml`.
- For full setup, see `../../docs/SETUP.md`.
