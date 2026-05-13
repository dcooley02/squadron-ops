from sqlalchemy import (
    Column, Integer, String, DateTime, Date, Float, Boolean,
    ForeignKey, Enum as SQLEnum, Text, JSON, UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import relationship
from datetime import datetime
import enum
from app.database import Base


# ---------- Enums ----------

class Role(str, enum.Enum):
    PILOT = "pilot"
    AIRCREW = "aircrew"
    SDO = "sdo"
    TRAINING_O = "training_officer"
    MAINT_CONTROL = "maint_control"
    CO_XO = "co_xo"
    ADMIN = "admin"


class CrewPosition(str, enum.Enum):
    HAC = "HAC"            # Helicopter Aircraft Commander
    H2P = "H2P"            # Qualified 2nd Pilot
    H2P_U = "H2P_U"        # Unqualified 2P / under instruction
    CREW_CHIEF = "CREW_CHIEF"
    AIRCREW = "AIRCREW"
    AWS = "AWS"            # Aviation Warfare Systems Operator


class AircraftStatus(str, enum.Enum):
    FMC = "FMC"            # Fully Mission Capable
    PMC = "PMC"            # Partially Mission Capable
    NMC = "NMC"            # Non-Mission Capable (general)
    NMCM = "NMCM"          # NMC for Maintenance
    NMCS = "NMCS"          # NMC for Supply


class DiscrepancySeverity(str, enum.Enum):
    MINOR = "MINOR"
    MAJOR = "MAJOR"
    DOWNING = "DOWNING"


class DiscrepancyWorkStatus(str, enum.Enum):
    OPEN      = "OPEN"
    IN_WORK   = "IN_WORK"
    AWP       = "AWP"        # Awaiting Parts
    AWM       = "AWM"        # Awaiting Maintenance
    COMPLETED = "COMPLETED"
    CLOSED    = "CLOSED"


class FlightMode(str, enum.Enum):
    LIVE = "LIVE"
    SIM_TOFT = "SIM_TOFT"


class CapabilityArea(str, enum.Enum):
    MOB = "MOB"    # Mobility
    FSO = "FSO"    # Fleet Support Operations
    ASU = "ASU"    # Anti-Surface Warfare
    SOF = "SOF"    # Special Operations Forces
    PR  = "PR"     # Personnel Recovery
    STW = "STW"    # Strike Warfare
    LOG = "LOG"    # Logistics
    MIW = "MIW"    # Mine Warfare


class TaskGrade(str, enum.Enum):
    Q  = "Q"    # Qualified
    CQ = "CQ"   # Conditionally Qualified
    U  = "U"    # Unqualified
    NO = "NO"   # Not Observed / Not Performed
    NG = "NG"   # No Grade / Not Applicable


class CrewScope(str, enum.Enum):
    INDIVIDUAL = "INDIVIDUAL"  # only the performing aircrew member logs
    CREW       = "CREW"        # whole crew logs


# ---------- Syllabus / gradecard enums ----------

class SyllabusLevel(str, enum.Enum):
    L2 = "2"
    L3 = "3"
    L4 = "4"
    L5 = "5"


class SyllabusStage(str, enum.Enum):
    INTRO      = "INTRO"
    ASU        = "ASU"
    CSAR       = "CSAR"
    SOF_LOG    = "SOF_LOG"
    STAN_EVAL  = "STAN_EVAL"
    AMCM_INTRO = "AMCM_INTRO"
    ALMDS      = "ALMDS"
    AMNS       = "AMNS"


class SyllabusTrack(str, enum.Enum):
    PILOT_CORE   = "PILOT_CORE"
    PILOT_AMCM   = "PILOT_AMCM"
    AIRCREW_CORE = "AIRCREW_CORE"
    AIRCREW_AMCM = "AIRCREW_AMCM"


class EventVenue(str, enum.Enum):
    AIRCRAFT = "AIRCRAFT"
    TOFT     = "TOFT"
    LAB      = "LAB"
    BOARD    = "BOARD"


class GradingScheme(str, enum.Enum):
    COMPLETION = "COMPLETION"
    FOUR_TIER  = "FOUR_TIER"


class GradecardSection(str, enum.Enum):
    PLANNING_BRIEFING    = "PLANNING_BRIEFING"
    PRELAUNCH            = "PRELAUNCH"
    ENROUTE              = "ENROUTE"
    EXECUTION            = "EXECUTION"
    COMMUNICATION        = "COMMUNICATION"
    GENERAL_FLIGHT_CONDUCT = "GENERAL_FLIGHT_CONDUCT"
    DEBRIEF              = "DEBRIEF"


class LineItemRole(str, enum.Enum):
    D = "D"   # Demonstrate
    I = "I"   # Instruct/Introduce
    P = "P"   # Perform


class GradecardStatus(str, enum.Enum):
    COMPLETE         = "COMPLETE"
    INCOMPLETE       = "INCOMPLETE"
    PASS             = "PASS"
    CONDITIONAL_PASS = "CONDITIONAL_PASS"
    UNSAT            = "UNSAT"
    IN_PROGRESS      = "IN_PROGRESS"


class CompletionStatus(str, enum.Enum):
    COMPLETE   = "COMPLETE"
    INCOMPLETE = "INCOMPLETE"


class FourTierScore(str, enum.Enum):
    UNSAT_1_0          = "UNSAT_1_0"
    BELOW_STANDARD_2_0 = "BELOW_STANDARD_2_0"
    STANDARD_3_0       = "STANDARD_3_0"
    EXCEPTIONAL_4_0    = "EXCEPTIONAL_4_0"


class CurrencyAudience(str, enum.Enum):
    ALL_PILOTS        = "ALL_PILOTS"
    HAC_ONLY          = "HAC_ONLY"
    AMCM_QUAL_PILOTS  = "AMCM_QUAL_PILOTS"
    ALL_AIRCREWMEN    = "ALL_AIRCREWMEN"
    AWS_ONLY          = "AWS_ONLY"
    HOIST_OP_QUAL     = "HOIST_OP_QUAL"


class ApproachType(str, enum.Enum):
    ILS     = "ILS"
    GPS     = "GPS"
    RNAV    = "RNAV"
    TACAN   = "TACAN"
    VOR     = "VOR"
    PAR     = "PAR"
    ASR     = "ASR"
    ENROUTE = "ENROUTE"


class ApproachConditions(str, enum.Enum):
    ACTUAL    = "ACTUAL"
    SIMULATED = "SIMULATED"


class DataProvenance(str, enum.Enum):
    ENTERED             = "ENTERED"              # pilot/crew entered at debrief
    BACKFILLED          = "BACKFILLED"           # migrated from sortie-level aggregate
    SYSTEM_CALCULATED   = "SYSTEM_CALCULATED"    # computed by system (e.g. proportional split)


# ---------- Core entities ----------

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


class Aircraft(Base):
    """A single MH-60S airframe, identified by BuNo."""
    __tablename__ = "aircraft"
    id = Column(Integer, primary_key=True)
    bureau_number = Column(String, unique=True, nullable=False, index=True)
    side_number = Column(String)
    type_model_series = Column(String, default="MH-60S", nullable=False)
    total_airframe_hours = Column(Float, default=0.0, nullable=False)
    hours_since_phase = Column(Float, default=0.0, nullable=False)
    phase_interval = Column(Float, default=200.0, nullable=False)
    status = Column(SQLEnum(AircraftStatus), default=AircraftStatus.FMC, nullable=False)
    manual_status_override = Column(SQLEnum(AircraftStatus), nullable=True)
    notes = Column(Text)

    discrepancies = relationship("Discrepancy", back_populates="aircraft", cascade="all, delete-orphan", foreign_keys="Discrepancy.aircraft_id")
    inspections = relationship("AircraftInspection", back_populates="aircraft", cascade="all, delete-orphan")
    sorties = relationship("Sortie", back_populates="aircraft")


# ---------- Qualifications & currencies ----------

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

class CbrTaskOption(Base):
    """WTM Capability-Based Readiness task option library."""
    __tablename__ = "cbr_task_options"
    id = Column(Integer, primary_key=True)
    code = Column(String, unique=True, nullable=False, index=True)
    capability_area = Column(SQLEnum(CapabilityArea), nullable=False)
    description = Column(String, nullable=False)
    crew_scope = Column(SQLEnum(CrewScope), nullable=False)
    sim_eligible = Column(Boolean, default=False, nullable=False)
    parent_code = Column(String, nullable=True)
    confers_codes = Column(JSON, default=list, nullable=True)
    min_time_hours = Column(Float, default=0.5, nullable=False)
    recommended_min_hours = Column(Float, nullable=True)
    recommended_max_hours = Column(Float, nullable=True)
    moe_notes = Column(Text, nullable=True)
    mop_notes = Column(Text, nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)


# ---------- Flight operations ----------

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

    aircraft = relationship("Aircraft", back_populates="sorties")
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
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

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
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    closed_at = Column(DateTime, nullable=True)

    sortie = relationship("Sortie", back_populates="safety_reports")
    reported_by = relationship("Person", back_populates="safety_reports_filed", foreign_keys=[reported_by_person_id])


# ---------- Maintenance ----------

class Discrepancy(Base):
    """An open or closed maintenance issue against an aircraft."""
    __tablename__ = "discrepancies"
    id = Column(Integer, primary_key=True)
    aircraft_id = Column(Integer, ForeignKey("aircraft.id"), nullable=False, index=True)
    description = Column(Text, nullable=False)
    severity = Column(SQLEnum(DiscrepancySeverity), default=DiscrepancySeverity.MINOR, nullable=False)
    opened_date = Column(DateTime, default=datetime.utcnow, nullable=False)
    closed_date = Column(DateTime)
    is_open = Column(Boolean, default=True, nullable=False, index=True)
    notes = Column(Text)
    # Batch 5a NAMP fields
    maf_number = Column(String, nullable=True, index=True)
    work_status = Column(SQLEnum(DiscrepancyWorkStatus), default=DiscrepancyWorkStatus.OPEN, nullable=False)
    system_affected = Column(String, nullable=True)
    corrective_action = Column(Text, nullable=True)
    # CNAF M-4790.2 work-order discrimination
    type_wo_code = Column(String(2), nullable=True)
    jcn = Column(String(9), nullable=True, index=True)

    # New in flight-logging
    sortie_id = Column(Integer, ForeignKey("sorties.id"), nullable=True, index=True)
    reported_by_person_id = Column(Integer, ForeignKey("persons.id"), nullable=True)

    aircraft = relationship("Aircraft", back_populates="discrepancies", foreign_keys=[aircraft_id])
    sortie = relationship("Sortie", back_populates="discrepancies_filed", foreign_keys=[sortie_id])
    reported_by = relationship("Person", back_populates="discrepancies_reported", foreign_keys=[reported_by_person_id])


# ---------- Inspection catalog ----------

class InspectionType(Base):
    """Catalog of recurring maintenance inspection definitions."""
    __tablename__ = "inspection_types"
    id = Column(Integer, primary_key=True)
    code = Column(String, unique=True, nullable=False, index=True)
    name = Column(String, nullable=False)
    periodicity_days = Column(Integer, nullable=True)
    periodicity_hours = Column(Float, nullable=True)
    description = Column(Text, nullable=True)
    is_downing_when_overdue = Column(Boolean, default=True, nullable=False)

    inspections = relationship("AircraftInspection", back_populates="inspection_type")


class AircraftInspection(Base):
    """Per-aircraft tracking row — one per (aircraft, inspection_type)."""
    __tablename__ = "aircraft_inspections"
    __table_args__ = (
        UniqueConstraint("aircraft_id", "inspection_type_id", name="uq_aircraft_inspection_type"),
    )
    id = Column(Integer, primary_key=True)
    aircraft_id = Column(Integer, ForeignKey("aircraft.id", ondelete="CASCADE"), nullable=False, index=True)
    inspection_type_id = Column(Integer, ForeignKey("inspection_types.id"), nullable=False, index=True)
    last_completed_date = Column(Date, nullable=True)
    last_completed_hours = Column(Float, nullable=True)
    next_due_date = Column(Date, nullable=True)
    next_due_hours = Column(Float, nullable=True)
    last_completion_notes = Column(Text, nullable=True)

    aircraft = relationship("Aircraft", back_populates="inspections")
    inspection_type = relationship("InspectionType", back_populates="inspections")


# ---------- Gradecard templates ----------

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
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

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
    logged_at = Column(DateTime, default=datetime.utcnow, nullable=False)

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


# ---------- Audit log ----------

class AuditLog(Base):
    """Append-only record of every state-changing API call."""
    __tablename__ = "audit_log"
    id = Column(Integer, primary_key=True)
    ts = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    actor = Column(String(120), nullable=True)
    method = Column(String(8), nullable=False)
    path = Column(String(512), nullable=False, index=True)
    query_string = Column(String(512), nullable=True)
    response_status = Column(Integer, nullable=False)
    request_body = Column(JSONB, nullable=True)
    client_host = Column(String(64), nullable=True)
    duration_ms = Column(Integer, nullable=True)
