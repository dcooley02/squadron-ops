# Known Limitations

Squadron Ops is a portfolio demonstration platform. The following limitations are intentional, known risks, or planned for future releases. See [ROADMAP.md](../ROADMAP.md) for phased remediation.

---

## Authentication & access control

- JWT login is required for all `/api/*` routes (except login and OpenAPI docs)
- **RBAC is enforced** on routes that declare `require_roles(...)` (ADMIN always allowed)
- Open ACL for demos: set `DEMO_OPEN_RBAC=true` (API) and `VITE_DEMO_OPEN_RBAC=true` (SPA)
- Frontend nav and sensitive routes (`/ops`, `/schedule`, `/admin`) are role-gated unless open-ACL mode is on
- Not every write route is fully role-scoped yet (e.g. sortie complete is any authenticated user) — expand as product needs demand
- Admin “password reset” sets the person to the configured demo password — not a real recovery flow
- Demo password (`demo1234`) and default JWT secret are for local use only; never deploy with repository defaults
- Setting `ENVIRONMENT=production` refuses the demo JWT secret and refuses `DEMO_OPEN_RBAC=true` (startup ValidationError)
- Password reset as a product feature is not implemented

---

## Flight completion integrity

- Sortie complete takes `SELECT … FOR UPDATE` on the sortie (and aircraft for LIVE hour increments)
- Unknown TMR codes, unknown CBR task codes, and task-credit person IDs not on the sortie return **400**
- Per-crew landings are supported on Complete Sortie; if left blank, legacy sortie-level landings still mirror to HAC
- HTTP 500 on complete no longer echoes raw exception text

---

## Readiness (WTM)

- T-ratings use table-driven anchor tasks and simplified Appendix D math
- CBR task library is an **Enclosure 2-shaped** HSC demo catalog (92 tasks / 13 anchors in `app/catalogs/cbr_enclosure2.py`) — not a verbatim CHSCWPINST 3500.1F extract
- Hand verification against the live Wing Training Manual is still required before any operational claim

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
- Timestamps use `app.core.time.utc_now()` (naive UTC wall clock for TIMESTAMP WITHOUT TIME ZONE); prefer this over deprecated `datetime.utcnow()`
- Frontend API base URL defaults to `http://localhost:8001`; override with `VITE_API_BASE_URL` (see `frontend/.env.example`)
- Demo seed lives in `backend/seed/` package (shim `backend/seed.py` → `seed.run.main()`); Complete Sortie and Aircraft Maintenance are thin shells with panels under `completeSortie/` and `aircraftMaintenance/` (Phase E). Large service/catalog modules (`flight_completion`, `cbr_enclosure2`, `scheduling`) remain intentional
- Transaction ownership: domain services flush; routes commit (Phase B) — audit middleware still owns its own session
- Frontend unit tests are smoke-level (Vitest); no browser e2e suite yet
- Automated backend suite: **54** pytest integration tests (PostgreSQL required on port 5433)
- Tests fail hard if Docker/Postgres is not running — use `./scripts/verify.sh` or `docker compose up -d`
- CI: GitHub Actions (Postgres → pytest → frontend lint → FE unit test → build)

---

## Architecture invariants

When extending this codebase:

- Three-layer backend: SQLAlchemy models → Pydantic schemas → FastAPI routes
- Business logic in `app/services/`, not route handlers
- Type hints throughout; Pydantic v2 with `ConfigDict(from_attributes=True)`
- All timestamps UTC-stored (prefer aware UTC going forward)
- Frontend: TypeScript strict mode, TanStack Query for data fetching
- Status colors: green (good) · yellow (warning) · red (action required)
- Prefer `joinedload` / `selectinload` for relationship-heavy reads (avoid N+1)

See [ROADMAP.md](../ROADMAP.md) for engineering phases (A–F) and domain build order. Structure map: [MODULE_MAP.md](MODULE_MAP.md).

---

*Last updated: August 2026*
