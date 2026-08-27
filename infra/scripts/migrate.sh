#!/usr/bin/env bash
# Run Alembic migrations against the configured DATABASE_URL.
set -euo pipefail
cd "$(dirname "$0")/../.."
if [ -f infra/.env ]; then
  set -a; . infra/.env; set +a
fi
cd services/api
exec alembic upgrade head
