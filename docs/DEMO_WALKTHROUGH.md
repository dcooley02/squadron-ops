# Squadron Ops — Demonstration Walkthrough

**Duration:** ~12 minutes  
**Audience:** SDO, maintainer, senior aviator, or program manager  
**Prerequisite:** `./scripts/demo-prep.sh` and servers running on ports 5174 (UI) and 8001 (API)

---

## 0:00 — Login

Open **http://localhost:5174/login**

| Username | Role | Talking points |
|----------|------|----------------|
| `anderson.robert` | SDO | Schedule publish, ops console |
| `morgan.david` | Maint control | Maintenance rollups |
| `mitchell.james` | Line pilot | Crew jacket, logbook |
| `admin` | Admin | Audit log |

Password for all accounts: `demo1234` (local demonstration only)

**Start as:** `anderson.robert`

**Talking points:**
- JWT authentication on all API routes
- Full navigation available to authenticated users in this demonstration build
- Use different accounts to illustrate role-appropriate workflows, not access restrictions

---

## 0:00–1:00 — Dashboard

**Route:** `/`

**Talking points:**
- Morning brief: personnel, aircraft readiness, currency warnings
- Stamped vs. computed: stamped reflects line-released safe-for-flight status; computed reflects open discrepancies and overdue inspections
- WTM capability strip links to full readiness view (distinct from individual Table B-2 currency)
- Next 24 Hours: today's scheduled sorties

**Action:** Click Maintenance if drift banner is visible (expect three aircraft after reseed)

---

## 1:00–3:00 — Readiness (WTM T-Ratings)

**Route:** `/readiness`

**Talking points:**
- Squadron T-rating rollup across eight capability areas
- Table-driven rules: anchor tasks, T-1/T-2 recency windows, currency gates
- Explainability: click an area → per-pilot contributing factors and anchor status
- Aircrew rollup section
- Distinct from individual Table B-2 currency on the dashboard

**Actions:**
1. Click MOB (or any yellow/red area)
2. Expand a pilot row — show anchor task recency (current / stale / absent)
3. Optional: Export PDF → readiness brief for CO/XO review

**Note for senior aviators:** Appendix D math is simplified in this build — hand-check before claiming full WTM parity.

---

## 3:00–5:00 — Maintenance

**Route:** `/maintenance`

**Talking points:**
- Stat strip uses computed FMC/PMC/NMC
- Phase and release forecast cards
- Yellow banner: aircraft awaiting QA release

**Drift scenarios (side numbers):**

| Aircraft | Stamped | Computed | QA release |
|----------|---------|----------|------------|
| 614 | FMC | PMC | Allowed |
| 615 | FMC | NMCM | Blocked (DOWNING) |
| 617 | FMC | NMCS | Blocked (AWP) |

**Action:** Open aircraft **614** → maintenance detail

**Detail page talking points:**
- Inspections with overdue/downing flags
- Discrepancy → MAF → work order chain
- Line discrepancy entry
- Aircraft logbook (ASR/MSR-style entries)
- Release forecast for this tail

If no drift is visible, run `./scripts/demo-prep.sh` before presenting.

---

## 5:00–6:00 — QA Release

**Route:** `/maintenance/{614-id}`

**Actions:**
1. Open QA Release
2. Enter notes: *"QA inspection complete; FLIR degraded ops authorized IAW NATOPS"*
3. Release for Flight
4. Confirm toast; stamped status syncs to PMC

**Optional:** Attempt release on 615 or 617 — show blocked (not safe for flight)

**Return:** Dashboard — drift count decreased

---

## 6:00–8:00 — Sortie Completion (Cascade)

**Route:** `/sorties` → select incomplete sortie (prefer ASU/NVG P211 on day+2)

**Talking points:**
- Schedule assigned crew; Complete Sortie logs actuals
- Per-crew night/NVG/instrument hours; Apply mission profile to all crew
- Validation prevents incomplete times or missing crew hours

**Actions:**
1. Complete Sortie
2. Confirm takeoff/landing times and crew hours
3. Submit

**Route:** `/crew/{HAC-id}` — show `NIGHT_NVD` currency renewed and WTM readiness card

**Talking points:**
- One cascade: sortie → currencies → aircraft hours → training jacket → readiness
- Integrated system vs. disconnected spreadsheets and exports

**Optional:** Complete SIM TOFT P200 sortie — sim-ineligible currencies skip renewal

---

## 8:00–9:00 — Assisted Scheduling (optional)

**Route:** `/schedule`

**Actions:**
1. Select unmanned future sortie → Suggest crew
2. Show ranked suggestions with fitness warnings
3. Optional: Propose Week — human accepts each sortie (never auto-publish)

**Talking points:** Assisted, not automatic — transparent ranking a senior aviator can override

---

## 9:00–10:00 — SDO Ops & Training (optional)

**Route:** `/ops` — publish schedule, watchbill, sortie status; export ATO PDF

**Route:** `/training` — syllabus, boards, gradecard PDF export

---

## 10:00–12:00 — TV Board & Audit

**Route:** `/board/readiness` — fullscreen squadron snapshot with WTM strip

**Route:** `/admin` — audit log (QA release, sortie completion, publish actions with actor)

**Closing:**
> Fly, log, readiness updates, maintenance reconciles — one integrated system. WTM T-ratings, 4790 maintenance chain, assisted scheduling, and SDO tools are live in this demonstration. Full Appendix D parity and wing-level rollups are planned next.

---

## Pre-Demo Checklist

- [ ] `./scripts/demo-prep.sh` completed
- [ ] Login works (`anderson.robert` / `demo1234`)
- [ ] Dashboard shows Next 24 Hours sorties
- [ ] `/readiness` loads with area drill-down
- [ ] Maintenance shows drift aircraft 614, 615, 617
- [ ] QA release on 614 succeeds; 615 blocked
- [ ] Complete one sortie → crew currency advances
- [ ] `pytest -q` passes (37 tests) and `npm run build` succeeds