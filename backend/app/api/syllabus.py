from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session, joinedload
from typing import List, Optional

from app.database import get_db
from app.models.models import (
    SyllabusEvent, GradecardLineItem, Gradecard, GradecardLineItemResult,
    Person, Sortie, FlightLog, Qualification,
    SyllabusLevel, SyllabusTrack, GradingScheme, GradecardStatus, Role,
)
from app.schemas.syllabus import (
    SyllabusEventOut, SyllabusEventTemplate,
    GradecardCreate, GradecardCreateBlank, GradecardOut, GradecardSummary,
    GradecardLineItemResultOut, GradecardLineItemResultPatch, GradecardPatch,
)
from app.schemas.persons import PersonSummary
from app.services.gradecards import compute_overall_status, credit_syllabus_for_gradecard

router = APIRouter(prefix="/api/syllabus", tags=["syllabus"])


# ---------- Helpers ----------

def _load_event_with_items(db: Session, event_code: str) -> SyllabusEvent:
    event = (
        db.query(SyllabusEvent)
        .options(joinedload(SyllabusEvent.line_items))
        .filter(SyllabusEvent.event_code == event_code)
        .first()
    )
    if not event:
        raise HTTPException(status_code=404, detail=f"Syllabus event '{event_code}' not found")
    return event


def _load_gradecard(db: Session, gradecard_id: int) -> Gradecard:
    gc = (
        db.query(Gradecard)
        .options(
            joinedload(Gradecard.line_item_results).joinedload(GradecardLineItemResult.line_item),
        )
        .filter(Gradecard.id == gradecard_id)
        .first()
    )
    if not gc:
        raise HTTPException(status_code=404, detail=f"Gradecard {gradecard_id} not found")
    return gc


# ---------- Syllabus event endpoints ----------

@router.get("/events", response_model=List[SyllabusEventOut])
def list_events(
    track: Optional[SyllabusTrack] = Query(None),
    level: Optional[SyllabusLevel] = Query(None),
    is_stan_eval: Optional[bool] = Query(None),
    db: Session = Depends(get_db),
):
    """List syllabus events. Filters: track, level, is_stan_eval."""
    q = db.query(SyllabusEvent)
    if track is not None:
        q = q.filter(SyllabusEvent.track == track)
    if level is not None:
        q = q.filter(SyllabusEvent.level == level)
    if is_stan_eval is not None:
        q = q.filter(SyllabusEvent.is_stan_eval == is_stan_eval)
    return q.order_by(SyllabusEvent.code).all()


@router.get("/events/{event_code}/template", response_model=SyllabusEventTemplate)
def get_event_template(event_code: str, db: Session = Depends(get_db)):
    """Return one event with its full line item template (alias of detail endpoint)."""
    return _load_event_with_items(db, event_code)


@router.get("/events/{event_code}", response_model=SyllabusEventTemplate)
def get_event(event_code: str, db: Session = Depends(get_db)):
    """Return one event with its full line item template."""
    return _load_event_with_items(db, event_code)


@router.get("/events/{event_id}/instructors", response_model=List[PersonSummary])
def list_eligible_instructors(event_id: int, db: Session = Depends(get_db)):
    """
    Return persons eligible to instruct on this event.
    PILOT_* tracks: active pilots with HAC qualification.
    AIRCREW_* tracks: active aircrewmen with AWS_QUAL qualification.
    """
    event = db.query(SyllabusEvent).filter(SyllabusEvent.id == event_id).first()
    if not event:
        raise HTTPException(status_code=404, detail=f"SyllabusEvent {event_id} not found")

    track_str = event.track.value if event.track else ""
    q = db.query(Person).filter(Person.is_active == True)

    if track_str.startswith("PILOT"):
        q = q.filter(Person.role == Role.PILOT).filter(
            Person.qualifications.any(Qualification.qual_code == "HAC")
        )
    elif track_str.startswith("AIRCREW"):
        q = q.filter(Person.role == Role.AIRCREW).filter(
            Person.qualifications.any(Qualification.qual_code == "AWS_QUAL")
        )

    return q.order_by(Person.last_name, Person.first_name).all()


# ---------- Gradecard endpoints ----------

@router.post("/gradecards/blank", response_model=GradecardOut, status_code=201)
def create_blank_gradecard(payload: GradecardCreateBlank, db: Session = Depends(get_db)):
    """
    Create an IN_PROGRESS gradecard with empty result rows auto-populated
    from the syllabus event's line item template. For the fill-as-you-go
    workflow — instructor scores each line item afterwards via PATCH.
    """
    person = db.query(Person).filter(Person.id == payload.person_id).first()
    if not person:
        raise HTTPException(status_code=404, detail=f"Person {payload.person_id} not found")

    event = (
        db.query(SyllabusEvent)
        .options(joinedload(SyllabusEvent.line_items))
        .filter(SyllabusEvent.id == payload.syllabus_event_id)
        .first()
    )
    if not event:
        raise HTTPException(status_code=404, detail=f"SyllabusEvent {payload.syllabus_event_id} not found")
    if event.grading_scheme is None:
        raise HTTPException(
            status_code=400,
            detail=f"SyllabusEvent {payload.syllabus_event_id} has no grading_scheme; "
                   "set grading_scheme on the event before creating a gradecard",
        )

    if payload.instructor_person_id is not None:
        if not db.query(Person).filter(Person.id == payload.instructor_person_id).first():
            raise HTTPException(status_code=404, detail=f"Instructor {payload.instructor_person_id} not found")

    gc = Gradecard(
        person_id=payload.person_id,
        syllabus_event_id=payload.syllabus_event_id,
        sortie_id=payload.sortie_id,
        flight_log_id=payload.flight_log_id,
        instructor_person_id=payload.instructor_person_id,
        card_date=payload.card_date,
        grading_scheme=event.grading_scheme,
        overall_status=GradecardStatus.IN_PROGRESS,
        remarks=payload.remarks,
    )
    db.add(gc)
    db.flush()

    for li in event.line_items:
        db.add(GradecardLineItemResult(
            gradecard_id=gc.id,
            line_item_id=li.id,
            waived=False,
            completion_status=None,
            four_tier_score=None,
            remarks=None,
        ))

    db.commit()
    return _load_gradecard(db, gc.id)


@router.post("/gradecards", response_model=GradecardOut, status_code=201)
def create_gradecard(payload: GradecardCreate, db: Session = Depends(get_db)):
    """
    Submit a completed (or in-progress) gradecard.
    Derives grading_scheme from the event template and computes overall_status.
    """
    person = db.query(Person).filter(Person.id == payload.person_id).first()
    if not person:
        raise HTTPException(status_code=404, detail=f"Person {payload.person_id} not found")

    event = (
        db.query(SyllabusEvent)
        .options(joinedload(SyllabusEvent.line_items))
        .filter(SyllabusEvent.id == payload.syllabus_event_id)
        .first()
    )
    if not event:
        raise HTTPException(status_code=404, detail=f"SyllabusEvent {payload.syllabus_event_id} not found")
    if event.grading_scheme is None:
        raise HTTPException(
            status_code=400,
            detail=f"SyllabusEvent {payload.syllabus_event_id} has no grading_scheme; "
                   "set grading_scheme on the event before submitting gradecards",
        )

    if payload.sortie_id is not None:
        if not db.query(Sortie).filter(Sortie.id == payload.sortie_id).first():
            raise HTTPException(status_code=404, detail=f"Sortie {payload.sortie_id} not found")

    if payload.flight_log_id is not None:
        if not db.query(FlightLog).filter(FlightLog.id == payload.flight_log_id).first():
            raise HTTPException(status_code=404, detail=f"FlightLog {payload.flight_log_id} not found")

    if payload.instructor_person_id is not None:
        if not db.query(Person).filter(Person.id == payload.instructor_person_id).first():
            raise HTTPException(status_code=404, detail=f"Instructor {payload.instructor_person_id} not found")

    overall_status = compute_overall_status(
        event.grading_scheme,
        event.line_items,
        payload.line_item_results,
    )

    gc = Gradecard(
        person_id=payload.person_id,
        syllabus_event_id=payload.syllabus_event_id,
        sortie_id=payload.sortie_id,
        flight_log_id=payload.flight_log_id,
        instructor_person_id=payload.instructor_person_id,
        card_date=payload.card_date,
        grading_scheme=event.grading_scheme,
        overall_status=overall_status,
        remarks=payload.remarks,
    )
    db.add(gc)
    db.flush()

    for r in payload.line_item_results:
        db.add(GradecardLineItemResult(
            gradecard_id=gc.id,
            line_item_id=r.line_item_id,
            waived=r.waived,
            completion_status=r.completion_status,
            four_tier_score=r.four_tier_score,
            remarks=r.remarks,
        ))

    db.flush()

    # Credit the syllabus event on the flight log if the card passed —
    # runs inside the same transaction so a failure rolls back the whole gradecard.
    try:
        credit_syllabus_for_gradecard(gc, db)
    except Exception as exc:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Syllabus credit update failed: {exc}") from exc

    db.commit()
    return _load_gradecard(db, gc.id)


@router.get("/gradecards/{gradecard_id}", response_model=GradecardOut)
def get_gradecard(gradecard_id: int, db: Session = Depends(get_db)):
    """Return one gradecard with all line item results."""
    return _load_gradecard(db, gradecard_id)


@router.patch(
    "/gradecards/{gradecard_id}/line-items/{result_id}",
    response_model=GradecardLineItemResultOut,
)
def update_gradecard_line_item(
    gradecard_id: int,
    result_id: int,
    payload: GradecardLineItemResultPatch,
    db: Session = Depends(get_db),
):
    """
    Update a single line item result. Used for autosave during gradecard fill.
    Does not recompute overall_status — that happens via PATCH /gradecards/{id}.
    """
    result = (
        db.query(GradecardLineItemResult)
        .options(joinedload(GradecardLineItemResult.line_item))
        .filter(GradecardLineItemResult.id == result_id)
        .first()
    )
    if not result:
        raise HTTPException(status_code=404, detail=f"Line item result {result_id} not found")
    if result.gradecard_id != gradecard_id:
        raise HTTPException(
            status_code=400,
            detail=f"Result {result_id} does not belong to gradecard {gradecard_id}",
        )

    updates = payload.model_dump(exclude_unset=True)
    for k, v in updates.items():
        setattr(result, k, v)

    db.commit()
    db.refresh(result)
    return result


@router.patch("/gradecards/{gradecard_id}", response_model=GradecardOut)
def update_gradecard(
    gradecard_id: int,
    payload: GradecardPatch,
    db: Session = Depends(get_db),
):
    """
    Update gradecard header fields. When overall_status transitions from
    IN_PROGRESS to a terminal value, fires credit_syllabus_for_gradecard.
    """
    gc = _load_gradecard(db, gradecard_id)
    prior_status = gc.overall_status

    updates = payload.model_dump(exclude_unset=True)
    for k, v in updates.items():
        setattr(gc, k, v)

    db.flush()

    if prior_status == GradecardStatus.IN_PROGRESS and gc.overall_status != GradecardStatus.IN_PROGRESS:
        try:
            credit_syllabus_for_gradecard(gc, db)
        except Exception as exc:
            db.rollback()
            raise HTTPException(status_code=500, detail=f"Syllabus credit update failed: {exc}") from exc

    db.commit()
    return _load_gradecard(db, gradecard_id)


@router.get("/persons/{person_id}/gradecards", response_model=List[GradecardSummary])
def list_person_gradecards(person_id: int, db: Session = Depends(get_db)):
    """List a person's gradecards (trimmed, newest first)."""
    if not db.query(Person).filter(Person.id == person_id).first():
        raise HTTPException(status_code=404, detail=f"Person {person_id} not found")

    gcs = (
        db.query(Gradecard)
        .options(joinedload(Gradecard.syllabus_event))
        .filter(Gradecard.person_id == person_id)
        .order_by(Gradecard.card_date.desc())
        .all()
    )

    person = db.query(Person).filter(Person.id == person_id).first()
    person_name = f"{person.last_name}, {person.first_name}"

    return [
        GradecardSummary.model_validate({
            "id": gc.id,
            "event_code": gc.syllabus_event.event_code if gc.syllabus_event else None,
            "person_name": person_name,
            "card_date": gc.card_date,
            "overall_status": gc.overall_status,
            "grading_scheme": gc.grading_scheme,
        })
        for gc in gcs
    ]
