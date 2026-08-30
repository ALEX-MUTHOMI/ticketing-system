#!/usr/bin/env bash
# Shared helpers for the Cloud Agent environment scripts.
# Meant to be *sourced* by install.sh and start.sh, not executed directly.

# Absolute path to the repository root (this file lives in <repo>/.cursor).
REPO_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

# Poetry installs to the user bin; make sure it is always resolvable.
export PATH="$HOME/.local/bin:$PATH"

# Postgres role/database names. Keep in sync with DATABASE_URL in .cursor/dev.env.
PG_ROLE="ticketing"
PG_PASSWORD="devpassword"

log() { echo "==> [$1] ${*:2}"; }

# Load the non-secret dev environment variables into the current shell.
load_env() {
  set -a
  # shellcheck disable=SC1091
  source "$REPO_DIR/.cursor/dev.env"
  set +a
}

# Start the PostgreSQL cluster (idempotent) and block until it accepts
# connections. Returns non-zero if it never becomes ready.
start_postgres() {
  sudo pg_ctlcluster 16 main start 2>/dev/null || true
  for _ in $(seq 1 30); do
    sudo -u postgres pg_isready -q && return 0
    sleep 1
  done
  return 1
}

# Start Redis as a daemon only if it is not already responding (idempotent).
start_redis() {
  redis-cli ping >/dev/null 2>&1 || sudo redis-server /etc/redis/redis.conf --daemonize yes
}

# Create the application role if it does not already exist (idempotent).
ensure_role() {
  sudo -u postgres psql -tc "SELECT 1 FROM pg_roles WHERE rolname='${PG_ROLE}'" | grep -q 1 \
    || sudo -u postgres psql -c "CREATE USER ${PG_ROLE} WITH PASSWORD '${PG_PASSWORD}' CREATEDB;"
}

# Create a single database owned by the app role if missing (idempotent).
ensure_database() {
  local db="$1"
  sudo -u postgres psql -tc "SELECT 1 FROM pg_database WHERE datname='${db}'" | grep -q 1 \
    || sudo -u postgres psql -c "CREATE DATABASE ${db} OWNER ${PG_ROLE};"
}

# Ensure the role plus every database passed as an argument exists.
ensure_databases() {
  ensure_role
  local db
  for db in "$@"; do
    ensure_database "$db"
  done
}

# Apply Django migrations using the dev environment settings.
apply_migrations() {
  load_env
  poetry run python manage.py migrate --noinput
}
