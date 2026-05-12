from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import desc
from datetime import date, datetime, time as dt_time
from typing import List, Optional

from app.database import get_db
from app.models.models import (
    Sortie, FlightLog, CbrTaskOption, SortieTaskCredit,
    SafetyReport, Discrepancy, Person,
    CapabilityArea, DiscrepancySeverity,
)
from app.schemas.logging import (
    CbrTaskOptionOut,
    SortieCompletePayload,
    UnscheduledSortiePayload,
    SafetyReportCreate, SafetyReportOut,
    TrainingJacketEntry, TrainingJacketTaskEntry,
)
from app.schemas.sorties import SortieDetail, FlightLogOut
from app.schemas.aircraft import DiscrepancyOut
from app.services.flight_completion import complete_sortie, create_and_complete_unscheduled

router = APIRouter(prefix="/api/logging", tags=["logging"])


# ---------- Helpers ----------

def _sortie_detail(s: Sortie) -> SortieDetail:
    return SortieDetail.model_validate({
        "id": s.id,
        "event_code": s.event_code,
        "event_type": s.event_type,
        "aircraft_id": s.aircraft_id,
        "aircraft_side_number": s.aircraft.side_number if s.aircraft else None,
        "brief_time": s.brief_time,
        "takeoff_time": s.takeoff_time,
        "land_time": s.land_time,
        "duration_hours": s.duration_hours,
        "is_complete": s.is_complete,
        "day_hours": s.day_hours,
        "night_hours": s.night_hours,
        "nvg_hours": s.nvg_hours,
        "instrument_hours": s.instrument_hours,
        "notes": s.notes,
        "flight_logs": [
            FlightLogOut.model_validate({
                "id": fl.id,
                "person_id": fl.person_id,
                "person_name": f"{fl.person.last_name}, {fl.person.first_name}",
                "crew_position": fl.crew_position,
                "hours_logged": fl.hours_logged,
                "syllabus_event_completed": fl.syllabus_event_completed,
            })
            for fl in s.flight_logs
        ],
    })


def _load_sortie_full(db: Session, sortie_id: int) -> Sortie:
    """Load a sortie with all relationships needed for serialisation."""
    return (
        db.query(Sortie)
        .options(
            joinedload(Sortie.aircraft),
            joinedload(Sortie.flight_logs).joinedload(FlightLog.person),
        )
        .filter(Sortie.id == sortie_id)
        .first()
    )


# ---------- Sortie completion ----------

@router.post("/sorties/{sortie_id}/complete", response_model=SortieDetail)
def complete_sortie_endpoint(
    sortie_id: int,
    payload: SortieCompletePayload,
    db: Session = Depends(get_db),
):
    """
    Close out a completed sortie: update times/hours, assign task credits,
    refresh currencies, update aircraft hours, file discrepancies and safety reports.
    """
    # Pre-check existence and completion state before entering the service
    existing = db.query(Sortie.id, Sortie.is_complete).filter(Sortie.id == sortie_id).first()
    if not existing:
        raise HTTPException(status_code=404, detail=f"Sortie {sortie_id} not found")
    if existing.is_complete:
        raise HTTPException(status_code=400, detail=f"Sortie {sortie_id} is already complete")

    try:
        sortie = complete_sortie(db, sortie_id, payload)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    except Exception as exc:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Completion failed: {exc}") from exc

    loaded = _load_sortie_full(db, sortie.id)
    return _sortie_detail(loaded)


# ---------- Unscheduled / sim sorties ----------

@router.post("/unscheduled", response_model=SortieDetail, status_code=201)
def create_unscheduled(
    payload: UnscheduledSortiePayload,
    db: Session = Depends(get_db),
):
    """
    Create an ad-hoc flight or simulator event.
    If immediate_complete=True the completion cascade runs in the same request.
    """
    try:
        sortie = create_and_complete_unscheduled(db, payload)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    except Exception as exc:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Creation failed: {exc}") from exc

    loaded = _load_sortie_full(db, sortie.id)
    return _sortie_detail(loaded)


# ---------- CBR task option library ----------

@router.get("/tasks/options", response_model=List[CbrTaskOptionOut])
def list_task_options(
    capability_area: Optional[CapabilityArea] = Query(None),
    sim_eligible: Optional[bool] = Query(None),
    is_active: bool = Query(True),
    db: Session = Depends(get_db),
):
    """Return the CBR task option library, optionally filtered."""
    q = db.query(CbrTaskOption).filter(CbrTaskOption.is_active == is_active)
    if capability_area is not None:
        q = q.filter(CbrTaskOption.capability_area == capability_area)
    if sim_eligible is not None:
        q = q.filter(CbrTaskOption.sim_eligible == sim_eligible)
    return q.order_by(CbrTaskOption.code).all()


# ---------- Training jacket ----------

@router.get("/persons/{person_id}/training-jacket", response_model=List[TrainingJacketEntry])
def get_training_jacket(
    person_id: int,
    date_from: Optional[date] = Query(None),
    date_to: Optional[date] = Query(None),
    limit: int = Query(100, ge=1, le=500),
    db: Session = Depends(get_db),
):
    """
    Return a person's training jacket: chronological flight records for completed sorties,
    including task credits and instructor remarks.
    """
    person = db.query(Person).filter(Person.id == person_id).first()
    if not person:
        raise HTTPException(status_code=404, detail=f"Person {person_id} not found")

    q = (
        db.query(FlightLog)
        .join(Sortie, FlightLog.sortie_id == Sortie.id)
        .options(
            joinedload(FlightLog.sortie),
            joinedload(FlightLog.task_credits),
        )
        .filter(FlightLog.person_id == person_id, Sortie.is_complete == True)
    )
    if date_from is not None:
        q = q.filter(Sortie.takeoff_time >= datetime.combine(date_from, dt_time.min))
    if date_to is not None:
        q = q.filter(Sortie.takeoff_time <= datetime.combine(date_to, dt_time.max))

    logs = q.order_by(desc(Sortie.takeoff_time)).limit(limit).all()

    entries: List[TrainingJacketEntry] = []
    for fl in logs:
        s = fl.sortie
        entries.append(TrainingJacketEntry(
            sortie_id=s.id,
            sortie_date=s.takeoff_time.date() if s.takeoff_time else date.today(),
            event_code=s.event_code,
            event_type=s.event_type,
            flight_mode=s.flight_mode,
            crew_position=fl.crew_position,
            hours_logged=fl.hours_logged,
            instructor_remarks=fl.instructor_remarks,
            syllabus_event_completed=fl.syllabus_event_completed,
            task_credits=[
                TrainingJacketTaskEntry(
                    task_code=tc.task_code,
                    grade=tc.grade,
                    remarks=tc.remarks,
                )
                for tc in fl.task_credits
            ],
        ))
    return entries


# ---------- Aircraft Discrepancy Book (ADB) ----------

@router.get("/aircraft/{aircraft_id}/adb", response_model=List[DiscrepancyOut])
def get_adb(
    aircraft_id: int,
    is_open: Optional[bool] = Query(None, description="Filter by open/closed status"),
    db: Session = Depends(get_db),
):
    """Return the full discrepancy log (ADB) for an aircraft, sorted newest-first."""
    from app.models.models import Aircraft
    ac = db.query(Aircraft).filter(Aircraft.id == aircraft_id).first()
    if not ac:
        raise HTTPException(status_code=404, detail=f"Aircraft {aircraft_id} not found")

    q = db.query(Discrepancy).filter(Discrepancy.aircraft_id == aircraft_id)
    if is_open is not None:
        q = q.filter(Discrepancy.is_open == is_open)
    discs = q.order_by(desc(Discrepancy.opened_date)).all()
    return [DiscrepancyOut.model_validate(d) for d in discs]


# ---------- Safety reports ----------

@router.get("/safety/reports", response_model=List[SafetyReportOut])
def list_safety_reports(
    status: Optional[str] = Query(None, description="OPEN, UNDER_REVIEW, CLOSED"),
    severity: Optional[str] = Query(None, description="INFO, HAZARD, INCIDENT, MISHAP"),
    db: Session = Depends(get_db),
):
    """Return safety reports, newest first."""
    q = db.query(SafetyReport)
    if status is not None:
        q = q.filter(SafetyReport.status == status)
    if severity is not None:
        q = q.filter(SafetyReport.severity == severity)
    return q.order_by(desc(SafetyReport.created_at)).all()


@router.post("/safety/reports", response_model=SafetyReportOut, status_code=201)
def create_safety_report(
    payload: SafetyReportCreate,
    sortie_id: Optional[int] = Query(None),
    reported_by_person_id: int = Query(...),
    db: Session = Depends(get_db),
):
    """File a standalone safety report (not tied to flight completion)."""
    person = db.query(Person).filter(Person.id == reported_by_person_id).first()
    if not person:
        raise HTTPException(status_code=404, detail=f"Person {reported_by_person_id} not found")

    if sortie_id is not None:
        sortie = db.query(Sortie).filter(Sortie.id == sortie_id).first()
        if not sortie:
            raise HTTPException(status_code=404, detail=f"Sortie {sortie_id} not found")

    report = SafetyReport(
        sortie_id=sortie_id,
        reported_by_person_id=reported_by_person_id,
        severity=payload.severity,
        category=payload.category,
        description=payload.description,
        actions_taken=payload.actions_taken,
        status="OPEN",
    )
    db.add(report)
    db.commit()
    db.refresh(report)
    return report
