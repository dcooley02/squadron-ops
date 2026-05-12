from pydantic import BaseModel, ConfigDict
from datetime import date
from typing import Optional, List
from app.models.models import Role
from app.schemas.currency import CurrencyTypeOut


# ---------- Sub-schemas ----------

class QualificationOut(BaseModel):
    """A single qualification on a person."""
    model_config = ConfigDict(from_attributes=True)

    id: int
    qual_code: str
    qualified_date: Optional[date]
    expires_date: Optional[date]


class CurrencyOut(BaseModel):
    """A single currency status on a person."""
    model_config = ConfigDict(from_attributes=True)

    id: int
    currency_code: str
    last_event_date: Optional[date]
    expires_date: Optional[date]
    currency_type_id: Optional[int] = None
    currency_type: Optional[CurrencyTypeOut] = None


# ---------- Person schemas ----------

class PersonSummary(BaseModel):
    """Lightweight person record for list views."""
    model_config = ConfigDict(from_attributes=True)

    id: int
    last_name: str
    first_name: str
    callsign: Optional[str]
    rank: Optional[str]
    role: Role
    is_active: bool


class PersonDetail(PersonSummary):
    """Full person record with qualifications and currencies."""
    qualifications: List[QualificationOut] = []
    currencies: List[CurrencyOut] = []