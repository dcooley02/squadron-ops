from datetime import datetime, timedelta

from app.models.models import (
    Currency,
    FlightMode,
    SortieTaskCredit,
    TaskGrade,
)
from app.schemas.logging import TaskCreditCreate
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
    import pytest

    with pytest.raises(ValueError, match="already marked complete"):
        complete_sortie(db, sortie.id, payload)