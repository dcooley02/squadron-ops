from datetime import date

from fastapi import APIRouter, Depends, HTTPException, Response
from sqlalchemy.orm import Session

from app.core.deps import require_roles
from app.database import get_db
from app.models.models import Person, Role, Sortie, SortieOpsStatus
from app.schemas.ops import (
    DayOpsOut,
    SchedulePublishRequest,
    SchedulePublicationOut,
    SortieOpsStatusPatch,
    WatchbillEntryCreate,
    WatchbillEntryOut,
)
from app.services.ops_day import build_day_ops, publish_schedule
from app.services.ops_pdf import render_ato_pdf, render_brief_sheet_pdf

router = APIRouter(prefix="/api/ops", tags=["ops"])


@router.get("/day/{ops_date}", response_model=DayOpsOut)
def get_day_ops(ops_date: date, db: Session = Depends(get_db)):
    """ATO-style daily ops summary for SDO."""
    return build_day_ops(db, ops_date)


@router.post("/schedule/{ops_date}/publish", response_model=SchedulePublicationOut)
def publish_day_schedule(
    ops_date: date,
    body: SchedulePublishRequest,
    db: Session = Depends(get_db),
    user: Person = Depends(require_roles(Role.SDO, Role.CO_XO)),
):
    try:
        pub = publish_schedule(
            db,
            ops_date,
            body.published_by_person_id or user.id,
            body.remarks,
        )
    except ValueError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc

    from app.models.models import Person

    publisher = None
    if pub.published_by_person_id:
        publisher = db.query(Person).filter(Person.id == pub.published_by_person_id).first()

    return SchedulePublicationOut(
        id=pub.id,
        schedule_date=pub.schedule_date,
        published_at=pub.published_at,
        published_by_name=(
            f"{publisher.last_name}, {publisher.first_name}" if publisher else None
        ),
        remarks=pub.remarks,
    )


@router.patch("/sorties/{sortie_id}/status")
def patch_sortie_ops_status(
    sortie_id: int,
    body: SortieOpsStatusPatch,
    db: Session = Depends(get_db),
    _: Person = Depends(require_roles(Role.SDO, Role.CO_XO)),
):
    sortie = db.query(Sortie).filter(Sortie.id == sortie_id).first()
    if not sortie:
        raise HTTPException(status_code=404, detail=f"Sortie {sortie_id} not found")
    sortie.ops_status = body.ops_status
    if body.mission_summary is not None:
        sortie.mission_summary = body.mission_summary
    if body.comm_plan is not None:
        sortie.comm_plan = body.comm_plan
    if body.brief_sheet_notes is not None:
        sortie.brief_sheet_notes = body.brief_sheet_notes
    db.commit()
    return {"id": sortie_id, "ops_status": sortie.ops_status.value}


@router.post("/watchbill", response_model=WatchbillEntryOut, status_code=201)
def create_watchbill_entry(
    body: WatchbillEntryCreate,
    db: Session = Depends(get_db),
    _: Person = Depends(require_roles(Role.SDO, Role.CO_XO)),
):
    from app.models.models import Person, WatchbillEntry

    person = db.query(Person).filter(Person.id == body.person_id).first()
    if not person:
        raise HTTPException(status_code=404, detail="Person not found")

    existing = (
        db.query(WatchbillEntry)
        .filter(WatchbillEntry.duty_date == body.duty_date, WatchbillEntry.role == body.role)
        .first()
    )
    if existing:
        existing.person_id = body.person_id
        existing.shift_label = body.shift_label
        existing.notes = body.notes
        db.commit()
        db.refresh(existing)
        row = existing
    else:
        row = WatchbillEntry(
            duty_date=body.duty_date,
            role=body.role,
            person_id=body.person_id,
            shift_label=body.shift_label,
            notes=body.notes,
        )
        db.add(row)
        db.commit()
        db.refresh(row)

    return WatchbillEntryOut(
        id=row.id,
        duty_date=row.duty_date,
        role=row.role,
        person_id=row.person_id,
        person_name=f"{person.last_name}, {person.first_name}",
        shift_label=row.shift_label,
        notes=row.notes,
    )


@router.get("/day/{ops_date}/ato.pdf")
def get_ato_pdf(ops_date: date, db: Session = Depends(get_db)):
    try:
        pdf = render_ato_pdf(db, ops_date)
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    return Response(
        content=pdf,
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="ato_{ops_date.isoformat()}.pdf"'},
    )


@router.get("/sorties/{sortie_id}/brief-sheet.pdf")
def get_brief_sheet_pdf(sortie_id: int, db: Session = Depends(get_db)):
    try:
        pdf = render_brief_sheet_pdf(db, sortie_id)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    return Response(
        content=pdf,
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="brief_sheet_{sortie_id}.pdf"'},
    )