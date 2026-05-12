from pydantic import BaseModel, ConfigDict
from datetime import datetime
from typing import Optional, List
from app.models.models import CrewPosition, FlightMode, TaskGrade, DataProvenance
from app.schemas.logging import SortieTmrOut


class SortieLegRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    leg_number: int
    departure_location: str
    arrival_location: str
    takeoff_time: Optional[datetime] = None
    land_time: Optional[datetime] = None
    duration_hours: Optional[float] = None


class InstrumentApproachRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    approach_type: str
    actual_or_simulated: str
    airport_icao: str
    runway: Optional[str] = None
    remarks: Optional[str] = None
    logged_at: datetime


class FlightLogOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    person_id: int
    person_name: str
    crew_position: CrewPosition
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
    # NVG subcategories
    nvg_unaided_hl_hours: float = 0.0
    nvg_unaided_ll_hours: float = 0.0
    nvg_tactical_hl_hours: float = 0.0
    nvg_tactical_ll_hours: float = 0.0
    syllabus_event_completed: Optional[str] = None
    instructor_remarks: Optional[str] = None
    special_crew_time_hours: Optional[float] = None
    data_provenance: DataProvenance = DataProvenance.ENTERED
    instrument_approaches: List[InstrumentApproachRead] = []


class SortieTaskCreditOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    task_code: str
    grade: Optional[TaskGrade] = None
    remarks: Optional[str] = None
    person_id: int
    person_name: str


class SortieSummary(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    event_code: Optional[str] = None
    event_type: Optional[str] = None
    aircraft_id: Optional[int] = None
    aircraft_side_number: Optional[str] = None
    brief_time: Optional[datetime] = None
    takeoff_time: Optional[datetime] = None
    land_time: Optional[datetime] = None
    duration_hours: Optional[float] = None
    is_complete: bool


class SortieDetail(SortieSummary):
    debrief_notes: Optional[str] = None
    notes: Optional[str] = None
    flight_mode: FlightMode = FlightMode.LIVE
    # Activity quantities (null means not recorded / treat as 0)
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
    landings_shipboard_day: Optional[int] = None
    landings_shipboard_night: Optional[int] = None
    departure_location: Optional[str] = None
    arrival_location: Optional[str] = None
    legs: List[SortieLegRead] = []
    flight_logs: List[FlightLogOut] = []
    task_credits: List[SortieTaskCreditOut] = []
    tmr_codes: List[SortieTmrOut] = []
