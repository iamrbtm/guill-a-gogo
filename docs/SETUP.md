# Setup guide (development & production)

## Prerequisites
- Docker Engine + Docker Compose v2
- Python 3.14 (for local API work outside Docker)
- Node 22 + Expo CLI (for the mobile client)
- Optional: Google Maps API key, SMTP/relay (see `docs/KEYS_GUIDE.md`)

## 1. Environment file
```bash
cp infra/.env.example infra/.env
# Edit at least: POSTGRES_PASSWORD, JWT_SECRET, RP_ID, RP_ORIGIN
```
Generate secrets:
```bash
python -c "import secrets;print('JWT_SECRET='+secrets.token_urlsafe(48))"
python -c "import secrets;print('POSTGRES_PASSWORD='+secrets.token_urlsafe(24))"
```

## 2. Start the stack (development)
```bash
docker compose -f infra/docker-compose.yml -f infra/docker-compose.override.yml up --build
```
- API: http://localhost:8000  (health: `/healthz`, `/readyz`, `/api/v1/health`)
- Postgres/Redis publish ports in dev override only.

## 3. Run database migrations
```bash
bash infra/scripts/migrate.sh
# or inside the api container:
docker compose -f infra/docker-compose.yml exec api alembic upgrade head
```

## 4. Create the first owner (bootstrap)
Accounts are invitation-only, so the first owner is created out-of-band:
```bash
docker compose -f infra/docker-compose.yml exec api \
  python scripts/create_owner.py --email owner@example.com --name "Trip Owner"
```
This prints an invitation token/link. Use it in the client (or via the
`/api/v1/auth/register` WebAuthn flow) to register the owner's passkey.

## 5. Local API without Docker (Python venv)
```bash
cd services/api
python -m venv .venv && . .venv/bin/activate
pip install -e ".[dev]"
export DATABASE_URL="sqlite://"   # or a local Postgres URL
python -m flask --app app run
pytest                            # unit/integration tests (SQLite-backed)
```

## 6. Mobile client (Expo) — scaffold
```bash
cd apps/mobile
npm install
npx expo start        # web: press w ; device: scan QR with dev build
```
> Native passkeys require an EAS development build, not Expo Go. See
> `docs/KEYS_GUIDE.md` §2.

## 7. Production deployment
- Deploy behind your **existing reverse proxy** (TLS termination). The API joins
  the external network named by `EXTERNAL_NETWORK`; Postgres/Redis stay private.
- Use the base `infra/docker-compose.yml` (no port publishing).
- Run `infra/scripts/migrate.sh` before first launch.
- Schedule `infra/scripts/backup.sh` (see `infra/runbooks/BACKUP_RESTORE.md`).

## 8. Running tests & checks
```bash
cd services/api && pytest
# lint/type (add as configured): ruff / mypy
```
See `docs/PHASE_CHECKLIST.md` for per-phase verification commands.
