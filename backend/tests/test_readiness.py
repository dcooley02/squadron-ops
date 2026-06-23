from datetime import datetime, timedelta

import pytest
from fastapi.testclient import TestClient
from passlib.hash import bcrypt as bc

from app.models.models import (
    CapabilityArea,
    CapabilityAreaConfig,
    CbrTaskOption,
    CrewPosition,
    CrewScope,
    Person,
    Role,
    Sortie,
    SortieTaskCredit,
    TaskGrade,
)
from app.services.readiness import TRating, build_squadron_readiness, rate_person_area


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


def _add_anchor_tasks(db, codes, area=CapabilityArea.MOB):
    for code in codes:
        db.add(
            CbrTaskOption(
                code=code,
                capability_area=area,
                description=code,
                crew_scope=CrewScope.CREW,
                is_anchor_task=True,
            )
        )
    db.flush()


def test_rate_person_area_t1_all_current(db, pilot, aircraft, seed_currency):
    _add_anchor_tasks(db, ("MOB 203", "MOB 204", "MOB 209"))

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
    assert len(result["anchor_tasks"]) == 3
    assert all(a["status"] == "current" for a in result["anchor_tasks"])


def test_rate_person_area_t3_no_credits(db, pilot):
    result = rate_person_area(pilot.id, CapabilityArea.MOB, db)
    assert result["rating"] == TRating.T3.value
    assert result["contributing_factors"]


def test_rate_person_area_uses_db_config(db, pilot, aircraft):
    db.add(
        CapabilityAreaConfig(
            capability_area=CapabilityArea.MOB,
            label="Mobility (configured)",
            t1_recency_days=90,
            t2_recency_days=200,
            currency_codes=[],
            min_qual_codes=[],
        )
    )
    _add_anchor_tasks(db, ("MOB 203",))

    sortie = Sortie(aircraft_id=aircraft.id, is_complete=False)
    db.add(sortie)
    db.flush()
    from app.models.models import FlightLog

    fl = FlightLog(sortie_id=sortie.id, person_id=pilot.id, crew_position=CrewPosition.HAC)
    db.add(fl)
    db.flush()
    _credit(db, sortie, fl, "MOB 203", 120)

    result = rate_person_area(pilot.id, CapabilityArea.MOB, db)
    assert result["label"] == "Mobility (configured)"
    assert result["t1_window_days"] == 90
    assert result["rating"] == TRating.T2.value
    assert result["anchor_tasks"][0]["status"] == "stale"


def test_build_squadron_readiness_includes_aircrew(db, pilot):
    db.add(
        Person(
            last_name="Test",
            first_name="Aircrew",
            callsign="AWST",
            rank="AW2",
            role=Role.AIRCREW,
            username="test_aircrew",
            password_hash="x",
            is_active=True,
        )
    )
    db.flush()
    summary = build_squadron_readiness(db)
    assert summary["pilots_rated"] >= 1
    assert summary["aircrew_rated"] >= 1
    assert summary["aircrew_overall_rating"]
    assert isinstance(summary["aircrew"], list)


def test_readiness_brief_pdf_endpoint(client: TestClient, db):
    password = "test-readiness-pdf"
    db.add(
        Person(
            last_name="Readiness",
            first_name="Admin",
            role=Role.ADMIN,
            username="readiness.pdf",
            password_hash=bc.hash(password),
            is_active=True,
        )
    )
    db.flush()
    login = client.post(
        "/api/auth/login",
        json={"username": "readiness.pdf", "password": password},
    )
    token = login.json()["access_token"]
    response = client.get(
        "/api/readiness/squadron/brief.pdf",
        headers={"Authorization": f"Bearer {token}"},
    )
    if response.status_code == 503:
        pytest.skip("WeasyPrint not installed")
    assert response.status_code == 200
    assert response.headers["content-type"] == "application/pdf"
    assert response.content[:4] == b"%PDF"