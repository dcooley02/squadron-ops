"""Phase and release forecasting for maintenance planning."""
from __future__ import annotations

from datetime import date, timedelta
from typing import List

from sqlalchemy.orm import Session, joinedload

from app.models.models import (
    Aircraft,
    AircraftInspection,
    DiscrepancySeverity,
    DiscrepancyWorkStatus,
    PartsRequestStatus,
    WorkOrder,
)
from app.services.aircraft_detail import open_discrepancies, overdue_inspections
from app.services.aircraft_status import compute_status


def phase_forecast(
    db: Session,
    *,
    weekly_flight_hours: float = 25.0,
) -> list[dict]:
    """Project phase due date per aircraft from hours remaining and flight rate."""
    aircraft = db.query(Aircraft).order_by(Aircraft.side_number).all()
    out: list[dict] = []
    for ac in aircraft:
        hours_left = max(0.0, ac.phase_interval - ac.hours_since_phase)
        weeks = hours_left / weekly_flight_hours if weekly_flight_hours > 0 else None
        projected = date.today() + timedelta(weeks=int(weeks or 0)) if weeks is not None else None
        out.append({
            "aircraft_id": ac.id,
            "side_number": ac.side_number,
            "hours_since_phase": ac.hours_since_phase,
            "hours_to_phase": hours_left,
            "weekly_flight_hours_assumed": weekly_flight_hours,
            "projected_phase_date": projected,
        })
    return out


def release_forecast(db: Session, aircraft_id: int) -> dict:
    """Estimate when aircraft can be FMC / safe for flight."""
    ac = (
        db.query(Aircraft)
        .options(
            joinedload(Aircraft.discrepancies),
            joinedload(Aircraft.inspections).joinedload(AircraftInspection.inspection_type),
            joinedload(Aircraft.work_orders).joinedload(WorkOrder.parts_requests),
        )
        .filter(Aircraft.id == aircraft_id)
        .first()
    )
    if not ac:
        raise LookupError(f"Aircraft {aircraft_id} not found")

    today = date.today()
    open_discs = open_discrepancies(ac)
    overdue = overdue_inspections(ac, today)
    computed = compute_status(ac, open_discs, overdue)

    blockers: list[str] = []
    latest_parts_date: date | None = None

    for disc in open_discs:
        if disc.severity == DiscrepancySeverity.DOWNING:
            blockers.append(disc.maf_number or f"Discrepancy #{disc.id}")

    for wo in ac.work_orders:
        if wo.status not in (DiscrepancyWorkStatus.CLOSED, DiscrepancyWorkStatus.COMPLETED):
            if wo.status == DiscrepancyWorkStatus.AWP:
                for pr in wo.parts_requests:
                    if pr.status not in (PartsRequestStatus.RECEIVED, PartsRequestStatus.BCM):
                        if pr.expected_delivery_date:
                            latest_parts_date = max(latest_parts_date or pr.expected_delivery_date, pr.expected_delivery_date)
                        else:
                            blockers.append(f"AWP work order {wo.jcn} — parts pending")

    for insp in overdue:
        if insp.inspection_type.is_downing_when_overdue:
            blockers.append(f"Overdue: {insp.inspection_type.name}")

    projected_release = None
    if not blockers and computed in ("FMC", "PMC"):
        projected_release = today
    elif latest_parts_date:
        projected_release = latest_parts_date + timedelta(days=2)

    return {
        "aircraft_id": aircraft_id,
        "computed_status": computed.value,
        "blockers": blockers,
        "projected_release_date": projected_release,
        "open_discrepancy_count": len(open_discs),
        "open_work_order_count": sum(
            1 for wo in ac.work_orders
            if wo.status not in (DiscrepancyWorkStatus.CLOSED, DiscrepancyWorkStatus.COMPLETED)
        ),
    }