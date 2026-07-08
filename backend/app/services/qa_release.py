"""
QA release — stamp line status after QA signoff when aircraft is safe for flight.
"""
from datetime import date
from typing import List, Tuple

from sqlalchemy.orm import Session, joinedload

from app.models.models import (
    Aircraft,
    AircraftInspection,
    AircraftLogbookEntry,
    AircraftStatus,
    Discrepancy,
    DiscrepancySeverity,
    DiscrepancyWorkStatus,
    LogbookEntryType,
    WorkOrder,
)
from app.schemas.aircraft import AircraftDetail, QaReleaseRequest
from app.services.aircraft_detail import build_aircraft_detail, open_discrepancies, overdue_inspections
from app.services.aircraft_status import compute_status
from app.core.time import utc_now

NON_RELEASE_STATUSES = {AircraftStatus.NMC, AircraftStatus.NMCM, AircraftStatus.NMCS}


def _load_aircraft(db: Session, aircraft_id: int) -> Aircraft | None:
    return (
        db.query(Aircraft)
        .options(
            joinedload(Aircraft.discrepancies),
            joinedload(Aircraft.inspections).joinedload(AircraftInspection.inspection_type),
            joinedload(Aircraft.work_orders).joinedload(WorkOrder.qa_signoffs),
        )
        .filter(Aircraft.id == aircraft_id)
        .first()
    )


def collect_release_blockers(
    aircraft: Aircraft,
    open_discs: List[Discrepancy],
    overdue: List[AircraftInspection],
) -> Tuple[List[str], AircraftStatus]:
    """Return human-readable blockers and the computed status for the current state."""
    blockers: List[str] = []

    for disc in open_discs:
        if disc.severity == DiscrepancySeverity.DOWNING:
            label = disc.maf_number or f"#{disc.id}"
            blockers.append(f"Open DOWNING discrepancy {label}")

    for insp in overdue:
        if insp.inspection_type.is_downing_when_overdue:
            blockers.append(f"Overdue downing inspection: {insp.inspection_type.name}")

    computed = compute_status(aircraft, open_discs, overdue)
    if computed in NON_RELEASE_STATUSES:
        blockers.append(
            f"Computed status is {computed.value} — not safe for flight until maintenance is complete"
        )

    return blockers, computed


def _close_discrepancies(
    aircraft: Aircraft,
    body: QaReleaseRequest,
) -> None:
    if not body.close_discrepancy_ids:
        return

    by_id = {d.id: d for d in aircraft.discrepancies}
    for disc_id in body.close_discrepancy_ids:
        disc = by_id.get(disc_id)
        if disc is None:
            raise ValueError(f"Discrepancy {disc_id} not found on aircraft {aircraft.id}")
        if disc.work_status == DiscrepancyWorkStatus.CLOSED:
            continue

        if body.corrective_action:
            disc.corrective_action = body.corrective_action

        disc.work_status = DiscrepancyWorkStatus.CLOSED
        disc.is_open = False
        disc.closed_date = utc_now()


def _work_orders_missing_signoff(
    aircraft: Aircraft,
    close_ids: list[int] | None,
) -> list[str]:
    """Open or completing work orders slated for closure must have QA signoff."""
    missing: list[str] = []
    close_set = set(close_ids or [])
    for wo in aircraft.work_orders:
        if wo.discrepancy_id and wo.discrepancy_id in close_set:
            if not wo.qa_signoffs:
                missing.append(f"Work order {wo.jcn} lacks QA signoff")
    return missing


def qa_release(
    db: Session,
    aircraft_id: int,
    body: QaReleaseRequest,
) -> AircraftDetail:
    """
    Close selected discrepancies, validate release preconditions, and stamp aircraft.status
    to the freshly computed operational status after QA signoff.
    """
    aircraft = _load_aircraft(db, aircraft_id)
    if aircraft is None:
        raise LookupError(f"Aircraft {aircraft_id} not found")

    signoff_gaps = _work_orders_missing_signoff(aircraft, body.close_discrepancy_ids)
    if signoff_gaps:
        raise ValueError("; ".join(signoff_gaps))

    _close_discrepancies(aircraft, body)

    today = date.today()
    open_discs = open_discrepancies(aircraft)
    overdue = overdue_inspections(aircraft, today)
    blockers, computed = collect_release_blockers(aircraft, open_discs, overdue)

    if blockers:
        raise PermissionError(blockers)

    previous = aircraft.status
    aircraft.status = computed
    aircraft.manual_status_override = None

    stamp = utc_now().strftime("%Y-%m-%d %H:%M UTC")
    note_line = f"[{stamp} QA Release {previous.value}→{computed.value}] {body.qa_notes.strip()}"
    aircraft.notes = f"{aircraft.notes}\n\n{note_line}".strip() if aircraft.notes else note_line

    db.add(
        AircraftLogbookEntry(
            aircraft_id=aircraft.id,
            entry_type=LogbookEntryType.QA_RELEASE,
            hours_at_entry=aircraft.total_airframe_hours,
            title=f"QA Release {previous.value}→{computed.value}",
            description=body.qa_notes.strip(),
            created_by_person_id=body.inspector_person_id,
        )
    )

    db.flush()
    db.refresh(aircraft)
    return build_aircraft_detail(aircraft, today)