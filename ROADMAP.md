# Squadron Ops — Roadmap

Capability build order and scope commitments for the integrated naval aviation operations platform.

---

## Vision

Replace fragmented squadron tooling (OOMA for maintenance, SHARP for training/readiness, spreadsheets for scheduling) with a modern, integrated web application that a naval aviator, maintainer, or program manager recognizes as credible in their domain.

The build order prioritizes the operational spine first (flight → cascade → readiness), then domain depth (maintenance, training), then planning tools and production hardening.

---

## Scope commitments

| Area | Commitment |
|------|------------|
| **Readiness** | Full WTM math — T-1/T-2/T-3 thresholds, capability area rollups per CHSCWPINST 3500.1F Appendix D |
| **Maintenance** | Full 4790 chain — MAF, work orders, JCN, work center routing, QA signoff, QA release, phase tracking, aircraft logbook |
| **CBR tasks** | Full Appendix D Enclosure 2 task list per capability area (current library is scaffolding) |
| **Tenancy** | Single squadron until single-squadron capability is undeniable; multi-squadron deferred |

---

## Build order

### 1. Logbook — cascade verification
**Status:** Largely complete

The cascade from sortie → flight log → currency → syllabus credit → readiness → discrepancy is the foundation of every downstream claim.

- Batch 2 logging UI (scheduled, unscheduled, sim entry points)
- `complete_sortie()` verified on realistic seed data
- Observable UI path: log flight → currency updates → hours change → training progress

### 2. Readiness — full WTM math
**Status:** Core shipped; full parity in progress

- Eight capability areas modeled (MOB, FSO, ASU, SOF, PR, STW, LOG, MIW)
- Table-driven T-ratings with anchor tasks and drill-down
- Exportable readiness brief PDF
- **Remaining:** Full Enclosure 2 task list, hand-verified Appendix D math

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
**Status:** JWT shipped; RBAC planned

- Login and JWT authentication
- **Remaining:** Password reset, production RBAC, role-appropriate views, accessibility pass

### 7. Assisted scheduling
**Status:** Shipped

- Ranked crew suggestions, week proposals, conflict detection
- Human-in-the-loop only — no auto-publish

### 8. Multi-squadron
**Status:** Deferred

Pending stakeholder conversation on wing-level vs. squadron-level product direction.

---

## Non-goals

- Classified data handling (unclassified demonstration only)
- Mobile-first design (tablet-readable for maintainers; phone-first out of scope)
- Real-time collaborative editing (lock-on-edit is sufficient)
- Integration with existing Navy enterprise systems at demonstration stage

---

## Verification posture

Domain-critical math (readiness, maintenance) requires hand-checking against known cases before declaring complete. "Looks good" is not sufficient verification for batches 1–5.

---

## Open questions

- Sim sortie credit rules — exact 3710.7 / 3500.1F language for TOFT currency credit
- Configuration management depth in maintenance batch
- Gradesheet format — SHARP-recognizable vs. improved design
- Multi-squadron entry point — conversation before code