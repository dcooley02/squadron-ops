# ROADMAP.md

Squadron Ops v2 — capability build order and scope commitments.

## Thesis

One person with no prior coding background can build a better operations, training, and maintenance planning tool than OOMA and SHARP. The demo proves the claim by being a working, end-to-end artifact that a Naval Aviator, a maintainer, or a program manager can each look at and recognize as credible in their domain.

The roadmap is ordered to make the thesis defensible as early as possible: build the spine first (flight → cascade → readiness), then layer the domain-specific depth (maintenance, training) that proves parity with the systems being replaced, then planning tools, then production concerns.

Audience is intentionally undefined. Anyone from squadron CO to TYCOM N7 to NAVAIR PM to a defense tech investor could be looking at it. The roadmap assumes the highest-knowledge viewer in the room.

## Scope commitments (locked decisions)

- **Readiness Reports — full WTM math.** Real T-1/T-2/T-3 thresholds, capability area rollups per CHSCWPINST 3500.1F Appendix D. Not stubbed. Math has to survive a senior aviator reading it.
- **Maintenance — full 4790 chain.** MAF, work orders, job control, work center routing, QA signoff, RTS, phase tracking, BCM/AWP/AWM, aircraft logbook (ASR/MSR/equipment history). Not just the maintainer-facing slice.
- **Task option library — full Appendix D Enclosure 2 task list per capability area.** The current 20-entry library is treated as scaffolding, not the deliverable.
- **Scope is single squadron until single squadron is undeniable.** Multi-tenancy is deferred until after a real conversation with a wing or NAVAIR.

## Build order

### 1. Logbook — finish in-flight work
**Why first:** The cascade from sortie → flight log → currency update → syllabus credit → readiness recalc → discrepancy file is the spine of every other claim this app makes. Nothing downstream is trustworthy until this is verified end-to-end.

**Done means:**
- Batch 2 logging UI complete (scheduled, unscheduled, sim entry points)
- `complete_sortie()` cascade verified on real-feeling data (90+ historical sorties already seeded — use them)
- Cascade observable in the UI: log a flight, watch currency dates tick, watch aircraft hours change, watch syllabus events check off
- One full demo path: scheduled FAM-101 sortie → fly → log with grades → see HAC currency extend, aircraft hours increment, FAM-101 marked complete in pilot's jacket, any discrepancy filed appears on aircraft detail page

**Decision points:** Sim sortie cascade rules — confirm sim hours count toward currency where 3710.7 / 3500.1F allow, don't where they don't. Currently TOFT-flagged but not enforced.

### 2. Readiness Reports — full WTM math
**Why second:** The output side of the spine. Once the cascade is solid, readiness is the most legible proof that the data model works. A T-rating dashboard with real Appendix D math is the single most "this is better than SHARP" moment in the demo.

**Done means:**
- Capability areas modeled per 3500.1F Appendix D: MOB, FSO, ASU, SOF, PR, STW, LOG, MIW
- Full task list per capability area seeded (Enclosure 2)
- T-rating thresholds (T-1/T-2/T-3) computed per capability area per aircrew, with the recency windows and qualification minimums the WTM specifies
- Rollup logic: individual → crew → squadron
- Exportable readiness brief (PDF) — this is the "thing you can hand someone" deliverable
- Currency dashboard distinguishes capability-area readiness from individual currencies (they are related but not identical)

**Decision points:** How to display "I am T-2 in MOB because of currency X expiring in 14 days" — the explainability of the T-rating is what makes this better than SHARP, not the number itself. Plan for drill-down from squadron rollup → individual contributing factor.

**Risk:** WTM math is the kind of thing a senior aviator will check by hand against their own jacket. Errors here are credibility-fatal. Plan for a verification pass where the math is hand-checked against a known crewmember before showing it to anyone.

### 3. Maintenance deep-dive — full 4790 chain
**Why third:** Half the pitch is "OOMA replacement," and the current build is the weaker half. This is the largest single scope item on the roadmap and the one most likely to slip. Start it once readiness is locked because it doesn't block readiness, and maintainers and aviators tend to be different reviewers.

**Done means:**
- MAF data model with full field set per 4790.2 series
- Work order chain modeled: discrepancy → MAF → JCN → work center → corrective action → QA signoff → RTS
- Phase inspection tracking (200-hr for MH-60S, plus calendar-based items)
- BCM, AWP, AWM logic for parts and supply
- Aircraft logbook: ASR, MSR, equipment history records
- Phase forecasting: given flight hour projections, when does each aircraft hit phase?
- RTS projections: given open discrepancies and parts status, when is each aircraft FMC?
- Maintainer-facing workflow: ADB sign-out, discrepancy entry from the line, QA signoff path

**Decision points:** How much of the configuration management side of 4790 to model. Full config management (TD compliance, equipment tracking by serial) is a separate large lift. Recommend deferring config management to a later batch unless it surfaces as demo-relevant.

**Risk:** OOMA is 30 years of accumulated doctrine. Plan for this batch to take longer than any other. Break into sub-batches: data model first, then discrepancy/MAF workflow, then signoffs and RTS, then phase, then logbook, then forecasting. Verify each before moving on.

### 4. Training — syllabus, boards, instructor pairings
**Why fourth:** With #2 done, the readiness side of SHARP is replaced. This batch replaces the training-management side: syllabus progression, board scheduling, instructor assignment, gradesheets. Together with #2 this is the "SHARP replacement" half of the pitch.

**Done means:**
- Syllabus tracking per crewmember (FAM, TAC, SAR, etc. — already seeded)
- Board scheduling: HAC boards, instructor boards, NATOPS checks
- Instructor pairing logic: who's qualified to train whom, who's available, who hasn't taught X recently
- Gradesheet workflow: instructor enters grades, student sees them, signed gradesheet PDF exports
- Training jacket view per crewmember

**Decision points:** Gradesheet format — replicate the actual SHARP gradesheet format (recognizable to anyone in the community) or design something better? Recommend recognizable first, then offer an improved view as a toggle.

### 5. SDO tools — schedule publishing, ATO, daily ops
**Why fifth:** With #1–#4 done, the data foundation is complete. This batch turns the app from "tracker" into "planning tool." This is also the batch that makes the app useful to an SDO at 0500 the next morning, which is where day-to-day adoption would start.

**Done means:**
- Flight schedule publishing: lock the next day's schedule, distribute to crew
- ATO-style daily ops summary (mission, crew, aircraft, times, frequencies)
- Watchbill integration: SDO, ODO, duty crew, alert posture
- Brief sheets per sortie, exportable
- Day-of operations view: live schedule with status (briefed, manned up, airborne, recovered, debriefed)

**Decision points:** Comms/freq management — touch it or stay clear? Recommend stay clear for v1, defer to a security-cleared variant later.

### 6. Auth and polish
**Why sixth:** Auth is necessary before any pilot deployment but invisible in a demo. Build it before you'd deploy, not before you'd show. Polish belongs in the same batch because it's the same kind of work — making the thing presentable rather than additive.

**Done means:**
- Login, JWT, password reset
- RBAC with real roles: CO, XO, OPSO, training officer, MO, MMCO, SDO, line pilot, line maintainer, AT2-equivalent
- Role-appropriate views: SDO sees schedule-publishing UI, MO sees maintenance rollups, line pilot sees their jacket
- Audit logging on consequential actions (grade changes, MAF signoffs, schedule locks)
- Polish pass: consistent empty states, error states, loading states, accessibility, mobile-readable where it matters (line maintainer on a tablet)

### 7. Auto-schedule — assisted scheduling
**Why seventh:** This is the flashiest feature and the one most likely to misfire in front of a knowledgeable viewer. Save for after the data model is bulletproof. Scope as **assisted** scheduling (ranked suggestions, human accepts) rather than **automatic** scheduling. The crew-ranking work already done in scheduling intelligence is the foundation.

**Done means:**
- Schedule generator: given a flight requirement (mission, aircraft, time window, training needs), produce a ranked list of viable crews with explanations
- Conflict detection across the schedule: currency conflicts, qualification conflicts, crew-rest conflicts
- "Build me a week" mode: given a set of mission requirements and constraints, propose a week's schedule for the OPSO to edit
- Always human-in-the-loop. No auto-publish.

**Decision points:** How aggressive on optimization. Recommend "good enough" heuristic over true optimization — explainability matters more than optimality, and a senior aviator can't argue with a transparent ranking they can override.

### 8. Multi-squadron — deferred, pending real conversation
**Why eighth (or never, without a conversation first):** Multi-tenancy is a huge lift (data partitioning, cross-squadron permissions, wing-level rollups, type/model/series differences) that adds nothing to the "one person built this" pitch until the single-squadron version is undeniable.

**Before starting this batch:** Have a real conversation with someone at a wing, TYCOM, or NAVAIR about whether this is the right path. The answer might be "build the second squadron as a clone, prove it works, then talk about wing-level rollups," or it might be "wing rollups are the actual product, single-squadron is the wedge." Don't guess.

## Non-goals for v2

- Classified data handling. v2 stays unclassified. A future classified variant is a separate program.
- Mobile-first design. Tablet-readable where maintainers need it. Phone-first is not in scope.
- Real-time collaboration (multiple users editing the same schedule simultaneously). Lock-on-edit is fine.
- Integration with existing Navy systems. Not feasible at the demo stage and not necessary for the thesis.

## Verification posture

Every batch ends with a verification gate before the next starts. For batches with domain-critical math (Readiness, Maintenance), verification includes hand-checking the math against a known case before declaring done. "Looks good" is not a verification result for anything in #1–#5.

## Open questions to revisit

- Sim sortie credit rules — exact 3710.7 / 3500.1F language for currency credit from TOFT sims
- Configuration management depth in Maintenance batch
- Gradesheet format choice in Training batch
- Multi-squadron entry point — conversation, not code

## Status

- Current batch: #1 Logbook (Batch 2 logging UI in flight, cascade verification pending)
- Last verified milestone: scheduling intelligence with crew ranking, TV Board mode
- Frozen v1: `github.com/dcooley02/hsc-squadron-ops` tag `v1.0-demo`
