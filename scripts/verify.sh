#!/usr/bin/env bash
# Full local verification: Postgres up → pytest → frontend build → lint.
# Mirrors CI plus frontend lint (Phase A quality bar).
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

SKIP_COMPOSE="${SKIP_COMPOSE:-0}"
SKIP_LINT="${SKIP_LINT:-0}"

echo "==> Squadron Ops verify"
echo "    ROOT=$ROOT"

if [[ "$SKIP_COMPOSE" != "1" ]]; then
  if ! command -v docker >/dev/null 2>&1; then
    echo "Docker is required (or set SKIP_COMPOSE=1 if Postgres is already on :5433)." >&2
    exit 1
  fi
  if ! docker info >/dev/null 2>&1; then
    echo "Docker daemon is not running. Start Docker Desktop, then re-run." >&2
    exit 1
  fi

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
else
  echo "==> SKIP_COMPOSE=1 — assuming Postgres is already available"
fi

echo "==> Backend pytest..."
cd "$ROOT/backend"
if [[ -f .venv/bin/activate ]]; then
  # shellcheck disable=SC1091
  source .venv/bin/activate
else
  echo "Warning: backend/.venv not found — using system Python" >&2
fi
pytest -q

echo "==> Frontend install (if needed), test, build, lint..."
cd "$ROOT/frontend"
if [[ ! -d node_modules ]]; then
  npm ci
fi
npm run test
npm run build

if [[ "$SKIP_LINT" != "1" ]]; then
  npm run lint
else
  echo "==> SKIP_LINT=1 — skipping frontend lint"
fi

echo ""
echo "Verify complete: pytest + frontend test + build${SKIP_LINT:+ }${SKIP_LINT:+(lint skipped)}${SKIP_LINT:- + lint}."
