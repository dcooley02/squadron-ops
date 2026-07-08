"""
Rank instructors for training boards and syllabus events.
Transparent heuristics — human selects from ranked suggestions.
"""
from datetime import date, datetime, timedelta, time as dt_time
from typing import List, Optional

from sqlalchemy.orm import Session, joinedload

from app.models.models import (
    BoardSchedule,
    BoardStatus,
    BoardType,
    Gradecard,
    Person,
    Role,
    SyllabusEvent,
)

BOARD_INSTRUCTOR_QUALS: dict[BoardType, set[str]] = {
    BoardType.HAC_BOARD: {"HAC"},
    BoardType.INSTRUCTOR_BOARD: {"HAC", "FCP"},
    BoardType.NATOPS_CHECK: {"HAC", "NSI", "INSTR"},
    BoardType.STAN_EVAL: {"FCP", "NSI", "INSTR"},
}


def _person_quals(person: Person) -> set[str]:
    return {q.qual_code for q in person.qualifications}


def _recent_instruction_count(
    db: Session,
    instructor_id: int,
    syllabus_event_id: Optional[int],
    since: date,
) -> int:
    q = db.query(Gradecard).filter(
        Gradecard.instructor_person_id == instructor_id,
        Gradecard.card_date >= since,
    )
    if syllabus_event_id is not None:
        q = q.filter(Gradecard.syllabus_event_id == syllabus_event_id)
    return q.count()


def _boards_same_day(db: Session, instructor_id: int, day: date) -> int:
    start = datetime.combine(day, dt_time.min)
    end = datetime.combine(day, dt_time.max)
    return (
        db.query(BoardSchedule)
        .filter(
            BoardSchedule.instructor_person_id == instructor_id,
            BoardSchedule.status == BoardStatus.SCHEDULED,
            BoardSchedule.scheduled_at >= start,
            BoardSchedule.scheduled_at <= end,
        )
        .count()
    )


def rank_instructors(
    db: Session,
    *,
    board_type: BoardType,
    examinee_person_id: int,
    scheduled_at: datetime,
    syllabus_event_id: Optional[int] = None,
) -> List[dict]:
    required = BOARD_INSTRUCTOR_QUALS.get(board_type, {"HAC"})
    day = scheduled_at.date()
    since = day - timedelta(days=30)

    event: Optional[SyllabusEvent] = None
    if syllabus_event_id is not None:
        event = db.query(SyllabusEvent).filter(SyllabusEvent.id == syllabus_event_id).first()

    track = (event.track.value if event and event.track else "") or ""
    q = (
        db.query(Person)
        .options(joinedload(Person.qualifications))
        .filter(Person.is_active.is_(True))
    )
    if track.startswith("AIRCREW"):
        q = q.filter(Person.role == Role.AIRCREW)
    else:
        q = q.filter(Person.role.in_([Role.PILOT, Role.CO_XO]))

    candidates = q.all()
    ranked: List[dict] = []

    for person in candidates:
        if person.id == examinee_person_id:
            continue
        quals = _person_quals(person)
        if not required.intersection(quals):
            continue

        score = 100
        factors: List[str] = []
        matching = required.intersection(quals)
        factors.append(f"Quals: {', '.join(sorted(matching))}")

        recent = _recent_instruction_count(db, person.id, syllabus_event_id, since)
        if recent > 0:
            penalty = min(recent * 15, 45)
            score -= penalty
            factors.append(f"Taught this event {recent}× in last 30 days")

        same_day = _boards_same_day(db, person.id, day)
        if same_day > 0:
            score -= same_day * 20
            factors.append(f"{same_day} other board(s) same day")

        if "FCP" in quals and board_type == BoardType.STAN_EVAL:
            score += 5
        if "NSI" in quals and board_type == BoardType.NATOPS_CHECK:
            score += 5

        ranked.append({
            "person_id": person.id,
            "person_name": f"{person.last_name}, {person.first_name}",
            "callsign": person.callsign,
            "rank": person.rank,
            "score": score,
            "factors": factors,
        })

    ranked.sort(key=lambda r: r["score"], reverse=True)
    return ranked