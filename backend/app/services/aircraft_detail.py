"""Shared helper to build AircraftDetail responses from ORM state."""
from datetime import date
from typing import List

from app.models.models import (
    Aircraft,
    AircraftInspection,
    Discrepancy,
    DiscrepancyWorkStatus,
)
from app.schemas.aircraft import AircraftDetail
from app.services.aircraft_status import compute_status, is_inspection_overdue
from app.services.maintenance_chain import build_discrepancy_out


def open_discrepancies(aircraft: Aircraft) -> List[Discrepancy]:
    return [d for d in aircraft.discrepancies if d.work_status != DiscrepancyWorkStatus.CLOSED]


def overdue_inspections(aircraft: Aircraft, today: date | None = None) -> List[AircraftInspection]:
    today = today or date.today()
    return [
        insp for insp in aircraft.inspections
        if is_inspection_overdue(insp, today, aircraft.total_airframe_hours)
    ]


def build_aircraft_detail(aircraft: Aircraft, today: date | None = None) -> AircraftDetail:
    today = today or date.today()
    open_discs = open_discrepancies(aircraft)
    overdue = overdue_inspections(aircraft, today)
    computed = compute_status(aircraft, open_discs, overdue)
    open_disc_out = [build_discrepancy_out(d) for d in aircraft.discrepancies if d.is_open]
    return AircraftDetail(
        id=aircraft.id,
        bureau_number=aircraft.bureau_number,
        side_number=aircraft.side_number,
        type_model_series=aircraft.type_model_series,
        total_airframe_hours=aircraft.total_airframe_hours,
        hours_since_phase=aircraft.hours_since_phase,
        phase_interval=aircraft.phase_interval,
        status=aircraft.status,
        manual_status_override=aircraft.manual_status_override,
        computed_status=computed,
        open_discrepancies=open_disc_out,
    )