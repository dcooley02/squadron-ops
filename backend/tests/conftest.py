"""Postgres-backed pytest fixtures (enums/JSON require Postgres, not SQLite)."""
import os
from datetime import datetime, timedelta

import pytest
from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session, sessionmaker

from app.database import Base
from app.models import models  # noqa: F401
from app.models.models import (
    Aircraft,
    AircraftStatus,
    CapabilityArea,
    CbrTaskOption,
    CrewPosition,
    CrewScope,
    Currency,
    CurrencyApplicability,
    CurrencyAudience,
    CurrencyType,
    FlightLog,
    FlightMode,
    Person,
    Role,
    Sortie,
    TaskGrade,
)

TEST_DATABASE_URL = os.getenv(
    "TEST_DATABASE_URL",
    "postgresql+psycopg://squadron_ops:changeme@localhost:5433/squadron_ops_test",
)


def _ensure_test_database() -> None:
    db_name = TEST_DATABASE_URL.rsplit("/", 1)[-1]
    admin_url = TEST_DATABASE_URL.rsplit("/", 1)[0] + "/postgres"
    admin_engine = create_engine(admin_url, isolation_level="AUTOCOMMIT")
    with admin_engine.connect() as conn:
        exists = conn.execute(
            text("SELECT 1 FROM pg_database WHERE datname = :name"),
            {"name": db_name},
        ).scalar()
        if not exists:
            conn.execute(text(f'CREATE DATABASE "{db_name}"'))
    admin_engine.dispose()


@pytest.fixture(scope="session")
def engine():
    _ensure_test_database()
    eng = create_engine(TEST_DATABASE_URL)
    Base.metadata.drop_all(eng)
    Base.metadata.create_all(eng)
    yield eng
    eng.dispose()


@pytest.fixture
def db(engine) -> Session:
    connection = engine.connect()
    transaction = connection.begin()
    session = sessionmaker(bind=connection)()
    yield session
    session.close()
    transaction.rollback()
    connection.close()


@pytest.fixture
def pilot(db: Session) -> Person:
    person = Person(
        last_name="Test",
        first_name="Pilot",
        callsign="TEST",
        rank="LT",
        role=Role.PILOT,
        username="test_pilot",
        password_hash="x",
        is_active=True,
    )
    db.add(person)
    db.flush()
    return person


@pytest.fixture
def aircraft(db: Session) -> Aircraft:
    ac = Aircraft(
        bureau_number="999999",
        side_number="999",
        type_model_series="MH-60S",
        total_airframe_hours=1000.0,
        hours_since_phase=50.0,
        status=AircraftStatus.FMC,
    )
    db.add(ac)
    db.flush()
    return ac


@pytest.fixture
def cbr_tasks(db: Session) -> dict[str, CbrTaskOption]:
    specs = [
        ("MOB 203", CapabilityArea.MOB, False),
        ("MOB 202", CapabilityArea.MOB, True),
        ("ASU 201", CapabilityArea.ASU, False),
        ("MIW 203", CapabilityArea.MIW, True),
    ]
    out: dict[str, CbrTaskOption] = {}
    for code, area, sim_eligible in specs:
        row = CbrTaskOption(
            code=code,
            capability_area=area,
            description=f"Test task {code}",
            crew_scope=CrewScope.CREW,
            sim_eligible=sim_eligible,
        )
        db.add(row)
        out[code] = row
    db.flush()
    return out


@pytest.fixture
def currency_types(db: Session) -> dict[str, CurrencyType]:
    specs = [
        ("NIGHT_NVD", False, CurrencyAudience.ALL_PILOTS),
        ("STRAFE_DRY", True, CurrencyAudience.ALL_PILOTS),
    ]
    out: dict[str, CurrencyType] = {}
    for code, sim_eligible, audience in specs:
        ct = CurrencyType(
            code=code,
            name=code,
            periodicity_days=45,
            requirement_text="test",
            sim_eligible=sim_eligible,
        )
        db.add(ct)
        db.flush()
        db.add(CurrencyApplicability(currency_type_id=ct.id, applies_to=audience))
        out[code] = ct
    db.flush()
    return out


def make_open_sortie(
    db: Session,
    *,
    aircraft: Aircraft,
    pilot: Person,
    flight_mode: FlightMode = FlightMode.LIVE,
) -> tuple[Sortie, FlightLog]:
    now = datetime.utcnow()
    sortie = Sortie(
        event_type="PROFICIENCY",
        aircraft_id=aircraft.id,
        brief_time=now,
        flight_mode=flight_mode,
        is_complete=False,
    )
    db.add(sortie)
    db.flush()
    fl = FlightLog(
        sortie_id=sortie.id,
        person_id=pilot.id,
        crew_position=CrewPosition.HAC,
        hours_logged=2.0,
    )
    db.add(fl)
    db.flush()
    return sortie, fl


def complete_payload_for(
    sortie: Sortie,
    fl: FlightLog,
    *,
    flight_mode: FlightMode | None = None,
    night_hours: float = 0.0,
    nvg_hours: float = 0.0,
    strafe_profiles_day: int = 0,
    strafe_profiles_night: int = 0,
    task_credits: list | None = None,
):
    from app.schemas.logging import FlightLogActuals, SortieCompletePayload, TaskCreditCreate

    now = datetime.utcnow()
    return SortieCompletePayload(
        actual_takeoff_time=now - timedelta(hours=2),
        actual_land_time=now,
        duration_hours=2.0,
        flight_mode=flight_mode,
        strafe_dry_profiles_day=strafe_profiles_day,
        strafe_dry_profiles_night=strafe_profiles_night,
        flight_log_actuals=[
            FlightLogActuals(
                flight_log_id=fl.id,
                hours_logged=2.0,
                night_hours=night_hours,
                nvg_hours=nvg_hours,
            )
        ],
        task_credits=task_credits or [],
    )


@pytest.fixture
def seed_currency(db: Session, pilot: Person, currency_types: dict[str, CurrencyType]) -> Currency:
    ct = currency_types["NIGHT_NVD"]
    today = datetime.utcnow().date()
    row = Currency(
        person_id=pilot.id,
        currency_type_id=ct.id,
        currency_code=ct.code,
        last_event_date=today - timedelta(days=10),
        expires_date=today + timedelta(days=35),
    )
    db.add(row)
    db.flush()
    return row