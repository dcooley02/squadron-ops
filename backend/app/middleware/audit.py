"""ASGI middleware that records every state-changing API call to the
audit_log table.

State-changing = POST / PUT / PATCH / DELETE. GETs are skipped because they
are read-only and would dominate the table without adding accountability.

Request bodies are captured as JSON when the content-type is JSON and the
payload is under ~4KB. Larger or binary bodies are recorded as a small
{"_truncated": true, "_size": N} sentinel.
"""
from __future__ import annotations

import json
import time
from typing import Any

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

from app.database import SessionLocal
from app.models.models import AuditLog


_AUDITED_METHODS = {"POST", "PUT", "PATCH", "DELETE"}
_MAX_BODY_BYTES = 4096
_AUDIT_PATH_EXCLUDES = ("/health", "/openapi.json", "/docs")


class AuditLogMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        method = request.method.upper()
        path = request.url.path
        skip = (
            method not in _AUDITED_METHODS
            or any(path.startswith(p) for p in _AUDIT_PATH_EXCLUDES)
        )

        body_json: Any = None
        if not skip:
            raw_body = await request.body()
            if raw_body:
                if len(raw_body) > _MAX_BODY_BYTES:
                    body_json = {"_truncated": True, "_size": len(raw_body)}
                else:
                    content_type = request.headers.get("content-type", "")
                    if "application/json" in content_type:
                        try:
                            body_json = json.loads(raw_body)
                        except json.JSONDecodeError:
                            body_json = {"_unparsed": True, "_size": len(raw_body)}
                    else:
                        body_json = {"_non_json": True, "_size": len(raw_body)}

            # We've consumed the body — restore it so downstream handlers can read.
            async def receive() -> dict:
                return {"type": "http.request", "body": raw_body, "more_body": False}

            request = Request(request.scope, receive=receive)

        start = time.perf_counter()
        response: Response = await call_next(request)
        elapsed_ms = int((time.perf_counter() - start) * 1000)

        if not skip:
            try:
                db = SessionLocal()
                db.add(AuditLog(
                    actor=None,  # B6 will set this from the authenticated user
                    method=method,
                    path=path,
                    query_string=request.url.query or None,
                    response_status=response.status_code,
                    request_body=body_json,
                    client_host=request.client.host if request.client else None,
                    duration_ms=elapsed_ms,
                ))
                db.commit()
            except Exception:
                # Audit logging must never break a real request — swallow.
                db.rollback()
            finally:
                db.close()

        return response
