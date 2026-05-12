from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session, joinedload, selectinload
from sqlalchemy import desc
from datetime import date, datetime, time as dt_time
from typing import List, Optional

from app.database import get_db
from app.models.models import (
    Sortie, FlightLog, CbrTaskOption, SortieTaskCredit,
    SafetyReport, Discrepancy, Person, SortieTmrCode,
    CapabilityArea, DiscrepancySeverity, CrewPosition, FlightMode,
)
from app.schemas.logging import (
    CbrTaskOptionOut,
    SortieCompletePayload,
    UnscheduledSortiePayload,
    SafetyReportCreate, SafetyReportOut,
    TrainingJacketEntry, TrainingJacketTaskEntry,
    ApproachEntry, LogbookEntry, LogbookTotals, LogbookWindowTotals,
    LogbookFiltersApplied, LogbookPersonOut, LogbookResponse,
    LogbookTmrOut,
)
from app.schemas.sorties import SortieDetail, FlightLogOut
from app.schemas.aircraft import DiscrepancyOut
from app.services.flight_completion import complete_sortie, create_and_complete_unscheduled
from app.services.logbook import build_window_totals

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
        "notes": s.notes,
        "flight_logs": [
            FlightLogOut.model_validate({
                "id": fl.id,
                "person_id": fl.person_id,
                "person_name": f"{fl.person.last_name}, {fl.person.first_name}",
                "crew_position": fl.crew_position,
                "hours_logged": fl.hours_logged,
                "night_hours": fl.night_hours or 0.0,
                "nvg_hours": fl.nvg_hours or 0.0,
                "actual_instrument_hours": fl.actual_instrument_hours or 0.0,
                "sim_instrument_hours": fl.sim_instrument_hours or 0.0,
                "total_hours": fl.total_hours or fl.hours_logged,
                "first_pilot_hours": fl.first_pilot_hours or 0.0,
                "copilot_hours": fl.copilot_hours or 0.0,
                "ac_commander_hours": fl.ac_commander_hours or 0.0,
                "mission_commander_hours": fl.mission_commander_hours or 0.0,
                "instructor_hours": fl.instructor_hours or 0.0,
                "nvg_unaided_hl_hours": fl.nvg_unaided_hl_hours or 0.0,
                "nvg_unaided_ll_hours": fl.nvg_unaided_ll_hours or 0.0,
                "nvg_tactical_hl_hours": fl.nvg_tactical_hl_hours or 0.0,
                "nvg_tactical_ll_hours": fl.nvg_tactical_ll_hours or 0.0,
                "syllabus_event_completed": fl.syllabus_event_completed,
                "instructor_remarks": fl.instructor_remarks,
                "special_crew_time_hours": fl.special_crew_time_hours,
                "data_provenance": fl.data_provenance,
                "instrument_approaches": [],
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
            joinedload(Sortie.sortie_tmr_codes).joinedload(SortieTmrCode.tmr_code),
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


# ---------- Logbook ----------

@router.get("/logbook/{person_id}", response_model=LogbookResponse)
def get_logbook(
    person_id: int,
    date_from: Optional[date] = Query(None, description="Filter entries on or after this date (YYYY-MM-DD)"),
    date_to: Optional[date] = Query(None, description="Filter entries on or before this date, end-of-day inclusive"),
    aircraft_id: Optional[int] = Query(None),
    event_code: Optional[str] = Query(None),
    crew_position: Optional[CrewPosition] = Query(None),
    flight_mode: Optional[FlightMode] = Query(None),
    db: Session = Depends(get_db),
):
    """
    Return a person's full flight logbook.

    entries: completed sorties, filtered by query params, newest first.
    totals: four fixed windows (career / 365d / 90d / 30d) computed from ALL
            completed entries regardless of the user's filter.
    """
    person = db.query(Person).filter(Person.id == person_id).first()
    if not person:
        raise HTTPException(status_code=404, detail="Person not found")

    # Single query: all completed flight logs for this person.
    # joinedload for many-to-one (sortie → aircraft); selectinload for one-to-many (approaches).
    all_logs: List[FlightLog] = (
        db.query(FlightLog)
        .join(Sortie, FlightLog.sortie_id == Sortie.id)
        .options(
            joinedload(FlightLog.sortie).joinedload(Sortie.aircraft),
            selectinload(FlightLog.instrument_approaches),
        )
        .filter(
            FlightLog.person_id == person_id,
            Sortie.is_complete == True,
        )
        .order_by(desc(Sortie.takeoff_time), desc(Sortie.id))
        .all()
    )

    # Apply user filters (entries display only — totals always use all_logs)
    display_logs = all_logs
    if date_from is not None:
        cutoff = datetime.combine(date_from, dt_time.min)
        display_logs = [fl for fl in display_logs
                        if fl.sortie.takeoff_time and fl.sortie.takeoff_time >= cutoff]
    if date_to is not None:
        cutoff = datetime.combine(date_to, dt_time.max)
        display_logs = [fl for fl in display_logs
                        if fl.sortie.takeoff_time and fl.sortie.takeoff_time <= cutoff]
    if aircraft_id is not None:
        display_logs = [fl for fl in display_logs if fl.sortie.aircraft_id == aircraft_id]
    if event_code is not None:
        display_logs = [fl for fl in display_logs if fl.sortie.event_code == event_code]
    if crew_position is not None:
        display_logs = [fl for fl in display_logs if fl.crew_position == crew_position]
    if flight_mode is not None:
        display_logs = [fl for fl in display_logs if fl.sortie.flight_mode == flight_mode]

    # Batch-fetch TMR codes for displayed sorties (one query, no N+1)
    display_sortie_ids = [fl.sortie_id for fl in display_logs]
    tmr_by_sortie: dict[int, List[LogbookTmrOut]] = {}
    if display_sortie_ids:
        tmr_rows = (
            db.query(SortieTmrCode)
            .options(joinedload(SortieTmrCode.tmr_code))
            .filter(SortieTmrCode.sortie_id.in_(display_sortie_ids))
            .order_by(SortieTmrCode.slot)
            .all()
        )
        for stc in tmr_rows:
            if stc.tmr_code:
                tmr_by_sortie.setdefault(stc.sortie_id, []).append(
                    LogbookTmrOut(code=stc.tmr_code.code, slot=stc.slot, hours=stc.hours)
                )

    # Build entry list
    entries: List[LogbookEntry] = []
    for fl in display_logs:
        s = fl.sortie
        ac = s.aircraft
        entries.append(LogbookEntry(
            sortie_id=s.id,
            flight_log_id=fl.id,
            date=s.takeoff_time.date().isoformat() if s.takeoff_time else "",
            tms=ac.type_model_series if ac else None,
            bureau_number=ac.bureau_number if ac else None,
            side_number=ac.side_number if ac else None,
            event_code=s.event_code,
            flight_mode=s.flight_mode.value,
            crew_position=fl.crew_position.value,
            departure_location=s.departure_location,
            arrival_location=s.arrival_location,
            total_hours=fl.total_hours or fl.hours_logged,
            night_hours=fl.night_hours or 0.0,
            nvg_hours=fl.nvg_hours or 0.0,
            actual_instrument_hours=fl.actual_instrument_hours or 0.0,
            sim_instrument_hours=fl.sim_instrument_hours or 0.0,
            first_pilot_hours=fl.first_pilot_hours or 0.0,
            copilot_hours=fl.copilot_hours or 0.0,
            ac_commander_hours=fl.ac_commander_hours or 0.0,
            mission_commander_hours=fl.mission_commander_hours or 0.0,
            instructor_hours=fl.instructor_hours or 0.0,
            special_crew_time_hours=fl.special_crew_time_hours or 0.0,
            nvg_unaided_hl_hours=fl.nvg_unaided_hl_hours or 0.0,
            nvg_unaided_ll_hours=fl.nvg_unaided_ll_hours or 0.0,
            nvg_tactical_hl_hours=fl.nvg_tactical_hl_hours or 0.0,
            nvg_tactical_ll_hours=fl.nvg_tactical_ll_hours or 0.0,
            landings_day=s.landings_day or 0,
            landings_night=s.landings_night or 0,
            landings_dve_day=s.landings_dve_day or 0,
            landings_dve_night=s.landings_dve_night or 0,
            landings_shipboard_day=s.landings_shipboard_day or 0,
            landings_shipboard_night=s.landings_shipboard_night or 0,
            approaches=[
                ApproachEntry(
                    type=appr.approach_type.value,
                    conditions=appr.actual_or_simulated.value,
                    airport_icao=appr.airport_icao,
                    runway=appr.runway,
                    approach_remarks=appr.remarks,
                )
                for appr in fl.instrument_approaches
            ],
            tmr_codes=tmr_by_sortie.get(s.id, []),
            remarks=fl.instructor_remarks or s.debrief_notes or None,
            data_provenance=fl.data_provenance.value if fl.data_provenance else None,
        ))

    # Fixed-window totals (independent of user filter)
    window_dict = build_window_totals(all_logs)

    return LogbookResponse(
        person=LogbookPersonOut(
            id=person.id,
            name=f"{person.last_name}, {person.first_name}",
            callsign=person.callsign,
            rank=person.rank,
            role=person.role.value,
        ),
        filters_applied=LogbookFiltersApplied(
            date_from=date_from.isoformat() if date_from else None,
            date_to=date_to.isoformat() if date_to else None,
            aircraft_id=aircraft_id,
            event_code=event_code,
            crew_position=crew_position.value if crew_position else None,
            flight_mode=flight_mode.value if flight_mode else None,
        ),
        entries=entries,
        totals=LogbookWindowTotals(**window_dict),
    )
