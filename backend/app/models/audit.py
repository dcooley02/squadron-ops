"""SQLAlchemy domain models — audit log."""
from __future__ import annotations

from sqlalchemy import (
    Column, Integer, String, DateTime,
)
from sqlalchemy.dialects.postgresql import JSONB

from app.database import Base
from app.core.time import utc_now
from app.models.enums import *  # noqa: F403

class AuditLog(Base):
    """Append-only record of every state-changing API call."""
    __tablename__ = "audit_log"
    id = Column(Integer, primary_key=True)
    ts = Column(DateTime, default=utc_now, nullable=False, index=True)
    actor = Column(String(120), nullable=True)
    method = Column(String(8), nullable=False)
    path = Column(String(512), nullable=False, index=True)
    query_string = Column(String(512), nullable=True)
    response_status = Column(Integer, nullable=False)
    request_body = Column(JSONB, nullable=True)
    client_host = Column(String(64), nullable=True)
    duration_ms = Column(Integer, nullable=True)

