# Squadron Ops — Modularity / Growth Architecture Pass

**Date:** 2026-08-02  
**Status:** Design approved (brainstorm); awaiting implementation plan  
**Repo:** `dcooley02/squadron-ops`  
**Approach:** Docs-first, extract-in-place (Approach 1)

## Problem

Original build momentum left a credible product with living docs (Phases A–D done for demo scope), but reviewer navigation still hits large blobs (`seed.py` ~1.9k, `CompleteSortie.tsx` ~990, `AircraftMaintenance.tsx` ~1.1k) and structure is described in several places without one scannable module map. Growth should feel modular without multi-squadron tenancy or a domain monorepo rewrite.

## Goals

1. **10-minute mental model** — One canonical doc: domains, cascade spine, “where is X?”, layer cake.
2. **Clone-to-demo confidence** — Documented path: compose → seed → API/UI → verify → accounts → limitations link.
3. **Growth without multi-squadron** — Three short extension recipes with concrete file checklists.
4. **Honest structure** — Targeted extractions so the map points at real modules. Behavior unchanged.

## Non-goals

- Multi-squadron / tenancy
- New domain features or cascade rule changes
- Domain monorepo (`app/domains/...`)
- OpenAPI typegen as source of truth (hand-maintained `types.ts` stays; optional path remains documented)
- Password productization, configuration-management depth, browser e2e suite
- Visual redesign or API contract changes
- Refactoring `flight_completion.py` / `scheduling.py` / `cbr_enclosure2.py` for line-count alone

## Product constraints (locked)

| Constraint | Value |
|------------|--------|
| Posture | Portfolio demonstration, unclassified synthetic data |
| Tenancy | Single squadron; multi-squadron deferred |
| Cascade | Preserve domain cascade (sortie complete → currency, hours, CBR, maint path) |
| Risk bar | Strict behavior freeze |
| Verification | `./scripts/verify.sh` is the release gate for this pass |

## Success criteria

| # | Criterion |
|---|-----------|
| 1 | `docs/MODULE_MAP.md` exists and is the reviewer entry for structure |
| 2 | README, CONTRIBUTOR_GUIDE, and PROJECT_OVERVIEW link to MODULE_MAP (no contradictory trees) |
| 3 | Seed is a package plus shim; `python seed.py` / `./scripts/demo-prep.sh` still work |
| 4 | `CompleteSortie.tsx` and `AircraftMaintenance.tsx` are thin route shells; sections live under helper packages |
| 5 | Three extension recipes are present and file-accurate post-extraction |
| 6 | Demo path documented end-to-end (ports, accounts, spine proof, verify) |
| 7 | `./scripts/verify.sh` passes; no intentional product/cascade change |
| 8 | ROADMAP notes Phase E (reviewer modularity / growth map) status |

**Explicit non-success:** “every large file under N lines,” domain monorepo, or new features.

---

## Architecture decision

### Approach: docs-first, extract-in-place

Keep existing layering:

- Backend: models → schemas → API routes → services (business logic) → DB  
- Frontend: pages → components / page helpers → `lib/api` → FastAPI  

Do **not** introduce domain monorepo packages. Change shape only for:

1. `backend/seed/` package (+ shim `backend/seed.py`)
2. `frontend/src/pages/completeSortie/` (finish extraction)
3. `frontend/src/pages/aircraftMaintenance/` (finish extraction)

Document domains as a **logical index** over existing folders.

### Canonical documentation

| Doc | Role |
|-----|------|
| **`docs/MODULE_MAP.md`** (new) | Primary reviewer entry: layers, domain index, cascade pointer, post-extraction tree, recipes, demo/verify path |
| `README.md` | Point architecture readers to MODULE_MAP; keep quickstart |
| `docs/PROJECT_OVERVIEW.md` | Keep cascade + inventory; link MODULE_MAP for navigation |
| `docs/internal/CONTRIBUTOR_GUIDE.md` | Structure → MODULE_MAP; keep glossary + invariants |
| `docs/LIMITATIONS.md` | Unchanged content; MODULE_MAP links for caveats |
| `ROADMAP.md` | Phase E snapshot when implementing |

### MODULE_MAP outline

1. Product posture (portfolio, single squadron, synthetic)
2. Layer cake (UI → api client → routes → services → models/DB)
3. Domain index table (routes, services, pages, tests)
4. Cascade spine pointer + demo proof path
5. File tree matching post-extraction reality
6. Three extension recipes
7. Verify / demo path (scripts, ports, accounts)

### Domain index (logical)

| Domain | Backend entry points | Frontend entry points |
|--------|----------------------|------------------------|
| Logging / cascade | `api/logging.py`, `services/flight_completion.py` | Complete Sortie, logbook |
| Readiness / WTM | `services/readiness.py`, `catalogs/cbr_*` | Readiness, readiness board |
| Maintenance | `api/maintenance.py`, maintenance chain / QA services | Aircraft Maintenance, maint pages |
| Training | `api/syllabus.py`, gradecard services | Training, gradecard pages |
| Ops / SDO | `api/ops.py`, `ops_day`, scheduling | Ops, Schedule, boards |
| Auth / governance | auth API, middleware, audit | Login, Admin, permissions |

**Spine callout:** `flight_completion` stays a focused service on purpose; integrity tests pin it. Do not split in this pass.

---

## Extraction design

### Freeze rules (all extractions)

- No API path, payload, status code, or schema renames
- No cascade rule, currency math, QA/maint status logic, or seed **content** changes (same demo world; reorganized source only)
- No intentional UI copy, layout, or behavior changes
- Public entrypoints stay stable: `python seed.py` (demo-prep), same React routes
- Gate: `./scripts/verify.sh` green
- Prefer move code → thin re-exports over rewrites

### Seed: `backend/seed.py` → `backend/seed/` package

**Target layout** (merge small sections if a file would be trivial):

```
backend/seed/
  __init__.py
  __main__.py          # python -m seed
  run.py               # SessionLocal + ordered steps
  constants.py         # DEMO_PW, TODAY, random.seed(42)
  swtp_catalog.py      # SWTP / syllabus catalog tables
  people.py
  aircraft.py
  sorties.py
  maintenance.py
  training.py
  ops.py
  cbr.py               # load Enclosure 2 catalog into DB (thin)
backend/seed.py        # shim → seed.run.main() so demo-prep keeps `python seed.py`
```

Split along **existing comment sections** in `seed.py`, preserving call order and `random.seed(42)`.

**Out of scope:** roster, passwords, scenario outcome changes.

### Complete Sortie UI

**Target layout:**

```
frontend/src/pages/CompleteSortie.tsx          # thin shell: load, submit, layout
frontend/src/pages/completeSortie/
  helpers.ts                 # keep pure helpers
  helpers.test.ts            # keep; extend only if pure logic moves
  types.ts                   # optional extract from helpers
  Section.tsx
  CrewActualsPanel.tsx
  TaskCreditsPanel.tsx
  DiscrepanciesPanel.tsx
  SafetyPanel.tsx
  useCompleteSortieForm.ts   # only if state entanglement requires it
```

Extract by **UI section / pure builder**. Payload assembly stays pure and tested where already covered.

**Out of scope:** new debrief fields, validation product changes, API client redesign.

### Aircraft Maintenance UI

**Target layout:**

```
frontend/src/pages/AircraftMaintenance.tsx     # shell: queries, mutations, composition
frontend/src/pages/aircraftMaintenance/
  statusHelpers.ts           # keep
  DiscrepancyPanel.tsx
  WorkOrderPanel.tsx
  InspectionPanel.tsx
  LogbookPanel.tsx
  QaReleasePanel.tsx
  types.ts                   # optional
```

Shared query keys and invalidations stay in the shell so refresh behavior is unchanged.

**Out of scope:** new maint workflows, CM, stamped/computed rule changes.

### Explicitly not extracted

| Blob | Reason |
|------|--------|
| `catalogs/cbr_enclosure2.py` | Data catalog; large size expected |
| `services/scheduling.py` | Service-sized; document in map only |
| `services/flight_completion.py` | Cascade spine; tests pin it |
| `lib/api/types.ts` | Hand-maintained; separate optional work |

---

## Demo / clone path (to document)

Aligned with current README and `scripts/demo-prep.sh`:

1. Prerequisites: Docker, Python 3.12, Node 20+
2. `./scripts/demo-prep.sh` — Postgres on `127.0.0.1:5433`, migrations, `python seed.py`
3. API: uvicorn on port **8001**
4. UI: Vite on port **5174** → `/login`
5. Demo accounts (existing README table): SDO / pilot / maint / admin
6. Prove spine: complete NVG-related sortie → currency / hours / jacket / optional discrepancy path (see PROJECT_OVERVIEW cascade)
7. `./scripts/verify.sh` before claiming green
8. Link `docs/LIMITATIONS.md` for demo secrets, open RBAC flags, portfolio posture

---

## Extension recipes (documentation only in this pass)

### Recipe 1 — Add a currency type

| Step | Where |
|------|--------|
| Table-driven types | `CurrencyType` / applicability models |
| Seed type + applicability | `seed/people.py` (or currency section) |
| Renewal rules | `services/currency_renewal_rules.py`, applicability helpers |
| Cascade if complete renews it | `services/flight_completion.py` only when needed |
| FE | Prefer API-driven surfaces; avoid hardcoding new codes only in UI |
| Tests | Extend currency / complete tests if renewal is claimed |

**Invariant:** catalog/DB-driven currencies; do not add codes only in scheduling heuristics without seed + types.

### Recipe 2 — MAF / discrepancy chain field or step

| Step | Where |
|------|--------|
| Model + Alembic | `models/maintenance.py`, migrations |
| API + schemas | `api/maintenance.py`, `schemas/` |
| Chain / QA | `services/maintenance_chain.py`, `qa_release.py` as needed |
| Seed sample | `seed/maintenance.py` |
| FE | `aircraftMaintenance/*`, `lib/api/maintenance.ts`, `types.ts` if exposed |
| Tests | `tests/test_maintenance_chain.py`, QA tests |

**Invariant:** stamped vs computed status and QA release semantics; services flush, routes commit.

### Recipe 3 — Add a syllabus event (SWTP-shaped)

| Step | Where |
|------|--------|
| Catalog row | `seed/swtp_catalog.py` — paraphrased descriptions only |
| Seed | training seed path → `SyllabusEvent` |
| Progress / boards | `services/syllabus_progress.py`, boards APIs if scheduled |
| FE | Training / gradecard consume API; avoid hardcoded event lists in UI |
| Tests | training/board tests if behavior is asserted |

**Invariant:** unclassified paraphrase only; preserve AMCM code-collision convention documented in seed header.

---

## Implementation order

1. Write `docs/MODULE_MAP.md` against **current** tree (honest baseline)
2. Seed package + shim → verify
3. Complete Sortie extraction → verify
4. Aircraft Maintenance extraction → verify
5. Refresh MODULE_MAP tree + recipe paths; link README / CONTRIBUTOR / PROJECT_OVERVIEW; ROADMAP Phase E

Docs early so extractions have a target; refresh at end so paths match reality.

## Verification matrix

| Change | Must still pass |
|--------|-----------------|
| Seed package | demo-prep / seed run; pytest (seed-dependent expectations) |
| Complete Sortie | FE helper unit tests; backend complete tests; build/lint |
| Aircraft Maintenance | FE build/lint; no backend contract change |
| All | `./scripts/verify.sh` |

## Risks and mitigations

| Risk | Mitigation |
|------|------------|
| Seed split changes ordering → different demo world | Preserve call order; `random.seed(42)`; no data edits |
| FE split breaks submit payload | Keep payload builders pure; existing helper tests; no API changes |
| Doc drift | MODULE_MAP owns navigation; other docs link only |
| Scope creep into flight_completion | Map documents spine; no refactor in this pass |

## Out of scope follow-ups (not this pass)

- Broader write-route RBAC coverage (LIMITATIONS)
- Optional OpenAPI type regeneration
- Further page splits (Logbook, Training, GradecardFill) if still large after this pass
- Domain monorepo if product direction later requires multi-squadron

---

## Decision log (brainstorm)

| Question | Choice |
|----------|--------|
| Success definition | Reviewer-ready structure (A) |
| Code movement | Targeted extractions: seed, Complete Sortie, Aircraft Maintenance (C) |
| Risk bar | Strict behavior freeze (A) |
| Reviewer outcome | Module map + demo path + three extension recipes (D) |
| Approach | Docs-first, extract-in-place (1) |

---

*Design produced via Superpowers brainstorming. Next step after user approves this file: writing-plans → implementation plan only (no code until plan is approved).*
