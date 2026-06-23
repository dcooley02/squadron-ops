#!/usr/bin/env bash
# Prepare a fresh demo dataset: Postgres up, migrations applied, seed loaded.
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

echo "==> Starting Postgres (docker compose)..."
docker compose up -d

echo "==> Waiting for Postgres on :5433..."
for i in {1..30}; do
  if docker compose exec -T db pg_isready -U squadron_ops >/dev/null 2>&1; then
    break
  fi
  if [[ $i -eq 30 ]]; then
    echo "Postgres did not become ready in time." >&2
    exit 1
  fi
  sleep 1
done

echo "==> Applying migrations..."
cd backend
if [[ -f .venv/bin/activate ]]; then
  # shellcheck disable=SC1091
  source .venv/bin/activate
else
  echo "Warning: backend/.venv not found — using system Python" >&2
fi
alembic upgrade head

echo "==> Seeding demo data..."
python seed.py

echo ""
echo "Demo prep complete."
echo "  Start backend:  cd backend && source .venv/bin/activate && uvicorn app.main:app --reload --port 8001"
echo "  Start frontend: cd frontend && npm run dev"
echo "  Open app:       http://localhost:5174/login  (anderson.robert / demo1234)"
echo "  Walkthrough:    docs/DEMO_WALKTHROUGH.md"