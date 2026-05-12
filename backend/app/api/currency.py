from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session, joinedload
from typing import List

from app.database import get_db
from app.models.models import CurrencyType, Person
from app.schemas.currency import CurrencyTypeOut
from app.services.currency_applicability import currencies_for_person

router = APIRouter(prefix="/api/currency", tags=["currency"])


@router.get("/types", response_model=List[CurrencyTypeOut])
def list_currency_types(db: Session = Depends(get_db)):
    """List all Wing Table B-2 currency type definitions."""
    return (
        db.query(CurrencyType)
        .options(joinedload(CurrencyType.applicability))
        .filter(CurrencyType.is_active.is_(True))
        .all()
    )


# NOTE: this route MUST come before /types/{code} so FastAPI doesn't try to
# match the literal string "applicable-to" as a {code} value.
@router.get("/types/applicable-to/{person_id}", response_model=List[CurrencyTypeOut])
def list_applicable_currencies(person_id: int, db: Session = Depends(get_db)):
    """Return currency types that apply to a specific person (by role/quals)."""
    person = (
        db.query(Person)
        .options(joinedload(Person.qualifications))
        .filter(Person.id == person_id)
        .first()
    )
    if not person:
        raise HTTPException(status_code=404, detail=f"Person {person_id} not found")
    return currencies_for_person(person, db)


@router.get("/types/{code}", response_model=CurrencyTypeOut)
def get_currency_type(code: str, db: Session = Depends(get_db)):
    """Return one currency type by its code (e.g. 'CSW', 'NIGHT_NVD')."""
    ct = (
        db.query(CurrencyType)
        .options(joinedload(CurrencyType.applicability))
        .filter(CurrencyType.code == code)
        .first()
    )
    if not ct:
        raise HTTPException(status_code=404, detail=f"Currency type '{code}' not found")
    return ct
