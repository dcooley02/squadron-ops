# squadron-ops — Known Issues & Notes

This project forked from hsc-squadron-ops at v1.0-demo on 2026-05-11.
The v1 demo is preserved at https://github.com/dcooley02/hsc-squadron-ops
(tagged v1.0-demo). This is v2: expanded scope, demo-first development
order.

## Active scope
See ROADMAP.md for capabilities and ordering.

## Carried-over technical debt from v1
- LOW papercuts deferred: crew header filter count, donut tooltip,
  sortie year display, 41 N+1 gradecard fetches on Readiness Board
- datetime.utcnow() deprecation warnings in seed.py (3 instances)
- HSC-specific syllabus and currency catalog (will be replaced by
  per-community templates in roadmap item 6)

## Architecture invariants (don't break these)
- Three-layer backend: SQLAlchemy models -> Pydantic schemas -> FastAPI routes
- Business logic in app/services/
- Type hints everywhere; Pydantic v2 with ConfigDict(from_attributes=True)
- All datetimes UTC-stored
- Frontend: TypeScript strict, useQuery patterns established in v1
- Status colors: green good / yellow warning / red action needed
