"""SQLAlchemy domain models — sorties, flight logs, TMR, approaches."""
from __future__ import annotations

from sqlalchemy import (
    Column, Integer, String, DateTime, Float, Boolean,
    ForeignKey, Enum as SQLEnum, Text, UniqueConstraint,
)
from sqlalchemy.orm import relationship

from app.database import Base
from app.core.time import utc_now
from app.models.enums import *  # noqa: F403

class Sortie(Base):
    """A single flight: one aircraft, one set of times, possibly multiple crew."""
    __tablename__ = "sorties"
    id = Column(Integer, primary_key=True)
    event_code = Column(String)
    event_type = Column(String)
    aircraft_id = Column(Integer, ForeignKey("aircraft.id"), index=True)
    brief_time = Column(DateTime)
    takeoff_time = Column(DateTime)
    land_time = Column(DateTime)
    duration_hours = Column(Float, default=0.0)
    notes = Column(Text)
    is_complete = Column(Boolean, default=False, nullable=False)

    # New in flight-logging
    flight_mode = Column(SQLEnum(FlightMode), default=FlightMode.LIVE, nullable=False)
    debrief_notes = Column(Text, nullable=True)
    simulator_id = Column(String, nullable=True)

    # Activity quantity columns — populated at sortie completion; null = 0 in cascade math.
    rounds_fired_20mm      = Column(Integer, nullable=True)
    ugr_fired              = Column(Integer, nullable=True)
    csw_rounds             = Column(Integer, nullable=True)
    csw_rounds_night       = Column(Integer, nullable=True)
    landings_day           = Column(Integer, nullable=True)
    landings_night         = Column(Integer, nullable=True)
    landings_dve_day       = Column(Integer, nullable=True)
    landings_dve_night     = Column(Integer, nullable=True)
    hoist_streams          = Column(Integer, nullable=True)
    hoist_recoveries       = Column(Integer, nullable=True)
    amns_iterations        = Column(Integer, nullable=True)
    almds_hours            = Column(Float,   nullable=True)
    amns_ntrs              = Column(Integer, nullable=True)
    strafe_dry_profiles_day   = Column(Integer, nullable=True)
    strafe_dry_profiles_night = Column(Integer, nullable=True)

    # Logbook / NAVFLIR fields
    landings_shipboard_day   = Column(Integer, nullable=True)
    landings_shipboard_night = Column(Integer, nullable=True)
    departure_location = Column(String(16), nullable=True)   # ICAO code or hull number
    arrival_location   = Column(String(16), nullable=True)

    # SDO / day-of-ops (Phase 5)
    ops_status = Column(
        SQLEnum(SortieOpsStatus), default=SortieOpsStatus.PLANNED, nullable=False
    )
    mission_summary = Column(Text, nullable=True)
    comm_plan = Column(Text, nullable=True)
    brief_sheet_notes = Column(Text, nullable=True)
    schedule_publication_id = Column(
        Integer, ForeignKey("schedule_publications.id"), nullable=True, index=True
    )

    aircraft = relationship("Aircraft", back_populates="sorties")
    schedule_publication = relationship("SchedulePublication", back_populates="sorties")
    flight_logs = relationship("FlightLog", back_populates="sortie", cascade="all, delete-orphan")
    task_credits = relationship("SortieTaskCredit", back_populates="sortie", cascade="all, delete-orphan")
    safety_reports = relationship("SafetyReport", back_populates="sortie")
    discrepancies_filed = relationship("Discrepancy", back_populates="sortie", foreign_keys="Discrepancy.sortie_id")
    gradecards = relationship("Gradecard", back_populates="sortie")
    legs = relationship("SortieLeg", back_populates="sortie", cascade="all, delete-orphan", order_by="SortieLeg.leg_number")
    sortie_tmr_codes = relationship("SortieTmrCode", back_populates="sortie", cascade="all, delete-orphan")

class FlightLog(Base):
    """One person's record on one sortie. Multiple per sortie (one per crewmember)."""
    __tablename__ = "flight_logs"
    id = Column(Integer, primary_key=True)
    sortie_id = Column(Integer, ForeignKey("sorties.id"), nullable=False, index=True)
    person_id = Column(Integer, ForeignKey("persons.id"), nullable=False, index=True)
    crew_position = Column(SQLEnum(CrewPosition), nullable=False)
    hours_logged = Column(Float, default=0.0)
    syllabus_event_completed = Column(String)

    # New in flight-logging
    instructor_remarks = Column(Text, nullable=True)
    readiness_credits_count = Column(Integer, default=0, nullable=False)
    # CNAF M-3710.7 single-letter qualification code, attached per-flight
    crew_qual_code = Column(String(1), nullable=True)

    # Per-crewmember hour categories
    night_hours              = Column(Float, default=0.0, nullable=False)
    nvg_hours                = Column(Float, default=0.0, nullable=False)
    actual_instrument_hours  = Column(Float, default=0.0, nullable=False)   # actual IMC
    sim_instrument_hours     = Column(Float, default=0.0, nullable=False)   # safety-pilot / TOFT
    # Role hours (CNAF M-3710.7 categories)
    total_hours              = Column(Float, default=0.0, nullable=True)
    first_pilot_hours        = Column(Float, default=0.0, nullable=True)
    copilot_hours            = Column(Float, default=0.0, nullable=True)
    ac_commander_hours       = Column(Float, default=0.0, nullable=True)
    mission_commander_hours  = Column(Float, default=0.0, nullable=True)
    instructor_hours         = Column(Float, default=0.0, nullable=True)
    # NVG sub-categories
    nvg_unaided_hl_hours     = Column(Float, default=0.0, nullable=True)
    nvg_unaided_ll_hours     = Column(Float, default=0.0, nullable=True)
    nvg_tactical_hl_hours    = Column(Float, default=0.0, nullable=True)
    nvg_tactical_ll_hours    = Column(Float, default=0.0, nullable=True)
    # Logbook / NAVFLIR fields
    special_crew_time_hours  = Column(Float, default=0.0, nullable=False)   # maps to 3710.7 "Spec Crw" / SCT
    data_provenance = Column(SQLEnum(DataProvenance), default=DataProvenance.ENTERED, nullable=False)
    # Per-crewmember landings (B1). Sortie-level columns remain as the rollup.
    landings_day              = Column(Integer, default=0, nullable=False)
    landings_night            = Column(Integer, default=0, nullable=False)
    landings_dve_day          = Column(Integer, default=0, nullable=False)
    landings_dve_night        = Column(Integer, default=0, nullable=False)
    landings_shipboard_day    = Column(Integer, default=0, nullable=False)
    landings_shipboard_night  = Column(Integer, default=0, nullable=False)

    sortie = relationship("Sortie", back_populates="flight_logs")
    person = relationship("Person", back_populates="flight_logs")
    task_credits = relationship("SortieTaskCredit", back_populates="flight_log", cascade="all, delete-orphan")
    gradecards = relationship("Gradecard", back_populates="flight_log")
    instrument_approaches = relationship("InstrumentApproach", back_populates="flight_log", cascade="all, delete-orphan")

# ---------- CBR task credits ----------

class SortieTaskCredit(Base):
    """Records that a person was graded on a CBR task during a sortie."""
    __tablename__ = "sortie_task_credits"
    __table_args__ = (
        UniqueConstraint("flight_log_id", "task_code", name="uq_credit_log_task"),
    )

    id = Column(Integer, primary_key=True)
    sortie_id = Column(Integer, ForeignKey("sorties.id"), nullable=False, index=True)
    flight_log_id = Column(Integer, ForeignKey("flight_logs.id"), nullable=False, index=True)
    task_code = Column(String, nullable=False)
    grade = Column(SQLEnum(TaskGrade), nullable=True)
    remarks = Column(Text, nullable=True)
    created_at = Column(DateTime, default=utc_now, nullable=False)

    sortie = relationship("Sortie", back_populates="task_credits")
    flight_log = relationship("FlightLog", back_populates="task_credits")

# ---------- Safety ----------

class SafetyReport(Base):
    """A safety observation, hazard, incident, or mishap report."""
    __tablename__ = "safety_reports"
    id = Column(Integer, primary_key=True)
    sortie_id = Column(Integer, ForeignKey("sorties.id"), nullable=True, index=True)
    reported_by_person_id = Column(Integer, ForeignKey("persons.id"), nullable=False)
    severity = Column(String, nullable=False)           # INFO / HAZARD / INCIDENT / MISHAP
    category = Column(String, nullable=True)            # FOD / BIRDSTRIKE / AIRCRAFT_SYSTEM / PROCEDURAL / ORM / OTHER
    description = Column(Text, nullable=False)
    actions_taken = Column(Text, nullable=True)
    status = Column(String, default="OPEN", nullable=False)   # OPEN / UNDER_REVIEW / CLOSED
    created_at = Column(DateTime, default=utc_now, nullable=False)
    closed_at = Column(DateTime, nullable=True)

    sortie = relationship("Sortie", back_populates="safety_reports")
    reported_by = relationship("Person", back_populates="safety_reports_filed", foreign_keys=[reported_by_person_id])

# ---------- Maintenance ----------

class SortieLeg(Base):
    """One routing leg of a sortie. Only created when the sortie visits multiple locations."""
    __tablename__ = "sortie_legs"
    __table_args__ = (
        UniqueConstraint("sortie_id", "leg_number", name="uq_sortie_leg_number"),
    )

    id = Column(Integer, primary_key=True)
    sortie_id = Column(Integer, ForeignKey("sorties.id"), nullable=False, index=True)
    leg_number = Column(Integer, nullable=False)
    departure_location = Column(String(16), nullable=False)   # ICAO code or hull number (e.g. CVN-71)
    arrival_location = Column(String(16), nullable=False)
    takeoff_time = Column(DateTime, nullable=True)
    land_time = Column(DateTime, nullable=True)
    duration_hours = Column(Float, nullable=True)

    sortie = relationship("Sortie", back_populates="legs")

# ---------- Instrument approaches (per-pilot per-sortie) ----------

class InstrumentApproach(Base):
    """One instrument approach logged by one crewmember on one sortie."""
    __tablename__ = "instrument_approaches"

    id = Column(Integer, primary_key=True)
    flight_log_id = Column(Integer, ForeignKey("flight_logs.id"), nullable=False, index=True)
    sortie_id = Column(Integer, ForeignKey("sorties.id"), nullable=False, index=True)
    approach_type = Column(SQLEnum(ApproachType), nullable=False)
    actual_or_simulated = Column(SQLEnum(ApproachConditions), nullable=False)
    airport_icao = Column(String(16), nullable=False)
    runway = Column(String(10), nullable=True)
    remarks = Column(Text, nullable=True)
    logged_at = Column(DateTime, default=utc_now, nullable=False)

    flight_log = relationship("FlightLog", back_populates="instrument_approaches")
    sortie = relationship("Sortie")

# ---------- TMR (Training and Readiness) code catalog ----------

class TmrCode(Base):
    """CNAF M-3710.7 Appendix D Training and Readiness Matrix code definition."""
    __tablename__ = "tmr_codes"

    id = Column(Integer, primary_key=True)
    code = Column(String(4), unique=True, nullable=False, index=True)  # e.g. "1A1"
    fpc = Column(String(1), nullable=False)    # Functional Performance Code
    gpc = Column(String(1), nullable=False)    # Grouping Performance Code
    spc = Column(String(1), nullable=False)    # Sub-grouping Performance Code
    description = Column(String, nullable=False)
    capability_area = Column(SQLEnum(CapabilityArea), nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)

class SortieTmrCode(Base):
    """Junction: TMR codes logged for a sortie (up to 3 slots per CNAF M-3710.7 Appendix D)."""
    __tablename__ = "sortie_tmr_codes"

    id = Column(Integer, primary_key=True)
    sortie_id = Column(Integer, ForeignKey("sorties.id"), nullable=False, index=True)
    tmr_code_id = Column(Integer, ForeignKey("tmr_codes.id"), nullable=False, index=True)
    slot = Column(Integer, nullable=False)   # MSN slot: 1, 2, or 3
    hours = Column(Float, nullable=True)

    sortie = relationship("Sortie", back_populates="sortie_tmr_codes")
    tmr_code = relationship("TmrCode")

# ---------- Training boards (Phase 4) ----------

