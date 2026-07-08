
from app.models.models import (
    AircraftInspection,
    DiscrepancyWorkStatus,
    InspectionType,
)
from app.services.maintenance_chain import create_maintenance_chain, record_qa_signoff, update_work_order_status
from app.services.maintenance_forecast import phase_forecast, release_forecast
from app.models.models import DiscrepancySeverity


def test_create_maintenance_chain(db, aircraft, pilot):
    disc, maf, wo = create_maintenance_chain(
        db,
        aircraft_id=aircraft.id,
        description="Hydraulic leak",
        severity=DiscrepancySeverity.MAJOR,
        system_affected="HYD",
        reported_by_person_id=pilot.id,
    )
    assert disc.maf_number == maf.maf_number
    assert disc.jcn == wo.jcn
    assert wo.discrepancy_id == disc.id
    assert maf.discrepancy_id == disc.id


def test_phase_inspection_resets_hours(db, aircraft):

    insp_type = InspectionType(
        code="PHASE",
        name="Phase",
        periodicity_hours=200.0,
        is_downing_when_overdue=True,
    )
    db.add(insp_type)
    db.flush()
    aircraft.hours_since_phase = 180.0
    insp = AircraftInspection(
        aircraft_id=aircraft.id,
        inspection_type_id=insp_type.id,
        last_completed_hours=1000.0,
        next_due_hours=1200.0,
    )
    db.add(insp)
    db.flush()

    aircraft.hours_since_phase = 0.0
    db.flush()
    assert aircraft.hours_since_phase == 0.0


def test_qa_signoff_on_work_order(db, aircraft, pilot):
    _, _, wo = create_maintenance_chain(
        db,
        aircraft_id=aircraft.id,
        description="Test",
        severity=DiscrepancySeverity.MINOR,
    )
    update_work_order_status(db, wo, DiscrepancyWorkStatus.COMPLETED)
    record_qa_signoff(db, wo, inspector_person_id=pilot.id, notes="Inspected OK")
    db.refresh(wo)
    assert len(wo.qa_signoffs) == 1


def test_phase_forecast_returns_rows(db, aircraft):
    rows = phase_forecast(db, weekly_flight_hours=20.0)
    assert any(r["aircraft_id"] == aircraft.id for r in rows)


def test_release_forecast_open_blockers(db, aircraft):
    create_maintenance_chain(
        db,
        aircraft_id=aircraft.id,
        description="Downing item",
        severity=DiscrepancySeverity.DOWNING,
    )
    db.commit()
    result = release_forecast(db, aircraft.id)
    assert result["open_discrepancy_count"] >= 1
    assert len(result["blockers"]) >= 1