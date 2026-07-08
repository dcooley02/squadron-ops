"""4790 maintenance chain: discrepancy → MAF → work order → QA signoff."""
from __future__ import annotations

from sqlalchemy import text
from sqlalchemy.orm import Session

from app.models.models import (
    Aircraft,
    AircraftLogbookEntry,
    Discrepancy,
    DiscrepancySeverity,
    DiscrepancyWorkStatus,
    LogbookEntryType,
    Maf,
    MafStatus,
    PartsRequest,
    PartsRequestStatus,
    QaSignoff,
    WorkOrder,
)
from app.schemas.aircraft import DiscrepancyOut
from app.schemas.maintenance import WorkOrderOut
from app.services.jcn import assign_jcn
from app.core.time import utc_now


def _next_maf_number(db: Session, *, year: int | None = None) -> str:
    yr = year or utc_now().year
    max_seq = db.execute(
        text(
            "SELECT MAX(CAST(SUBSTRING(maf_number FROM 9) AS INTEGER)) "
            "FROM mafs WHERE maf_number LIKE :pattern"
        ),
        {"pattern": f"M-{yr}-%"},
    ).scalar()
    if max_seq is None:
        legacy = db.execute(
            text(
                "SELECT MAX(CAST(SUBSTRING(maf_number FROM 9) AS INTEGER)) "
                "FROM discrepancies WHERE maf_number LIKE :pattern"
            ),
            {"pattern": f"M-{yr}-%"},
        ).scalar()
        max_seq = legacy or 0
    return f"M-{yr}-{int(max_seq) + 1:04d}"


def _maf_status_from_work(status: DiscrepancyWorkStatus, *, closed: bool) -> MafStatus:
    if closed or status == DiscrepancyWorkStatus.CLOSED:
        return MafStatus.CLOSED
    if status == DiscrepancyWorkStatus.COMPLETED:
        return MafStatus.COMPLETED
    if status in (DiscrepancyWorkStatus.IN_WORK, DiscrepancyWorkStatus.AWP, DiscrepancyWorkStatus.AWM):
        return MafStatus.IN_WORK
    return MafStatus.OPEN


def sync_discrepancy_from_work_order(wo: WorkOrder, disc: Discrepancy) -> None:
    """Keep denormalized discrepancy fields aligned with the work order."""
    disc.work_status = wo.status
    disc.jcn = wo.jcn
    disc.type_wo_code = wo.type_wo_code
    disc.corrective_action = wo.corrective_action
    if wo.status == DiscrepancyWorkStatus.CLOSED:
        disc.is_open = False
        disc.closed_date = wo.completed_at or utc_now()
    elif wo.status == DiscrepancyWorkStatus.COMPLETED:
        disc.is_open = True
    if wo.maf_id and wo.maf:
        disc.maf_number = wo.maf.maf_number
        wo.maf.status = _maf_status_from_work(wo.status, closed=not disc.is_open)


def create_maintenance_chain(
    db: Session,
    *,
    aircraft_id: int,
    description: str,
    severity: DiscrepancySeverity,
    system_affected: str | None = None,
    notes: str | None = None,
    type_wo_code: str = "DM",
    sortie_id: int | None = None,
    reported_by_person_id: int | None = None,
    work_center_id: int | None = None,
) -> tuple[Discrepancy, Maf, WorkOrder]:
    """Create discrepancy + MAF + work order in one chain."""
    opened = utc_now()
    maf_number = _next_maf_number(db)
    jcn = assign_jcn(db, opened_date=opened, model=WorkOrder)

    disc = Discrepancy(
        aircraft_id=aircraft_id,
        sortie_id=sortie_id,
        reported_by_person_id=reported_by_person_id,
        description=description,
        severity=severity,
        system_affected=system_affected,
        notes=notes,
        maf_number=maf_number,
        type_wo_code=type_wo_code,
        jcn=jcn,
        work_status=DiscrepancyWorkStatus.OPEN,
        opened_date=opened,
        is_open=True,
    )
    db.add(disc)
    db.flush()

    maf = Maf(
        maf_number=maf_number,
        aircraft_id=aircraft_id,
        discrepancy_id=disc.id,
        reported_by_person_id=reported_by_person_id,
        system_affected=system_affected,
        severity=severity,
        status=MafStatus.OPEN,
        opened_date=opened,
        notes=notes,
    )
    db.add(maf)
    db.flush()

    wo = WorkOrder(
        jcn=jcn,
        type_wo_code=type_wo_code,
        aircraft_id=aircraft_id,
        maf_id=maf.id,
        discrepancy_id=disc.id,
        work_center_id=work_center_id,
        status=DiscrepancyWorkStatus.OPEN,
        opened_date=opened,
    )
    db.add(wo)
    db.flush()

    db.add(
        AircraftLogbookEntry(
            aircraft_id=aircraft_id,
            entry_type=LogbookEntryType.DISCREPANCY,
            entry_date=opened,
            hours_at_entry=_aircraft_hours(db, aircraft_id),
            title=f"Discrepancy {maf_number}",
            description=description,
            work_order_id=wo.id,
            sortie_id=sortie_id,
            created_by_person_id=reported_by_person_id,
        )
    )
    db.flush()
    return disc, maf, wo


def _aircraft_hours(db: Session, aircraft_id: int) -> float:
    ac = db.query(Aircraft).filter(Aircraft.id == aircraft_id).first()
    return ac.total_airframe_hours if ac else 0.0


def update_work_order_status(
    db: Session,
    wo: WorkOrder,
    status: DiscrepancyWorkStatus,
    *,
    corrective_action: str | None = None,
) -> WorkOrder:
    wo.status = status
    if corrective_action is not None:
        wo.corrective_action = corrective_action
    now = utc_now()
    if status == DiscrepancyWorkStatus.IN_WORK and wo.assigned_at is None:
        wo.assigned_at = now
    if status in (DiscrepancyWorkStatus.COMPLETED, DiscrepancyWorkStatus.CLOSED):
        wo.completed_at = now
    if wo.discrepancy:
        sync_discrepancy_from_work_order(wo, wo.discrepancy)
    db.flush()
    return wo


def create_parts_request(
    db: Session,
    wo: WorkOrder,
    *,
    part_name: str,
    nsn: str | None = None,
    qty_ordered: int = 1,
    bcm_on_shelf: bool = False,
) -> PartsRequest:
    status = PartsRequestStatus.BCM if bcm_on_shelf else PartsRequestStatus.REQUESTED
    pr = PartsRequest(
        work_order_id=wo.id,
        part_name=part_name,
        nsn=nsn,
        qty_ordered=qty_ordered,
        status=status,
        bcm_on_shelf=bcm_on_shelf,
    )
    db.add(pr)
    if wo.status == DiscrepancyWorkStatus.OPEN:
        update_work_order_status(db, wo, DiscrepancyWorkStatus.AWP)
    db.flush()
    return pr


def build_discrepancy_out(disc: Discrepancy) -> DiscrepancyOut:
    wo = disc.work_order
    reporter = disc.reported_by
    return DiscrepancyOut.model_validate({
        "id": disc.id,
        "aircraft_id": disc.aircraft_id,
        "sortie_id": disc.sortie_id,
        "description": disc.description,
        "severity": disc.severity,
        "work_status": disc.work_status,
        "maf_number": disc.maf_number,
        "system_affected": disc.system_affected,
        "corrective_action": disc.corrective_action,
        "notes": disc.notes,
        "is_open": disc.is_open,
        "opened_date": disc.opened_date,
        "closed_date": disc.closed_date,
        "type_wo_code": disc.type_wo_code,
        "jcn": disc.jcn,
        "reported_by_name": (
            f"{reporter.last_name}, {reporter.first_name}" if reporter else None
        ),
        "work_order_id": wo.id if wo else None,
        "work_center_code": wo.work_center.code if wo and wo.work_center else None,
        "has_qa_signoff": bool(wo and wo.qa_signoffs),
    })


def build_work_order_out(wo: WorkOrder) -> WorkOrderOut:
    return WorkOrderOut.model_validate({
        "id": wo.id,
        "jcn": wo.jcn,
        "type_wo_code": wo.type_wo_code,
        "aircraft_id": wo.aircraft_id,
        "maf_id": wo.maf_id,
        "discrepancy_id": wo.discrepancy_id,
        "work_center_id": wo.work_center_id,
        "work_center_code": wo.work_center.code if wo.work_center else None,
        "work_center_name": wo.work_center.name if wo.work_center else None,
        "status": wo.status,
        "corrective_action": wo.corrective_action,
        "opened_date": wo.opened_date,
        "assigned_at": wo.assigned_at,
        "completed_at": wo.completed_at,
        "maf_number": wo.maf.maf_number if wo.maf else None,
        "has_qa_signoff": bool(wo.qa_signoffs),
    })


def record_qa_signoff(
    db: Session,
    wo: WorkOrder,
    *,
    inspector_person_id: int,
    notes: str,
    release_eligible: bool = True,
) -> QaSignoff:
    row = QaSignoff(
        work_order_id=wo.id,
        aircraft_id=wo.aircraft_id,
        inspector_person_id=inspector_person_id,
        notes=notes,
        release_eligible=release_eligible,
    )
    db.add(row)
    if wo.status != DiscrepancyWorkStatus.COMPLETED:
        update_work_order_status(db, wo, DiscrepancyWorkStatus.COMPLETED)
    db.flush()
    return row