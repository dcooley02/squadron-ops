"""SQLAlchemy domain models — syllabus events and gradecards."""
from __future__ import annotations

from sqlalchemy import (
    Column, Integer, String, DateTime, Date, Float, Boolean,
    ForeignKey, Enum as SQLEnum, Text, JSON,
)
from sqlalchemy.orm import relationship

from app.database import Base
from app.core.time import utc_now
from app.models.enums import *  # noqa: F403

class SyllabusEvent(Base):
    """A T&R / SWTP syllabus event definition."""
    __tablename__ = "syllabus_events"
    id = Column(Integer, primary_key=True)
    code = Column(String, unique=True, nullable=False, index=True)
    name = Column(String, nullable=False)
    stage_legacy = Column(String)       # legacy placeholder value; renamed from 'stage'
    prerequisites = Column(String)
    description = Column(Text)

    # SWTP extensions — all nullable for backward compat with existing seed rows
    level = Column(SQLEnum(SyllabusLevel, values_callable=lambda x: [e.value for e in x]), nullable=True)
    stage = Column(SQLEnum(SyllabusStage), nullable=True)
    series = Column(Integer, nullable=True)
    track = Column(SQLEnum(SyllabusTrack), nullable=True)
    event_code = Column(String, nullable=True, index=True)
    min_instructor_level = Column(Integer, nullable=True)
    aircraft_or_sim = Column(SQLEnum(EventVenue), nullable=True)
    time_hours = Column(Float, nullable=True)
    is_stan_eval = Column(Boolean, default=False, nullable=False)
    grading_scheme = Column(SQLEnum(GradingScheme), nullable=True)
    prerequisites_text = Column(Text, nullable=True)
    force_composition = Column(Text, nullable=True)
    recommended_soe = Column(Text, nullable=True)
    unsat_criteria = Column(Text, nullable=True)
    references = Column(JSON, nullable=True)

    line_items = relationship("GradecardLineItem", back_populates="syllabus_event", cascade="all, delete-orphan")
    gradecards = relationship("Gradecard", back_populates="syllabus_event")

# ---------- CBR Task Option library ----------

class GradecardLineItem(Base):
    """Template row for one graded line item on a syllabus event's gradecard."""
    __tablename__ = "gradecard_line_items"
    id = Column(Integer, primary_key=True)
    syllabus_event_id = Column(Integer, ForeignKey("syllabus_events.id"), nullable=False, index=True)
    section = Column(SQLEnum(GradecardSection), nullable=False)
    item_name = Column(String, nullable=False)
    role = Column(SQLEnum(LineItemRole), nullable=False)
    is_critical = Column(Boolean, default=False, nullable=False)   # asterisk in PDF
    is_required = Column(Boolean, default=True, nullable=False)    # bold text in PDF
    display_order = Column(Integer, nullable=False)
    mop_below_standard = Column(Text, nullable=True)
    mop_standard = Column(Text, nullable=True)

    syllabus_event = relationship("SyllabusEvent", back_populates="line_items")
    results = relationship("GradecardLineItemResult", back_populates="line_item")

# ---------- Gradecard instances ----------

class Gradecard(Base):
    """A filled-out gradecard instance: one person, one sortie, one event."""
    __tablename__ = "gradecards"
    id = Column(Integer, primary_key=True)
    person_id = Column(Integer, ForeignKey("persons.id"), nullable=False, index=True)
    syllabus_event_id = Column(Integer, ForeignKey("syllabus_events.id"), nullable=False, index=True)
    sortie_id = Column(Integer, ForeignKey("sorties.id"), nullable=True, index=True)
    flight_log_id = Column(Integer, ForeignKey("flight_logs.id"), nullable=True, index=True)
    instructor_person_id = Column(Integer, ForeignKey("persons.id"), nullable=True)
    card_date = Column(Date, nullable=False)
    grading_scheme = Column(SQLEnum(GradingScheme), nullable=False)
    overall_status = Column(SQLEnum(GradecardStatus), nullable=False)
    remarks = Column(Text, nullable=True)
    created_at = Column(DateTime, default=utc_now, nullable=False)
    updated_at = Column(DateTime, default=utc_now, onupdate=utc_now, nullable=False)

    person = relationship("Person", back_populates="gradecards", foreign_keys=[person_id])
    instructor = relationship("Person", back_populates="gradecards_instructed", foreign_keys=[instructor_person_id])
    syllabus_event = relationship("SyllabusEvent", back_populates="gradecards")
    sortie = relationship("Sortie", back_populates="gradecards")
    flight_log = relationship("FlightLog", back_populates="gradecards")
    line_item_results = relationship("GradecardLineItemResult", back_populates="gradecard", cascade="all, delete-orphan")

class GradecardLineItemResult(Base):
    """One scored result row per line item on a Gradecard instance."""
    __tablename__ = "gradecard_line_item_results"
    id = Column(Integer, primary_key=True)
    gradecard_id = Column(Integer, ForeignKey("gradecards.id", ondelete="CASCADE"), nullable=False, index=True)
    line_item_id = Column(Integer, ForeignKey("gradecard_line_items.id"), nullable=False, index=True)
    waived = Column(Boolean, default=False, nullable=False)
    completion_status = Column(SQLEnum(CompletionStatus), nullable=True)
    four_tier_score = Column(SQLEnum(FourTierScore), nullable=True)
    remarks = Column(Text, nullable=True)

    gradecard = relationship("Gradecard", back_populates="line_item_results")
    line_item = relationship("GradecardLineItem", back_populates="results")

# ---------- Multi-leg sortie routing ----------

