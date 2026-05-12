from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session, joinedload
from typing import List, Optional
from datetime import date

from app.database import get_db
from app.models.models import Aircraft, AircraftStatus, AircraftInspection, Discrepancy, DiscrepancyWorkStatus
from app.schemas.aircraft import AircraftSummary, AircraftDetail, DiscrepancyOut
from app.services.aircraft_status import compute_status, is_inspection_overdue

router = APIRouter(prefix="/api/aircraft", tags=["aircraft"])


@router.get("", response_model=List[AircraftSummary])
def list_aircraft(
    status: Optional[str] = Query(None, description="Filter by status (FMC, PMC, NMC, NMCM, NMCS)"),
    db: Session = Depends(get_db),
):
    """List all aircraft, optionally filtered by status."""
    query = db.query(Aircraft).options(
        joinedload(Aircraft.discrepancies),
        joinedload(Aircraft.inspections).joinedload(AircraftInspection.inspection_type),
    )
    if status is not None:
        try:
            status_enum = AircraftStatus(status.upper())
        except ValueError:
            valid = [e.value for e in AircraftStatus]
            raise HTTPException(
                status_code=400,
                detail=f"Invalid status '{status}'. Valid values: {valid}",
            )
        query = query.filter(Aircraft.status == status_enum)
    rows = query.order_by(Aircraft.side_number).all()
    today = date.today()
    results = []
    for ac in rows:
        open_discs = [d for d in ac.discrepancies if d.work_status != DiscrepancyWorkStatus.CLOSED]
        overdue_insps = [
            insp for insp in ac.inspections
            if is_inspection_overdue(insp, today, ac.total_airframe_hours)
        ]
        computed = compute_status(ac, open_discs, overdue_insps)
        summary = AircraftSummary.model_validate(ac)
        summary.computed_status = computed
        results.append(summary)
    return results


@router.get("/{aircraft_id}", response_model=AircraftDetail)
def get_aircraft(aircraft_id: int, db: Session = Depends(get_db)):
    """Get one aircraft with open discrepancies, inspection state, and computed status."""
    ac = (
        db.query(Aircraft)
        .options(
            joinedload(Aircraft.discrepancies),
            joinedload(Aircraft.inspections).joinedload(AircraftInspection.inspection_type),
        )
        .filter(Aircraft.id == aircraft_id)
        .first()
    )
    if not ac:
        raise HTTPException(status_code=404, detail=f"Aircraft {aircraft_id} not found")

    today = date.today()
    open_discs = [d for d in ac.discrepancies if d.work_status != DiscrepancyWorkStatus.CLOSED]
    overdue_insps = [
        insp for insp in ac.inspections
        if is_inspection_overdue(insp, today, ac.total_airframe_hours)
    ]
    status = compute_status(ac, open_discs, overdue_insps)

    open_disc_out = [DiscrepancyOut.model_validate(d) for d in ac.discrepancies if d.is_open]
    return AircraftDetail(
        id=ac.id,
        bureau_number=ac.bureau_number,
        side_number=ac.side_number,
        type_model_series=ac.type_model_series,
        total_airframe_hours=ac.total_airframe_hours,
        hours_since_phase=ac.hours_since_phase,
        phase_interval=ac.phase_interval,
        status=ac.status,
        manual_status_override=ac.manual_status_override,
        computed_status=status,
        open_discrepancies=open_disc_out,
    )
