"""Shared domain enums for SQLAlchemy models."""
from __future__ import annotations

import enum

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

class MafStatus(str, enum.Enum):
    OPEN = "OPEN"
    IN_WORK = "IN_WORK"
    COMPLETED = "COMPLETED"
    CLOSED = "CLOSED"

class PartsRequestStatus(str, enum.Enum):
    REQUESTED = "REQUESTED"
    ORDERED = "ORDERED"
    RECEIVED = "RECEIVED"
    BCM = "BCM"

class LogbookEntryType(str, enum.Enum):
    ASR = "ASR"
    MSR = "MSR"
    EQUIPMENT_CHANGE = "EQUIPMENT_CHANGE"
    QA_RELEASE = "QA_RELEASE"
    PHASE_INSPECTION = "PHASE_INSPECTION"
    DISCREPANCY = "DISCREPANCY"

class FlightMode(str, enum.Enum):
    LIVE = "LIVE"
    SIM_TOFT = "SIM_TOFT"

class SortieOpsStatus(str, enum.Enum):
    PLANNED = "PLANNED"
    PUBLISHED = "PUBLISHED"
    BRIEFED = "BRIEFED"
    MANNED = "MANNED"
    AIRBORNE = "AIRBORNE"
    RECOVERED = "RECOVERED"
    DEBRIEFED = "DEBRIEFED"

class BoardType(str, enum.Enum):
    HAC_BOARD = "HAC_BOARD"
    INSTRUCTOR_BOARD = "INSTRUCTOR_BOARD"
    NATOPS_CHECK = "NATOPS_CHECK"
    STAN_EVAL = "STAN_EVAL"

class BoardStatus(str, enum.Enum):
    SCHEDULED = "SCHEDULED"
    COMPLETED = "COMPLETED"
    CANCELLED = "CANCELLED"

class WatchbillRole(str, enum.Enum):
    SDO = "SDO"
    ODO = "ODO"
    DUTY_PILOT = "DUTY_PILOT"
    DUTY_AIRCREW = "DUTY_AIRCREW"
    ALERT = "ALERT"

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

