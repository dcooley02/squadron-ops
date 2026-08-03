# Phase E — Reviewer Modularity / Growth Map Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make Squadron Ops reviewer-navigable via a canonical module map, demo path, and three extension recipes, with honest extractions of `seed.py`, Complete Sortie, and Aircraft Maintenance under a strict behavior freeze.

**Architecture:** Docs-first, extract-in-place. Keep existing three-layer backend and page/`lib/api` frontend. Do not introduce domain monorepos. Split seed into `backend/seed/` + shim; finish page helper packages under `completeSortie/` and `aircraftMaintenance/`. Phase F (mobile) is out of scope.

**Tech Stack:** Python 3.12, FastAPI app already in tree, React 19 + TypeScript + Vite + TanStack Query, PostgreSQL via Docker Compose, `./scripts/verify.sh`.

**Spec:** `docs/superpowers/specs/2026-08-02-modularity-growth-architecture-design.md`  
**Roadmap:** Phase E (this plan) then Phase F (mobile) — do not implement F here.

## Global Constraints

- **Behavior freeze:** no API path/payload/schema renames; no cascade/currency/QA math changes; no intentional UI copy/layout/behavior changes; no seed *content* changes (same demo world, reorganized source only).
- **Public entrypoints:** `cd backend && python seed.py` and `./scripts/demo-prep.sh` must keep working; React routes unchanged.
- **Gate:** `./scripts/verify.sh` green after each code task that touches runtime.
- **Prefer move + thin re-exports** over rewrites; preserve `random.seed(42)` and seed `main()` call order.
- **Do not** refactor `flight_completion.py`, `scheduling.py`, or `cbr_enclosure2.py` for line count.
- **Do not** start Phase F (mobile/responsive) in this plan.
- Working directory for commands: repo root `/Users/dilloncooley/Documents/GitHub/squadron-ops` unless a step says `cd backend` or `cd frontend`.

---

## File map (locked decomposition)

| Path | Responsibility |
|------|----------------|
| `docs/MODULE_MAP.md` | **Create** — reviewer entry: layers, domain index, cascade, tree, recipes, demo/verify |
| `README.md` | **Modify** — Architecture section links MODULE_MAP |
| `docs/PROJECT_OVERVIEW.md` | **Modify** — navigation link + seed path note |
| `docs/internal/CONTRIBUTOR_GUIDE.md` | **Modify** — structure points at MODULE_MAP |
| `ROADMAP.md` | **Modify** — Phase E status → Done when complete |
| `docs/LIMITATIONS.md` | **Modify lightly** — only if seed path text still says monolith-only |
| `backend/seed/__init__.py` | Package marker |
| `backend/seed/__main__.py` | `python -m seed` → `run.main()` |
| `backend/seed/constants.py` | `DEMO_PW`, `TODAY`, `random.seed(42)`, shared aliases used by seed modules |
| `backend/seed/swtp_catalog.py` | `_SWTP_EVENTS` tables + gradecard line-item builders currently above people seed |
| `backend/seed/cbr.py` | `seed_capability_area_configs`, `seed_cbr_task_options` |
| `backend/seed/people.py` | wipe helpers if person-scoped, `seed_currency_types`, `seed_persons`, quals, currencies |
| `backend/seed/aircraft.py` | `seed_aircraft`, inspection types/inspections |
| `backend/seed/sorties.py` | historical sorties, approaches, task credits, safety, future sorties |
| `backend/seed/maintenance.py` | discrepancies / MAF seed |
| `backend/seed/training.py` | syllabus events, historical gradecards |
| `backend/seed/ops.py` | watchbill, boards, schedule publish |
| `backend/seed/run.py` | `wipe`, `main()` orchestration (exact print order) |
| `backend/seed.py` | **Replace body with shim** calling `seed.run.main()` |
| `frontend/src/pages/CompleteSortie.tsx` | Thin shell: queries, mutation, compose panels |
| `frontend/src/pages/completeSortie/helpers.ts` | Keep pure helpers (may move types out) |
| `frontend/src/pages/completeSortie/helpers.test.ts` | Keep; run every FE change |
| `frontend/src/pages/completeSortie/Section.tsx` | Collapsible section + `Lbl` if shared |
| `frontend/src/pages/completeSortie/TimesHoursPanel.tsx` | Times, duration, flight mode, hour breakdown, landings |
| `frontend/src/pages/completeSortie/CrewActualsPanel.tsx` | Per-crew hours/landings/approaches |
| `frontend/src/pages/completeSortie/TaskCreditsPanel.tsx` | CBR task credits UI |
| `frontend/src/pages/completeSortie/DiscrepanciesPanel.tsx` | Discrepancy rows |
| `frontend/src/pages/completeSortie/SafetyPanel.tsx` | Safety report rows |
| `frontend/src/pages/AircraftMaintenance.tsx` | Thin shell: queries, header, compose panels/modals |
| `frontend/src/pages/aircraftMaintenance/statusHelpers.ts` | Keep |
| `frontend/src/pages/aircraftMaintenance/QaReleaseModal.tsx` | Extract existing modal |
| `frontend/src/pages/aircraftMaintenance/RecordInspectionModal.tsx` | Extract |
| `frontend/src/pages/aircraftMaintenance/UpdateDiscrepancyModal.tsx` | Extract |
| `frontend/src/pages/aircraftMaintenance/CreateDiscrepancyModal.tsx` | Extract |
| `frontend/src/pages/aircraftMaintenance/Overlay.tsx` | Shared modal overlay |
| `frontend/src/pages/aircraftMaintenance/InspectionSection.tsx` | Inspection list + rows |
| `frontend/src/pages/aircraftMaintenance/DiscrepancySection.tsx` | Open/closed discs + rows |
| `frontend/src/pages/aircraftMaintenance/WorkOrderSection.tsx` | Work orders |
| `frontend/src/pages/aircraftMaintenance/LogbookSection.tsx` | Logbook entries |
| `frontend/src/pages/aircraftMaintenance/ReleaseSection.tsx` | QA release card/CTA using blockers |

**Merge rule for seed:** if a target module would be &lt; ~40 lines after split, keep it in the nearest neighbor (document the merge in the commit message). Do not invent new seed data.

---

### Task 1: Baseline MODULE_MAP (current tree)

**Files:**
- Create: `docs/MODULE_MAP.md`
- Modify: none yet (links come in Task 5 so map can be refreshed after extractions; optional README one-liner allowed if you prefer early discoverability — prefer wait until Task 5)

**Interfaces:**
- Consumes: design spec domain index and demo path
- Produces: `docs/MODULE_MAP.md` with sections listed below (honest **current** paths; note “seed package pending” where relevant)

- [ ] **Step 1: Create `docs/MODULE_MAP.md`**

Write a scannable doc with these sections (content must match the repo today):

1. **Product posture** — portfolio demo, single squadron, unclassified synthetic; desktop-primary UI; Phase F mobile after Phase E (link ROADMAP).
2. **Layer cake** — UI → `lib/api` → FastAPI routes → services → models → PostgreSQL.
3. **Domain index** table:

| Domain | Backend | Frontend | Tests |
|--------|---------|----------|-------|
| Logging / cascade | `api/logging.py`, `services/flight_completion.py` | `pages/CompleteSortie.tsx`, Logbook | `tests/test_flight_completion.py` |
| Readiness / WTM | `services/readiness.py`, `catalogs/cbr_enclosure2.py` | `pages/Readiness.tsx`, boards | `tests/test_readiness.py`, `test_appendix_d_fixtures.py` |
| Maintenance | `api/maintenance.py`, `services/maintenance_chain.py`, `qa_release.py` | `pages/AircraftMaintenance.tsx`, Maintenance | `tests/test_maintenance_chain.py`, `test_qa_release.py` |
| Training | `api/syllabus.py`, gradecard services | `pages/Training.tsx`, gradecards | related board/ops tests as applicable |
| Ops / SDO | `api/ops.py`, `ops_day.py`, `scheduling.py` | Ops, Schedule, boards | `tests/test_ops_and_boards.py`, `test_scheduling_assist.py` |
| Auth | `api/auth.py`, middleware, `require_roles` | Login, Admin, `permissions.ts` | `tests/test_auth.py` |

4. **Cascade spine** — pointer to `complete_sortie` flow in PROJECT_OVERVIEW; demo path: complete NVG-related sortie → currency/hours/jacket.
5. **Repository layout (current)** — include `backend/seed.py` as monolith; note target `backend/seed/` package.
6. **Extension recipes** (file checklists from design): currency type; MAF/discrepancy field; syllabus event — with invariants.
7. **Demo / verify** — `./scripts/demo-prep.sh`, ports 8001/5174/5433, accounts from README, `./scripts/verify.sh`, link LIMITATIONS.

- [ ] **Step 2: Sanity-check paths exist**

Run:

```bash
cd /Users/dilloncooley/Documents/GitHub/squadron-ops
test -f backend/app/services/flight_completion.py && test -f frontend/src/pages/CompleteSortie.tsx && test -f docs/MODULE_MAP.md && echo OK
```

Expected: `OK`

- [ ] **Step 3: Commit**

```bash
git add docs/MODULE_MAP.md
git commit -m "docs: add MODULE_MAP baseline for Phase E modularity"
```

---

### Task 2: Seed package + shim

**Files:**
- Create: `backend/seed/__init__.py`, `__main__.py`, `constants.py`, `swtp_catalog.py`, `cbr.py`, `people.py`, `aircraft.py`, `sorties.py`, `maintenance.py`, `training.py`, `ops.py`, `run.py`
- Modify: `backend/seed.py` → thin shim only
- Test: full pytest suite + seed smoke (via demo-prep or `python seed.py`)

**Interfaces:**
- Consumes: existing functions/data currently in `backend/seed.py` (move, do not rewrite logic)
- Produces:
  - `seed.run.main() -> None` — same orchestration as current `main()`
  - `backend/seed.py` shim:

```python
"""Shim: demo-prep and docs call `python seed.py` from backend/."""
from seed.run import main

if __name__ == "__main__":
    main()
```

  - `backend/seed/__main__.py`:

```python
from seed.run import main

if __name__ == "__main__":
    main()
```

**Preserve `main()` order exactly** (from current `seed.py`):

1. `wipe(db)`
2. `seed_aircraft`
3. `seed_persons`
4. `seed_qualifications`
5. `seed_currency_types`
6. `seed_currencies`
7. `seed_syllabus_events`
8. `seed_cbr_task_options`
9. `seed_capability_area_configs`
10. `seed_inspection_types`
11. `seed_aircraft_inspections`
12. `seed_sorties`
13. `seed_instrument_approaches`
14. `seed_discrepancies`
15. `seed_task_credits`
16. `seed_safety_reports`
17. `seed_historical_gradecards`
18. `seed_future_sorties`
19. `seed_watchbill_and_boards`
20. `seed_publish_today_schedule`
21. `db.commit()` + summary print

Suggested module placement (adjust only if imports force a merge):

| Module | Contents (by existing function names) |
|--------|----------------------------------------|
| `constants.py` | `DEMO_PW`, `TODAY`, `random.seed(42)`, short aliases (`GCS`, etc.) needed package-wide |
| `swtp_catalog.py` | `_SWTP_EVENTS`, `_mop`, `_pilot_items`, `_aircrew_items`, `_lab_items`, `_board_items`, `_get_line_items` |
| `people.py` | `seed_currency_types`, `seed_persons`, `seed_qualifications`, `seed_currencies`, person tables |
| `aircraft.py` | `seed_aircraft`, `seed_inspection_types`, `seed_aircraft_inspections` |
| `training.py` | `seed_syllabus_events`, `seed_historical_gradecards` |
| `cbr.py` | `seed_capability_area_configs`, `seed_cbr_task_options` |
| `sorties.py` | activity helpers, `seed_sorties`, approaches, task credits, safety, future sorties |
| `maintenance.py` | `seed_discrepancies` |
| `ops.py` | `seed_watchbill_and_boards`, `seed_publish_today_schedule` |
| `run.py` | `wipe`, `main` |

- [ ] **Step 1: Ensure Postgres is up**

```bash
cd /Users/dilloncooley/Documents/GitHub/squadron-ops
docker compose up -d
# wait until ready
docker compose exec -T db pg_isready -U squadron_ops
```

Expected: accepts connections.

- [ ] **Step 2: Move code into package (mechanical)**

1. Create `backend/seed/` directory.
2. Cut sections from monolithic `seed.py` into modules listed above **without editing business data or control flow**.
3. Fix imports: each module imports models from `app.models.models` / catalogs from `app.catalogs.cbr_enclosure2` as today; cross-module imports use `from seed.X import ...` or relative imports.
4. Put orchestration in `seed/run.py`.
5. Replace `backend/seed.py` with the shim (see Interfaces).
6. Add `__main__.py`.

**Import pitfall:** When running `python seed.py` from `backend/`, the top-level package name is `seed` (directory). Do not name a module that shadows `app`. Keep `sys.path` behavior: run from `backend/` as today.

- [ ] **Step 3: Smoke-run seed**

```bash
cd /Users/dilloncooley/Documents/GitHub/squadron-ops/backend
source .venv/bin/activate
python seed.py
```

Expected: same style summary as before (aircraft/persons/sorties counts print; no traceback). If counts differ wildly from prior runs with same code, investigate order/data edits — **revert content changes**.

- [ ] **Step 4: Run backend tests**

```bash
cd /Users/dilloncooley/Documents/GitHub/squadron-ops/backend
source .venv/bin/activate
pytest -q
```

Expected: all tests pass (suite size ~51; exact count may match project).

- [ ] **Step 5: Commit**

```bash
git add backend/seed.py backend/seed/
git commit -m "refactor: split demo seed into package with shim entrypoint"
```

---

### Task 3: Complete Sortie page extraction

**Files:**
- Modify: `frontend/src/pages/CompleteSortie.tsx`
- Create: `frontend/src/pages/completeSortie/Section.tsx`, `TimesHoursPanel.tsx`, `CrewActualsPanel.tsx`, `TaskCreditsPanel.tsx`, `DiscrepanciesPanel.tsx`, `SafetyPanel.tsx`
- Keep: `helpers.ts`, `helpers.test.ts`
- Test: `npm run test`, `npm run build`, `npm run lint`

**Interfaces:**
- Consumes: existing helpers from `./completeSortie/helpers` (`buildFlightLogActuals`, types, etc.)
- Produces: shell that only owns route params, queries, form state (or passes state into panels), and `completeSortie` mutation — **same payload shape** as today

**Extraction guide (map existing comments in `CompleteSortie.tsx`):**

| Extract to | Source in current file |
|------------|------------------------|
| `Section.tsx` | `Section` + `Lbl` components (~lines 34–82) |
| `TimesHoursPanel.tsx` | “Section 1: Times & Hours” block (times, duration, mode, hour breakdown, landings as currently grouped) |
| `CrewActualsPanel.tsx` | Per-crewmember actuals section |
| `TaskCreditsPanel.tsx` | Task credits section |
| `DiscrepanciesPanel.tsx` | Discrepancies section |
| `SafetyPanel.tsx` | Safety section |
| Shell keeps | Header, submit error, sticky submit bar, mutation, pre-fill effect, guards |

**Props pattern (example — match real state names in file):**

```tsx
// TimesHoursPanel.tsx — illustrative; use actual state field names from CompleteSortie.tsx
type Props = {
  takeoff: string;
  land: string;
  duration: string;
  flightMode: FlightMode;
  onTakeoffChange: (v: string) => void;
  onLandChange: (v: string) => void;
  setDuration: (v: string) => void;
  setFlightMode: (m: FlightMode) => void;
  // ... remaining hour/landing fields currently in Section 1
};
```

Do **not** change CSS class strings, labels, or validation messages.

- [ ] **Step 1: Run existing helper tests (baseline)**

```bash
cd /Users/dilloncooley/Documents/GitHub/squadron-ops/frontend
npm run test
```

Expected: pass (permissions + completeSortie helpers).

- [ ] **Step 2: Extract `Section.tsx` + one panel, compile**

Move `Section`/`Lbl` first; update imports in shell; run:

```bash
npm run build
```

Expected: success.

- [ ] **Step 3: Extract remaining panels**

Move each section without altering JSX structure inside panels beyond import boundaries. Shell composes:

```tsx
<TimesHoursPanel ... />
<CrewActualsPanel ... />
<TaskCreditsPanel ... />
<DiscrepanciesPanel ... />
<SafetyPanel ... />
```

- [ ] **Step 4: Verify FE**

```bash
cd /Users/dilloncooley/Documents/GitHub/squadron-ops/frontend
npm run test && npm run lint && npm run build
```

Expected: all pass.

- [ ] **Step 5: Commit**

```bash
git add frontend/src/pages/CompleteSortie.tsx frontend/src/pages/completeSortie/
git commit -m "refactor: extract Complete Sortie panels under completeSortie/"
```

---

### Task 4: Aircraft Maintenance page extraction

**Files:**
- Modify: `frontend/src/pages/AircraftMaintenance.tsx`
- Create: under `frontend/src/pages/aircraftMaintenance/`:
  - `Overlay.tsx`
  - `QaReleaseModal.tsx`
  - `RecordInspectionModal.tsx`
  - `UpdateDiscrepancyModal.tsx`
  - `CreateDiscrepancyModal.tsx`
  - `InspectionSection.tsx` (includes `InspectionRow` or co-locate row in same file)
  - `DiscrepancySection.tsx` (includes `DiscrepancyRow`)
  - `WorkOrderSection.tsx` (includes `WorkOrderRow`)
  - `LogbookSection.tsx`
  - `ReleaseSection.tsx` (blockers + open release modal CTA)
- Keep: `statusHelpers.ts`
- Test: `npm run test`, `npm run lint`, `npm run build`

**Interfaces:**
- Consumes: `statusHelpers` (`STATUS_VARIANT`, `collectReleaseBlockers`, etc.), API client unchanged
- Produces: shell owns `useParams`, all `useQuery` keys (same keys as today), modal open state, toast; sections receive data + callbacks

**Current co-located components to move (by comment banners):**

| Component | Approx. start in file |
|-----------|------------------------|
| `QaReleaseModal` | ~line 44 |
| `RecordInspectionModal` | ~line 226 |
| `UpdateDiscrepancyModal` | ~line 321 |
| `Overlay` | ~line 417 |
| `InspectionRow` | ~line 434 |
| `DiscrepancyRow` | ~line 521 |
| `CreateDiscrepancyModal` | ~line 611 |
| `WorkOrderRow` | ~line 720 |
| Main page | ~line 804 |

**Query keys that must not change** (invalidate correctly from modals if they already do):

- `["aircraft-detail", id]`
- `["aircraft-inspections", id]`
- `["aircraft-discrepancies", id]`
- `["aircraft-work-orders", id]`
- `["aircraft-logbook", id]`
- `["release-forecast", id]`

- [ ] **Step 1: Extract modals + Overlay first**

Move pure-ish presentational/modal components; re-export imports from shell. Build:

```bash
cd /Users/dilloncooley/Documents/GitHub/squadron-ops/frontend
npm run build
```

- [ ] **Step 2: Extract section components**

Move list sections; shell retains data loading and header card metrics if tightly coupled — optional extract of header only if trivial. Prefer leaving **header card** in shell if extraction adds prop noise without clarity.

- [ ] **Step 3: Verify FE**

```bash
npm run test && npm run lint && npm run build
```

Expected: all pass.

- [ ] **Step 4: Commit**

```bash
git add frontend/src/pages/AircraftMaintenance.tsx frontend/src/pages/aircraftMaintenance/
git commit -m "refactor: extract Aircraft Maintenance panels and modals"
```

---

### Task 5: Refresh MODULE_MAP + doc links + ROADMAP Phase E done

**Files:**
- Modify: `docs/MODULE_MAP.md` (post-extraction tree + recipe paths)
- Modify: `README.md` Architecture section
- Modify: `docs/PROJECT_OVERVIEW.md` (seed path + link MODULE_MAP)
- Modify: `docs/internal/CONTRIBUTOR_GUIDE.md` (Project structure)
- Modify: `ROADMAP.md` Phase E status → Done
- Modify: `docs/LIMITATIONS.md` only if it still says `seed.py` monolith without package note

**Interfaces:**
- Consumes: final paths from Tasks 2–4
- Produces: single navigation story without contradictory trees

- [ ] **Step 1: Update MODULE_MAP tree**

Replace “current monolith” notes with:

```
backend/seed.py              # shim → seed.run.main()
backend/seed/                # package (constants, swtp, people, aircraft, ...)
frontend/src/pages/CompleteSortie.tsx
frontend/src/pages/completeSortie/   # panels + helpers
frontend/src/pages/AircraftMaintenance.tsx
frontend/src/pages/aircraftMaintenance/  # sections + modals + statusHelpers
```

Refresh recipe file paths (`seed/people.py`, `aircraftMaintenance/*`, etc.).

- [ ] **Step 2: Link from README**

In `README.md` after Design principles / Architecture diagram, add:

```markdown
**Module map:** [docs/MODULE_MAP.md](docs/MODULE_MAP.md) — domain index, cascade entry points, extension recipes, demo/verify path.
```

Keep the existing diagram; fix any stale `lib/api.ts` wording to `lib/api/` if still wrong.

- [ ] **Step 3: Link CONTRIBUTOR + PROJECT_OVERVIEW**

CONTRIBUTOR_GUIDE “Project structure” — first bullet or lead sentence:

```markdown
See [docs/MODULE_MAP.md](../MODULE_MAP.md) for the domain index and extension recipes.
```

PROJECT_OVERVIEW — under Architecture or Repository Layout:

```markdown
Navigation for contributors and reviewers: [MODULE_MAP.md](MODULE_MAP.md).
```

Update seed path text from only `backend/seed.py` to package + shim.

- [ ] **Step 4: ROADMAP Phase E status**

Change Phase E header from `Planned (next)` to:

```markdown
**Status:** Done (August 2026)
```

Strike through completed bullets or mark complete consistently with Phases A–D style.

- [ ] **Step 5: Commit**

```bash
git add docs/MODULE_MAP.md README.md docs/PROJECT_OVERVIEW.md docs/internal/CONTRIBUTOR_GUIDE.md ROADMAP.md docs/LIMITATIONS.md
git commit -m "docs: complete Phase E module map links and roadmap status"
```

---

### Task 6: Full verification gate

**Files:** none (run only)

- [ ] **Step 1: Run full verify**

```bash
cd /Users/dilloncooley/Documents/GitHub/squadron-ops
./scripts/verify.sh
```

Expected: Postgres up, pytest pass, frontend test/lint/build pass (script’s full sequence).

- [ ] **Step 2: Spot-check seed entrypoints**

```bash
cd /Users/dilloncooley/Documents/GitHub/squadron-ops/backend
source .venv/bin/activate
python -c "from seed.run import main; print(main.__name__)"
python -c "import seed; print('package ok')"
```

Expected: prints `main` and `package ok`.

- [ ] **Step 3: Confirm Phase F not started**

```bash
# No mobile nav/drawer work should appear in this branch vs freeze intent
git log --oneline origin/master..HEAD
```

Expected: only docs + seed package + CompleteSortie/AircraftMaintenance extractions + map links. No Layout/Sidebar responsive redesign.

- [ ] **Step 4: Final commit only if verify fixed anything**

If verify forced tiny fixes, commit them:

```bash
git add -A
git commit -m "fix: address Phase E verify findings"
```

If clean, no commit.

---

## Spec coverage checklist (plan self-review)

| Spec requirement | Task |
|------------------|------|
| MODULE_MAP.md | 1, 5 |
| README / CONTRIBUTOR / PROJECT_OVERVIEW links | 5 |
| Seed package + shim; demo-prep `python seed.py` | 2 |
| Complete Sortie thin shell + panels | 3 |
| Aircraft Maintenance thin shell + panels | 4 |
| Three extension recipes | 1, 5 |
| Demo path documented | 1, 5 |
| `./scripts/verify.sh` | 2 (partial), 6 (full) |
| ROADMAP Phase E status | 5 |
| Behavior freeze / no cascade service split | Global + Task 2–4 |
| Phase F not in this plan | Global + Task 6 check |

## Placeholder scan

No TBD steps. Seed module merge rule is explicit. Panel prop lists say “match actual state names” because the shell already defines them — implementers copy from live file, not invent.

---

## Execution handoff

After this plan is accepted:

**Plan complete and saved to `docs/superpowers/plans/2026-08-02-phase-e-modularity.md`. Two execution options:**

**1. Subagent-Driven (recommended)** — fresh subagent per task, review between tasks  

**2. Inline Execution** — execute tasks in this session with executing-plans checkpoints  

**Which approach?**
