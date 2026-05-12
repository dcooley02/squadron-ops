from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import asc, nullslast
from typing import List
from datetime import date, datetime, timedelta

from app.database import get_db
from app.models.models import Aircraft, AircraftInspection, InspectionType, Discrepancy, DiscrepancyWorkStatus
from app.schemas.aircraft import InspectionTypeOut, AircraftInspectionOut, DiscrepancyOut, DiscrepancyUpdate, InspectionUpdate
from app.services.aircraft_status import is_inspection_overdue

router = APIRouter(prefix="/api/maintenance", tags=["maintenance"])


@router.get("/inspections/types", response_model=List[InspectionTypeOut])
def list_inspection_types(db: Session = Depends(get_db)):
    """List all inspection type definitions."""
    return db.query(InspectionType).order_by(InspectionType.code).all()


@router.get("/aircraft/{aircraft_id}/inspections", response_model=List[AircraftInspectionOut])
def list_aircraft_inspections(aircraft_id: int, db: Session = Depends(get_db)):
    """List all 7 inspection rows for one aircraft, ordered by next_due_date ascending (nulls last)."""
    if not db.query(Aircraft).filter(Aircraft.id == aircraft_id).first():
        raise HTTPException(status_code=404, detail=f"Aircraft {aircraft_id} not found")

    ac = db.query(Aircraft).filter(Aircraft.id == aircraft_id).first()
    rows = (
        db.query(AircraftInspection)
        .options(joinedload(AircraftInspection.inspection_type))
        .filter(AircraftInspection.aircraft_id == aircraft_id)
        .order_by(nullslast(asc(AircraftInspection.next_due_date)))
        .all()
    )

    today = date.today()
    result = []
    for insp in rows:
        overdue = is_inspection_overdue(insp, today, ac.total_airframe_hours)
        out = AircraftInspectionOut.model_validate({
            "id": insp.id,
            "aircraft_id": insp.aircraft_id,
            "inspection_type_id": insp.inspection_type_id,
            "inspection_type": insp.inspection_type,
            "last_completed_date": insp.last_completed_date,
            "last_completed_hours": insp.last_completed_hours,
            "next_due_date": insp.next_due_date,
            "next_due_hours": insp.next_due_hours,
            "last_completion_notes": insp.last_completion_notes,
            "is_overdue": overdue,
        })
        result.append(out)
    return result


@router.get("/aircraft/{aircraft_id}/discrepancies", response_model=List[DiscrepancyOut])
def list_aircraft_discrepancies(
    aircraft_id: int,
    open_only: bool = Query(False, description="If true, return only open discrepancies"),
    db: Session = Depends(get_db),
):
    """All discrepancies for one aircraft (including closed). Filter by ?open_only=true."""
    if not db.query(Aircraft).filter(Aircraft.id == aircraft_id).first():
        raise HTTPException(status_code=404, detail=f"Aircraft {aircraft_id} not found")

    q = db.query(Discrepancy).filter(Discrepancy.aircraft_id == aircraft_id)
    if open_only:
        q = q.filter(Discrepancy.is_open.is_(True))
    return q.order_by(Discrepancy.opened_date.desc()).all()


@router.patch("/discrepancies/{discrepancy_id}", response_model=DiscrepancyOut)
def update_discrepancy(
    discrepancy_id: int,
    body: DiscrepancyUpdate,
    db: Session = Depends(get_db),
):
    """Update work status, system affected, or corrective action on a discrepancy.
    Closing (work_status=CLOSED) also stamps closed_date and sets is_open=False."""
    disc = db.query(Discrepancy).filter(Discrepancy.id == discrepancy_id).first()
    if not disc:
        raise HTTPException(status_code=404, detail=f"Discrepancy {discrepancy_id} not found")

    if body.work_status is not None:
        disc.work_status = body.work_status
        if body.work_status == DiscrepancyWorkStatus.CLOSED:
            disc.is_open = False
            disc.closed_date = datetime.utcnow()
        elif disc.is_open is False and body.work_status != DiscrepancyWorkStatus.CLOSED:
            disc.is_open = True
            disc.closed_date = None
    if body.system_affected is not None:
        disc.system_affected = body.system_affected
    if body.corrective_action is not None:
        disc.corrective_action = body.corrective_action

    db.commit()
    db.refresh(disc)
    return disc


@router.patch(
    "/aircraft/{aircraft_id}/inspections/{inspection_id}",
    response_model=AircraftInspectionOut,
)
def update_aircraft_inspection(
    aircraft_id: int,
    inspection_id: int,
    body: InspectionUpdate,
    db: Session = Depends(get_db),
):
    """Record completion of an inspection and recompute the next due date/hours."""
    insp = (
        db.query(AircraftInspection)
        .options(joinedload(AircraftInspection.inspection_type))
        .filter(
            AircraftInspection.id == inspection_id,
            AircraftInspection.aircraft_id == aircraft_id,
        )
        .first()
    )
    if not insp:
        raise HTTPException(
            status_code=404,
            detail=f"Inspection {inspection_id} not found on aircraft {aircraft_id}",
        )

    if body.last_completed_date is not None:
        insp.last_completed_date = body.last_completed_date
        it = insp.inspection_type
        if it.periodicity_days is not None:
            insp.next_due_date = body.last_completed_date + timedelta(days=it.periodicity_days)

    if body.last_completed_hours is not None:
        insp.last_completed_hours = body.last_completed_hours
        it = insp.inspection_type
        if it.periodicity_hours is not None:
            insp.next_due_hours = body.last_completed_hours + it.periodicity_hours

    if body.last_completion_notes is not None:
        insp.last_completion_notes = body.last_completion_notes

    db.commit()
    db.refresh(insp)

    ac = db.query(Aircraft).filter(Aircraft.id == aircraft_id).first()
    today = date.today()
    overdue = is_inspection_overdue(insp, today, ac.total_airframe_hours if ac else 0.0)
    return AircraftInspectionOut.model_validate({
        "id": insp.id,
        "aircraft_id": insp.aircraft_id,
        "inspection_type_id": insp.inspection_type_id,
        "inspection_type": insp.inspection_type,
        "last_completed_date": insp.last_completed_date,
        "last_completed_hours": insp.last_completed_hours,
        "next_due_date": insp.next_due_date,
        "next_due_hours": insp.next_due_hours,
        "last_completion_notes": insp.last_completion_notes,
        "is_overdue": overdue,
    })
