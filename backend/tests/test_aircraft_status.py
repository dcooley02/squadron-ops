from datetime import date

from app.models.models import (
    Aircraft,
    AircraftInspection,
    AircraftStatus,
    Discrepancy,
    DiscrepancySeverity,
    DiscrepancyWorkStatus,
    InspectionType,
)
from app.services.aircraft_status import compute_status


def _disc(severity, work_status):
    return Discrepancy(
        aircraft_id=1,
        description="test",
        severity=severity,
        work_status=work_status,
        is_open=work_status != DiscrepancyWorkStatus.CLOSED,
    )


def test_compute_status_fmc_when_clear():
    ac = Aircraft(bureau_number="1", status=AircraftStatus.FMC)
    assert compute_status(ac, [], []) == AircraftStatus.FMC


def test_compute_status_manual_override_wins():
    ac = Aircraft(
        bureau_number="1",
        status=AircraftStatus.FMC,
        manual_status_override=AircraftStatus.PMC,
    )
    assert compute_status(ac, [_disc(DiscrepancySeverity.DOWNING, DiscrepancyWorkStatus.OPEN)], []) == (
        AircraftStatus.PMC
    )


def test_compute_status_nmcs_on_downing_awp():
    ac = Aircraft(bureau_number="1", status=AircraftStatus.FMC)
    discs = [_disc(DiscrepancySeverity.DOWNING, DiscrepancyWorkStatus.AWP)]
    assert compute_status(ac, discs, []) == AircraftStatus.NMCS


def test_compute_status_nmcm_on_downing_in_work():
    ac = Aircraft(bureau_number="1", status=AircraftStatus.FMC)
    discs = [_disc(DiscrepancySeverity.DOWNING, DiscrepancyWorkStatus.IN_WORK)]
    assert compute_status(ac, discs, []) == AircraftStatus.NMCM


def test_compute_status_pmc_on_major_open():
    ac = Aircraft(bureau_number="1", status=AircraftStatus.FMC)
    discs = [_disc(DiscrepancySeverity.MAJOR, DiscrepancyWorkStatus.OPEN)]
    assert compute_status(ac, discs, []) == AircraftStatus.PMC


def test_compute_status_nmcm_on_downing_inspection_overdue():
    ac = Aircraft(bureau_number="1", status=AircraftStatus.FMC)
    insp_type = InspectionType(code="PHASE", name="Phase", is_downing_when_overdue=True)
    overdue = AircraftInspection(
        aircraft_id=1,
        inspection_type_id=1,
        inspection_type=insp_type,
        next_due_date=date(2020, 1, 1),
    )
    assert compute_status(ac, [], [overdue]) == AircraftStatus.NMCM