from pydantic import BaseModel, ConfigDict
from datetime import datetime
from typing import Optional, List, Literal
from app.models.models import CrewPosition


class EligibleCrewmember(BaseModel):
    person_id: int
    last_name: str
    first_name: str
    callsign: Optional[str] = None
    rank: Optional[str] = None
    score: float
    reasons: List[str]


class FitnessWarning(BaseModel):
    severity: Literal["red", "yellow"]
    message: str
    target: str  # e.g. "sortie", "aircraft:{id}", "person:{id}"


class SortieFitness(BaseModel):
    overall_status: Literal["green", "yellow", "red"]
    warnings: List[FitnessWarning]


class SortieCreate(BaseModel):
    event_type: Optional[str] = None
    event_code: Optional[str] = None
    aircraft_id: Optional[int] = None
    brief_time: Optional[datetime] = None
    takeoff_time: datetime
    land_time: Optional[datetime] = None
    duration_hours: Optional[float] = None
    notes: Optional[str] = None


class FlightLogCreate(BaseModel):
    person_id: int
    crew_position: CrewPosition
    hours_logged: Optional[float] = None
    syllabus_event_completed: Optional[str] = None


class CrewSuggestionSlot(BaseModel):
    crew_position: CrewPosition
    suggestions: List[EligibleCrewmember]
    recommended_person_id: Optional[int] = None


class SuggestCrewResponse(BaseModel):
    sortie_id: int
    slots: List[CrewSuggestionSlot]
    conflicts: List[FitnessWarning] = []


class ApplyCrewSuggestion(BaseModel):
    person_id: int
    crew_position: CrewPosition


class ApplySuggestionsResponse(BaseModel):
    assigned: List[FlightLogCreate]
    skipped: List[str] = []


class WeekMissionStub(BaseModel):
    event_type: Optional[str] = None
    event_code: Optional[str] = None
    aircraft_id: Optional[int] = None
    takeoff_time: datetime
    land_time: Optional[datetime] = None
    duration_hours: Optional[float] = 2.0
    positions: List[CrewPosition] = [CrewPosition.HAC, CrewPosition.CREW_CHIEF]


class ProposedCrewAssignment(BaseModel):
    crew_position: CrewPosition
    person_id: int
    last_name: str
    first_name: str
    reasons: List[str]


class ProposedSortie(BaseModel):
    stub_index: int
    event_type: Optional[str] = None
    event_code: Optional[str] = None
    aircraft_id: Optional[int] = None
    takeoff_time: datetime
    duration_hours: Optional[float] = None
    suggested_crew: List[ProposedCrewAssignment]
    warnings: List[FitnessWarning] = []


class ProposeWeekRequest(BaseModel):
    missions: List[WeekMissionStub]


class ProposeWeekResponse(BaseModel):
    proposals: List[ProposedSortie]
