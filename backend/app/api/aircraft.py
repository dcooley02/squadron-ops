from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session, joinedload
from typing import List, Optional
from datetime import date

from app.database import get_db
from app.models.models import Aircraft, AircraftStatus, AircraftInspection
from app.schemas.aircraft import AircraftSummary, AircraftDetail
from app.services.aircraft_detail import build_aircraft_detail, open_discrepancies, overdue_inspections
from app.services.aircraft_status import compute_status

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
        open_discs = open_discrepancies(ac)
        overdue_insps = overdue_inspections(ac, today)
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

    return build_aircraft_detail(ac)
