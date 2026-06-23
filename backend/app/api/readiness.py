from fastapi import APIRouter, Depends, HTTPException, Response
from sqlalchemy.orm import Session, joinedload

from app.database import get_db
from app.models.models import Person
from app.schemas.readiness import PersonReadinessSummary, SquadronReadinessOut
from app.services.readiness import build_person_readiness, build_squadron_readiness
from app.services.readiness_pdf import render_readiness_brief_pdf

router = APIRouter(prefix="/api/readiness", tags=["readiness"])


@router.get("/squadron", response_model=SquadronReadinessOut)
def get_squadron_readiness(db: Session = Depends(get_db)):
    """Squadron-wide WTM T-rating rollup by capability area."""
    return build_squadron_readiness(db)


@router.get("/persons/{person_id}", response_model=PersonReadinessSummary)
def get_person_readiness(person_id: int, db: Session = Depends(get_db)):
    """Per-person capability-area T-ratings with contributing factors."""
    person = (
        db.query(Person)
        .options(joinedload(Person.currencies))
        .filter(Person.id == person_id)
        .first()
    )
    if not person:
        raise HTTPException(status_code=404, detail=f"Person {person_id} not found")
    return build_person_readiness(db, person)


@router.get("/squadron/brief.pdf")
def get_squadron_readiness_brief_pdf(db: Session = Depends(get_db)):
    """Exportable WTM capability readiness brief (PDF)."""
    try:
        pdf = render_readiness_brief_pdf(db)
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    return Response(
        content=pdf,
        media_type="application/pdf",
        headers={"Content-Disposition": 'attachment; filename="readiness_brief.pdf"'},
    )