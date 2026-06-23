"""Read-only access to the audit log."""
from datetime import datetime
from typing import List, Optional

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel, ConfigDict
from sqlalchemy import desc
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.models import AuditLog


router = APIRouter(prefix="/api/audit", tags=["audit"])


class AuditLogOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    ts: datetime
    actor: Optional[str] = None
    method: str
    path: str
    query_string: Optional[str] = None
    response_status: int
    request_body: Optional[dict | list] = None
    client_host: Optional[str] = None
    duration_ms: Optional[int] = None


@router.get("", response_model=List[AuditLogOut])
def list_audit_log(
    method: Optional[str] = Query(None, description="POST/PUT/PATCH/DELETE"),
    path_contains: Optional[str] = Query(None),
    limit: int = Query(100, ge=1, le=500),
    db: Session = Depends(get_db),
):
    q = db.query(AuditLog)
    if method:
        q = q.filter(AuditLog.method == method.upper())
    if path_contains:
        q = q.filter(AuditLog.path.contains(path_contains))
    return q.order_by(desc(AuditLog.ts)).limit(limit).all()
