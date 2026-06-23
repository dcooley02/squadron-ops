from datetime import date, datetime, timedelta, time as dt_time
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session, joinedload

from app.database import get_db
from app.models.models import BoardSchedule, BoardStatus, Person, SyllabusEvent
from app.schemas.boards import BoardScheduleCreate, BoardScheduleOut, InstructorCandidate
from app.services.instructor_pairing import rank_instructors

router = APIRouter(prefix="/api/boards", tags=["boards"])


def _board_out(row: BoardSchedule) -> BoardScheduleOut:
    return BoardScheduleOut(
        id=row.id,
        board_type=row.board_type,
        scheduled_at=row.scheduled_at,
        examinee_person_id=row.examinee_person_id,
        examinee_name=(
            f"{row.examinee.last_name}, {row.examinee.first_name}" if row.examinee else ""
        ),
        instructor_person_id=row.instructor_person_id,
        instructor_name=(
            f"{row.instructor.last_name}, {row.instructor.first_name}"
            if row.instructor
            else None
        ),
        syllabus_event_id=row.syllabus_event_id,
        event_code=row.syllabus_event.event_code if row.syllabus_event else None,
        gradecard_id=row.gradecard_id,
        sortie_id=row.sortie_id,
        status=row.status,
        location=row.location,
        remarks=row.remarks,
    )


@router.get("", response_model=List[BoardScheduleOut])
def list_boards(
    days_ahead: int = Query(14, ge=1, le=60),
    status: Optional[BoardStatus] = Query(None),
    db: Session = Depends(get_db),
):
    """Upcoming training boards within the lookahead window."""
    now = datetime.combine(date.today(), dt_time.min)
    end = datetime.combine(date.today() + timedelta(days=days_ahead), dt_time.max)
    q = (
        db.query(BoardSchedule)
        .options(
            joinedload(BoardSchedule.examinee),
            joinedload(BoardSchedule.instructor),
            joinedload(BoardSchedule.syllabus_event),
        )
        .filter(BoardSchedule.scheduled_at >= now, BoardSchedule.scheduled_at <= end)
    )
    if status is not None:
        q = q.filter(BoardSchedule.status == status)
    rows = q.order_by(BoardSchedule.scheduled_at).all()
    return [_board_out(r) for r in rows]


@router.post("", response_model=BoardScheduleOut, status_code=201)
def create_board(payload: BoardScheduleCreate, db: Session = Depends(get_db)):
    if not db.query(Person).filter(Person.id == payload.examinee_person_id).first():
        raise HTTPException(status_code=404, detail="Examinee not found")
    if payload.instructor_person_id and not db.query(Person).filter(
        Person.id == payload.instructor_person_id
    ).first():
        raise HTTPException(status_code=404, detail="Instructor not found")
    if payload.syllabus_event_id and not db.query(SyllabusEvent).filter(
        SyllabusEvent.id == payload.syllabus_event_id
    ).first():
        raise HTTPException(status_code=404, detail="Syllabus event not found")

    row = BoardSchedule(
        board_type=payload.board_type,
        scheduled_at=payload.scheduled_at,
        examinee_person_id=payload.examinee_person_id,
        instructor_person_id=payload.instructor_person_id,
        syllabus_event_id=payload.syllabus_event_id,
        sortie_id=payload.sortie_id,
        location=payload.location,
        remarks=payload.remarks,
        status=BoardStatus.SCHEDULED,
    )
    db.add(row)
    db.commit()
    db.refresh(row)
    loaded = (
        db.query(BoardSchedule)
        .options(
            joinedload(BoardSchedule.examinee),
            joinedload(BoardSchedule.instructor),
            joinedload(BoardSchedule.syllabus_event),
        )
        .filter(BoardSchedule.id == row.id)
        .first()
    )
    return _board_out(loaded)


@router.get("/instructor-candidates", response_model=List[InstructorCandidate])
def instructor_candidates(
    board_type: str = Query(...),
    examinee_person_id: int = Query(...),
    scheduled_at: datetime = Query(...),
    syllabus_event_id: Optional[int] = Query(None),
    db: Session = Depends(get_db),
):
    from app.models.models import BoardType as BT

    try:
        bt = BT(board_type)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=f"Invalid board_type: {board_type}") from exc

    return rank_instructors(
        db,
        board_type=bt,
        examinee_person_id=examinee_person_id,
        scheduled_at=scheduled_at,
        syllabus_event_id=syllabus_event_id,
    )