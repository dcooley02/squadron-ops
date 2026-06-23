from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import asc, nullslast
from typing import List
from datetime import date, datetime, timedelta

from app.core.deps import get_current_user, require_roles
from app.database import get_db
from app.models.models import (
    Aircraft,
    AircraftInspection,
    AircraftLogbookEntry,
    Discrepancy,
    DiscrepancyWorkStatus,
    InspectionType,
    LogbookEntryType,
    Person,
    Role,
    WorkCenter,
    WorkOrder,
)
from app.schemas.aircraft import (
    AircraftDetail,
    InspectionTypeOut,
    AircraftInspectionOut,
    DiscrepancyOut,
    DiscrepancyUpdate,
    InspectionUpdate,
    QaReleaseRequest,
)
from app.schemas.maintenance import (
    DiscrepancyCreateLine,
    WorkCenterOut,
    WorkOrderOut,
    WorkOrderUpdate,
    QaSignoffCreate,
    QaSignoffOut,
    PartsRequestCreate,
    PartsRequestOut,
    LogbookEntryCreate,
    LogbookEntryOut,
    PhaseForecastRow,
    ReleaseForecastOut,
)
from app.services.aircraft_status import is_inspection_overdue
from app.services.maintenance_chain import (
    build_discrepancy_out,
    build_work_order_out,
    create_maintenance_chain,
    create_parts_request,
    record_qa_signoff,
    sync_discrepancy_from_work_order,
    update_work_order_status,
    _aircraft_hours,
)
from app.services.maintenance_forecast import phase_forecast, release_forecast
from app.services.qa_release import qa_release

router = APIRouter(prefix="/api/maintenance", tags=["maintenance"])


@router.get("/work-centers", response_model=List[WorkCenterOut])
def list_work_centers(db: Session = Depends(get_db), _: Person = Depends(get_current_user)):
    return db.query(WorkCenter).order_by(WorkCenter.code).all()


@router.get("/forecast/phase", response_model=List[PhaseForecastRow])
def get_phase_forecast(
    weekly_flight_hours: float = Query(25.0, ge=0),
    db: Session = Depends(get_db),
    _: Person = Depends(get_current_user),
):
    return phase_forecast(db, weekly_flight_hours=weekly_flight_hours)


@router.get("/forecast/release/{aircraft_id}", response_model=ReleaseForecastOut)
def get_release_forecast(
    aircraft_id: int,
    db: Session = Depends(get_db),
    _: Person = Depends(get_current_user),
):
    try:
        return release_forecast(db, aircraft_id)
    except LookupError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.get("/inspections/types", response_model=List[InspectionTypeOut])
def list_inspection_types(db: Session = Depends(get_db)):
    return db.query(InspectionType).order_by(InspectionType.code).all()


@router.get("/aircraft/{aircraft_id}/inspections", response_model=List[AircraftInspectionOut])
def list_aircraft_inspections(aircraft_id: int, db: Session = Depends(get_db)):
    if not db.query(Aircraft).filter(Aircraft.id == aircraft_id).first():
        raise HTTPException(status_code=404, detail=f"Aircraft {aircraft_id} not found")

    ac = db.query(Aircraft).filter(Aircraft.id == aircraft_id).first()
    rows = (
        db.query(AircraftInspection)
        .options(joinedload(AircraftInspection.inspection_type))
        .filter(AircraftInspection.aircraft_id == aircraft_id)
        .order_by(nullslast(asc(AircraftInspection.next_due_date)))
        .all()
    )

    today = date.today()
    result = []
    for insp in rows:
        overdue = is_inspection_overdue(insp, today, ac.total_airframe_hours)
        result.append(AircraftInspectionOut.model_validate({
            "id": insp.id,
            "aircraft_id": insp.aircraft_id,
            "inspection_type_id": insp.inspection_type_id,
            "inspection_type": insp.inspection_type,
            "last_completed_date": insp.last_completed_date,
            "last_completed_hours": insp.last_completed_hours,
            "next_due_date": insp.next_due_date,
            "next_due_hours": insp.next_due_hours,
            "last_completion_notes": insp.last_completion_notes,
            "is_overdue": overdue,
        }))
    return result


@router.get("/aircraft/{aircraft_id}/discrepancies", response_model=List[DiscrepancyOut])
def list_aircraft_discrepancies(
    aircraft_id: int,
    open_only: bool = Query(False),
    db: Session = Depends(get_db),
):
    if not db.query(Aircraft).filter(Aircraft.id == aircraft_id).first():
        raise HTTPException(status_code=404, detail=f"Aircraft {aircraft_id} not found")

    q = (
        db.query(Discrepancy)
        .options(
            joinedload(Discrepancy.reported_by),
            joinedload(Discrepancy.work_order).joinedload(WorkOrder.work_center),
            joinedload(Discrepancy.work_order).joinedload(WorkOrder.qa_signoffs),
        )
        .filter(Discrepancy.aircraft_id == aircraft_id)
    )
    if open_only:
        q = q.filter(Discrepancy.is_open.is_(True))
    return [build_discrepancy_out(d) for d in q.order_by(Discrepancy.opened_date.desc()).all()]


@router.post("/aircraft/{aircraft_id}/discrepancies", response_model=DiscrepancyOut, status_code=201)
def create_discrepancy(
    aircraft_id: int,
    body: DiscrepancyCreateLine,
    db: Session = Depends(get_db),
    user: Person = Depends(require_roles(Role.MAINT_CONTROL, Role.CO_XO)),
):
    if not db.query(Aircraft).filter(Aircraft.id == aircraft_id).first():
        raise HTTPException(status_code=404, detail=f"Aircraft {aircraft_id} not found")

    disc, _, _ = create_maintenance_chain(
        db,
        aircraft_id=aircraft_id,
        description=body.description,
        severity=body.severity,
        system_affected=body.system_affected,
        notes=body.notes,
        type_wo_code=body.type_wo_code,
        reported_by_person_id=user.id,
        work_center_id=body.work_center_id,
    )
    db.commit()
    loaded = (
        db.query(Discrepancy)
        .options(
            joinedload(Discrepancy.reported_by),
            joinedload(Discrepancy.work_order).joinedload(WorkOrder.work_center),
            joinedload(Discrepancy.work_order).joinedload(WorkOrder.qa_signoffs),
        )
        .filter(Discrepancy.id == disc.id)
        .first()
    )
    return build_discrepancy_out(loaded)


@router.get("/aircraft/{aircraft_id}/work-orders", response_model=List[WorkOrderOut])
def list_work_orders(aircraft_id: int, db: Session = Depends(get_db), _: Person = Depends(get_current_user)):
    rows = (
        db.query(WorkOrder)
        .options(
            joinedload(WorkOrder.work_center),
            joinedload(WorkOrder.maf),
            joinedload(WorkOrder.qa_signoffs),
        )
        .filter(WorkOrder.aircraft_id == aircraft_id)
        .order_by(WorkOrder.opened_date.desc())
        .all()
    )
    return [build_work_order_out(r) for r in rows]


@router.patch("/work-orders/{work_order_id}", response_model=WorkOrderOut)
def patch_work_order(
    work_order_id: int,
    body: WorkOrderUpdate,
    db: Session = Depends(get_db),
    _: Person = Depends(require_roles(Role.MAINT_CONTROL, Role.CO_XO)),
):
    wo = (
        db.query(WorkOrder)
        .options(
            joinedload(WorkOrder.work_center),
            joinedload(WorkOrder.maf),
            joinedload(WorkOrder.discrepancy),
            joinedload(WorkOrder.qa_signoffs),
        )
        .filter(WorkOrder.id == work_order_id)
        .first()
    )
    if not wo:
        raise HTTPException(status_code=404, detail=f"Work order {work_order_id} not found")

    if body.work_center_id is not None:
        wo.work_center_id = body.work_center_id
        wo.assigned_at = datetime.utcnow()
    if body.status is not None:
        update_work_order_status(db, wo, body.status, corrective_action=body.corrective_action)
    elif body.corrective_action is not None:
        wo.corrective_action = body.corrective_action
        if wo.discrepancy:
            sync_discrepancy_from_work_order(wo, wo.discrepancy)

    db.commit()
    db.refresh(wo)
    return build_work_order_out(wo)


@router.post("/work-orders/{work_order_id}/qa-signoff", response_model=QaSignoffOut, status_code=201)
def qa_signoff_work_order(
    work_order_id: int,
    body: QaSignoffCreate,
    db: Session = Depends(get_db),
    user: Person = Depends(require_roles(Role.MAINT_CONTROL, Role.CO_XO)),
):
    wo = (
        db.query(WorkOrder)
        .options(joinedload(WorkOrder.discrepancy))
        .filter(WorkOrder.id == work_order_id)
        .first()
    )
    if not wo:
        raise HTTPException(status_code=404, detail=f"Work order {work_order_id} not found")

    row = record_qa_signoff(
        db,
        wo,
        inspector_person_id=user.id,
        notes=body.notes,
        release_eligible=body.release_eligible,
    )
    db.commit()
    return QaSignoffOut(
        id=row.id,
        work_order_id=row.work_order_id,
        inspector_person_id=row.inspector_person_id,
        inspector_name=f"{user.last_name}, {user.first_name}",
        signed_at=row.signed_at,
        notes=row.notes,
        release_eligible=row.release_eligible,
    )


@router.post("/work-orders/{work_order_id}/parts", response_model=PartsRequestOut, status_code=201)
def add_parts_request(
    work_order_id: int,
    body: PartsRequestCreate,
    db: Session = Depends(get_db),
    _: Person = Depends(require_roles(Role.MAINT_CONTROL, Role.CO_XO)),
):
    wo = db.query(WorkOrder).filter(WorkOrder.id == work_order_id).first()
    if not wo:
        raise HTTPException(status_code=404, detail=f"Work order {work_order_id} not found")
    pr = create_parts_request(
        db,
        wo,
        part_name=body.part_name,
        nsn=body.nsn,
        qty_ordered=body.qty_ordered,
        bcm_on_shelf=body.bcm_on_shelf,
    )
    if body.expected_delivery_date:
        pr.expected_delivery_date = body.expected_delivery_date
    db.commit()
    db.refresh(pr)
    return pr


@router.get("/aircraft/{aircraft_id}/logbook", response_model=List[LogbookEntryOut])
def list_logbook(aircraft_id: int, db: Session = Depends(get_db), _: Person = Depends(get_current_user)):
    rows = (
        db.query(AircraftLogbookEntry)
        .options(joinedload(AircraftLogbookEntry.created_by))
        .filter(AircraftLogbookEntry.aircraft_id == aircraft_id)
        .order_by(AircraftLogbookEntry.entry_date.desc())
        .all()
    )
    return [
        LogbookEntryOut.model_validate({
            "id": r.id,
            "aircraft_id": r.aircraft_id,
            "entry_type": r.entry_type,
            "entry_date": r.entry_date,
            "hours_at_entry": r.hours_at_entry,
            "title": r.title,
            "description": r.description,
            "work_order_id": r.work_order_id,
            "sortie_id": r.sortie_id,
            "created_by_name": (
                f"{r.created_by.last_name}, {r.created_by.first_name}" if r.created_by else None
            ),
        })
        for r in rows
    ]


@router.post("/aircraft/{aircraft_id}/logbook", response_model=LogbookEntryOut, status_code=201)
def create_logbook_entry(
    aircraft_id: int,
    body: LogbookEntryCreate,
    db: Session = Depends(get_db),
    user: Person = Depends(require_roles(Role.MAINT_CONTROL, Role.CO_XO)),
):
    if not db.query(Aircraft).filter(Aircraft.id == aircraft_id).first():
        raise HTTPException(status_code=404, detail=f"Aircraft {aircraft_id} not found")
    row = AircraftLogbookEntry(
        aircraft_id=aircraft_id,
        entry_type=body.entry_type,
        title=body.title,
        description=body.description,
        hours_at_entry=body.hours_at_entry or _aircraft_hours(db, aircraft_id),
        created_by_person_id=user.id,
    )
    db.add(row)
    db.commit()
    db.refresh(row)
    return LogbookEntryOut.model_validate({
        "id": row.id,
        "aircraft_id": row.aircraft_id,
        "entry_type": row.entry_type,
        "entry_date": row.entry_date,
        "hours_at_entry": row.hours_at_entry,
        "title": row.title,
        "description": row.description,
        "work_order_id": row.work_order_id,
        "sortie_id": row.sortie_id,
        "created_by_name": f"{user.last_name}, {user.first_name}",
    })


@router.patch("/discrepancies/{discrepancy_id}", response_model=DiscrepancyOut)
def update_discrepancy(
    discrepancy_id: int,
    body: DiscrepancyUpdate,
    db: Session = Depends(get_db),
    _: Person = Depends(require_roles(Role.MAINT_CONTROL, Role.CO_XO)),
):
    disc = (
        db.query(Discrepancy)
        .options(
            joinedload(Discrepancy.reported_by),
            joinedload(Discrepancy.work_order).joinedload(WorkOrder.work_center),
            joinedload(Discrepancy.work_order).joinedload(WorkOrder.qa_signoffs),
        )
        .filter(Discrepancy.id == discrepancy_id)
        .first()
    )
    if not disc:
        raise HTTPException(status_code=404, detail=f"Discrepancy {discrepancy_id} not found")

    if body.work_status is not None:
        if disc.work_order:
            update_work_order_status(db, disc.work_order, body.work_status, corrective_action=body.corrective_action)
        else:
            disc.work_status = body.work_status
            if body.work_status == DiscrepancyWorkStatus.CLOSED:
                disc.is_open = False
                disc.closed_date = datetime.utcnow()
    if body.system_affected is not None:
        disc.system_affected = body.system_affected
    if body.corrective_action is not None and not disc.work_order:
        disc.corrective_action = body.corrective_action

    db.commit()
    db.refresh(disc)
    return build_discrepancy_out(disc)


@router.patch("/aircraft/{aircraft_id}/inspections/{inspection_id}", response_model=AircraftInspectionOut)
def update_aircraft_inspection(
    aircraft_id: int,
    inspection_id: int,
    body: InspectionUpdate,
    db: Session = Depends(get_db),
    _: Person = Depends(require_roles(Role.MAINT_CONTROL, Role.CO_XO)),
):
    insp = (
        db.query(AircraftInspection)
        .options(joinedload(AircraftInspection.inspection_type))
        .filter(
            AircraftInspection.id == inspection_id,
            AircraftInspection.aircraft_id == aircraft_id,
        )
        .first()
    )
    if not insp:
        raise HTTPException(status_code=404, detail=f"Inspection {inspection_id} not found")

    ac = db.query(Aircraft).filter(Aircraft.id == aircraft_id).first()

    if body.last_completed_date is not None:
        insp.last_completed_date = body.last_completed_date
        it = insp.inspection_type
        if it.periodicity_days is not None:
            insp.next_due_date = body.last_completed_date + timedelta(days=it.periodicity_days)

    if body.last_completed_hours is not None:
        insp.last_completed_hours = body.last_completed_hours
        it = insp.inspection_type
        if it.periodicity_hours is not None:
            insp.next_due_hours = body.last_completed_hours + it.periodicity_hours

    if body.last_completion_notes is not None:
        insp.last_completion_notes = body.last_completion_notes

    if insp.inspection_type.code == "PHASE" and ac:
        ac.hours_since_phase = 0.0
        db.add(
            AircraftLogbookEntry(
                aircraft_id=aircraft_id,
                entry_type=LogbookEntryType.PHASE_INSPECTION,
                hours_at_entry=ac.total_airframe_hours,
                title="Phase inspection completed",
                description=body.last_completion_notes,
            )
        )

    db.commit()
    db.refresh(insp)

    today = date.today()
    overdue = is_inspection_overdue(insp, today, ac.total_airframe_hours if ac else 0.0)
    return AircraftInspectionOut.model_validate({
        "id": insp.id,
        "aircraft_id": insp.aircraft_id,
        "inspection_type_id": insp.inspection_type_id,
        "inspection_type": insp.inspection_type,
        "last_completed_date": insp.last_completed_date,
        "last_completed_hours": insp.last_completed_hours,
        "next_due_date": insp.next_due_date,
        "next_due_hours": insp.next_due_hours,
        "last_completion_notes": insp.last_completion_notes,
        "is_overdue": overdue,
    })


@router.post("/aircraft/{aircraft_id}/qa-release", response_model=AircraftDetail)
def aircraft_qa_release(
    aircraft_id: int,
    body: QaReleaseRequest,
    db: Session = Depends(get_db),
    user: Person = Depends(require_roles(Role.MAINT_CONTROL, Role.CO_XO)),
):
    if not body.qa_notes.strip():
        raise HTTPException(status_code=400, detail="qa_notes is required")
    if body.inspector_person_id is None:
        body = body.model_copy(update={"inspector_person_id": user.id})

    try:
        return qa_release(db, aircraft_id, body)
    except LookupError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except PermissionError as exc:
        raise HTTPException(
            status_code=409,
            detail={"message": "Release blocked — not safe for flight", "blockers": list(exc.args[0])},
        ) from exc