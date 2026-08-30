#!/usr/bin/env bash
# Per-boot start script for the Cloud Agent environment.
# Brings up PostgreSQL + Redis, ensures the database exists, and applies any
# pending migrations. Idempotent and safe to run on every boot; it returns
# once services are ready (long-running processes live in `terminals`).
set -euo pipefail

# shellcheck source=common.sh
source "$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/common.sh"
cd "$REPO_DIR"

log start "Starting PostgreSQL"
start_postgres

log start "Starting Redis"
start_redis

log start "Ensuring role/databases exist (idempotent)"
ensure_databases ticketing

log start "Applying migrations"
apply_migrations

log start "Services ready (Postgres + Redis up, schema migrated)."
