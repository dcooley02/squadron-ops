from datetime import date

import pytest

from app.models.models import (
    AircraftInspection,
    AircraftStatus,
    Discrepancy,
    DiscrepancySeverity,
    DiscrepancyWorkStatus,
    InspectionType,
)
from app.schemas.aircraft import QaReleaseRequest
from app.services.qa_release import collect_release_blockers, qa_release
from app.core.time import utc_now


def _add_disc(db, aircraft, severity, work_status):
    disc = Discrepancy(
        aircraft_id=aircraft.id,
        description="test discrepancy",
        severity=severity,
        work_status=work_status,
        is_open=work_status != DiscrepancyWorkStatus.CLOSED,
        opened_date=utc_now(),
    )
    db.add(disc)
    db.flush()
    return disc


def test_collect_release_blockers_downing_open(db, aircraft):
    disc = _add_disc(db, aircraft, DiscrepancySeverity.DOWNING, DiscrepancyWorkStatus.IN_WORK)
    blockers, computed = collect_release_blockers(aircraft, [disc], [])
    assert computed == AircraftStatus.NMCM
    assert any("DOWNING" in b for b in blockers)


def test_qa_release_stamps_fmc_when_all_clear(db, aircraft):
    aircraft.status = AircraftStatus.NMCM
    body = QaReleaseRequest(qa_notes="QA signoff — safe for flight")
    detail = qa_release(db, aircraft.id, body)
    assert detail.status == AircraftStatus.FMC
    db.refresh(aircraft)
    assert "QA Release" in (aircraft.notes or "")


def test_qa_release_blocked_with_open_downing(db, aircraft):
    _add_disc(db, aircraft, DiscrepancySeverity.DOWNING, DiscrepancyWorkStatus.AWP)
    body = QaReleaseRequest(qa_notes="Attempt release")
    with pytest.raises(PermissionError) as exc:
        qa_release(db, aircraft.id, body)
    assert any("DOWNING" in msg or "NMCS" in msg for msg in exc.value.args[0])


def test_qa_release_closes_discrepancy_then_releases(db, aircraft):
    disc = _add_disc(db, aircraft, DiscrepancySeverity.MAJOR, DiscrepancyWorkStatus.COMPLETED)
    aircraft.status = AircraftStatus.PMC
    body = QaReleaseRequest(
        qa_notes="Major discrepancy corrected",
        close_discrepancy_ids=[disc.id],
        corrective_action="Replaced component",
    )
    detail = qa_release(db, aircraft.id, body)
    assert detail.status == AircraftStatus.FMC
    db.refresh(disc)
    assert disc.work_status == DiscrepancyWorkStatus.CLOSED


def test_qa_release_blocked_on_overdue_downing_inspection(db, aircraft):
    insp_type = InspectionType(code="PHASE", name="Phase", is_downing_when_overdue=True)
    db.add(insp_type)
    db.flush()
    overdue = AircraftInspection(
        aircraft_id=aircraft.id,
        inspection_type_id=insp_type.id,
        inspection_type=insp_type,
        next_due_date=date(2020, 1, 1),
    )
    db.add(overdue)
    db.flush()
    body = QaReleaseRequest(qa_notes="Attempt release")
    with pytest.raises(PermissionError):
        qa_release(db, aircraft.id, body)