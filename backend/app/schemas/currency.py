from pydantic import BaseModel, ConfigDict
from typing import Optional, List

from app.models.models import CurrencyAudience


class CurrencyApplicabilityOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    applies_to: CurrencyAudience
    required_qualification: Optional[str] = None


class CurrencyTypeOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    code: str
    name: str
    periodicity_days: int
    requirement_text: str
    description: Optional[str] = None
    sim_eligible: bool
    sim_notes: Optional[str] = None
    min_hours: Optional[float] = None
    min_count: Optional[int] = None
    count_unit: Optional[str] = None
    references: Optional[List[str]] = None
    is_active: bool
    applicability: List[CurrencyApplicabilityOut] = []
