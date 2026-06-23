# squadron-ops — Known Issues & Notes

This project forked from hsc-squadron-ops at v1.0-demo on 2026-05-11.
The v1 demo is preserved at https://github.com/dcooley02/hsc-squadron-ops
(tagged v1.0-demo). This is v2: expanded scope, demo-first development
order.

## Active scope
See ROADMAP.md for long-term commitments. Demo baseline: `v2.0-demo-rc8`.

## Carried-over technical debt from v1
- LOW papercuts deferred: crew header filter count, donut tooltip,
  sortie year display
- datetime.utcnow() deprecation warnings in seed.py (3 instances)
- HSC-specific syllabus and currency catalog (will be replaced by
  per-community templates in a future batch)

## Demo polish notes (June 2026 — rc8)
- Demo prep script: `./scripts/demo-prep.sh`
- Walkthrough: `DEMO_SCRIPT.txt` (12 min), quick ref: `DEMO_CHEATSHEET.txt`
- PDF exports require WeasyPrint in the backend venv (503 if missing)
- PDF downloads use `PdfExportButton` + `lib/pdf.ts` (JWT blob download, friendly errors)

## Auth / RBAC (rc8)
- JWT login required for `/api/*` (except `/api/auth/login`)
- Demo password `demo1234` for all seeded users
- Password reset not implemented
- **Demo mode:** all authenticated users see every nav item and can hit write
  endpoints; `require_roles()` authenticates only — re-enable role checks before production

## Readiness (rc6+)
- WTM T-ratings are table-driven (anchor tasks + area config) with simplified
  Appendix D math — hand-check before claiming full CHSCWPINST 3500.1F parity
- CBR library seeded at 61 tasks (scaffolding; full Enclosure 2 parity still open)
- Readiness brief PDF: `GET /api/readiness/squadron/brief.pdf`

## Maintenance (rc5)
- 4790-inspired MAF/WO chain, logbook, phase/release forecast shipped
- Full configuration management (TD compliance, serial-tracked equipment) deferred

## Scheduling assist (rc4)
- Crew ranking and week proposals are transparent heuristics, not optimization
- Human-in-the-loop only — no auto-publish

## SDO ops (rc3+)
- Ops status is manual advance (no automatic airborne detection)
- Comms/freq management intentionally out of scope per ROADMAP

## Testing
- pytest suite: 37 tests, Postgres required (`TEST_DATABASE_URL`)
- CI: GitHub Actions (postgres → pytest → npm build)

## Architecture invariants (don't break these)
- Three-layer backend: SQLAlchemy models -> Pydantic schemas -> FastAPI routes
- Business logic in app/services/
- Type hints everywhere; Pydantic v2 with ConfigDict(from_attributes=True)
- All datetimes UTC-stored
- Frontend: TypeScript strict, useQuery patterns established in v1
- Status colors: green good / yellow warning / red action needed