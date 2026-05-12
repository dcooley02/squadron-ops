cat > ~/Documents/GitHub/hsc-squadron-ops/KNOWN_ISSUES.md << 'EOF'
# Known Issues — HSC Squadron Ops

Tracking known bugs and the batch in which each will be addressed.

## From Batch 2 Cascade Verification (2026-05-09)

### B2-1: SAR_NIGHT renews on day-only SAR sortie (RESOLVED 2026-05-09)
- **Symptom:** Completing a sortie with `night_hours=0` and `nvg_hours=0` but `event_type=SAR` causes SAR_NIGHT currency to renew for crewmembers.
- **Verified on:** Sortie 398 (SAR-301, day-only, 2.5hr), Torres (person 77).
- **Why critical:** Silently inflates currency state. Crew may launch thinking they are night-current when they are not.
- **Resolution:** Fixed in **Batch 2.1** (currency-renewal hotfix, before Batch 3).

### B2-2: Aircraft status does not flip to NMCM/PMC on MAJOR discrepancy
- **Symptom:** Filed a MAJOR-severity discrepancy via `/api/logging/sorties/{id}/complete` payload; aircraft remained FMC and the discrepancy did not appear in `open_discrepancies`.
- **Verified on:** Sortie 398, Aircraft 28.
- **Resolution:** Fixed in **Batch 6** (NAMP-shaped maintenance overhaul). Discrepancy filing and severity → status mapping rewrites entirely.

### B2-3: Syllabus credit (`syllabus_event_completed`) never sets despite Q grades
- **Symptom:** Sortie 398 completed with FSO 207 / FSO 208 graded "Q" for HAC and H2P. All three crewmembers' training jackets show `syllabus_event_completed: null` for sortie 398.
- **Verified on:** Sortie 398 (SAR-301), HAC Navarro (78), H2P Torres (77), CC Ramos (90).
- **Resolution:** Obviated by **Batch 3** (syllabus/gradecard model overhaul). Current `SyllabusEvent` model is being replaced; credit logic rewrites against the new gradecard-driven schema.

## Seed Data Issues (lower priority)

### S-1: FAM-102 sortie credits FAM-101
- Sortie 310 (2026-04-01) has `event_code: "FAM-102"` but `syllabus_event_completed: "FAM-101"` in Torres's jacket.
- **Resolution:** Resolved by Batch 3 reseed.

### S-2: Aircrewmen have no seeded currencies
- Person 90 (Ramos, CREW_CHIEF) returns `currencies: []`. Aircrew currencies (AMNS Sensor Op, ALMDS Sensor Op, CSTRS Winch Op per Wing 3710.7G Table B-2) are not in the seed.
- **Resolution:** Addressed in Batch 4 (currency rewrite) and Batch 5 (CBR task seed expansion).

### S-3: PROFICIENCY sortie 396 has only HAC, no aircrewman
- Wing 3710.7G Ch.2 ¶1.a requires HAC + one Utility Aircrewman minimum.
- **Resolution:** Fix in seed during Batch 3 reseed cleanup.

## Identified During B2-1 Investigation (deferred to Batch 4)

### B4-Q1: NVG currency model doesn't match Wing 3710.7G Table B-2
- **Current:** Single `NVG` currency, 60-day periodicity.
- **Per Table B-2:** Distinct currencies: Night/NVD (45d, 2.0hrs), NVD TERF (30d, 2.0hrs), NVD TERF Instructor for HACs (45d, 10.0 flight hrs), Day DVE Approaches (60d, 3 day DVE), NVD DVE Approaches (30d, 6 NVD landings).
- **Resolution:** Full currency table rewrite in Batch 4.

### B4-Q2: Cascade does not differentiate LIVE vs SIM_TOFT for currency renewal
- **Current:** Currency cascade fires the same way regardless of `flight_mode`.
- **Per WTM App. D + Wing 3710.7G Table B-2 Notes:** Some currencies are sim-eligible (e.g., strafe per Note 3), some aren't. "Live confers sim" is the WTM rule for tasks; less clear for currencies.
- **Resolution:** Sim-eligibility flag per currency type added in Batch 4.

## From Batch 3b Verification (2026-05-09)

### B3b-1: Duplicate ALR critical line item on P291 (and likely other events)
- **Symptom:** P291 line item template has two "ALR" entries, both marked is_critical=True.
- **Root cause:** Likely the per-event template specifies ALR explicitly AND inherits from a shared General Flight Conduct template that also includes ALR.
- **Resolution:** De-duplicate line items in the seed by (event_id, section, item_name). Defer to next reseed pass.

### B3b-2: GradecardSummary API response missing grading_scheme
- **Symptom:** GET /api/syllabus/persons/{id}/gradecards returns scheme=None for every card; the DB has correct values.
- **Root cause:** Pydantic schema GradecardSummary in app/schemas/syllabus.py likely missing grading_scheme field, OR the serializer isn't pulling it from the SQLAlchemy enum.
- **Resolution:** Single-field Pydantic patch. Address before Batch 4.

### B3b-3: No gradecards seeded for non-flight events (LAB/BOARD)
- **Symptom:** 19 LAB events (L200-L302) and 3 BOARD events (P290, P390, A290) have zero gradecard instances seeded. Training jackets won't reflect ICW/lab/board completion.
- **Root cause:** seed_historical_gradecards() only iterates over historical sorties, not standalone event completions.
- **Resolution:** Add a separate seed pass for ground-event gradecards. Defer to Batch 5.

### S-4: Gradecard seed distribution skews pessimistic
- **Symptom:** 26% INCOMPLETE rate on COMPLETION-scheme cards (20 of 74).
- **Root cause:** Seed weights map to COMPLETION scheme without accounting for absence of "conditional" middle ground.
- **Resolution:** Tune seed weights for COMPLETION-scheme cards. Defer to next reseed pass.

EOF
### B4a-1: AMCM_SO and HOIST_OP quals not seeded on aircrewmen
- **Symptom:** ALMDS_SO, AMNS_SO, and CSTRS_WINCH currencies are defined and applicable rules exist, but no aircrewman in the seed has the required AMCM_SO or HOIST_OP_QUAL qualifications. Result: aircrewmen get only CSW from /currency/types/applicable-to/, never the AMCM- or hoist-specific currencies.
- **Resolution:** In Batch 4c (or Batch 5 reseed), add AMCM_SO qual to AWS-roled aircrewmen who actually hold the qual in real squadrons (typically the most experienced AWs). Add HOIST_OP_QUAL to aircrewmen who are hoist operators.

### B4b-1-1: CurrencyOut schema doesn't project nested currency_type
- **Symptom:** GET /api/persons/{id} returns currencies with currency_code populated (legacy) but currency_type field is null even though DB rows have currency_type_id set.
- **Root cause:** Pydantic schema or relationship loading — likely missing joinedload on the persons query or the schema doesn't have currency_type field declared correctly.
- **Resolution:** Single-field Pydantic patch + possibly a joinedload. Address before frontend pass (Batch 4c or wherever).

---

## Session checkpoint — 2026-05-09

### What's done
- Batch 2: cascade verified, B2-1 SAR hours-gate hotfix
- Batch 3a: SyllabusEvent schema + GradecardLineItem/Gradecard/GradecardLineItemResult tables
- Batch 3b: 83 SWTP events seeded across 4 tracks, 1767 line items, 78 historical gradecards
- Batch 3b cleanup: B3b-1 (line item dedup), B3b-2 (Pydantic scheme field), S-4 (gradecard distribution tuning)
- Batch 4a: Wing Table B-2 currency_types + currency_applicabilities (13 types, 14 applicability rows)
- Batch 4b-1: cascade rewire to activity-quantity-driven renewal, 97 per-person Currency rows
- Batch 4c: frontend pivot — Sorties sidebar entry, enriched Sortie detail, Training/Maintenance/Admin pages built, GradecardDetail with canonical 3502.8 section order and proper score badges

### What's deferred (not blocked, just not yet done)
- B4a-1: AMCM_SO and HOIST_OP_QUAL quals not seeded — ALMDS_SO, AMNS_SO, CSTRS_WINCH currencies apply to nobody. Backfill before any AMCM-focused demo.
- B4b-1-1: CurrencyOut Pydantic schema doesn't project nested currency_type relationship. Single-field fix.
- B4b-2: Historical sortie activity backfill — populate the 95 historical sorties with plausible activity quantities so currency timelines look more realistic. Deferred, not required for current demo.
- B2-2: Aircraft status auto-flip on MAJOR/downing discrepancy. Defer to Batch 6 NAMP-shaped maintenance.

### Pick-up suggestions for next session
- If polishing for a specific demo: fix B4b-1-1 (Pydantic field), seed AMCM_SO quals on a few AWs (B4a-1 partial), run 4b-2 backfill for visual depth
- If pushing scope: Batch 5 NAMP-shaped maintenance is the next big functional area (phase forecast with real flight rate, ADB workflow, MAF lifecycle)
- If polishing UI: there are minor papercuts in the Aircraft list/detail and Sortie list filter defaults — small one-shot fixes

### Demo-ready surfaces as of this checkpoint
- Dashboard, Crew list/detail, Aircraft list/detail, Schedule (day/week strip), Sorties list/detail, TV Board (3 modes)
- Training (3 tabs: People/Events/Gradecards), GradecardDetail
- Admin (3 tabs: Currency Catalog/People/Syllabus placeholder)
- Maintenance (basic: stat strip, status table, phase forecast)

### Demo gaps (mention if asked, don't volunteer)
- No auth (open access — fine for local demo, blocker for real deployment)
- ALMDS/AMNS/CSTRS currencies show in catalog but apply to nobody (B4a-1)
- Maintenance is read-only — no MAF creation, no inspection workflow yet
- No way to file a flight from the UI — sortie completion is API-only via /api/logging/sorties/{id}/complete

### B5b-1-1: DiscrepancyOut Pydantic schema doesn't project sortie_id
- **Symptom:** GET /api/aircraft/{id} returns open_discrepancies with sortie_id=None despite DB having sortie_id populated.
- **Root cause:** Pydantic schema field missing.
- **Resolution:** Add sortie_id to DiscrepancyOut schema. Address in B5b-2 frontend pass.

---

## Session checkpoint — 2026-05-09 (late)

### Batch 5 complete: NAMP-shaped maintenance operational
- 5a: schema (Discrepancy NAMP fields, InspectionType + AircraftInspection
  tables, computed_status derivation)
- 5b-1: cascade integration (auto-MAF, work_status, sortie linkage,
  PATCH endpoints for discrepancies and inspections)
- 5b-2: frontend rewire (Maintenance page, AircraftMaintenance detail
  page, dashboard rewire, both modals working)

### Resolved this session
- B2-2: aircraft status auto-flip — closed via computed_status
  architecture
- B5b-1-1: DiscrepancyOut sortie_id/aircraft_id projection — fixed in
  5b-2 schema patch

### Still deferred
- B4a-1: AMCM_SO and HOIST_OP_QUAL quals not seeded
- B4b-1-1: CurrencyOut Pydantic doesn't project nested currency_type
- B4b-2: historical sortie activity backfill
- Auth (no login, no JWT, no RBAC)
- Frontend "complete a sortie" UI (cascade is API-only currently)
- Frontend "fill a gradecard" UI

### Demo-ready surfaces as of this checkpoint
- Dashboard with computed-status readiness + drift alert
- Crew list/detail
- Aircraft list/detail with NAMP-shaped discrepancies
- Sorties list/detail with activity quantities, task credits, debrief
- Schedule (day/week, crew validation)
- Sorties timeline
- Training (3 tabs: People/Events/Gradecards) + GradecardDetail in
  canonical 3502.8 layout
- Admin (Currency Catalog/People/Syllabus placeholder)
- Maintenance (rebuilt: stat strip, drift alert, aircraft grid,
  phase forecast) + AircraftMaintenance detail with inspections,
  discrepancies, history, working modals
- TV Board

### Pick-up suggestions for next session
- If polishing for a specific demo: address B4a-1 (seed AMCM/Hoist Op
  quals), B4b-1-1 (single Pydantic field), and possibly B4b-2 (activity
  backfill for visual depth). All small.
- If pushing scope: frontend 'complete a sortie' UI (most-needed
  workflow gap) or auth (the only thing genuinely blocking deployment).
- If demo prep: walk through every page, capture papercuts, fix in a
  Batch 7 polish pass.

### Notable architectural decisions made this session
- aircraft.computed_status alongside legacy status (mixed approach)
  rather than full replacement — drift visualization is a feature
- Discrepancy severity = MINOR/MAJOR/DOWNING (impact classification);
  aircraft computed_status = FMC/PMC/NMC/NMCM/NMCS (aggregate result).
  UI may render aggregates as Up/Partial/Down but internal data stays
  NAMP-shape.
- Inspection table is full (all 7 types), with is_downing_when_overdue
  flag distinguishing paperwork from real-impact inspections

---

## Session checkpoint — 2026-05-10

### Resolved this session (Batch 6 polish)
- B4a-1: AMCM_SO and HOIST_OP_QUAL quals seeded; ALMDS_SO/AMNS_SO/CSTRS_WINCH currencies now apply to people
- B4b-1-1: CurrencyOut nests currency_type for inline catalog rendering
- B4b-2: Historical sortie activity quantities backfilled in seed.py

### Still deferred
- Auth (no login, no JWT, no RBAC)
- Frontend "complete a sortie" UI (cascade is API-only)
- Frontend "fill a gradecard" UI

### Demo-ready surfaces (unchanged from prior checkpoint, with deeper data)
- Dashboard, Crew, Aircraft, Sorties, Schedule, Training, Admin,
  Maintenance, TV Board — all functional with realistic data
- Currency Catalog now shows real holders for every Wing Table B-2
  currency type (no more "applies to nobody")
- Historical sorties show activity quantities matching their event type

---

## Session checkpoint — 2026-05-10 (late, second session today)

### Landed this session
- Batch 7: Complete-a-sortie UI — full multi-section form with pre-fills,
  inline task credits + discrepancies (compact mode), entry points on
  SortieDetail header and Schedule tiles. Verified end-to-end: DOWNING
  discrepancy filed via form flipped aircraft 615 computed_status
  PMC → NMCM with auto-MAF M-2026-0022.
- Batch 8a: Gradecard fill backend — POST /gradecards/blank with auto-
  populated empty result rows, PATCH endpoints for line items (autosave)
  and gradecard header (status flip), GET instructors-for-event filtered
  by track-appropriate qual.
- Batch 8b: Gradecard fill frontend — NewGradecardModal from both
  Training tabs (Gradecards + per-person People), GradecardFill page
  with autosave-on-blur + setQueryData cache update (no focus loss),
  Mark Complete/Incomplete/Reopen header actions, canonical section
  order. Verified end-to-end on Bennett P200 gradecard.

### Still deferred (in priority order)
- B7-1: GET /api/aircraft list endpoint doesn't project computed_status
  (dashboard works around via parallel detail fetches). Single-field
  Pydantic fix.
- Auth (login, JWT, RBAC) — the only thing genuinely blocking real
  deployment. Demoably invisible.
- Polish pass against screenshots — minor consistency issues caught:
  Mark Complete button visibility when already COMPLETE (cosmetic);
  "View read-only gradecard" link could be more prominent.

### Possible directions for next session
- B7-1 + checkpoint (~5 min, low risk)
- Auth — bounded but substantial; needs fresh head
- Mobile-responsive pass — never tested at narrow widths
- Demo prep walkthrough — capture papercuts page-by-page
- Backfill: complete-a-sortie has no audit trail of who completed it
  (no current_user concept until auth lands)

### Architecture notes from this session
- CompleteSortie initially had a temporal dead zone bug: derived values
  (canSubmit) referenced mutation.isPending before useMutation was
  declared. Fixed by moving derived-values block to AFTER early-return
  guards but BEFORE useMutation, with canSubmit recomputed after mutation.
- GradecardFill uses per-row useMutation + setQueryData (not refetch)
  to preserve focus during autosave. Score dropdowns save on onChange
  (selection is inherently deliberate), remarks input saves on onBlur.
- The frontend instructor dropdown filters out the student to prevent
  self-grading. Backend doesn't enforce this — could be added if real
  workflow requires.

### Demo-ready as of this checkpoint
All previously demoable surfaces, plus:
- /sorties/:id/complete — file a flight via UI
- /training/gradecard/:id/fill — fill a gradecard via UI
- New Gradecard modal accessible from both Training tabs
- "Continue filling" link on IN_PROGRESS gradecards in detail view

---

## v1.0 FINAL — 2026-05-11

This is the final state of v1: the HSC-specific demo. Future development
forks to a new repo (squadron-ops) with multi-squadron, multi-community,
and expanded capabilities (logbook, readiness reports, SDO page, auto-
scheduling). v1 is frozen here as a working demo.

### Landed in this session (post-checkpoint)
- B7-1: aircraft list endpoint projects computed_status
- B7-2: deterministic inspection seeding for demo-ready fleet story
- B9: 10 papercut fixes including 2 demo-blockers ([object Object] API
  requests on board routes, invisible focus rings on gradecard fill)

### Demo-ready surfaces
All 17 main pages walk cleanly. Both major write workflows (complete-a-
sortie, fill-a-gradecard) work end-to-end. TV Boards run with auto-refresh
and no network errors. Deterministic fleet story survives reseeds:
5 FMC + 1 PMC (615 FLIR) + 1 NMCM (616 hydraulics) + 1 NMCS (617 engine AWP).

### Known limitations preserved as-is
- No auth (open API on localhost)
- HSC-specific syllabus and currency catalog only
- LOW papercuts deferred (audit findings M-S)
- datetime.utcnow() deprecation warnings in seed.py

### How to run
docker compose up -d
cd backend && source .venv/bin/activate && uvicorn app.main:app --reload
cd frontend && npm run dev
Visit http://localhost:5173

### v2 successor
See https://github.com/dcooley02/squadron-ops (created 2026-05-11)
