"""Per-person syllabus progression from gradecards and flight log credits."""
from typing import List

from sqlalchemy.orm import Session

from app.models.models import (
    Gradecard,
    GradecardStatus,
    FlightLog,
    Person,
    Role,
    Sortie,
    SyllabusEvent,
    SyllabusTrack,
)

PASS_STATUSES = {GradecardStatus.PASS, GradecardStatus.COMPLETE}


def _tracks_for_person(person: Person) -> List[SyllabusTrack]:
    if person.role == Role.AIRCREW:
        return [SyllabusTrack.AIRCREW_CORE, SyllabusTrack.AIRCREW_AMCM]
    return [SyllabusTrack.PILOT_CORE, SyllabusTrack.PILOT_AMCM]


def build_syllabus_progress(db: Session, person_id: int) -> List[dict]:
    person = db.query(Person).filter(Person.id == person_id).first()
    if not person:
        return []

    tracks = _tracks_for_person(person)
    events = (
        db.query(SyllabusEvent)
        .filter(SyllabusEvent.track.in_(tracks))
        .order_by(SyllabusEvent.track, SyllabusEvent.level, SyllabusEvent.code)
        .all()
    )

    gradecards = (
        db.query(Gradecard)
        .filter(Gradecard.person_id == person_id)
        .all()
    )
    gc_by_event: dict[int, list[Gradecard]] = {}
    for gc in gradecards:
        gc_by_event.setdefault(gc.syllabus_event_id, []).append(gc)

    credited_codes = {
        row.syllabus_event_completed
        for row in (
            db.query(FlightLog.syllabus_event_completed)
            .join(Sortie, FlightLog.sortie_id == Sortie.id)
            .filter(
                FlightLog.person_id == person_id,
                Sortie.is_complete.is_(True),
                FlightLog.syllabus_event_completed.isnot(None),
            )
            .all()
        )
        if row.syllabus_event_completed
    }

    progress: List[dict] = []
    for event in events:
        cards = gc_by_event.get(event.id, [])
        terminal = [c for c in cards if c.overall_status in PASS_STATUSES]
        in_progress = [c for c in cards if c.overall_status == GradecardStatus.IN_PROGRESS]

        if terminal or (event.event_code and event.event_code in credited_codes):
            status = "COMPLETE"
            gradecard_id = terminal[0].id if terminal else (cards[0].id if cards else None)
        elif in_progress:
            status = "IN_PROGRESS"
            gradecard_id = in_progress[0].id
        else:
            status = "NOT_STARTED"
            gradecard_id = None

        progress.append({
            "syllabus_event_id": event.id,
            "event_code": event.event_code,
            "name": event.name,
            "track": event.track,
            "level": event.level,
            "status": status,
            "gradecard_id": gradecard_id,
            "is_stan_eval": event.is_stan_eval,
        })

    return progress