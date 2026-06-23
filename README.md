# squadron-ops

A modern naval aviation operations platform. Multi-squadron, multi-community,
designed to expand to all Navy aviation communities.

Forked from [hsc-squadron-ops](https://github.com/dcooley02/hsc-squadron-ops)
v1.0-demo (single-tenant HSC prototype). See `ROADMAP.md` for scope and
`PROJECT_SUMMARY.txt` for a full capability inventory.

## Status

**Demo baseline: `v2.0-demo-rc8`** — integrated ops, training, maintenance,
WTM readiness, JWT auth (open demo access), and assisted scheduling on realistic
HSC/MH-60S seed data.

## Stack

- Backend: FastAPI + SQLAlchemy 2.0 + PostgreSQL 16 + Alembic, Python 3.12
- Frontend: React 18 + TypeScript + Vite + Tailwind CSS + TanStack Query
- Database: PostgreSQL via Docker Compose (host port 5433)
- Auth: JWT login required; all authenticated users see full nav for demo (demo password `demo1234`)

## Quickstart

```bash
# One-command demo prep (docker + migrate + seed)
./scripts/demo-prep.sh

# Terminal 1 — API on :8001
cd backend && source .venv/bin/activate && uvicorn app.main:app --reload --port 8001

# Terminal 2 — UI on :5174
cd frontend && npm run dev
```

Visit http://localhost:5174/login — use `anderson.robert` / `demo1234` (SDO) or
see `DEMO_CHEATSHEET.txt` for other demo accounts.

**Demo walkthrough:** `DEMO_SCRIPT.txt` (12-minute scripted path)

**v1 predecessor** (separate repo): http://localhost:5173 on ports 5173/8000

## Verify

```bash
cd backend && pytest -q          # 37 tests (requires Postgres on :5433)
cd frontend && npm run build
```

## Key routes

| Path | Purpose |
|------|---------|
| `/` | Squadron dashboard |
| `/readiness` | WTM T-ratings by capability area |
| `/maintenance` | Computed vs stamped status, forecasts |
| `/schedule` | Flight schedule + assisted crew suggestions |
| `/ops` | SDO daily ops, ATO/brief PDFs |
| `/board/readiness` | Fullscreen TV snapshot |