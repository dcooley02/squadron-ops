"""Watchbill, training boards, and schedule publication."""
from datetime import datetime, timedelta

from app.core.time import utc_now
from app.models.models import (
    Person, Role, WatchbillEntry, WatchbillRole, BoardSchedule, BoardType,
    BoardStatus, SchedulePublication, Sortie, SortieOpsStatus,
)

from seed.constants import TODAY

# ═══════════════════════════════════════════════════════════════════════════════
# SDO watchbill, boards, schedule publication (Phase 4/5 demo)
# ═══════════════════════════════════════════════════════════════════════════════

def seed_watchbill_and_boards(db, all_pilots, aircrew_list, syllabus_events):
    sdo = db.query(Person).filter(Person.role == Role.SDO).first()
    board_count = 0
    if sdo:
        for role, person in [
            (WatchbillRole.SDO, sdo),
            (WatchbillRole.ODO, all_pilots[0] if all_pilots else sdo),
            (WatchbillRole.DUTY_PILOT, all_pilots[1 % len(all_pilots)] if all_pilots else sdo),
            (WatchbillRole.DUTY_AIRCREW, aircrew_list[0] if aircrew_list else sdo),
            (WatchbillRole.ALERT, all_pilots[2 % len(all_pilots)] if len(all_pilots) > 2 else sdo),
        ]:
            db.add(WatchbillEntry(
                duty_date=TODAY, role=role, person_id=person.id,
                shift_label="0700–1900" if role != WatchbillRole.ALERT else "24hr",
            ))

    stan_events = [e for e in syllabus_events if e.is_stan_eval][:2]
    students = [p for p in all_pilots if p.rank in ("LTJG", "LT")][:2]
    instructors = [p for p in all_pilots if p.rank in ("LCDR", "LT")][:2]
    for i, (student, event) in enumerate(zip(students, stan_events)):
        instr = instructors[i % len(instructors)] if instructors else None
        db.add(BoardSchedule(
            board_type=BoardType.HAC_BOARD if i == 0 else BoardType.NATOPS_CHECK,
            scheduled_at=datetime.combine(TODAY + timedelta(days=2 + i), datetime.min.time().replace(hour=13)),
            examinee_person_id=student.id,
            instructor_person_id=instr.id if instr else None,
            syllabus_event_id=event.id,
            status=BoardStatus.SCHEDULED,
            location="Squadron ready room",
            remarks=f"Scheduled {event.event_code} board",
        ))
        board_count += 1

    db.flush()
    return board_count


def seed_publish_today_schedule(db):
    """Publish today's flight schedule for SDO demo."""
    start = datetime.combine(TODAY, datetime.min.time())
    end = datetime.combine(TODAY, datetime.max.time())
    sorties = (
        db.query(Sortie)
        .filter(Sortie.takeoff_time >= start, Sortie.takeoff_time <= end, Sortie.is_complete.is_(False))
        .all()
    )
    if not sorties:
        return 0
    sdo = db.query(Person).filter(Person.role == Role.SDO).first()
    pub = SchedulePublication(
        schedule_date=TODAY,
        published_at=utc_now(),
        published_by_person_id=sdo.id if sdo else None,
        remarks="Daily schedule published — crew notified via squadron ops",
    )
    db.add(pub)
    db.flush()
    for s in sorties:
        s.schedule_publication_id = pub.id
        if s.ops_status == SortieOpsStatus.PLANNED:
            s.ops_status = SortieOpsStatus.PUBLISHED
    db.flush()
    return len(sorties)
