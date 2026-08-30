#!/usr/bin/env bash
# Idempotent install script for the Cloud Agent environment.
# Runs after the repository is checked out. Installs system services
# (PostgreSQL + Redis), Python dependencies (Poetry), provisions the database
# role/databases, and applies migrations. Safe to run repeatedly.
set -euo pipefail

REPO_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$REPO_DIR"

echo "==> [install] Installing system packages (PostgreSQL 16, Redis)"
export DEBIAN_FRONTEND=noninteractive
sudo apt-get update -qq
sudo apt-get install -y -qq redis-server postgresql postgresql-contrib libpq-dev

echo "==> [install] Installing Poetry (if missing)"
if [ ! -x "$HOME/.local/bin/poetry" ] && ! command -v poetry >/dev/null 2>&1; then
  pip install --user --quiet poetry
fi
export PATH="$HOME/.local/bin:$PATH"

echo "==> [install] Installing Python dependencies"
poetry config virtualenvs.in-project true
poetry install --no-root

echo "==> [install] Starting PostgreSQL for schema provisioning"
sudo pg_ctlcluster 16 main start 2>/dev/null || true
for _ in $(seq 1 30); do
  sudo -u postgres pg_isready -q && break
  sleep 1
done

echo "==> [install] Provisioning database role and databases (idempotent)"
sudo -u postgres psql -tc "SELECT 1 FROM pg_roles WHERE rolname='ticketing'" | grep -q 1 \
  || sudo -u postgres psql -c "CREATE USER ticketing WITH PASSWORD 'devpassword' CREATEDB;"
sudo -u postgres psql -tc "SELECT 1 FROM pg_database WHERE datname='ticketing'" | grep -q 1 \
  || sudo -u postgres psql -c "CREATE DATABASE ticketing OWNER ticketing;"
sudo -u postgres psql -tc "SELECT 1 FROM pg_database WHERE datname='ticketing_test'" | grep -q 1 \
  || sudo -u postgres psql -c "CREATE DATABASE ticketing_test OWNER ticketing;"

echo "==> [install] Applying migrations"
set -a; source "$REPO_DIR/.cursor/dev.env"; set +a
poetry run python manage.py migrate --noinput

echo "==> [install] Done."
