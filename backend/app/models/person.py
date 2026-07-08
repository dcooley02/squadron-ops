"""SQLAlchemy domain models — persons, qualifications, currencies."""
from __future__ import annotations

from sqlalchemy import (
    Column, Integer, String, Date, Float, Boolean,
    ForeignKey, Enum as SQLEnum, Text, JSON,
)
from sqlalchemy.orm import relationship

from app.database import Base
from app.models.enums import *  # noqa: F403

class Person(Base):
    """Anyone in the squadron with a login: pilots, aircrew, ops, maint, command."""
    __tablename__ = "persons"
    id = Column(Integer, primary_key=True)
    last_name = Column(String, nullable=False)
    first_name = Column(String, nullable=False)
    callsign = Column(String)
    rank = Column(String)
    role = Column(SQLEnum(Role), nullable=False)
    username = Column(String, unique=True, nullable=False, index=True)
    password_hash = Column(String, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)

    qualifications = relationship("Qualification", back_populates="person", cascade="all, delete-orphan")
    currencies = relationship("Currency", back_populates="person", cascade="all, delete-orphan")
    flight_logs = relationship("FlightLog", back_populates="person")
    safety_reports_filed = relationship("SafetyReport", back_populates="reported_by", foreign_keys="SafetyReport.reported_by_person_id")
    discrepancies_reported = relationship("Discrepancy", back_populates="reported_by", foreign_keys="Discrepancy.reported_by_person_id")
    gradecards = relationship("Gradecard", back_populates="person", foreign_keys="Gradecard.person_id")
    gradecards_instructed = relationship("Gradecard", back_populates="instructor", foreign_keys="Gradecard.instructor_person_id")

class Qualification(Base):
    """An earned qualification. Generally non-perishable (HAC, NVG-qual, FCP, NSI)."""
    __tablename__ = "qualifications"
    id = Column(Integer, primary_key=True)
    person_id = Column(Integer, ForeignKey("persons.id"), nullable=False, index=True)
    qual_code = Column(String, nullable=False)
    qualified_date = Column(Date)
    expires_date = Column(Date)
    notes = Column(Text)

    person = relationship("Person", back_populates="qualifications")

class Currency(Base):
    """A perishable currency. Updated whenever a qualifying event is flown."""
    __tablename__ = "currencies"
    id = Column(Integer, primary_key=True)
    person_id = Column(Integer, ForeignKey("persons.id"), nullable=False, index=True)
    currency_code = Column(String, nullable=False)
    last_event_date = Column(Date)
    expires_date = Column(Date)
    # Nullable: populated once migrated to table-driven model (Batch 4b+).
    # Legacy rows keep currency_code only; new rows will set both.
    currency_type_id = Column(Integer, ForeignKey("currency_types.id"), nullable=True, index=True)

    person = relationship("Person", back_populates="currencies")
    currency_type = relationship("CurrencyType", back_populates="currency_records")

# ---------- Wing Table B-2 currency type catalog ----------

class CurrencyType(Base):
    """One row per Wing Table B-2 currency definition."""
    __tablename__ = "currency_types"
    id = Column(Integer, primary_key=True)
    code = Column(String, unique=True, nullable=False, index=True)
    name = Column(String, nullable=False)
    periodicity_days = Column(Integer, nullable=False)
    requirement_text = Column(Text, nullable=False)
    description = Column(Text, nullable=True)
    sim_eligible = Column(Boolean, default=False, nullable=False)
    sim_notes = Column(Text, nullable=True)
    min_hours = Column(Float, nullable=True)
    min_count = Column(Integer, nullable=True)
    count_unit = Column(String, nullable=True)
    references = Column(JSON, nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)

    applicability = relationship("CurrencyApplicability", back_populates="currency_type", cascade="all, delete-orphan")
    currency_records = relationship("Currency", back_populates="currency_type")

class CurrencyApplicability(Base):
    """Which audience a CurrencyType applies to."""
    __tablename__ = "currency_applicabilities"
    id = Column(Integer, primary_key=True)
    currency_type_id = Column(Integer, ForeignKey("currency_types.id", ondelete="CASCADE"), nullable=False, index=True)
    applies_to = Column(SQLEnum(CurrencyAudience), nullable=False)
    required_qualification = Column(String, nullable=True)

    currency_type = relationship("CurrencyType", back_populates="applicability")

# ---------- Syllabus ----------

