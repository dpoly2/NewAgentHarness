#!/usr/bin/env bash
# run_pg_tests.sh — run the ArchonHub DB test suite against a throwaway Postgres,
# locally, the same way the postgres leg of .github/workflows/archonhub-db-ci.yml
# does. Mirrors T5 (docs/AGENT_WORKPLAN.md).
#
# Usage (from app/v3):
#   ./scripts/run_pg_tests.sh              # uses `python`
#   PYTHON=python3 ./scripts/run_pg_tests.sh
#
# A fresh/empty database is REQUIRED each run — several tests create rows with
# default unique keys that would collide on a reused DB. The container is
# recreated every invocation, which guarantees that.
set -euo pipefail

PYTHON="${PYTHON:-python}"
PORT="${PORT:-5433}"
CONTAINER="${CONTAINER:-archonhub-pg-test}"

APP_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"   # app/v3
cd "$APP_DIR"

cleanup() { echo "==> Tearing down container"; docker rm -f "$CONTAINER" >/dev/null 2>&1 || true; }
trap cleanup EXIT

echo "==> Starting throwaway postgres:16 on port $PORT"
docker rm -f "$CONTAINER" >/dev/null 2>&1 || true
docker run -d --name "$CONTAINER" \
  -e POSTGRES_USER=archonhub \
  -e POSTGRES_PASSWORD=archonhub \
  -e POSTGRES_DB=archonhub \
  -p "${PORT}:5432" postgres:16 >/dev/null

echo "==> Waiting for postgres to accept connections"
for _ in $(seq 1 30); do
  if docker exec "$CONTAINER" pg_isready -U archonhub >/dev/null 2>&1; then break; fi
  sleep 1
done

export DB_BACKEND=postgres
export DATABASE_URL="postgresql://archonhub:archonhub@localhost:${PORT}/archonhub"
export PYTHONPATH="$APP_DIR"

echo "==> Installing Postgres driver"
"$PYTHON" -m pip install "psycopg[binary]>=3.1" "psycopg_pool>=3.1" >/dev/null

echo "==> Initializing schema via app _init_schema()"
"$PYTHON" -c "import core.database as d; d._init_schema(); print('PG schema initialized')"

echo "==> Running DB test suite against Postgres"
"$PYTHON" -m pytest -q -p no:cacheprovider \
  tests/test_hub_db.py \
  tests/test_pg_migration.py \
  tests/test_job_claim_concurrency.py \
  tests/test_migrate_ordering.py
