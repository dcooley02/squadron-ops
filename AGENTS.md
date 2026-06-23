# Squadron Ops — Agent Guide

Naval aviation operations platform (v2). Forked from hsc-squadron-ops v1.0-demo.
See README.md, ROADMAP.md, and KNOWN_ISSUES.md for scope and status.

## Stack
- Backend: FastAPI + SQLAlchemy 2.0 + PostgreSQL 16 + Alembic, Python 3.12
- Frontend: React 18 + TypeScript + Vite + Tailwind CSS + shadcn/ui
- Auth: JWT-based RBAC (planned — not yet implemented)
- Database runs in Docker (see docker-compose.yml)

## Project structure
- `backend/app/models/` — SQLAlchemy ORM models
- `backend/app/schemas/` — Pydantic request/response schemas
- `backend/app/api/` — FastAPI route handlers, organized by feature
- `backend/app/core/` — auth, config, shared utilities
- `backend/app/services/` — business logic (cascade, currency, scheduling, logbook)
- `backend/alembic/` — database migrations
- `frontend/src/pages/` — top-level page components
- `frontend/src/components/` — reusable components
- `frontend/src/lib/` — API client, hooks, utilities

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

### Qualifications (subset for demo)
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
- Status colors: green good / yellow warning / red action needed
- Per-crewmember flight hours live on `FlightLog`, not sortie-level fields

## Quickstart
```bash
docker compose up -d
cd backend && source .venv/bin/activate && uvicorn app.main:app --reload --port 8001
# in another terminal
cd frontend && npm run dev
```
Visit http://localhost:5174 (v2; v1 demo uses :5173/:8000)