from pydantic import BaseModel, ConfigDict
from datetime import date, datetime
from typing import Optional, List
from app.models.models import (
    CrewPosition, DiscrepancySeverity, FlightMode, CapabilityArea, TaskGrade, CrewScope,
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


# ---------- Flight log actuals ----------

class FlightLogActuals(BaseModel):
    """Actual figures for one crewmember after debriefing."""
    flight_log_id: int
    hours_logged: float
    syllabus_event_completed: Optional[str] = None
    instructor_remarks: Optional[str] = None


# ---------- Sortie completion ----------

class SortieCompletePayload(BaseModel):
    """Everything needed to close out a completed sortie."""
    actual_takeoff_time: datetime
    actual_land_time: datetime
    duration_hours: float
    day_hours: float
    night_hours: float
    nvg_hours: float
    instrument_hours: float
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
    flight_log_actuals: List[FlightLogActuals]
    task_credits: List[TaskCreditCreate] = []
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
    day_hours: Optional[float] = 0.0
    night_hours: Optional[float] = 0.0
    nvg_hours: Optional[float] = 0.0
    instrument_hours: Optional[float] = 0.0
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
