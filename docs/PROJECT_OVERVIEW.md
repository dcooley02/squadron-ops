# Squadron Ops — Technical Overview

Integrated naval aviation operations platform for HSC/MH-60S squadrons. This document describes architecture, capabilities, data design, and current maturity for technical reviewers.

---

## Purpose

Squadron Ops addresses fragmentation in squadron operations: flight logging, readiness reporting, maintenance tracking, and training management are typically spread across disconnected systems. This application models those domains in one cohesive platform with realistic synthetic data and observable cross-domain cascades.

**Community focus:** Helicopter Sea Combat (HSC), MH-60S  
**Scope:** Single-squadron demonstration; multi-squadron architecture deferred  
**Classification:** Unclassified synthetic data only  
**Maturity:** Portfolio demonstration with deep domain modeling. Phases A–D cover quality bar, RBAC, complete integrity, maintainability, Enclosure 2-shaped CBR catalog, Appendix D fixtures, and per-crew landings. See [LIMITATIONS.md](LIMITATIONS.md) and [ROADMAP.md](../ROADMAP.md).

---

## Technology Stack

**Backend:** Python 3.12 · FastAPI · SQLAlchemy 2.0 · Pydantic · Alembic · PostgreSQL 16  
**Frontend:** React 19 · TypeScript (strict) · Vite · Tailwind CSS · TanStack Query  
**Infrastructure:** Docker Compose (database only); application runs on the host  
**Authentication:** JWT bearer tokens + `require_roles` (ADMIN always allowed; `DEMO_OPEN_RBAC` for open demos)  
**PDF generation:** WeasyPrint (optional local dependency)

---

## Architecture

### Backend (three-layer pattern)

1. **SQLAlchemy models** — `backend/app/models/` domain package (`enums`, `person`, `sortie`, `maintenance`, …; `models.py` re-exports for compatibility)
2. **Pydantic schemas** — request/response validation
3. **FastAPI routes** — `backend/app/api/` organized by feature (~76 route handlers)

Business logic resides in `backend/app/services/` (cascade, scheduling, readiness, maintenance, logbook, QA release). HTTP audit middleware records state-changing API actions. JWT middleware gates `/api/*` except login and docs.

### Frontend

- **Pages** — `frontend/src/pages/` (routed views; some large debrief/maintenance screens)
- **Components** — shared UI, modals, badges
- **Board views** — fullscreen TV displays (`frontend/src/board/`)
- **API client** — `frontend/src/lib/api/` (domain modules + hand-maintained `types.ts`; route-level `React.lazy` code-splitting)
- **Auth** — `AuthContext` + `ProtectedRoute` + `RoleRoute` / `canSeeNav` (role-gated unless `VITE_DEMO_OPEN_RBAC`)

### Status semantics

| Color | Meaning |
|-------|---------|
| Green | FMC, current currency, no action required |
| Yellow | PMC, expiring currency, stamped/computed drift |
| Red | NMC*, expired currency, DOWNING discrepancies |

**Stamped vs. computed:** `Aircraft.status` is the line-maintainer stamped value. `computed_status` derives from open discrepancies and overdue inspections. Maintainers perform **QA release** (safe for flight) after QA signoff — not "RTS" (Ready to Strike).

---

## Core Data Model

### Operations
- `Person`, `Aircraft`, `Sortie`, `FlightLog`, `SortieLeg`
- `SortieTaskCredit`, `SortieTmrCode`, `TmrCode`

### Readiness & training
- `Qualification`, `Currency`, `CurrencyType`, `CurrencyApplicability`
- `SyllabusEvent`, `Gradecard`, `GradecardLineItem`, `GradecardLineItemResult`
- `CbrTaskOption` — capability-based readiness task library

### Maintenance
- `Discrepancy`, `InspectionType`, `AircraftInspection`
- MAF/work order chain (4790-inspired)

### Governance
- `SafetyReport`, `InstrumentApproach`, `AuditLog`

---

## Sortie Completion Cascade

The spine of the application. `POST /api/logging/sorties/{id}/complete` triggers:

1. Sortie times, completion flag, flight mode
2. Per-crewmember `FlightLog` rows (hours, landings, approaches)
3. Currency renewal (only if event date ≥ last event date)
4. Aircraft total airframe hours increment (LIVE only)
5. CBR task credit grades (sim sorties skip non-sim-eligible tasks)
6. Optional discrepancy and safety report filing
7. TMR code hour attachment

**Demonstration path:** Complete an NVG sortie → `NIGHT_NVD` currency extends → aircraft hours increment → training jacket updates → maintenance reflects any filed discrepancy.

**Integrity (Phase B):** row lock on complete; unknown TMR/task codes and off-crew person IDs rejected; services flush, routes commit.

---

## Capability Inventory

### Shipped

| Domain | Capabilities |
|--------|-------------|
| **Operations** | Dashboard, sortie scheduling, crew assignment, fitness checks |
| **Logging** | Complete sortie UI, digital logbook, training jacket, PDF export |
| **Readiness** | WTM T-ratings, anchor tasks, area drill-down, aircrew rollup, brief PDF |
| **Maintenance** | Computed/stamped status, MAF/WO chain, inspections, QA release, forecasts |
| **Training** | Syllabus catalog, gradecards, boards, instructor pairing, progress tracking |
| **SDO** | Schedule publish, watchbill, ops status, ATO/brief PDFs |
| **Scheduling assist** | Ranked crew suggestions, week proposals, conflict detection |
| **Governance** | JWT auth, RBAC, audit log, admin viewer (`DEMO_OPEN_RBAC` opt-out) |
| **Display** | Fullscreen TV boards (ops, maintenance, readiness snapshot) |

### Planned (see [ROADMAP.md](../ROADMAP.md))

**Engineering (post Phase C)**
- Broader write-route role coverage
- Optional OpenAPI type regeneration as schemas churn (see `frontend/scripts/generate-api-types.md`)

**Domain (post Phase D)**
- Verbatim WTM Enclosure 2 for operational communities (catalog is demo-shaped)
- Productized password reset
- Full 4790 configuration management
- Multi-squadron tenancy (pending stakeholder requirements)

---

## API Surface (summary)

Prefix: `/api` unless noted. Approximately **76** route handlers across feature modules.

| Area | Key endpoints |
|------|---------------|
| Health | `GET /health` |
| Auth | `POST /auth/login`, `GET /auth/me` |
| Persons | `GET /persons`, `GET /persons/{id}` |
| Aircraft | `GET /aircraft`, `GET /aircraft/{id}` |
| Sorties | `GET /sorties`, `GET /sorties/{id}` |
| Dashboard | `GET /dashboard/summary` |
| Scheduling | upcoming sorties, eligible crew, fitness, CRUD, suggest/propose |
| Logging | `POST /logging/sorties/{id}/complete`, logbook, PDF |
| Maintenance | discrepancies, inspections, work orders, `POST .../qa-release` |
| Readiness | `GET /readiness/squadron`, `GET /readiness/persons/{id}`, brief PDF |
| Syllabus | events, gradecards, progress, boards |
| Ops | day ops, publish, watchbill, ATO/brief PDFs |
| Audit | `GET /audit` |

Full interactive documentation: `http://localhost:8001/docs`

---

## Seed Data

`backend/seed.py` wipes and repopulates a realistic squadron:

- 8 MH-60S aircraft (side numbers 610–617)
- ~12 pilots, 8 aircrew, staff roles
- 90+ historical sorties; scheduled flights including today
- Three intentional **stamped vs. computed drift** scenarios (614, 615, 617)
- 92 CBR task options (Enclosure 2-shaped); Wing Table B-2 currency distribution (~88% current)
- Gradecards, inspections, qualifications, safety reports

Run: `./scripts/demo-prep.sh` or `cd backend && python seed.py`

---

## Testing & CI

| Check | Command / notes |
|-------|-----------------|
| Full gate | `./scripts/verify.sh` — compose → pytest → FE test → build → lint |
| Backend tests | `cd backend && pytest -q` — **51** tests; requires Postgres (port **5433**) |
| Frontend tests | `cd frontend && npm run test` — Vitest unit smoke tests |
| Frontend build | `cd frontend && npm run build` (`tsc -b` + Vite, code-split chunks) |
| Frontend lint | `cd frontend && npm run lint` — gated in CI |
| CI | GitHub Actions: Postgres → pytest → lint → FE test → build |

Without Docker, most integration tests error on connection refused; pure unit tests (e.g. aircraft status helpers) still run.

Coverage includes cascade, readiness, QA release, scheduling assist, ops/boards, auth, RBAC denials, and complete-sortie validation. Gaps: many remaining write routes, frontend tests.

---

## Repository Layout

```
backend/
  app/api/          REST handlers
  app/models/       ORM package (enums, person, sortie, maintenance, …)
  app/schemas/      Pydantic I/O
  app/services/     Business logic
  alembic/          Migrations
  tests/            Pytest suite
  seed.py           Demo dataset

frontend/
  src/pages/        Routed views (+ page helper modules)
  src/components/   Shared UI
  src/board/        TV board layouts
  src/lib/api/      Domain API client + types
  src/lib/          permissions, pdf, dates, …
  src/context/      Auth provider

docs/               Overview, limitations, demo scripts
scripts/            demo-prep.sh
ROADMAP.md          Domain + engineering phases
```

---

## Related documents

| Document | Purpose |
|----------|---------|
| [LIMITATIONS.md](LIMITATIONS.md) | Known gaps and integrity risks |
| [../ROADMAP.md](../ROADMAP.md) | Domain build order + engineering phases A–D |
| [DEMO_WALKTHROUGH.md](DEMO_WALKTHROUGH.md) | 12-minute demo script |
| [DEMO_QUICK_REFERENCE.md](DEMO_QUICK_REFERENCE.md) | Accounts and troubleshooting |

---

*Last updated: July 2026*
