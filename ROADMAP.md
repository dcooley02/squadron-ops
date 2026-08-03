# Squadron Ops — Roadmap

Capability build order, engineering phases, and scope commitments for the integrated naval aviation operations platform.

---

## Vision

Replace fragmented squadron tooling (OOMA for maintenance, SHARP for training/readiness, spreadsheets for scheduling) with a modern, integrated web application that a naval aviator, maintainer, or program manager recognizes as credible in their domain.

The original build order prioritized the operational spine first (flight → cascade → readiness), then domain depth (maintenance, training), then planning tools. **Domain capability through assisted scheduling is largely shipped.** Near-term work shifts to integrity, production-shaped access control, maintainability, and full WTM parity.

---

## Current status (snapshot)

| Area | Status |
|------|--------|
| Flight cascade (complete → currency → hours → CBR → maint) | Shipped; integration-tested when Postgres is up |
| WTM readiness + brief PDF | Shipped with Enclosure 2-shaped catalog (92 tasks) + hand-verified Appendix D fixtures |
| Maintenance 4790 chain + QA release | Core shipped; config management deferred |
| Training / boards / gradecards | Shipped |
| SDO ops + PDFs + TV boards | Shipped |
| Assisted scheduling | Shipped (human-in-the-loop only) |
| JWT authentication | Shipped |
| Production RBAC | **Enforced** (`require_roles` + frontend guards); opt-out via `DEMO_OPEN_RBAC` / `VITE_DEMO_OPEN_RBAC` |
| Automated tests | 51 pytest cases (Postgres required); no frontend tests |
| CI | GitHub Actions: Postgres → pytest → frontend production build |
| Product posture | Portfolio demonstration — not production-hardened |

See [docs/LIMITATIONS.md](docs/LIMITATIONS.md) for known gaps and integrity risks.

---

## Scope commitments

| Area | Commitment |
|------|------------|
| **Readiness** | Full WTM math — T-1/T-2/T-3 thresholds, capability area rollups per CHSCWPINST 3500.1F Appendix D |
| **Maintenance** | Full 4790 chain — MAF, work orders, JCN, work center routing, QA signoff, QA release, phase tracking, aircraft logbook |
| **CBR tasks** | Enclosure 2-shaped HSC catalog (92 tasks, 13 anchors) in `app/catalogs/cbr_enclosure2.py` — unclassified paraphrase, not verbatim doctrine |
| **Tenancy** | Single squadron until single-squadron capability is undeniable; multi-squadron deferred |
| **Access control** | Production-shaped RBAC with role-appropriate navigation and route enforcement (demo may keep an explicit open-ACL flag) |

---

## Domain build order (capability)

### 1. Logbook — cascade verification
**Status:** Largely complete

The cascade from sortie → flight log → currency → syllabus credit → readiness → discrepancy is the foundation of every downstream claim.

- Batch 2 logging UI (scheduled, unscheduled, sim entry points)
- `complete_sortie()` verified on realistic seed data
- Observable UI path: log flight → currency updates → hours change → training progress
- **Remaining integrity work:** concurrent complete protection, strict TMR/person validation (see Engineering phases)

### 2. Readiness — full WTM math
**Status:** Shipped (demo-grade Enclosure 2 catalog + verified fixtures)

- Eight capability areas modeled (MOB, FSO, ASU, SOF, PR, STW, LOG, MIW)
- Table-driven T-ratings with anchor tasks and drill-down
- Exportable readiness brief PDF
- Enclosure 2-shaped CBR catalog (92 tasks / 13 anchors) + Appendix D fixture tests
- **Remaining (if operational use):** hand-check against live CHSCWPINST 3500.1F for each squadron community

### 3. Maintenance — 4790 chain
**Status:** Core shipped; config management deferred

- MAF/work order chain, inspections, QA release, logbook, forecasts
- **Remaining:** Full configuration management (TD compliance, serial equipment)

### 4. Training — syllabus, boards, instructor pairing
**Status:** Shipped

- Syllabus tracking, board scheduling, instructor candidates, gradecard PDF
- Training jacket and progress per crewmember

### 5. SDO tools — schedule publishing, ATO, daily ops
**Status:** Shipped

- Schedule publish, watchbill, sortie ops status, ATO/brief PDF export
- Comms/frequency management deferred

### 6. Auth and polish
**Status:** JWT + RBAC shipped; polish remaining

- Login, JWT authentication, `require_roles` enforcement, frontend nav/route guards
- Open-demo flag: `DEMO_OPEN_RBAC` / `VITE_DEMO_OPEN_RBAC`
- **Remaining:** Password productization (beyond demo reset-to-demo-password), broader write-route coverage, accessibility pass

### 7. Assisted scheduling
**Status:** Shipped

- Ranked crew suggestions, week proposals, conflict detection
- Human-in-the-loop only — no auto-publish

### 8. Multi-squadron
**Status:** Deferred

Pending stakeholder conversation on wing-level vs. squadron-level product direction.

---

## Engineering phases (recommended next work)

These phases are ordered by integrity and maintainability, not by new domain surface area. Prefer finishing Phase B before large feature expansion.

### Phase A — Stabilize demo and quality bar
**Status:** Done (July 2026)

1. ~~Document and script local verify~~ — `./scripts/verify.sh` (compose → pytest → build → lint)
2. ~~Frontend lint in CI~~ — `.github/workflows/ci.yml` runs `npm run lint` before build
3. ~~Environment-based API base URL~~ — `VITE_API_BASE_URL` via `frontend/src/lib/api.ts` + `.env.example`
4. ~~Replace `datetime.utcnow()`~~ — `app.core.time.utc_now()` / `utc_today()` across models, services, seed, tests

### Phase B — Integrity and access control
**Status:** Done (July 2026)

1. ~~**Real RBAC**~~ — `require_roles` enforces roles (ADMIN always allowed); `DEMO_OPEN_RBAC=true` restores open ACL. Frontend: `canSeeNav`, `RoleRoute`, `VITE_DEMO_OPEN_RBAC`
2. ~~**Harden `complete_sortie`**~~ — `SELECT … FOR UPDATE` on sortie + aircraft; unknown TMR / CBR task codes and off-crew person IDs raise `ValueError` (HTTP 400); complete flag set only after validation
3. ~~**Normalize transactions**~~ — `complete_sortie`, `create_and_complete_unscheduled`, `qa_release`, `publish_schedule` flush only; routes commit
4. ~~**Expand tests**~~ — RBAC denial/allow + open-ACL; complete rejects unknown TMR/task/person; hours applied once on re-complete

### Phase C — Maintainability
**Status:** Done (July 2026)

1. ~~Split monolith modules~~ — `app/models/` domain package (`enums`, `person`, `sortie`, `maintenance`, …); `lib/api/` client package; page helpers under `completeSortie/` and `aircraftMaintenance/`
2. ~~Code-split routes~~ — `React.lazy` + `Suspense` in `App.tsx` (main chunk ~236 KB vs prior single ~565 KB bundle)
3. ~~OpenAPI typegen path~~ — documented optional flow in `frontend/scripts/generate-api-types.md` (hand-maintained `types.ts` remains source of truth)
4. ~~Frontend unit tests~~ — Vitest smoke tests for permissions + complete-sortie helpers (`npm run test`, gated in CI)

### Phase D — Domain depth (roadmap commitments)
**Status:** Done for demo scope (July 2026)

1. ~~Enclosure 2-shaped CBR catalog + hand-verified Appendix D fixtures~~ — `app/catalogs/cbr_enclosure2.py` (92 tasks); `tests/test_appendix_d_fixtures.py`
2. ~~Per-crew landings on Complete Sortie~~ — debrief UI + `FlightLogActuals` + cascade rollup (legacy sortie-level HAC mirror retained when per-crew empty)
3. Maintenance configuration management — still deferred (stakeholder-driven)
4. Multi-squadron — still deferred

### Phase E — Reviewer modularity / growth map
**Status:** Done (August 2026)

Docs-first, extract-in-place under a **strict behavior freeze**. Spec:
`docs/superpowers/specs/2026-08-02-modularity-growth-architecture-design.md`

1. ~~Canonical `docs/MODULE_MAP.md`~~ (domain index, cascade pointer, demo/verify path, three extension recipes)
2. ~~Split `backend/seed.py` into `backend/seed/` package + shim~~ (`python seed.py` / demo-prep unchanged)
3. ~~Finish Complete Sortie and Aircraft Maintenance page extractions~~ (thin route shells + panel helpers)
4. ~~Link README / CONTRIBUTOR / PROJECT_OVERVIEW; refresh map after extractions~~
5. ~~Gate: `./scripts/verify.sh`~~ — no intentional cascade/API/UI behavior change

**Depends on:** Phases A–D (done for demo scope).  
**Enables:** Phase F (responsive shell is easier once dense pages are panelized).

### Phase F — Responsive / mobile-friendly access
**Status:** Planned — **after Phase E** (do not start until modularity pass is done)

Desktop remains the primary demo surface today (fixed sidebar, dense ops/maint/debrief flows). Phase F makes the product usable on **maintainer tablet and large phone** for priority paths without aiming for full phone-first parity.

**Draft in scope**

1. Responsive app chrome — collapsible / drawer nav so the sidebar does not permanently consume narrow viewports
2. Reflow primary surfaces — Dashboard, Complete Sortie, Aircraft Maintenance, and key ops/maint read paths stack cleanly
3. Touch-friendly primary actions on those paths (adequate targets; no horizontal “trap” at ~390px width for the acceptance set)

**Draft out of scope (Phase F v1)**

- Phone-first visual redesign of every page
- Full TV-board fidelity on small phones
- Offline / PWA
- Every admin table and edge workflow

**Acceptance (draft — refine when Phase F is designed)**

- Login + Dashboard + one maintenance path + complete-sortie path usable at ~390px width without layout trap
- Sidebar not permanently eating the content column on narrow viewports
- Desktop layout remains credible for portfolio review (no regression to “mobile-only” chrome)

**Depends on:** Phase E preferred first (panel extractions reduce reflow risk).

### Priority stack (summary)

| Priority | Work |
|----------|------|
| **P0** | ~~Real RBAC; sortie-complete lock + strict TMR validation~~ (Phase B done) |
| **P1** | ~~Timezone-aware datetimes; `VITE_API_BASE_URL`; local verify script; CI lint~~ (Phase A done) |
| **P2** | ~~Split large modules; code-split bundle; FE unit tests~~ (Phase C done) |
| **P3** | ~~Enclosure 2 catalog + Appendix D fixtures; per-crew landings~~ (Phase D done) |
| **P4** | ~~**Phase E** — reviewer modularity / MODULE_MAP / seed + page extractions~~ (done) |
| **P5** | **Phase F** — responsive / mobile-friendly access (next) |
| **P6** | Password productization; CM depth; multi-squadron (if stakeholders require) |

---

## Non-goals

- Classified data handling (unclassified demonstration only)
- **Phone-first parity with desktop** until Phase F is designed and shipped; current demo is **desktop-primary** (tablet-readable only where grids already reflow). Phase F adds responsive access — not a mobile-only product.
- Real-time collaborative editing (lock-on-edit is sufficient)
- Integration with existing Navy enterprise systems at demonstration stage

---

## Verification posture

Domain-critical math (readiness, maintenance) requires hand-checking against known cases before declaring complete. "Looks good" is not sufficient verification for domain batches.

Local automated checks:

```bash
./scripts/verify.sh              # compose up → pytest → FE test → build → lint
# or:
cd backend && pytest -q          # 51 tests (Postgres on :5433)
cd frontend && npm run test && npm run build && npm run lint
```

CI runs Postgres → pytest → frontend lint → FE unit tests → frontend build on push/PR to `main`/`master`.

---

## Open questions

- Sim sortie credit rules — exact 3710.7 / 3500.1F language for TOFT currency credit
- Configuration management depth in maintenance batch
- Gradesheet format — SHARP-recognizable vs. improved design
- Multi-squadron entry point — conversation before code
- ~~Whether demo deployments keep open RBAC behind a named flag~~ — yes: `DEMO_OPEN_RBAC` / `VITE_DEMO_OPEN_RBAC`

---

*Last updated: August 2026*
