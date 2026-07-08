from datetime import datetime, timedelta, time as dt_time

from passlib.hash import bcrypt as bc

from app.models.models import CrewPosition, FlightLog, Person, Qualification, Role, Sortie
from app.services.scheduling import (
    compute_fitness,
    detect_person_conflicts,
    propose_week,
    suggest_crew_for_sortie,
)
from app.schemas.scheduling import WeekMissionStub
from app.core.time import utc_now


def _seed_hac(db, *, username: str, last: str) -> Person:
    p = Person(
        last_name=last,
        first_name="Test",
        role=Role.PILOT,
        username=username,
        password_hash=bc.hash("x"),
        is_active=True,
    )
    db.add(p)
    db.flush()
    db.add(Qualification(person_id=p.id, qual_code="HAC"))
    db.flush()
    return p


def test_detect_double_booking(db, aircraft, pilot):
    t0 = utc_now() + timedelta(days=1)
    s1 = Sortie(aircraft_id=aircraft.id, takeoff_time=t0, is_complete=False)
    s2 = Sortie(
        aircraft_id=aircraft.id,
        takeoff_time=t0 + timedelta(minutes=30),
        is_complete=False,
    )
    db.add_all([s1, s2])
    db.flush()
    db.add(FlightLog(sortie_id=s1.id, person_id=pilot.id, crew_position=CrewPosition.HAC))
    db.flush()

    msgs = detect_person_conflicts(db, pilot.id, s2.takeoff_time, s2.takeoff_time + timedelta(hours=2))
    assert any("double-booked" in m.lower() for m in msgs)


def _noon_on(day_offset: int) -> datetime:
    d = utc_now().date() + timedelta(days=day_offset)
    return datetime.combine(d, dt_time(hour=10, minute=0))


def test_suggest_crew_returns_open_slots(db, aircraft):
    hac = _seed_hac(db, username="hac.one", last="One")
    sortie = Sortie(
        aircraft_id=aircraft.id,
        event_code="FAM-101",
        takeoff_time=_noon_on(2),
        duration_hours=2.0,
        is_complete=False,
    )
    db.add(sortie)
    db.flush()

    result = suggest_crew_for_sortie(db, sortie)
    positions = {s.crew_position for s in result.slots}
    assert CrewPosition.HAC in positions
    assert CrewPosition.CREW_CHIEF in positions
    hac_slot = next(s for s in result.slots if s.crew_position == CrewPosition.HAC)
    assert hac_slot.recommended_person_id == hac.id


def test_compute_fitness_red_without_hac(db, aircraft, pilot):
    sortie = Sortie(
        aircraft_id=aircraft.id,
        takeoff_time=utc_now() + timedelta(days=1),
        is_complete=False,
    )
    db.add(sortie)
    db.flush()
    db.add(
        FlightLog(sortie_id=sortie.id, person_id=pilot.id, crew_position=CrewPosition.H2P)
    )
    db.flush()

    fitness = compute_fitness(db, sortie.id)
    assert fitness is not None
    assert fitness.overall_status == "red"
    assert any("HAC slot" in w.message for w in fitness.warnings)


def test_propose_week_draft_not_persisted(db, aircraft):
    before = db.query(Sortie).count()
    stub = WeekMissionStub(
        event_type="PROFICIENCY",
        event_code="FAM-101",
        aircraft_id=aircraft.id,
        takeoff_time=utc_now() + timedelta(days=3),
        positions=[CrewPosition.HAC, CrewPosition.CREW_CHIEF],
    )
    result = propose_week(db, [stub])
    assert len(result.proposals) == 1
    assert db.query(Sortie).count() == before