# HSC Squadron Ops

A demo web application for tracking MH-60S helicopter squadron operations:
pilot/aircrew flight hours, qualifications, currencies, syllabus progression,
flight scheduling, and aircraft maintenance. Designed to eventually replace
NALCOMIS/OOMA and SHARP for an HSC squadron.

## Stack
- Backend: FastAPI + SQLAlchemy 2.0 + PostgreSQL 16 + Alembic
- Frontend: React 18 + TypeScript + Vite + Tailwind CSS + shadcn/ui
- Auth: JWT-based with role-based access control
- Database runs in Docker (see docker-compose.yml)

## Project structure
- `backend/app/models/` — SQLAlchemy ORM models
- `backend/app/schemas/` — Pydantic request/response schemas
- `backend/app/api/` — FastAPI route handlers, organized by feature
- `backend/app/core/` — auth, config, shared utilities
- `backend/app/services/` — business logic (currency calc, crew suggester)
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

### Currencies (with default windows)
NVG (60d), INSTR (60d), DAY_DL (30d), NIGHT_DL (60d), SAR_DAY (90d), SAR_NIGHT (90d)

### Syllabus stages
FAM (Familiarization), TAC-D (Tactical Day/Night), SAR (Search and Rescue),
OL (Overland), FCF (Functional Check Flight)

## What this app does
1. Tracks flight hours per aircrew by category (day/night/NVG/instrument)
2. Tracks qualifications and currencies with auto-expiration
3. Tracks syllabus progression with prerequisite checking
4. Tracks aircraft hours and maintenance status
5. Provides a flight schedule with crew validation and currency forecasting
6. Suggests optimal crew for events based on quals, currency, and syllabus needs
7. Provides TV-board fullscreen views for ready room and maintenance spaces
8. Generates readiness reports and rollups

## Current state (paused [07May2026])

Working:
- Backend: all 4 API resources (persons, aircraft, sorties, dashboard)
  with full schemas, routes, seeded data
- Frontend: Dashboard page (full), Crew list + detail pages (full),
  app shell with sidebar nav

In progress:
- Aircraft + Sorties pages — Claude Code prompt submitted, may need review

Not started:
- Schedule view (the centerpiece)
- Training, Maintenance pages
- TV Board mode
- Auth (still wide open, no login)
- Crew suggester / optimization logic

To resume:
1. cd ~/Documents/GitHub/hsc-squadron-ops
2. docker compose up -d
3. Backend terminal: cd backend && source .venv/bin/activate && uvicorn app.main:app --reload
4. Frontend terminal: cd frontend && npm run dev
5. Open http://localhost:5173