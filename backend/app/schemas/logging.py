from pydantic import BaseModel, ConfigDict, Field
from datetime import date, datetime
from typing import Optional, List, Dict
from app.models.models import (
    CrewPosition, DiscrepancySeverity, FlightMode, CapabilityArea, TaskGrade, CrewScope,
    ApproachType, ApproachConditions, DataProvenance,
)


# ---------- CBR task options ----------

class CbrTaskOptionOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    code: str
    capability_area: CapabilityArea
    description: str
    crew_scope: CrewScope
    sim_eligible: bool
    parent_code: Optional[str] = None
    confers_codes: Optional[List[str]] = []
    min_time_hours: float
    recommended_min_hours: Optional[float] = None
    recommended_max_hours: Optional[float] = None
    moe_notes: Optional[str] = None
    mop_notes: Optional[str] = None
    is_active: bool


# ---------- Task credits ----------

class TaskCreditCreate(BaseModel):
    """Credit one task option to a list of person IDs in a single payload entry."""
    task_code: str
    person_ids: List[int]
    grade: Optional[TaskGrade] = None
    remarks: Optional[str] = None


class TaskCreditOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    person_id: int
    person_name: str           # derived — not on ORM, built by route handler
    task_code: str
    grade: Optional[TaskGrade] = None
    remarks: Optional[str] = None


# ---------- Discrepancies & safety ----------

class DiscrepancyCreate(BaseModel):
    description: str
    severity: DiscrepancySeverity
    system_affected: Optional[str] = None
    notes: Optional[str] = None
    type_wo_code: Optional[str] = None


class SafetyReportCreate(BaseModel):
    severity: str               # INFO / HAZARD / INCIDENT / MISHAP
    category: Optional[str] = None
    description: str
    actions_taken: Optional[str] = None


class SafetyReportOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    sortie_id: Optional[int] = None
    reported_by_person_id: int
    severity: str
    category: Optional[str] = None
    description: str
    actions_taken: Optional[str] = None
    status: str
    created_at: datetime
    closed_at: Optional[datetime] = None


# ---------- Logbook sub-schemas ----------

class ApproachPayload(BaseModel):
    """One instrument approach logged per crewmember at debrief."""
    approach_type: ApproachType
    actual_or_simulated: ApproachConditions
    airport_icao: str
    runway: Optional[str] = None
    remarks: Optional[str] = None


class SortieLegPayload(BaseModel):
    """One routing leg for a multi-stop sortie."""
    leg_number: int
    departure_location: str
    arrival_location: str
    takeoff_time: Optional[datetime] = None
    land_time: Optional[datetime] = None
    duration_hours: Optional[float] = None


# ---------- Flight log actuals ----------

class FlightLogActuals(BaseModel):
    """Actual figures for one crewmember after debriefing."""
    flight_log_id: int
    hours_logged: float
    # Environment hours
    night_hours: float = 0.0
    nvg_hours: float = 0.0
    actual_instrument_hours: float = 0.0
    sim_instrument_hours: float = 0.0
    # Role hours
    total_hours: float = 0.0
    first_pilot_hours: float = 0.0
    copilot_hours: float = 0.0
    ac_commander_hours: float = 0.0
    mission_commander_hours: float = 0.0
    instructor_hours: float = 0.0
    # NVG sub-categories
    nvg_unaided_hl_hours: float = 0.0
    nvg_unaided_ll_hours: float = 0.0
    nvg_tactical_hl_hours: float = 0.0
    nvg_tactical_ll_hours: float = 0.0
    syllabus_event_completed: Optional[str] = None
    instructor_remarks: Optional[str] = None
    special_crew_time_hours: float = 0.0
    approaches: List[ApproachPayload] = []


# ---------- Sortie completion ----------

class TmrCodeAssignment(BaseModel):
    """Assign a TMR code to a MSN slot (1–3) for a sortie per CNAF M-3710.7 Appendix D."""
    code: str
    slot: int = Field(ge=1, le=3, description="MSN slot: 1 (MSN1), 2 (MSN2), or 3 (MSN3)")
    hours: Optional[float] = None


class SortieCompletePayload(BaseModel):
    """Everything needed to close out a completed sortie."""
    actual_takeoff_time: datetime
    actual_land_time: datetime
    duration_hours: float
    debrief_notes: Optional[str] = None
    # Activity quantities — all optional; null treated as 0 by the cascade.
    rounds_fired_20mm: Optional[int] = None
    ugr_fired: Optional[int] = None
    csw_rounds: Optional[int] = None
    csw_rounds_night: Optional[int] = None
    landings_day: Optional[int] = None
    landings_night: Optional[int] = None
    landings_dve_day: Optional[int] = None
    landings_dve_night: Optional[int] = None
    hoist_streams: Optional[int] = None
    hoist_recoveries: Optional[int] = None
    amns_iterations: Optional[int] = None
    almds_hours: Optional[float] = None
    amns_ntrs: Optional[int] = None
    strafe_dry_profiles_day: Optional[int] = None
    strafe_dry_profiles_night: Optional[int] = None
    # Logbook / NAVFLIR fields
    landings_shipboard_day: int = 0
    landings_shipboard_night: int = 0
    departure_location: Optional[str] = None
    arrival_location: Optional[str] = None
    legs: List[SortieLegPayload] = []
    flight_log_actuals: List[FlightLogActuals]
    task_credits: List[TaskCreditCreate] = []
    tmr_codes: List[TmrCodeAssignment] = Field(default=[], max_length=3)
    new_discrepancies: List[DiscrepancyCreate] = []
    safety_reports: List[SafetyReportCreate] = []


# ---------- Unscheduled / sim sorties ----------

class FlightLogCreateFull(BaseModel):
    """Crew slot for an unscheduled sortie creation."""
    person_id: int
    crew_position: CrewPosition
    hours_logged: Optional[float] = None
    syllabus_event_completed: Optional[str] = None


class UnscheduledSortiePayload(BaseModel):
    """
    Creates an ad-hoc flight (or sim event) that wasn't in the schedule.
    If immediate_complete=True the completion cascade also runs in the same request.
    """
    # Sortie fields
    event_type: Optional[str] = None
    event_code: Optional[str] = None
    aircraft_id: Optional[int] = None
    brief_time: Optional[datetime] = None
    takeoff_time: datetime
    land_time: Optional[datetime] = None
    duration_hours: Optional[float] = None
    notes: Optional[str] = None
    flight_mode: FlightMode = FlightMode.LIVE
    simulator_id: Optional[str] = None

    # Crew assignments
    crew: List[FlightLogCreateFull] = []

    # Completion
    immediate_complete: bool = False
    completion: Optional[SortieCompletePayload] = None


# ---------- Training jacket ----------

class TrainingJacketTaskEntry(BaseModel):
    task_code: str
    grade: Optional[TaskGrade] = None
    remarks: Optional[str] = None


class TrainingJacketEntry(BaseModel):
    sortie_id: int
    sortie_date: date
    event_code: Optional[str] = None
    event_type: Optional[str] = None
    flight_mode: FlightMode
    crew_position: CrewPosition
    hours_logged: float
    instructor_remarks: Optional[str] = None
    syllabus_event_completed: Optional[str] = None
    task_credits: List[TrainingJacketTaskEntry] = []


# ---------- TMR read schemas ----------

class LogbookTmrOut(BaseModel):
    code: str
    slot: int
    hours: Optional[float] = None


class SortieTmrOut(BaseModel):
    code: str
    description: str
    slot: int
    hours: Optional[float] = None


class TmrCodeOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    code: str
    description: str
    fpc: str
    gpc: str
    spc: str
    capability_area: Optional[str] = None


# ---------- Logbook endpoint ----------

class ApproachEntry(BaseModel):
    type: str
    conditions: str
    airport_icao: Optional[str] = None
    runway: Optional[str] = None
    approach_remarks: Optional[str] = None


class LogbookEntry(BaseModel):
    sortie_id: int
    flight_log_id: int
    date: str
    tms: Optional[str] = None
    bureau_number: Optional[str] = None
    side_number: Optional[str] = None
    event_code: Optional[str] = None
    flight_mode: str
    crew_position: str
    crew_qual_code: Optional[str] = None
    departure_location: Optional[str] = None
    arrival_location: Optional[str] = None
    # Hours
    total_hours: float
    night_hours: float
    nvg_hours: float
    actual_instrument_hours: float
    sim_instrument_hours: float
    # Role hours
    first_pilot_hours: float = 0.0
    copilot_hours: float = 0.0
    ac_commander_hours: float = 0.0
    mission_commander_hours: float = 0.0
    instructor_hours: float = 0.0
    special_crew_time_hours: float
    # NVG subcategories
    nvg_unaided_hl_hours: float = 0.0
    nvg_unaided_ll_hours: float = 0.0
    nvg_tactical_hl_hours: float = 0.0
    nvg_tactical_ll_hours: float = 0.0
    # Landings
    landings_day: int
    landings_night: int
    landings_dve_day: int
    landings_dve_night: int
    landings_shipboard_day: int
    landings_shipboard_night: int
    approaches: List[ApproachEntry] = []
    tmr_codes: List[LogbookTmrOut] = []
    remarks: Optional[str] = None
    data_provenance: Optional[str] = None


class LogbookTotals(BaseModel):
    total_hours: float
    night_hours: float
    nvg_hours: float
    total_actual_instrument_hours: float
    total_sim_instrument_hours: float
    total_first_pilot_hours: float
    total_copilot_hours: float
    total_ac_commander_hours: float
    total_mission_commander_hours: float
    total_instructor_hours: float
    total_spec_crew_hours: float
    landings_day: int
    landings_night: int
    landings_dve_day: int
    landings_dve_night: int
    landings_shipboard_day: int
    landings_shipboard_night: int
    approaches_total: int
    approaches_by_type: Dict[str, int]
    sortie_count: int
    flight_log_count: int
    data_provenance_breakdown: Dict[str, int] = {}


class LogbookWindowTotals(BaseModel):
    career: LogbookTotals
    last_365d: LogbookTotals
    last_90d: LogbookTotals
    last_30d: LogbookTotals


class LogbookFiltersApplied(BaseModel):
    date_from: Optional[str] = None
    date_to: Optional[str] = None
    aircraft_id: Optional[int] = None
    event_code: Optional[str] = None
    crew_position: Optional[str] = None
    flight_mode: Optional[str] = None


class LogbookPersonOut(BaseModel):
    id: int
    name: str
    callsign: Optional[str] = None
    rank: str
    role: str


class LogbookResponse(BaseModel):
    person: LogbookPersonOut
    filters_applied: LogbookFiltersApplied
    entries: List[LogbookEntry]
    totals: LogbookWindowTotals
