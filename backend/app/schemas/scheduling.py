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
