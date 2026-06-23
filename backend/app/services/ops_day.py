"""
SDO day-of-ops aggregation: schedule publication, watchbill, sortie status strip.
"""
from datetime import date, datetime, time as dt_time
from typing import List, Optional

from sqlalchemy.orm import Session, joinedload

from app.models.models import (
    FlightLog,
    SchedulePublication,
    Sortie,
    SortieOpsStatus,
    WatchbillEntry,
)


def _sorties_for_day(db: Session, day: date) -> List[Sortie]:
    start = datetime.combine(day, dt_time.min)
    end = datetime.combine(day, dt_time.max)
    return (
        db.query(Sortie)
        .options(
            joinedload(Sortie.aircraft),
            joinedload(Sortie.flight_logs).joinedload(FlightLog.person),
            joinedload(Sortie.schedule_publication),
        )
        .filter(Sortie.takeoff_time >= start, Sortie.takeoff_time <= end)
        .order_by(Sortie.takeoff_time)
        .all()
    )


def build_day_ops(db: Session, day: date) -> dict:
    sorties = _sorties_for_day(db, day)
    publication = (
        db.query(SchedulePublication)
        .options(joinedload(SchedulePublication.published_by))
        .filter(SchedulePublication.schedule_date == day)
        .first()
    )
    watchbill = (
        db.query(WatchbillEntry)
        .options(joinedload(WatchbillEntry.person))
        .filter(WatchbillEntry.duty_date == day)
        .order_by(WatchbillEntry.role)
        .all()
    )

    sortie_rows: List[dict] = []
    for s in sorties:
        crew = [
            {
                "person_id": fl.person_id,
                "person_name": f"{fl.person.last_name}, {fl.person.first_name}" if fl.person else "",
                "crew_position": fl.crew_position.value,
            }
            for fl in s.flight_logs
        ]
        sortie_rows.append({
            "id": s.id,
            "event_code": s.event_code,
            "event_type": s.event_type,
            "aircraft_side_number": s.aircraft.side_number if s.aircraft else None,
            "brief_time": s.brief_time,
            "takeoff_time": s.takeoff_time,
            "land_time": s.land_time,
            "ops_status": s.ops_status.value if s.ops_status else SortieOpsStatus.PLANNED.value,
            "is_complete": s.is_complete,
            "mission_summary": s.mission_summary,
            "comm_plan": s.comm_plan,
            "crew": crew,
        })

    return {
        "ops_date": day,
        "is_published": publication is not None,
        "publication": {
            "id": publication.id,
            "schedule_date": publication.schedule_date,
            "published_at": publication.published_at,
            "published_by_name": (
                f"{publication.published_by.last_name}, {publication.published_by.first_name}"
                if publication and publication.published_by
                else None
            ),
            "remarks": publication.remarks if publication else None,
        } if publication else None,
        "watchbill": [
            {
                "id": w.id,
                "role": w.role.value,
                "person_id": w.person_id,
                "person_name": f"{w.person.last_name}, {w.person.first_name}",
                "shift_label": w.shift_label,
                "notes": w.notes,
            }
            for w in watchbill
        ],
        "sorties": sortie_rows,
        "sortie_count": len(sortie_rows),
        "airborne_count": sum(
            1 for s in sorties if s.ops_status == SortieOpsStatus.AIRBORNE
        ),
    }


def publish_schedule(
    db: Session,
    day: date,
    published_by_person_id: Optional[int],
    remarks: Optional[str] = None,
) -> SchedulePublication:
    existing = (
        db.query(SchedulePublication)
        .filter(SchedulePublication.schedule_date == day)
        .first()
    )
    if existing:
        raise ValueError(f"Schedule for {day.isoformat()} is already published")

    pub = SchedulePublication(
        schedule_date=day,
        published_at=datetime.utcnow(),
        published_by_person_id=published_by_person_id,
        remarks=remarks,
    )
    db.add(pub)
    db.flush()

    sorties = _sorties_for_day(db, day)
    for s in sorties:
        if not s.is_complete and s.ops_status == SortieOpsStatus.PLANNED:
            s.ops_status = SortieOpsStatus.PUBLISHED
        s.schedule_publication_id = pub.id

    db.commit()
    db.refresh(pub)
    return pub