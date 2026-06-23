from datetime import datetime, timedelta

from app.models.models import (
    CapabilityArea,
    CbrTaskOption,
    CrewPosition,
    CrewScope,
    Sortie,
    SortieTaskCredit,
    TaskGrade,
)
from app.services.readiness import TRating, rate_person_area


def _credit(db, sortie, fl, code, days_ago: int):
    sortie.is_complete = True
    sortie.land_time = datetime.utcnow() - timedelta(days=days_ago)
    db.add(
        SortieTaskCredit(
            sortie_id=sortie.id,
            flight_log_id=fl.id,
            task_code=code,
            grade=TaskGrade.Q,
        )
    )
    db.flush()


def test_rate_person_area_t1_all_current(db, pilot, aircraft, seed_currency):
    for code in ("MOB 203", "MOB 204", "MOB 209"):
        db.add(
            CbrTaskOption(
                code=code,
                capability_area=CapabilityArea.MOB,
                description=code,
                crew_scope=CrewScope.CREW,
            )
        )
    db.flush()

    sortie = Sortie(aircraft_id=aircraft.id, is_complete=False)
    db.add(sortie)
    db.flush()
    from app.models.models import FlightLog

    fl = FlightLog(sortie_id=sortie.id, person_id=pilot.id, crew_position=CrewPosition.HAC)
    db.add(fl)
    db.flush()

    for code, days in (("MOB 203", 30), ("MOB 204", 45), ("MOB 209", 60)):
        _credit(db, sortie, fl, code, days)

    result = rate_person_area(pilot.id, CapabilityArea.MOB, db)
    assert result["rating"] == TRating.T1.value


def test_rate_person_area_t3_no_credits(db, pilot):
    result = rate_person_area(pilot.id, CapabilityArea.MOB, db)
    assert result["rating"] == TRating.T3.value
    assert result["contributing_factors"]