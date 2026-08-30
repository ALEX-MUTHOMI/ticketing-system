#!/usr/bin/env bash
# Per-boot start script for the Cloud Agent environment.
# Brings up PostgreSQL + Redis, ensures the database exists, and applies any
# pending migrations. Idempotent and safe to run on every boot; it returns
# once services are ready (long-running processes live in `terminals`).
set -euo pipefail

REPO_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$REPO_DIR"
export PATH="$HOME/.local/bin:$PATH"

echo "==> [start] Starting PostgreSQL"
sudo pg_ctlcluster 16 main start 2>/dev/null || true
for _ in $(seq 1 30); do
  sudo -u postgres pg_isready -q && break
  sleep 1
done

echo "==> [start] Starting Redis"
if ! redis-cli ping >/dev/null 2>&1; then
  sudo redis-server /etc/redis/redis.conf --daemonize yes
fi

echo "==> [start] Ensuring role/databases exist (idempotent)"
sudo -u postgres psql -tc "SELECT 1 FROM pg_roles WHERE rolname='ticketing'" | grep -q 1 \
  || sudo -u postgres psql -c "CREATE USER ticketing WITH PASSWORD 'devpassword' CREATEDB;"
sudo -u postgres psql -tc "SELECT 1 FROM pg_database WHERE datname='ticketing'" | grep -q 1 \
  || sudo -u postgres psql -c "CREATE DATABASE ticketing OWNER ticketing;"

echo "==> [start] Applying migrations"
set -a; source "$REPO_DIR/.cursor/dev.env"; set +a
poetry run python manage.py migrate --noinput

echo "==> [start] Services ready (Postgres + Redis up, schema migrated)."
