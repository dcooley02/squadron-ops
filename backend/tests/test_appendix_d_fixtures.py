"""Hand-verified Appendix D T-rating fixtures.

These cases encode the simplified WTM Appendix D rules implemented in
``app.services.readiness``:

* **T-1** — all area anchor tasks credited within the T-1 recency window AND
  linked Table B-2 currencies current (not expiring within 14 days).
* **T-2** — at least one anchor within the T-2 window, but not all T-1 conditions
  (stale anchors and/or currency expiring within 14 days).
* **T-3** — no anchor within T-2, or required qualifications missing.

Anchor set and windows are table-driven (CapabilityAreaConfig + is_anchor_task).
"""
from __future__ import annotations

from datetime import date, timedelta

from app.catalogs.cbr_enclosure2 import ANCHOR_TASK_CODES, CBR_TASK_SPECS, catalog_stats
from app.models.models import (
    CapabilityArea,
    CapabilityAreaConfig,
    CbrTaskOption,
    CrewPosition,
    CrewScope,
    Currency,
    FlightLog,
    Person,
    Qualification,
    Sortie,
    SortieTaskCredit,
    TaskGrade,
)
from app.services.readiness import TRating, rate_person_area
from app.core.time import utc_now


def test_enclosure2_catalog_integrity():
    stats = catalog_stats()
    assert stats["total_tasks"] >= 90
    assert stats["anchor_tasks"] == len(ANCHOR_TASK_CODES) == 13
    # Every capability area has series coverage
    for area, count in stats["by_area"].items():
        assert count >= 6, f"{area} has only {count} tasks"
    # Anchors exist in catalog and are flagged
    codes = {s.code: s for s in CBR_TASK_SPECS}
    for code in ANCHOR_TASK_CODES:
        assert code in codes
        assert codes[code].is_anchor_task is True
    # Unique codes
    assert len(codes) == len(CBR_TASK_SPECS)


def _seed_mob_area(db):
    db.add(
        CapabilityAreaConfig(
            capability_area=CapabilityArea.MOB,
            label="Mobility",
            t1_recency_days=180,
            t2_recency_days=365,
            currency_codes=["NIGHT_NVD"],
            min_qual_codes=[],
        )
    )
    for code in ("MOB 203", "MOB 204", "MOB 209"):
        db.add(
            CbrTaskOption(
                code=code,
                capability_area=CapabilityArea.MOB,
                description=code,
                crew_scope=CrewScope.CREW,
                is_anchor_task=True,
            )
        )
    db.flush()


def _credit(db, fl: FlightLog, sortie: Sortie, code: str, days_ago: int):
    sortie.is_complete = True
    sortie.land_time = utc_now() - timedelta(days=days_ago)
    db.add(
        SortieTaskCredit(
            sortie_id=sortie.id,
            flight_log_id=fl.id,
            task_code=code,
            grade=TaskGrade.Q,
        )
    )
    db.flush()


def _open_log(db, pilot: Person, aircraft) -> tuple[Sortie, FlightLog]:
    sortie = Sortie(aircraft_id=aircraft.id, is_complete=False)
    db.add(sortie)
    db.flush()
    fl = FlightLog(sortie_id=sortie.id, person_id=pilot.id, crew_position=CrewPosition.HAC)
    db.add(fl)
    db.flush()
    return sortie, fl


def test_fixture_t1_all_anchors_current_and_currency_current(db, pilot, aircraft, currency_types):
    """Fixture A — T-1: three MOB anchors within 180d + NIGHT_NVD current."""
    _seed_mob_area(db)
    today = date.today()
    ct = currency_types["NIGHT_NVD"]
    db.add(
        Currency(
            person_id=pilot.id,
            currency_type_id=ct.id,
            currency_code=ct.code,
            last_event_date=today - timedelta(days=10),
            expires_date=today + timedelta(days=35),
        )
    )
    db.flush()

    sortie, fl = _open_log(db, pilot, aircraft)
    for code, days in (("MOB 203", 20), ("MOB 204", 40), ("MOB 209", 90)):
        _credit(db, fl, sortie, code, days)

    result = rate_person_area(pilot.id, CapabilityArea.MOB, db, today=today)
    assert result["rating"] == TRating.T1.value
    assert all(a["status"] == "current" for a in result["anchor_tasks"])


def test_fixture_t2_stale_anchor(db, pilot, aircraft, currency_types):
    """Fixture B — T-2: one anchor outside T-1 (180d) but inside T-2 (365d)."""
    _seed_mob_area(db)
    today = date.today()
    ct = currency_types["NIGHT_NVD"]
    db.add(
        Currency(
            person_id=pilot.id,
            currency_type_id=ct.id,
            currency_code=ct.code,
            last_event_date=today - timedelta(days=10),
            expires_date=today + timedelta(days=35),
        )
    )
    db.flush()

    sortie, fl = _open_log(db, pilot, aircraft)
    _credit(db, fl, sortie, "MOB 203", 30)
    _credit(db, fl, sortie, "MOB 204", 30)
    _credit(db, fl, sortie, "MOB 209", 200)  # stale (between 180 and 365)

    result = rate_person_area(pilot.id, CapabilityArea.MOB, db, today=today)
    assert result["rating"] == TRating.T2.value
    statuses = {a["task_code"]: a["status"] for a in result["anchor_tasks"]}
    assert statuses["MOB 209"] == "stale"
    assert any("stale" in f for f in result["contributing_factors"])


def test_fixture_t2_currency_expiring_within_14d(db, pilot, aircraft, currency_types):
    """Fixture C — T-2 gate: anchors current but currency expires within 14 days."""
    _seed_mob_area(db)
    today = date.today()
    ct = currency_types["NIGHT_NVD"]
    db.add(
        Currency(
            person_id=pilot.id,
            currency_type_id=ct.id,
            currency_code=ct.code,
            last_event_date=today - timedelta(days=40),
            expires_date=today + timedelta(days=7),
        )
    )
    db.flush()

    sortie, fl = _open_log(db, pilot, aircraft)
    for code in ("MOB 203", "MOB 204", "MOB 209"):
        _credit(db, fl, sortie, code, 15)

    result = rate_person_area(pilot.id, CapabilityArea.MOB, db, today=today)
    assert result["rating"] == TRating.T2.value
    assert any("expiring" in f.lower() or "expires" in f.lower() for f in result["contributing_factors"])


def test_fixture_t3_no_anchors(db, pilot):
    """Fixture D — T-3: no qualifying anchor credits."""
    _seed_mob_area(db)
    result = rate_person_area(pilot.id, CapabilityArea.MOB, db)
    assert result["rating"] == TRating.T3.value
    assert any("no qualifying credit" in f for f in result["contributing_factors"])


def test_fixture_t3_missing_required_qualification(db, pilot, aircraft):
    """Fixture E — T-3: area requires a qualification the pilot does not hold."""
    db.add(
        CapabilityAreaConfig(
            capability_area=CapabilityArea.MOB,
            label="Mobility",
            t1_recency_days=180,
            t2_recency_days=365,
            currency_codes=[],
            min_qual_codes=["HAC"],
        )
    )
    db.add(
        CbrTaskOption(
            code="MOB 203",
            capability_area=CapabilityArea.MOB,
            description="MOB 203",
            crew_scope=CrewScope.CREW,
            is_anchor_task=True,
        )
    )
    db.flush()
    # Pilot has no HAC qualification
    sortie, fl = _open_log(db, pilot, aircraft)
    _credit(db, fl, sortie, "MOB 203", 10)

    result = rate_person_area(pilot.id, CapabilityArea.MOB, db)
    assert result["rating"] == TRating.T3.value
    assert any("HAC" in f for f in result["contributing_factors"])


def test_fixture_t1_with_required_qualification(db, pilot, aircraft):
    """Fixture F — T-1 when required qual is present and anchors current."""
    db.add(
        CapabilityAreaConfig(
            capability_area=CapabilityArea.MOB,
            label="Mobility",
            t1_recency_days=180,
            t2_recency_days=365,
            currency_codes=[],
            min_qual_codes=["HAC"],
        )
    )
    for code in ("MOB 203", "MOB 204", "MOB 209"):
        db.add(
            CbrTaskOption(
                code=code,
                capability_area=CapabilityArea.MOB,
                description=code,
                crew_scope=CrewScope.CREW,
                is_anchor_task=True,
            )
        )
    db.add(Qualification(person_id=pilot.id, qual_code="HAC"))
    db.flush()

    sortie, fl = _open_log(db, pilot, aircraft)
    for code in ("MOB 203", "MOB 204", "MOB 209"):
        _credit(db, fl, sortie, code, 10)

    result = rate_person_area(pilot.id, CapabilityArea.MOB, db)
    assert result["rating"] == TRating.T1.value
