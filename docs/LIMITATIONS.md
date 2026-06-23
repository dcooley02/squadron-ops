# Known Limitations

Squadron Ops is a portfolio demonstration platform. The following limitations are intentional or planned for future releases.

---

## Authentication & access control

- JWT login is required for API access
- Demonstration build grants full navigation and write access to all authenticated users
- Production role-based access control (per-route permissions) is not yet enforced
- Password reset is not implemented
- Demo password (`demo1234`) is for local use only

---

## Readiness (WTM)

- T-ratings use table-driven anchor tasks and simplified Appendix D math
- CBR task library contains 61 seeded tasks — full Enclosure 2 parity is planned
- Hand verification against CHSCWPINST 3500.1F is recommended before operational claims

---

## Maintenance

- 4790-inspired MAF/work order chain, logbook, and forecasting are implemented
- Full configuration management (TD compliance, serial-tracked equipment) is deferred

---

## Scheduling

- Crew ranking and week proposals use transparent heuristics, not optimization
- Human-in-the-loop only — no automatic schedule publish
- SDO ops status is manually advanced (no automatic airborne detection)
- Communications and frequency management are out of scope

---

## PDF exports

- Require WeasyPrint installed in the backend environment
- Returns HTTP 503 with guidance when WeasyPrint is unavailable

---

## Technical notes

- HSC-specific syllabus and currency catalog (community templates planned)
- `datetime.utcnow()` deprecation warnings in seed data scripts
- Automated test suite: 37 integration tests (PostgreSQL required)
- CI: GitHub Actions (postgres → pytest → frontend build)

---

## Architecture invariants

When extending this codebase:

- Three-layer backend: SQLAlchemy models → Pydantic schemas → FastAPI routes
- Business logic in `app/services/`, not route handlers
- Type hints throughout; Pydantic v2 with `ConfigDict(from_attributes=True)`
- All timestamps UTC-stored
- Frontend: TypeScript strict mode, TanStack Query for data fetching
- Status colors: green (good) · yellow (warning) · red (action required)

See [ROADMAP.md](../ROADMAP.md) for planned capabilities.