# Optional OpenAPI → TypeScript type generation

Hand-maintained types live in `src/lib/api/types.ts` (kept in sync with backend
Pydantic schemas). Automated generation is optional for larger schema churn.

## Prerequisites

- Backend running locally (`uvicorn` on `:8001`)
- Node 20+

## One-shot generation

```bash
# From frontend/
npx --yes openapi-typescript http://localhost:8001/openapi.json -o src/lib/api/generated.d.ts
```

Review `generated.d.ts` and promote stable models into `types.ts` (or re-export
from domain modules). Do **not** replace the hand-written client functions
automatically — OpenAPI paths still need thin wrappers for auth headers and
error handling.

## CI note

Generation is not gated in CI (requires a live API). Prefer updating
`types.ts` in the same PR as backend schema changes.
