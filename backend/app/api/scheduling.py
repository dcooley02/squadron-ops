from fastapi import APIRouter, Depends, HTTPException, Query, Response
from sqlalchemy.orm import Session, joinedload
from datetime import date, datetime, timedelta, time as dt_time
from typing import List

from app.core.deps import get_current_user, require_roles
from app.database import get_db
from app.models.models import Person, Sortie, FlightLog, CrewPosition, Role
from app.schemas.sorties import SortieSummary, FlightLogOut
from app.schemas.scheduling import (
    EligibleCrewmember, SortieFitness,
    SortieCreate, FlightLogCreate,
    SuggestCrewResponse, ApplyCrewSuggestion, ApplySuggestionsResponse,
    ProposeWeekRequest, ProposeWeekResponse,
)
from app.services.scheduling import (
    get_eligible_crew,
    compute_fitness,
    suggest_crew_for_sortie,
    propose_week,
)

router = APIRouter(prefix="/api/scheduling", tags=["scheduling"])


# ─── Local helpers (mirror app.api.sorties but kept here for module independence) ──

def _sortie_summary(s: Sortie) -> SortieSummary:
    return SortieSummary.model_validate({
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
        "ops_status": s.ops_status,
        "mission_summary": s.mission_summary,
    })


def _log_out(fl: FlightLog) -> FlightLogOut:
    return FlightLogOut.model_validate({
        "id": fl.id,
        "person_id": fl.person_id,
        "person_name": f"{fl.person.last_name}, {fl.person.first_name}",
        "crew_position": fl.crew_position,
        "hours_logged": fl.hours_logged,
        "syllabus_event_completed": fl.syllabus_event_completed,
        "crew_qual_code": fl.crew_qual_code,
    })


# ─── Endpoints ────────────────────────────────────────────────────────────────

@router.get("/sorties/upcoming", response_model=List[SortieSummary])
def upcoming_sorties(db: Session = Depends(get_db)):
    """List incomplete sorties scheduled in the next 7 days."""
    now = datetime.combine(date.today(), dt_time.min)
    end = datetime.combine(date.today() + timedelta(days=7), dt_time.max)
    sorties = (
        db.query(Sortie)
        .options(joinedload(Sortie.aircraft))
        .filter(
            Sortie.is_complete == False,
            Sortie.takeoff_time >= now,
            Sortie.takeoff_time <= end,
        )
        .order_by(Sortie.takeoff_time)
        .all()
    )
    return [_sortie_summary(s) for s in sorties]


@router.get("/sorties/{sortie_id}/eligible-crew", response_model=List[EligibleCrewmember])
def eligible_crew(
    sortie_id: int,
    crew_position: CrewPosition = Query(..., description="Crew position to fill"),
    db: Session = Depends(get_db),
):
    """Return ranked eligible crew for a given position on a sortie."""
    sortie = db.query(Sortie).filter(Sortie.id == sortie_id).first()
    if not sortie:
        raise HTTPException(status_code=404, detail=f"Sortie {sortie_id} not found")
    return get_eligible_crew(db, sortie, crew_position)


@router.get("/sorties/{sortie_id}/fitness", response_model=SortieFitness)
def sortie_fitness(sortie_id: int, db: Session = Depends(get_db)):
    """Return the fitness assessment for a sortie's assigned crew."""
    result = compute_fitness(db, sortie_id)
    if result is None:
        raise HTTPException(status_code=404, detail=f"Sortie {sortie_id} not found")
    return result


@router.post("/sorties/{sortie_id}/suggest-crew", response_model=SuggestCrewResponse)
def suggest_crew(sortie_id: int, db: Session = Depends(get_db), _: Person = Depends(get_current_user)):
    sortie = (
        db.query(Sortie)
        .options(joinedload(Sortie.flight_logs))
        .filter(Sortie.id == sortie_id)
        .first()
    )
    if not sortie:
        raise HTTPException(status_code=404, detail=f"Sortie {sortie_id} not found")
    return suggest_crew_for_sortie(db, sortie)


@router.post("/sorties/{sortie_id}/apply-suggestions", response_model=ApplySuggestionsResponse)
def apply_suggestions(
    sortie_id: int,
    payload: List[ApplyCrewSuggestion],
    db: Session = Depends(get_db),
    _: Person = Depends(require_roles(Role.SDO, Role.CO_XO)),
):
    sortie = db.query(Sortie).filter(Sortie.id == sortie_id).first()
    if not sortie:
        raise HTTPException(status_code=404, detail=f"Sortie {sortie_id} not found")

    assigned: list[FlightLogCreate] = []
    skipped: list[str] = []

    for item in payload:
        duplicate = (
            db.query(FlightLog)
            .filter(FlightLog.sortie_id == sortie_id, FlightLog.person_id == item.person_id)
            .first()
        )
        if duplicate:
            skipped.append(f"Person {item.person_id} already assigned")
            continue
        pos_taken = (
            db.query(FlightLog)
            .filter(FlightLog.sortie_id == sortie_id, FlightLog.crew_position == item.crew_position)
            .first()
        )
        if pos_taken:
            skipped.append(f"{item.crew_position.value} slot already filled")
            continue
        fl = FlightLog(
            sortie_id=sortie_id,
            person_id=item.person_id,
            crew_position=item.crew_position,
            hours_logged=sortie.duration_hours or 0.0,
        )
        db.add(fl)
        assigned.append(FlightLogCreate(
            person_id=item.person_id,
            crew_position=item.crew_position,
            hours_logged=sortie.duration_hours,
        ))

    db.commit()
    return ApplySuggestionsResponse(assigned=assigned, skipped=skipped)


@router.post("/propose-week", response_model=ProposeWeekResponse)
def propose_week_schedule(
    body: ProposeWeekRequest,
    db: Session = Depends(get_db),
    _: Person = Depends(get_current_user),
):
    if not body.missions:
        raise HTTPException(status_code=400, detail="At least one mission stub is required")
    return propose_week(db, body.missions)


@router.post("/sorties", response_model=SortieSummary, status_code=201)
def create_sortie(
    payload: SortieCreate,
    db: Session = Depends(get_db),
    _: Person = Depends(require_roles(Role.SDO, Role.CO_XO)),
):
    """Create a new planned sortie (is_complete=False)."""
    sortie = Sortie(
        event_type=payload.event_type,
        event_code=payload.event_code,
        aircraft_id=payload.aircraft_id,
        brief_time=payload.brief_time,
        takeoff_time=payload.takeoff_time,
        land_time=payload.land_time,
        duration_hours=payload.duration_hours,
        notes=payload.notes,
        is_complete=False,
    )
    db.add(sortie)
    db.flush()
    sortie_id = sortie.id

    loaded = (
        db.query(Sortie)
        .options(joinedload(Sortie.aircraft))
        .filter(Sortie.id == sortie_id)
        .first()
    )
    response = _sortie_summary(loaded)
    db.commit()
    return response


@router.post("/sorties/{sortie_id}/crew", response_model=FlightLogOut, status_code=201)
def add_crew(
    sortie_id: int,
    payload: FlightLogCreate,
    db: Session = Depends(get_db),
    _: Person = Depends(require_roles(Role.SDO, Role.CO_XO)),
):
    """Assign a person to a planned sortie."""
    sortie = db.query(Sortie).filter(Sortie.id == sortie_id).first()
    if not sortie:
        raise HTTPException(status_code=404, detail=f"Sortie {sortie_id} not found")

    duplicate = (
        db.query(FlightLog)
        .filter(FlightLog.sortie_id == sortie_id, FlightLog.person_id == payload.person_id)
        .first()
    )
    if duplicate:
        raise HTTPException(
            status_code=400,
            detail=f"Person {payload.person_id} is already assigned to sortie {sortie_id}",
        )

    hours = payload.hours_logged if payload.hours_logged is not None else (sortie.duration_hours or 0.0)
    fl = FlightLog(
        sortie_id=sortie_id,
        person_id=payload.person_id,
        crew_position=payload.crew_position,
        hours_logged=hours,
        syllabus_event_completed=payload.syllabus_event_completed,
    )
    db.add(fl)
    db.flush()
    fl_id = fl.id

    loaded_fl = (
        db.query(FlightLog)
        .options(joinedload(FlightLog.person))
        .filter(FlightLog.id == fl_id)
        .first()
    )
    response = _log_out(loaded_fl)
    db.commit()
    return response


@router.delete("/sorties/{sortie_id}/crew/{flight_log_id}", status_code=204)
def remove_crew(
    sortie_id: int,
    flight_log_id: int,
    db: Session = Depends(get_db),
    _: Person = Depends(require_roles(Role.SDO, Role.CO_XO)),
):
    """Remove a crewmember assignment from a sortie."""
    fl = (
        db.query(FlightLog)
        .filter(FlightLog.id == flight_log_id, FlightLog.sortie_id == sortie_id)
        .first()
    )
    if not fl:
        raise HTTPException(
            status_code=404,
            detail=f"Flight log {flight_log_id} not found on sortie {sortie_id}",
        )
    db.delete(fl)
    db.commit()
    return Response(status_code=204)


@router.delete("/sorties/{sortie_id}", status_code=204)
def delete_sortie(
    sortie_id: int,
    db: Session = Depends(get_db),
    _: Person = Depends(require_roles(Role.SDO, Role.CO_XO)),
):
    """Delete a planned sortie. Refused for completed (historical) sorties."""
    sortie = db.query(Sortie).filter(Sortie.id == sortie_id).first()
    if not sortie:
        raise HTTPException(status_code=404, detail=f"Sortie {sortie_id} not found")
    if sortie.is_complete:
        raise HTTPException(
            status_code=400,
            detail="Cannot delete a completed sortie — it is a historical record",
        )
    db.delete(sortie)
    db.commit()
    return Response(status_code=204)
