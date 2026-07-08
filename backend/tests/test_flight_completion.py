import pytest

from app.models.models import (
    Currency,
    FlightMode,
    SortieTaskCredit,
    TaskGrade,
)
from app.schemas.logging import TaskCreditCreate, TmrCodeAssignment
from app.services.flight_completion import complete_sortie
from tests.conftest import complete_payload_for, make_open_sortie


def test_complete_sortie_updates_hours_and_marks_complete(db, pilot, aircraft, cbr_tasks):
    sortie, fl = make_open_sortie(db, aircraft=aircraft, pilot=pilot)
    payload = complete_payload_for(sortie, fl)
    result = complete_sortie(db, sortie.id, payload)
    assert result.is_complete is True
    assert result.duration_hours == 2.0
    db.refresh(aircraft)
    assert aircraft.total_airframe_hours == 1002.0


def test_sim_toft_skips_non_sim_task_credits(db, pilot, aircraft, cbr_tasks):
    sortie, fl = make_open_sortie(
        db, aircraft=aircraft, pilot=pilot, flight_mode=FlightMode.SIM_TOFT
    )
    payload = complete_payload_for(
        sortie,
        fl,
        flight_mode=FlightMode.SIM_TOFT,
        task_credits=[
            TaskCreditCreate(
                task_code="MOB 203",
                person_ids=[pilot.id],
                grade=TaskGrade.Q,
            ),
            TaskCreditCreate(
                task_code="MOB 202",
                person_ids=[pilot.id],
                grade=TaskGrade.Q,
            ),
        ],
    )
    complete_sortie(db, sortie.id, payload)
    codes = {
        row.task_code
        for row in db.query(SortieTaskCredit).filter(SortieTaskCredit.flight_log_id == fl.id).all()
    }
    assert "MOB 202" in codes
    assert "MOB 203" not in codes


def test_sim_toft_renews_sim_eligible_currency_only(
    db, pilot, aircraft, cbr_tasks, currency_types
):
    sortie, fl = make_open_sortie(
        db, aircraft=aircraft, pilot=pilot, flight_mode=FlightMode.SIM_TOFT
    )
    payload = complete_payload_for(
        sortie,
        fl,
        flight_mode=FlightMode.SIM_TOFT,
        night_hours=2.0,
        nvg_hours=2.0,
        strafe_profiles_day=3,
        strafe_profiles_night=3,
    )
    hours_before = aircraft.total_airframe_hours
    complete_sortie(db, sortie.id, payload)

    db.refresh(aircraft)
    assert aircraft.total_airframe_hours == hours_before

    codes = {c.currency_code for c in db.query(Currency).filter(Currency.person_id == pilot.id).all()}
    assert "STRAFE_DRY" in codes
    assert "NIGHT_NVD" not in codes


def test_complete_sortie_idempotent_task_credits(db, pilot, aircraft, cbr_tasks):
    sortie, fl = make_open_sortie(db, aircraft=aircraft, pilot=pilot)
    credits = [
        TaskCreditCreate(task_code="MOB 203", person_ids=[pilot.id], grade=TaskGrade.Q),
    ]
    payload = complete_payload_for(sortie, fl, task_credits=credits)
    complete_sortie(db, sortie.id, payload)
    count = db.query(SortieTaskCredit).filter(SortieTaskCredit.flight_log_id == fl.id).count()
    assert count == 1


def test_complete_sortie_rejects_already_complete(db, pilot, aircraft, cbr_tasks):
    sortie, fl = make_open_sortie(db, aircraft=aircraft, pilot=pilot)
    payload = complete_payload_for(sortie, fl)
    complete_sortie(db, sortie.id, payload)

    with pytest.raises(ValueError, match="already marked complete"):
        complete_sortie(db, sortie.id, payload)

    # Hours applied once only despite second attempt
    db.refresh(aircraft)
    assert aircraft.total_airframe_hours == 1002.0


def test_complete_sortie_rejects_unknown_tmr_code(db, pilot, aircraft, cbr_tasks):
    sortie, fl = make_open_sortie(db, aircraft=aircraft, pilot=pilot)
    payload = complete_payload_for(sortie, fl)
    payload = payload.model_copy(
        update={"tmr_codes": [TmrCodeAssignment(code="ZZZZ", slot=1, hours=1.0)]}
    )
    with pytest.raises(ValueError, match="Unknown TMR code"):
        complete_sortie(db, sortie.id, payload)
    db.refresh(sortie)
    assert sortie.is_complete is False
    db.refresh(aircraft)
    assert aircraft.total_airframe_hours == 1000.0


def test_complete_sortie_rejects_person_not_on_sortie(db, pilot, aircraft, cbr_tasks):
    sortie, fl = make_open_sortie(db, aircraft=aircraft, pilot=pilot)
    payload = complete_payload_for(
        sortie,
        fl,
        task_credits=[
            TaskCreditCreate(
                task_code="MOB 203",
                person_ids=[999999],
                grade=TaskGrade.Q,
            ),
        ],
    )
    with pytest.raises(ValueError, match="not on sortie"):
        complete_sortie(db, sortie.id, payload)
    db.refresh(sortie)
    assert sortie.is_complete is False


def test_complete_sortie_rejects_unknown_task_code(db, pilot, aircraft, cbr_tasks):
    sortie, fl = make_open_sortie(db, aircraft=aircraft, pilot=pilot)
    payload = complete_payload_for(
        sortie,
        fl,
        task_credits=[
            TaskCreditCreate(
                task_code="NOT A REAL TASK",
                person_ids=[pilot.id],
                grade=TaskGrade.Q,
            ),
        ],
    )
    with pytest.raises(ValueError, match="Unknown CBR task code"):
        complete_sortie(db, sortie.id, payload)


def test_complete_sortie_per_crew_landings_rollup(db, pilot, aircraft, cbr_tasks):
    """Per-crew landing fields write FlightLog rows and sum to sortie totals."""
    from app.models.models import CrewPosition, FlightLog, Person, Role
    from app.schemas.logging import FlightLogActuals

    co = Person(
        last_name="Co",
        first_name="Pilot",
        role=Role.PILOT,
        username="co.landings",
        password_hash="x",
        is_active=True,
    )
    db.add(co)
    db.flush()
    sortie, hac_fl = make_open_sortie(db, aircraft=aircraft, pilot=pilot)
    co_fl = FlightLog(
        sortie_id=sortie.id,
        person_id=co.id,
        crew_position=CrewPosition.H2P,
        hours_logged=2.0,
    )
    db.add(co_fl)
    db.flush()

    payload = complete_payload_for(sortie, hac_fl)
    payload = payload.model_copy(
        update={
            "flight_log_actuals": [
                FlightLogActuals(
                    flight_log_id=hac_fl.id,
                    hours_logged=2.0,
                    total_hours=2.0,
                    landings_day=2,
                    landings_night=1,
                    landings_shipboard_day=1,
                ),
                FlightLogActuals(
                    flight_log_id=co_fl.id,
                    hours_logged=2.0,
                    total_hours=2.0,
                    landings_day=1,
                    landings_night=0,
                    landings_shipboard_day=0,
                ),
            ],
            # legacy sortie-level should be ignored when per-crew present
            "landings_day": 99,
            "landings_night": 99,
        }
    )
    complete_sortie(db, sortie.id, payload)
    db.refresh(hac_fl)
    db.refresh(co_fl)
    db.refresh(sortie)
    assert hac_fl.landings_day == 2
    assert hac_fl.landings_night == 1
    assert co_fl.landings_day == 1
    assert sortie.landings_day == 3
    assert sortie.landings_night == 1
    assert sortie.landings_shipboard_day == 1

