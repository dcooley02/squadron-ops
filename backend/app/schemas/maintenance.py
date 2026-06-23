from datetime import date, datetime
from typing import List, Optional

from pydantic import BaseModel, ConfigDict

from app.models.models import (
    DiscrepancySeverity,
    DiscrepancyWorkStatus,
    LogbookEntryType,
    PartsRequestStatus,
)


class WorkCenterOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    code: str
    name: str
    description: Optional[str] = None


class WorkOrderOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    jcn: str
    type_wo_code: str
    aircraft_id: int
    maf_id: Optional[int] = None
    discrepancy_id: Optional[int] = None
    work_center_id: Optional[int] = None
    work_center_code: Optional[str] = None
    work_center_name: Optional[str] = None
    status: DiscrepancyWorkStatus
    corrective_action: Optional[str] = None
    opened_date: datetime
    assigned_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    maf_number: Optional[str] = None
    has_qa_signoff: bool = False


class DiscrepancyCreateLine(BaseModel):
    description: str
    severity: DiscrepancySeverity = DiscrepancySeverity.MINOR
    system_affected: Optional[str] = None
    notes: Optional[str] = None
    type_wo_code: str = "DM"
    work_center_id: Optional[int] = None


class WorkOrderUpdate(BaseModel):
    status: Optional[DiscrepancyWorkStatus] = None
    corrective_action: Optional[str] = None
    work_center_id: Optional[int] = None


class QaSignoffCreate(BaseModel):
    notes: str
    release_eligible: bool = True


class QaSignoffOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    work_order_id: int
    inspector_person_id: int
    inspector_name: Optional[str] = None
    signed_at: datetime
    notes: Optional[str] = None
    release_eligible: bool


class PartsRequestCreate(BaseModel):
    part_name: str
    nsn: Optional[str] = None
    qty_ordered: int = 1
    bcm_on_shelf: bool = False
    expected_delivery_date: Optional[date] = None


class PartsRequestOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    work_order_id: int
    part_name: str
    nsn: Optional[str] = None
    qty_ordered: int
    status: PartsRequestStatus
    expected_delivery_date: Optional[date] = None
    bcm_on_shelf: bool


class LogbookEntryCreate(BaseModel):
    entry_type: LogbookEntryType
    title: str
    description: Optional[str] = None
    hours_at_entry: Optional[float] = None


class LogbookEntryOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    aircraft_id: int
    entry_type: LogbookEntryType
    entry_date: datetime
    hours_at_entry: Optional[float] = None
    title: str
    description: Optional[str] = None
    work_order_id: Optional[int] = None
    sortie_id: Optional[int] = None
    created_by_name: Optional[str] = None


class PhaseForecastRow(BaseModel):
    aircraft_id: int
    side_number: Optional[str] = None
    hours_since_phase: float
    hours_to_phase: float
    weekly_flight_hours_assumed: float
    projected_phase_date: Optional[date] = None


class ReleaseForecastOut(BaseModel):
    aircraft_id: int
    computed_status: str
    blockers: List[str]
    projected_release_date: Optional[date] = None
    open_discrepancy_count: int
    open_work_order_count: int