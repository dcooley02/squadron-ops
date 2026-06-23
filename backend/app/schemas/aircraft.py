from pydantic import BaseModel, ConfigDict, computed_field
from datetime import datetime, date
from typing import Optional, List
from app.models.models import AircraftStatus, DiscrepancySeverity, DiscrepancyWorkStatus


class DiscrepancyOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    aircraft_id: int
    sortie_id: Optional[int] = None
    description: str
    severity: DiscrepancySeverity
    work_status: DiscrepancyWorkStatus
    maf_number: Optional[str] = None
    system_affected: Optional[str] = None
    corrective_action: Optional[str] = None
    notes: Optional[str] = None
    is_open: bool
    opened_date: datetime
    closed_date: Optional[datetime] = None
    # CNAF M-4790.2
    type_wo_code: Optional[str] = None
    jcn: Optional[str] = None


class DiscrepancyCreate(BaseModel):
    description: str
    severity: DiscrepancySeverity = DiscrepancySeverity.MINOR
    notes: Optional[str] = None
    maf_number: Optional[str] = None
    work_status: DiscrepancyWorkStatus = DiscrepancyWorkStatus.OPEN
    system_affected: Optional[str] = None
    corrective_action: Optional[str] = None
    type_wo_code: Optional[str] = None


class DiscrepancyUpdate(BaseModel):
    work_status: Optional[DiscrepancyWorkStatus] = None
    system_affected: Optional[str] = None
    corrective_action: Optional[str] = None


class InspectionUpdate(BaseModel):
    last_completed_date: Optional[date] = None
    last_completed_hours: Optional[float] = None
    last_completion_notes: Optional[str] = None


class InspectionTypeOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    code: str
    name: str
    periodicity_days: Optional[int] = None
    periodicity_hours: Optional[float] = None
    description: Optional[str] = None
    is_downing_when_overdue: bool


class AircraftInspectionOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    aircraft_id: int
    inspection_type_id: int
    inspection_type: InspectionTypeOut
    last_completed_date: Optional[date] = None
    last_completed_hours: Optional[float] = None
    next_due_date: Optional[date] = None
    next_due_hours: Optional[float] = None
    last_completion_notes: Optional[str] = None
    is_overdue: bool = False


class AircraftSummary(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    bureau_number: str
    side_number: Optional[str]
    type_model_series: str
    total_airframe_hours: float
    hours_since_phase: float
    phase_interval: float
    status: AircraftStatus
    computed_status: Optional[AircraftStatus] = None


class AircraftDetail(AircraftSummary):
    open_discrepancies: List[DiscrepancyOut] = []
    manual_status_override: Optional[AircraftStatus] = None
    computed_status: AircraftStatus = AircraftStatus.FMC

    @computed_field
    @property
    def hours_to_phase(self) -> float:
        return self.phase_interval - self.hours_since_phase
