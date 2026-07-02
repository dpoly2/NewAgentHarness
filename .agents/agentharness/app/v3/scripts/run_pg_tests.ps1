<#
run_pg_tests.ps1 — run the ArchonHub DB test suite against a throwaway Postgres,
locally, the same way the postgres leg of .github/workflows/archonhub-db-ci.yml
does. Mirrors T5 (docs/AGENT_WORKPLAN.md).

What it does:
  1. starts a throwaway `postgres:16` container (docker) on port 5433,
  2. installs the Postgres driver into the current Python,
  3. initializes the schema via the app's own _init_schema() (no DDL re-declared),
  4. runs the four DB-relevant test files against it,
  5. tears the container down.

Usage (from app/v3):
    ./scripts/run_pg_tests.ps1
    ./scripts/run_pg_tests.ps1 -Python "C:/path/to/python.exe"

NO DOCKER? If `docker` is unavailable you can point at any Postgres 16 by setting
$env:DATABASE_URL yourself and skipping the container (see the "native postgres"
note at the bottom). A fresh/empty database is REQUIRED each run — several tests
create rows with default unique keys that collide on a reused DB.
#>
param(
    [string]$Python = "python",
    [int]$Port = 5433,
    [string]$Container = "archonhub-pg-test"
)

$ErrorActionPreference = "Stop"
$AppDir = Split-Path -Parent $PSScriptRoot   # app/v3
Push-Location $AppDir
try {
    Write-Host "==> Starting throwaway postgres:16 on port $Port"
    docker rm -f $Container 2>$null | Out-Null
    docker run -d --name $Container `
        -e POSTGRES_USER=archonhub `
        -e POSTGRES_PASSWORD=archonhub `
        -e POSTGRES_DB=archonhub `
        -p "${Port}:5432" postgres:16 | Out-Null

    Write-Host "==> Waiting for postgres to accept connections"
    for ($i = 0; $i -lt 30; $i++) {
        docker exec $Container pg_isready -U archonhub 2>$null | Out-Null
        if ($LASTEXITCODE -eq 0) { break }
        Start-Sleep -Seconds 1
    }

    $env:DB_BACKEND   = "postgres"
    $env:DATABASE_URL = "postgresql://archonhub:archonhub@localhost:$Port/archonhub"
    $env:PYTHONPATH   = $AppDir

    Write-Host "==> Installing Postgres driver"
    & $Python -m pip install "psycopg[binary]>=3.1" "psycopg_pool>=3.1" | Out-Null

    Write-Host "==> Initializing schema via app _init_schema()"
    & $Python -c "import core.database as d; d._init_schema(); print('PG schema initialized')"

    Write-Host "==> Running DB test suite against Postgres"
    & $Python -m pytest -q -p no:cacheprovider `
        tests/test_hub_db.py `
        tests/test_pg_migration.py `
        tests/test_job_claim_concurrency.py `
        tests/test_migrate_ordering.py
    $rc = $LASTEXITCODE
}
finally {
    Write-Host "==> Tearing down container"
    docker rm -f $Container 2>$null | Out-Null
    Pop-Location
}
exit $rc

# ── native postgres (no docker) ──────────────────────────────────────────────
# initdb -D pgdata -U postgres -A trust
# postgres -D pgdata -p 5433            # in a separate terminal
# createdb -U postgres -h 127.0.0.1 -p 5433 archonhub
# $env:DB_BACKEND="postgres"
# $env:DATABASE_URL="postgresql://postgres:postgres@127.0.0.1:5433/archonhub"
# $env:PYTHONPATH=(Resolve-Path .).Path
# python -c "import core.database as d; d._init_schema()"
# python -m pytest -q tests/test_hub_db.py tests/test_pg_migration.py `
#     tests/test_job_claim_concurrency.py tests/test_migrate_ordering.py
