"""SQLAlchemy domain models — WTM / CBR readiness catalog."""
from __future__ import annotations

from sqlalchemy import (
    Column, Integer, String, Float, Boolean,
    Enum as SQLEnum, Text, JSON,
)

from app.database import Base
from app.models.enums import *  # noqa: F403

class CapabilityAreaConfig(Base):
    """Per-area WTM T-rating thresholds and currency gates (Appendix D)."""
    __tablename__ = "capability_area_configs"
    capability_area = Column(SQLEnum(CapabilityArea), primary_key=True)
    label = Column(String(80), nullable=False)
    t1_recency_days = Column(Integer, default=180, nullable=False)
    t2_recency_days = Column(Integer, default=365, nullable=False)
    currency_codes = Column(JSON, default=list, nullable=False)
    min_qual_codes = Column(JSON, default=list, nullable=False)

class CbrTaskOption(Base):
    """WTM Capability-Based Readiness task option library."""
    __tablename__ = "cbr_task_options"
    id = Column(Integer, primary_key=True)
    code = Column(String, unique=True, nullable=False, index=True)
    capability_area = Column(SQLEnum(CapabilityArea), nullable=False)
    description = Column(String, nullable=False)
    crew_scope = Column(SQLEnum(CrewScope), nullable=False)
    sim_eligible = Column(Boolean, default=False, nullable=False)
    is_anchor_task = Column(Boolean, default=False, nullable=False)
    parent_code = Column(String, nullable=True)
    confers_codes = Column(JSON, default=list, nullable=True)
    min_time_hours = Column(Float, default=0.5, nullable=False)
    recommended_min_hours = Column(Float, nullable=True)
    recommended_max_hours = Column(Float, nullable=True)
    moe_notes = Column(Text, nullable=True)
    mop_notes = Column(Text, nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)

# ---------- Flight operations ----------

