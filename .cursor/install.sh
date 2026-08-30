#!/usr/bin/env bash
# Idempotent install script for the Cloud Agent environment.
# Runs after the repository is checked out. Installs system services
# (PostgreSQL + Redis), Python dependencies (Poetry), provisions the database
# role/databases, and applies migrations. Safe to run repeatedly.
set -euo pipefail

# shellcheck source=common.sh
source "$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/common.sh"
cd "$REPO_DIR"

log install "Installing system packages (PostgreSQL 16, Redis)"
export DEBIAN_FRONTEND=noninteractive
sudo apt-get update -qq
sudo apt-get install -y -qq redis-server postgresql postgresql-contrib libpq-dev

log install "Installing Poetry (if missing)"
if [ ! -x "$HOME/.local/bin/poetry" ] && ! command -v poetry >/dev/null 2>&1; then
  pip install --user --quiet poetry
fi

log install "Installing Python dependencies"
poetry config virtualenvs.in-project true
poetry install --no-root

log install "Starting PostgreSQL for schema provisioning"
start_postgres

log install "Provisioning database role and databases (idempotent)"
ensure_databases ticketing ticketing_test

log install "Applying migrations"
apply_migrations

log install "Done."
