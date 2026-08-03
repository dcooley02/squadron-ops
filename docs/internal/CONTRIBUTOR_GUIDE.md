# Contributor Guide

Development conventions and domain reference for Squadron Ops contributors.

See [README.md](../../README.md), [ROADMAP.md](../../ROADMAP.md), [docs/PROJECT_OVERVIEW.md](../PROJECT_OVERVIEW.md), and [docs/LIMITATIONS.md](../LIMITATIONS.md) for project scope and current status.

**Near-term priorities:** stakeholder-driven (CM, multi-squadron, password productization). Phases A–F done for demo scope (incl. responsive shell). Full list: [ROADMAP.md](../../ROADMAP.md).

## Stack

- Backend: FastAPI + SQLAlchemy 2.0 + PostgreSQL 16 + Alembic, Python 3.12
- Frontend: React 19 + TypeScript (strict) + Vite + Tailwind CSS + TanStack Query
- Auth: JWT + `require_roles` (ADMIN always allowed). Open ACL: `DEMO_OPEN_RBAC=true` / `VITE_DEMO_OPEN_RBAC=true`
- Database runs in Docker (see `docker-compose.yml`); app runs on the host
- Services **flush** only; route handlers **commit** (see flight completion, QA release, schedule publish)

## Project structure

See [docs/MODULE_MAP.md](../MODULE_MAP.md) for the domain index and extension recipes.

- `backend/app/models/` — ORM package by domain (`enums`, `person`, `sortie`, `maintenance`, …); `models.py` re-exports
- `backend/app/schemas/` — Pydantic request/response schemas
- `backend/app/api/` — FastAPI route handlers, organized by feature
- `backend/app/core/` — auth, config, shared utilities (`time.utc_now`)
- `backend/app/services/` — business logic (cascade, currency, scheduling, logbook, qa_release)
- `backend/alembic/` — database migrations
- `backend/seed/` — demo dataset package; `backend/seed.py` is a thin shim (`python seed.py`)
- `frontend/src/pages/` — top-level page shells; Complete Sortie / Aircraft Maintenance panels under `completeSortie/` and `aircraftMaintenance/`
- `frontend/src/components/` — reusable components
- `frontend/src/lib/api/` — domain API client + types (import as `../lib/api`)
- `frontend/src/lib/` — permissions, pdf, dates

## Conventions

- Use type hints everywhere in Python; Pydantic for all API I/O
- Use TypeScript strict mode; no `any` unless justified in a comment
- API routes follow REST: `/api/{resource}` for list, `/api/{resource}/{id}` for detail
- All timestamps in UTC, displayed in local time on the frontend
- Database operations go through SQLAlchemy sessions via `get_db` dependency
- Use TanStack Query for all frontend data fetching
- Tailwind for styling; shadcn/ui for components; lucide-react for icons
- Business logic belongs in `app/services/`, not route handlers

## Domain knowledge

### Roles
PILOT, AIRCREW, SDO, TRAINING_OFFICER, MAINT_CONTROL, CO_XO, ADMIN

### Crew positions (MH-60S)
HAC (Helicopter Aircraft Commander), H2P (2nd Pilot qualified),
H2P_U (Unqualified 2P/under instruction), CREW_CHIEF, AIRCREW, AWS

### Aircraft status codes
FMC (Fully Mission Capable), PMC (Partially Mission Capable),
NMC (Non-Mission Capable), NMCM (NMC for Maintenance), NMCS (NMC for Supply)

**Stamped vs. computed:** `Aircraft.status` is the line-maintainer stamped value;
`computed_status` is derived from open discrepancies and overdue inspections.
After QA signoff, maintainers **release** the aircraft **safe for flight** via
`POST /api/maintenance/aircraft/{id}/qa-release` — do not use "RTS" (conflicts with
Ready to Strike). UI copy: QA release, release for flight, safe for flight.

### Qualifications
H2P, HAC, NVG, FCP (Functional Check Pilot), NSI (NATOPS Standardization Instructor),
INSTR (Instrument)

### Currencies
Wing Table B-2 catalog is table-driven (`CurrencyType` model). Legacy codes like
`NVG` and `NIGHT_DL` appear in some scheduling checks but seeded types use codes
such as `NIGHT_NVD` — align with the catalog when touching currency logic.

### Syllabus stages
FAM (Familiarization), TAC-D (Tactical Day/Night), SAR (Search and Rescue),
OL (Overland), FCF (Functional Check Flight)

## Architecture invariants

- Three-layer backend: SQLAlchemy models → Pydantic schemas → FastAPI routes
- Business logic in `app/services/`, not route handlers
- Status colors: green good / yellow warning / red action needed
- Per-crewmember flight hours live on `FlightLog`, not sortie-level fields
- Prefer `joinedload` / `selectinload` for relationship-heavy reads
- Prefer timezone-aware UTC (`datetime.now(timezone.utc)`) over `datetime.utcnow()`

## Testing

- Prefer `./scripts/verify.sh` before opening a PR (starts Postgres if needed)
- Pytest integration tests require Postgres on port **5433**
- Without Docker, most tests error on connection refused
- Frontend: `npm run test` + `npm run build` + `npm run lint` (all gated in CI)
- Prefer `from app.models import X` (or existing `from app.models.models import X`)
- CBR / WTM catalog: `app/catalogs/cbr_enclosure2.py` (seed + integrity tests); do not hardcode task lists in services
- API base URL: `VITE_API_BASE_URL` (default `http://localhost:8001`)
- Clock helpers: `from app.core.time import utc_now` (not `datetime.utcnow`)
- RBAC tests must clear settings cache: `get_settings.cache_clear()` after toggling `DEMO_OPEN_RBAC`
- When changing cascade, readiness, QA release, or auth: add or extend tests in `backend/tests/`
- RBAC: always include **denial** cases (wrong role → 403)

## Quickstart

```bash
docker compose up -d
cd backend && source .venv/bin/activate && uvicorn app.main:app --reload --port 8001
# in another terminal
cd frontend && npm run dev
```

Visit http://localhost:5174