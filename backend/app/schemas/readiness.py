from datetime import date
from typing import List, Optional

from pydantic import BaseModel

from app.models.models import CapabilityArea, Role


class AnchorTaskStatus(BaseModel):
    task_code: str
    status: str
    days_since: Optional[int] = None


class PersonAreaRating(BaseModel):
    capability_area: CapabilityArea
    label: str
    rating: str
    contributing_factors: List[str] = []
    anchor_tasks: List[AnchorTaskStatus] = []


class PersonReadinessSummary(BaseModel):
    person_id: int
    person_name: str
    callsign: Optional[str] = None
    role: Role
    overall_rating: str
    areas: List[PersonAreaRating]


class SquadronAreaSummary(BaseModel):
    capability_area: CapabilityArea
    label: str
    squadron_rating: str
    t1_count: int
    t2_count: int
    t3_count: int
    pilots_rated: int


class SquadronReadinessOut(BaseModel):
    as_of_date: date
    pilots_rated: int
    squadron_overall_rating: str
    areas: List[SquadronAreaSummary]
    persons: List[PersonReadinessSummary]