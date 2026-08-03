# Squadron Ops — Module Map

Canonical **structure map** for reviewers and contributors: domains, layer cake, cascade entry points, extension recipes, and demo/verify path.

This map reflects the **post Phase E/F** tree: seed package + shim, Complete Sortie / Aircraft Maintenance panels, and responsive shell (drawer nav &lt; `md`). Paths match the current repository.

Related: [PROJECT_OVERVIEW.md](PROJECT_OVERVIEW.md) (cascade detail), [LIMITATIONS.md](LIMITATIONS.md), [ROADMAP.md](../ROADMAP.md), [README.md](../README.md).

---

## 1. Product posture

| Constraint | Value |
|------------|--------|
| Purpose | Portfolio demonstration of integrated naval aviation ops |
| Community | HSC / MH-60S (designed to extend to other Navy aviation communities) |
| Tenancy | **Single squadron**; multi-squadron deferred |
| Data | Unclassified **synthetic** only |
| UI | **Desktop-primary** (≥ `md` permanent sidebar); dense boards/forms |
| Mobile | **Phase F done** — hamburger + overlay drawer &lt; `md`; demo paths at ~390px (Login, Dashboard, Complete Sortie, Aircraft Maintenance + Maintenance/Sorties/Crew/Readiness). Not full phone-first parity. Spec: [phase-f design](superpowers/specs/2026-08-03-phase-f-responsive-mobile-design.md) |
| Risk bar | Phase E was behavior-freeze modularity; Phase F is intentional UI chrome/reflow only |

Phases A–F are done for demo scope (quality bar, RBAC, cascade integrity, module splits, Enclosure 2-shaped CBR catalog, Appendix D fixtures, per-crew landings, reviewer modularity, responsive shell).

---

## 2. Layer cake

Request path top to bottom:

```
UI pages / boards / components
    → frontend/src/lib/api/*   (typed client + hand-maintained types.ts)
    → FastAPI routes           backend/app/api/*
    → services                 backend/app/services/*
    → SQLAlchemy models        backend/app/models/*
    → PostgreSQL 16            (Docker Compose, host port 5433)
```

Supporting layers:

| Layer | Location | Role |
|-------|----------|------|
| Schemas | `backend/app/schemas/` | Pydantic request/response I/O |
| Catalogs | `backend/app/catalogs/` | Static domain catalogs (e.g. CBR Enclosure 2-shaped) |
| Middleware | `backend/app/middleware/` | JWT gate, HTTP audit |
| Core | `backend/app/core/` | Config, security, `require_roles`, `utc_now` |
| Auth UI | `frontend/src/context/`, `lib/permissions.ts` | Session + nav RBAC |
| Seed | `backend/seed/` (+ `backend/seed.py` shim) | Demo dataset wipe + repopulate |

**Invariant:** services **flush**; route handlers **commit**. Business logic stays in services, not routes.

---

## 3. Domain index

Logical domains over existing folders (not a domain monorepo). Paths are relative to `backend/app/` or `frontend/src/` unless noted; tests under `backend/tests/`.

| Domain | Backend | Frontend | Tests |
|--------|---------|----------|-------|
| Logging / cascade | `api/logging.py`, `services/flight_completion.py` | `pages/CompleteSortie.tsx` + `pages/completeSortie/*`, Logbook | `tests/test_flight_completion.py` |
| Readiness / WTM | `services/readiness.py`, `catalogs/cbr_enclosure2.py` | `pages/Readiness.tsx`, boards | `tests/test_readiness.py`, `test_appendix_d_fixtures.py` |
| Maintenance | `api/maintenance.py`, `services/maintenance_chain.py`, `qa_release.py` | `pages/AircraftMaintenance.tsx` + `pages/aircraftMaintenance/*`, Maintenance | `tests/test_maintenance_chain.py`, `test_qa_release.py` |
| Training | `api/syllabus.py`, gradecard services | `pages/Training.tsx`, gradecards | related board/ops tests as applicable |
| Ops / SDO | `api/ops.py`, `ops_day.py`, `scheduling.py` | Ops, Schedule, boards | `tests/test_ops_and_boards.py`, `test_scheduling_assist.py` |
| Auth | `api/auth.py`, middleware, `require_roles` | Login, Admin, `permissions.ts` | `tests/test_auth.py` |

### Quick “where is X?”

| Concern | Start here |
|---------|------------|
| Complete-sortie cascade | `services/flight_completion.py` (spine — do not split for line count) |
| Currency renewal rules | `services/currency_renewal_rules.py`, `currency_applicability.py` |
| WTM / CBR ratings | `services/readiness.py`, `catalogs/cbr_enclosure2.py` |
| MAF / WO / QA release | `services/maintenance_chain.py`, `qa_release.py`, `api/maintenance.py` |
| Scheduling assist | `services/scheduling.py` (service-sized; map only) |
| Demo world | `backend/seed/` package; entry via `backend/seed.py` shim or `python -m seed` |
| Complete Sortie UI | `pages/CompleteSortie.tsx` shell + `pages/completeSortie/*` panels |
| Aircraft Maintenance UI | `pages/AircraftMaintenance.tsx` shell + `pages/aircraftMaintenance/*` sections/modals |
| API types (FE) | `frontend/src/lib/api/types.ts` (hand-maintained) |

---

## 4. Cascade spine

The application spine is **sortie completion**.

- **HTTP:** `POST /api/logging/sorties/{id}/complete` (`api/logging.py`)
- **Service:** `services/flight_completion.py` (row lock, validation, multi-domain writes)
- **Full step list:** [PROJECT_OVERVIEW.md — Sortie Completion Cascade](PROJECT_OVERVIEW.md#sortie-completion-cascade)

Summary of effects (LIVE path unless noted):

1. Sortie times, completion flag, flight mode  
2. Per-crewmember `FlightLog` (hours, landings, approaches)  
3. Currency renewal (only if event date ≥ last event date)  
4. Aircraft total airframe hours (LIVE only)  
5. CBR task credit grades (sim skips non-sim-eligible tasks)  
6. Optional discrepancy + safety report filing  
7. TMR code hour attachment  

**Demo proof path:** Complete an **NVG-related** sortie → `NIGHT_NVD` (or related) currency extends → aircraft hours increment → training jacket / logbook updates → maintenance reflects any filed discrepancy.

Integrity (Phase B): unknown TMR/task codes and off-crew person IDs rejected; services flush, routes commit. Pinned by `tests/test_flight_completion.py`.

---

## 5. Repository layout (current)

Post Phase E extraction layout. Large service/catalog modules remain intentional (not split for line count).

```
backend/
  app/
    api/              REST handlers (auth, logging, maintenance, ops, …)
    catalogs/         cbr_enclosure2.py (data catalog; large size expected)
    core/             config, security, deps, time
    middleware/       JWT + audit
    models/           ORM package by domain (+ models.py re-export)
    schemas/          Pydantic I/O
    services/         Business logic (flight_completion, readiness, …)
    templates/        WeasyPrint HTML
  alembic/            Migrations
  tests/              Pytest suite (54)
  seed.py             Shim → seed.run.main()  (demo-prep: python seed.py)
  seed/               Package
    run.py            Orchestration (wipe + main)
    constants.py      Shared seed constants
    people.py         Persons, quals, currencies, applicability
    aircraft.py       Aircraft fleet + inspection types/inspections
    cbr.py            CBR task options + capability area configs
    swtp_catalog.py   SWTP syllabus catalog
    training.py       Syllabus events / training seed
    sorties.py        Historical + scheduled sorties
    maintenance.py    Discrepancies
    ops.py            Ops day / SDO seed

frontend/
  src/
    pages/            Routed views
      CompleteSortie.tsx              Thin route shell (~488 lines)
      completeSortie/                 Panels + helpers
        helpers.ts, helpers.test.ts
        Section.tsx
        TimesHoursPanel.tsx
        CrewActualsPanel.tsx
        TaskCreditsPanel.tsx
        DiscrepanciesPanel.tsx
        SafetyPanel.tsx
      AircraftMaintenance.tsx         Thin route shell (~211 lines)
      aircraftMaintenance/            Sections + modals + helpers
        statusHelpers.ts
        Overlay.tsx
        DiscrepancySection.tsx, WorkOrderSection.tsx
        InspectionSection.tsx, LogbookSection.tsx, ReleaseSection.tsx
        CreateDiscrepancyModal.tsx, UpdateDiscrepancyModal.tsx
        RecordInspectionModal.tsx, QaReleaseModal.tsx
      Training.tsx, Logbook.tsx, Ops.tsx, Schedule.tsx, Readiness.tsx, …
    components/       Shared UI, modals, badges
    board/            TV boards (Ops, Maintenance, Readiness)
    lib/api/          Domain client modules + types.ts
    lib/              permissions, pdf, dates, …
    context/          AuthContext

docs/                 Overview, MODULE_MAP, limitations, demo scripts
scripts/              demo-prep.sh, verify.sh
ROADMAP.md
docker-compose.yml    Postgres only (host :5433)
```

**Not extracted in Phase E (document only):** `catalogs/cbr_enclosure2.py`, `services/scheduling.py`, `services/flight_completion.py`, `lib/api/types.ts`.

---

## 6. Extension recipes

File checklists for growth **without** multi-squadron tenancy. Paths match the **post-extraction** tree.

### Recipe 1 — Add a currency type

| Step | Where |
|------|-------|
| Table-driven types | `models/` — `CurrencyType` / applicability |
| Seed type + applicability | `backend/seed/people.py` (currency / people section) |
| Renewal rules | `services/currency_renewal_rules.py`, `currency_applicability.py` |
| Cascade if complete renews it | `services/flight_completion.py` only when needed |
| FE | Prefer API-driven surfaces (`lib/api/currency.ts`); avoid hardcoding new codes only in UI |
| Tests | Extend complete / currency-related tests if renewal is claimed |

**Invariant:** catalog/DB-driven currencies; do not add codes only in scheduling heuristics without seed + types. Seeded Wing Table B-2 codes (e.g. `NIGHT_NVD`) are authoritative over legacy naming in ad-hoc checks.

### Recipe 2 — MAF / discrepancy chain field or step

| Step | Where |
|------|-------|
| Model + Alembic | `models/maintenance.py`, `alembic/versions/` |
| API + schemas | `api/maintenance.py`, `schemas/maintenance.py` |
| Chain / QA | `services/maintenance_chain.py`, `qa_release.py` as needed |
| Seed sample | `backend/seed/maintenance.py` |
| FE | `pages/AircraftMaintenance.tsx` + `pages/aircraftMaintenance/*` sections/modals, `lib/api/maintenance.ts`, `types.ts` if exposed |
| Tests | `tests/test_maintenance_chain.py`, `test_qa_release.py` |

**Invariant:** stamped vs computed status and QA release semantics (safe for flight — not “RTS”); services flush, routes commit.

### Recipe 3 — Add a syllabus event (SWTP-shaped)

| Step | Where |
|------|-------|
| Catalog row | `backend/seed/swtp_catalog.py` — paraphrased descriptions only |
| Seed | `backend/seed/training.py` → `SyllabusEvent` |
| Progress / boards | `services/syllabus_progress.py`, `api/syllabus.py`, boards APIs if scheduled |
| FE | Training / gradecard pages consume API; avoid hardcoded event lists in UI |
| Tests | Training / board tests if behavior is asserted |

**Invariant:** unclassified paraphrase only; preserve AMCM code-collision convention documented in the seed package.

---

## 7. Demo / verify

### Clone-to-demo

1. **Prerequisites:** Docker, Python 3.12, Node.js 20+  
2. **Prepare:** `./scripts/demo-prep.sh` — Postgres on `127.0.0.1:5433`, migrations, `python seed.py`  
3. **API:** `cd backend && source .venv/bin/activate && uvicorn app.main:app --reload --port 8001`  
4. **UI:** `cd frontend && npm run dev` → **http://localhost:5174/login**  
5. **Accounts** (password `demo1234` for all — local demo only):

| Account | Role | Use case |
|---------|------|----------|
| `anderson.robert` | SDO | Schedule publish, ops console |
| `mitchell.james` | Line pilot | Crew jacket, logbook |
| `morgan.david` | Maint control | Maintenance workflows |
| `admin` | Admin | Audit log |

6. **Prove spine:** complete NVG-related sortie → currency / hours / jacket (see §4). Guided script: [DEMO_WALKTHROUGH.md](DEMO_WALKTHROUGH.md).  
7. **Caveats:** [LIMITATIONS.md](LIMITATIONS.md) (demo secrets, `DEMO_OPEN_RBAC`, portfolio posture).

### Ports

| Service | Port |
|---------|------|
| API (uvicorn) | **8001** |
| UI (Vite) | **5174** |
| PostgreSQL (Compose host map) | **5433** |

### Release gate

```bash
./scripts/verify.sh
# compose up → pytest → frontend test → build → lint
# SKIP_COMPOSE=1 / SKIP_LINT=1 available when needed
```

API interactive docs: `http://localhost:8001/docs`.

---

*Phase E complete (August 2026). Tree and recipes match seed package + page panel extractions.*
