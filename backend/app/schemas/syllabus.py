from pydantic import BaseModel, ConfigDict
from datetime import date, datetime
from typing import Optional, List

from app.models.models import (
    SyllabusLevel, SyllabusStage, SyllabusTrack, EventVenue,
    GradingScheme, GradecardSection, LineItemRole,
    GradecardStatus, CompletionStatus, FourTierScore,
)


# ---------- Line item template ----------

class GradecardLineItemTemplate(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    section: GradecardSection
    item_name: str
    role: LineItemRole
    is_critical: bool
    is_required: bool
    display_order: int
    mop_below_standard: Optional[str] = None
    mop_standard: Optional[str] = None


# ---------- Syllabus event ----------

class SyllabusEventOut(BaseModel):
    """Trimmed event record for list views (no line items)."""
    model_config = ConfigDict(from_attributes=True)

    id: int
    code: str
    name: str
    stage_legacy: Optional[str] = None
    prerequisites: Optional[str] = None
    description: Optional[str] = None
    level: Optional[SyllabusLevel] = None
    stage: Optional[SyllabusStage] = None
    series: Optional[int] = None
    track: Optional[SyllabusTrack] = None
    event_code: Optional[str] = None
    min_instructor_level: Optional[int] = None
    aircraft_or_sim: Optional[EventVenue] = None
    time_hours: Optional[float] = None
    is_stan_eval: bool = False
    grading_scheme: Optional[GradingScheme] = None
    prerequisites_text: Optional[str] = None
    force_composition: Optional[str] = None
    recommended_soe: Optional[str] = None
    unsat_criteria: Optional[str] = None
    references: Optional[List[str]] = None


class SyllabusEventTemplate(SyllabusEventOut):
    """Full event record with gradecard line item templates."""
    line_items: List[GradecardLineItemTemplate] = []


# ---------- Gradecard line item results ----------

class GradecardLineItemResultIn(BaseModel):
    line_item_id: int
    waived: bool = False
    completion_status: Optional[CompletionStatus] = None
    four_tier_score: Optional[FourTierScore] = None
    remarks: Optional[str] = None


class GradecardLineItemResultPatch(BaseModel):
    four_tier_score: Optional[FourTierScore] = None
    completion_status: Optional[CompletionStatus] = None
    remarks: Optional[str] = None
    waived: Optional[bool] = None


class GradecardLineItemResultOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    line_item_id: int
    waived: bool
    completion_status: Optional[CompletionStatus] = None
    four_tier_score: Optional[FourTierScore] = None
    remarks: Optional[str] = None
    line_item: GradecardLineItemTemplate


# ---------- Gradecard ----------

class GradecardCreateBlank(BaseModel):
    person_id: int
    syllabus_event_id: int
    sortie_id: Optional[int] = None
    flight_log_id: Optional[int] = None
    instructor_person_id: Optional[int] = None
    card_date: date
    remarks: Optional[str] = None


class GradecardCreate(BaseModel):
    person_id: int
    syllabus_event_id: int
    sortie_id: Optional[int] = None
    flight_log_id: Optional[int] = None
    instructor_person_id: Optional[int] = None
    card_date: date
    remarks: Optional[str] = None
    line_item_results: List[GradecardLineItemResultIn] = []


class GradecardOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    person_id: int
    syllabus_event_id: int
    sortie_id: Optional[int] = None
    flight_log_id: Optional[int] = None
    instructor_person_id: Optional[int] = None
    card_date: date
    grading_scheme: GradingScheme
    overall_status: GradecardStatus
    remarks: Optional[str] = None
    line_item_results: List[GradecardLineItemResultOut] = []
    created_at: datetime
    updated_at: datetime


class GradecardSummary(BaseModel):
    """Trimmed gradecard for list views."""
    model_config = ConfigDict(from_attributes=True)

    id: int
    event_code: Optional[str] = None   # built from syllabus_event by route handler
    person_name: str                    # built from person by route handler
    card_date: date
    overall_status: GradecardStatus
    grading_scheme: GradingScheme


class GradecardPatch(BaseModel):
    overall_status: Optional[GradecardStatus] = None
    remarks: Optional[str] = None
    instructor_person_id: Optional[int] = None
    card_date: Optional[date] = None
    sortie_id: Optional[int] = None
    flight_log_id: Optional[int] = None
