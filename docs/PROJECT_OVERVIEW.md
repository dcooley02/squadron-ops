# Squadron Ops — Technical Overview

Integrated naval aviation operations platform for HSC/MH-60S squadrons. This document describes architecture, capabilities, and data design for technical reviewers.

---

## Purpose

Squadron Ops addresses fragmentation in squadron operations: flight logging, readiness reporting, maintenance tracking, and training management are typically spread across disconnected systems. This application models those domains in one cohesive platform with realistic synthetic data and observable cross-domain cascades.

**Community focus:** Helicopter Sea Combat (HSC), MH-60S  
**Scope:** Single-squadron demonstration; multi-squadron architecture deferred  
**Classification:** Unclassified synthetic data only

---

## Technology Stack

**Backend:** Python 3.12 · FastAPI · SQLAlchemy 2.0 · Pydantic · Alembic · PostgreSQL 16  
**Frontend:** React 18 · TypeScript (strict) · Vite · Tailwind CSS · TanStack Query  
**Infrastructure:** Docker Compose (database); application runs locally  
**Authentication:** JWT bearer tokens  
**PDF generation:** WeasyPrint (optional local dependency)

---

## Architecture

### Backend (three-layer pattern)

1. **SQLAlchemy models** — `backend/app/models/`
2. **Pydantic schemas** — request/response validation
3. **FastAPI routes** — `backend/app/api/` organized by feature

Business logic resides in `backend/app/services/` (cascade, scheduling, readiness, maintenance, logbook, QA release). An HTTP audit middleware records consequential API actions.

### Frontend

- **Pages** — `frontend/src/pages/` (routed views)
- **Components** — shared UI, modals, badges
- **Board views** — fullscreen TV displays (`frontend/src/board/`)
- **API client** — typed client in `frontend/src/lib/api.ts`

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
4. Aircraft total airframe hours increment
5. CBR task credit grades (sim sorties skip non-sim-eligible tasks)
6. Optional discrepancy and safety report filing
7. TMR code hour attachment

**Demonstration path:** Complete an NVG sortie → `NIGHT_NVD` currency extends → aircraft hours increment → training jacket updates → maintenance reflects any filed discrepancy.

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
| **Governance** | JWT auth, audit log, admin viewer |
| **Display** | Fullscreen TV boards (ops, maintenance, readiness snapshot) |

### Planned (see [ROADMAP.md](../ROADMAP.md))

- Full Appendix D Enclosure 2 task parity and hand-verified WTM math
- Production role-based access control and password reset
- Full 4790 configuration management
- Multi-squadron tenancy (pending stakeholder requirements)

---

## API Surface (summary)

Prefix: `/api` unless noted.

| Area | Key endpoints |
|------|---------------|
| Health | `GET /health` |
| Persons | `GET /persons`, `GET /persons/{id}` |
| Aircraft | `GET /aircraft`, `GET /aircraft/{id}` |
| Sorties | `GET /sorties`, `GET /sorties/{id}` |
| Dashboard | `GET /dashboard/summary` |
| Scheduling | upcoming sorties, eligible crew, fitness, CRUD |
| Logging | `POST /logging/sorties/{id}/complete`, logbook, PDF |
| Maintenance | discrepancies, inspections, `POST .../qa-release` |
| Readiness | `GET /readiness/squadron`, `GET /readiness/persons/{id}`, brief PDF |
| Syllabus | events, gradecards, progress, boards |
| Audit | `GET /audit` |

Full interactive documentation: `http://localhost:8001/docs`

---

## Seed Data

`backend/seed.py` wipes and repopulates a realistic squadron:

- 8 MH-60S aircraft (side numbers 610–617)
- ~12 pilots, 8 aircrew, staff roles
- 90+ historical sorties; scheduled flights including today
- Three intentional **stamped vs. computed drift** scenarios (614, 615, 617)
- 61 CBR task options; Wing Table B-2 currency distribution (~88% current)
- Gradecards, inspections, qualifications, safety reports

Run: `./scripts/demo-prep.sh` or `cd backend && python seed.py`

---

## Testing & CI

- **37 pytest tests** — integration tests against PostgreSQL
- **GitHub Actions** — postgres service → pytest → `npm run build`
- **Local verify:** `cd backend && pytest -q` · `cd frontend && npm run build`

---

## Repository Layout

```
backend/
  app/api/          REST handlers
  app/models/       SQLAlchemy ORM
  app/schemas/      Pydantic I/O
  app/services/     Business logic
  alembic/          Migrations
  seed.py           Demo dataset

frontend/
  src/pages/        Routed views
  src/components/   Shared UI
  src/board/        TV board layouts
  src/lib/          API client, utilities

docs/               Documentation
scripts/            demo-prep.sh
```

---

*Last updated: June 2026*