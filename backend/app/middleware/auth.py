"""JWT gate for /api/* routes (login and docs excluded)."""
from __future__ import annotations

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse

from app.core.deps import bearer_user_id

_PUBLIC_PREFIXES = (
    "/health",
    "/docs",
    "/openapi.json",
    "/redoc",
    "/api/auth/login",
)


class AuthMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        if request.method == "OPTIONS":
            return await call_next(request)

        path = request.url.path
        if not path.startswith("/api/") or any(path.startswith(p) for p in _PUBLIC_PREFIXES):
            return await call_next(request)

        user_id = bearer_user_id(request.headers.get("Authorization"))
        if user_id is None:
            return JSONResponse(status_code=401, content={"detail": "Not authenticated"})

        request.state.user_id = user_id
        auth = request.headers.get("Authorization", "")
        if auth.startswith("Bearer "):
            from jose import JWTError
            from app.core.security import decode_access_token

            try:
                payload = decode_access_token(auth[7:])
                request.state.username = payload.get("username")
            except JWTError:
                request.state.username = None

        return await call_next(request)