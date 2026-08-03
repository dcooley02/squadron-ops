import os
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from app.api import (
    persons,
    aircraft,
    sorties,
    dashboard,
    scheduling,
    logging as flight_logging,
    syllabus,
    currency,
    maintenance,
    tmr_codes,
    audit,
    readiness,
    boards,
    ops,
    auth,
)
from app.middleware.audit import AuditLogMiddleware
from app.middleware.auth import AuthMiddleware

app = FastAPI(title="HSC Squadron Ops")

# Local Vite defaults + optional comma-separated CORS_ORIGINS env (Tailscale dual-port, etc.).
_CORS_ORIGINS = [
    "http://localhost:5173",
    "http://localhost:5174",
    "http://127.0.0.1:5173",
    "http://127.0.0.1:5174",
]
_extra = os.getenv("CORS_ORIGINS", "").strip()
if _extra:
    for origin in _extra.split(","):
        origin = origin.strip()
        if origin and origin not in _CORS_ORIGINS:
            _CORS_ORIGINS.append(origin)

app.add_middleware(
    CORSMiddleware,
    allow_origins=_CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.add_middleware(AuditLogMiddleware)
app.add_middleware(AuthMiddleware)

# Routers
app.include_router(auth.router)
app.include_router(persons.router)
app.include_router(aircraft.router)
app.include_router(sorties.router)
app.include_router(dashboard.router)
app.include_router(scheduling.router)
app.include_router(flight_logging.router)
app.include_router(syllabus.router)
app.include_router(currency.router)
app.include_router(maintenance.router)
app.include_router(tmr_codes.router)
app.include_router(audit.router)
app.include_router(readiness.router)
app.include_router(boards.router)
app.include_router(ops.router)


@app.get("/health")
def health():
    return {"status": "ok"}


# Optional SPA host (Pi deploy): set SQUADRON_OPS_STATIC_DIR to frontend/dist.
# Same-origin: build SPA with VITE_API_BASE_URL= (empty) so /api/* hits this process.
_static_dir = os.getenv("SQUADRON_OPS_STATIC_DIR", "").strip()
if _static_dir:
    _spa_root = Path(_static_dir).resolve()
    if _spa_root.is_dir():
        _assets = _spa_root / "assets"
        if _assets.is_dir():
            app.mount("/assets", StaticFiles(directory=str(_assets)), name="spa-assets")

        @app.get("/{full_path:path}")
        async def spa_fallback(full_path: str):
            """Serve built Vite files; fall back to index.html for client routes."""
            if full_path.startswith("api/") or full_path in (
                "docs",
                "openapi.json",
                "redoc",
                "health",
            ):
                raise HTTPException(status_code=404, detail="Not found")
            candidate = (_spa_root / full_path).resolve()
            try:
                candidate.relative_to(_spa_root)
            except ValueError as exc:
                raise HTTPException(status_code=404, detail="Not found") from exc
            if full_path and candidate.is_file():
                return FileResponse(candidate)
            index = _spa_root / "index.html"
            if index.is_file():
                return FileResponse(index)
            raise HTTPException(status_code=404, detail="SPA not built")
