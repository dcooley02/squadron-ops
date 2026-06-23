from datetime import datetime, timedelta

from app.models.models import BoardType, SortieOpsStatus
from app.services.instructor_pairing import rank_instructors
from app.schemas.ops import DayOpsOut
from app.services.ops_day import build_day_ops, publish_schedule


def test_rank_instructors_excludes_examinee(db, pilot, cbr_tasks):
    from app.models.models import Person, Qualification, Role

    db.add(Qualification(person_id=pilot.id, qual_code="HAC"))
    ip = Person(
        last_name="Instructor",
        first_name="One",
        role=Role.PILOT,
        username="instructor_one",
        password_hash="x",
        is_active=True,
    )
    db.add(ip)
    db.flush()
    db.add(Qualification(person_id=ip.id, qual_code="HAC"))
    db.flush()
    ranked = rank_instructors(
        db,
        board_type=BoardType.HAC_BOARD,
        examinee_person_id=pilot.id,
        scheduled_at=datetime.utcnow() + timedelta(days=1),
    )
    assert all(r["person_id"] != pilot.id for r in ranked)


def test_publish_schedule_sets_sorties_published(db, pilot, aircraft):
    from app.models.models import FlightLog, CrewPosition, Sortie

    tomorrow = datetime.utcnow().date() + timedelta(days=1)
    takeoff = datetime.combine(tomorrow, datetime.min.time().replace(hour=9))
    sortie = Sortie(
        aircraft_id=aircraft.id,
        event_code="TEST",
        takeoff_time=takeoff,
        is_complete=False,
        ops_status=SortieOpsStatus.PLANNED,
    )
    db.add(sortie)
    db.flush()
    db.add(FlightLog(sortie_id=sortie.id, person_id=pilot.id, crew_position=CrewPosition.HAC))
    db.flush()

    pub = publish_schedule(db, tomorrow, pilot.id, "Test publish")
    db.refresh(sortie)
    assert pub.schedule_date == tomorrow
    assert sortie.ops_status == SortieOpsStatus.PUBLISHED
    assert sortie.schedule_publication_id == pub.id


def test_build_day_ops_matches_schema(db):
    from datetime import date

    out = DayOpsOut.model_validate(build_day_ops(db, date.today()))
    assert out.ops_date == date.today()
    assert out.sortie_count >= 0
    for entry in out.watchbill:
        assert entry.duty_date is not None


def test_publish_schedule_idempotent_guard(db):
    from datetime import date

    day = date.today() + timedelta(days=3)
    publish_schedule(db, day, None, "first")
    import pytest

    with pytest.raises(ValueError, match="already published"):
        publish_schedule(db, day, None, "second")