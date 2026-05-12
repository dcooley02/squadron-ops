from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session, joinedload
from typing import List, Optional
from app.database import get_db
from app.models.models import Person, Role, Currency, CurrencyType
from app.schemas.persons import PersonSummary, PersonDetail

router = APIRouter(prefix="/api/persons", tags=["persons"])


@router.get("", response_model=List[PersonSummary])
def list_persons(
    role: Optional[Role] = Query(None, description="Filter by role"),
    active_only: bool = Query(True, description="Only return active personnel"),
    db: Session = Depends(get_db),
):
    """List all squadron personnel, optionally filtered by role."""
    query = db.query(Person)
    if active_only:
        query = query.filter(Person.is_active == True)
    if role is not None:
        query = query.filter(Person.role == role)
    return query.order_by(Person.last_name, Person.first_name).all()


@router.get("/{person_id}", response_model=PersonDetail)
def get_person(person_id: int, db: Session = Depends(get_db)):
    """Get one person with full qualification and currency details."""
    person = (
        db.query(Person)
        .options(
            joinedload(Person.qualifications),
            joinedload(Person.currencies)
                .joinedload(Currency.currency_type)
                .joinedload(CurrencyType.applicability),
        )
        .filter(Person.id == person_id)
        .first()
    )
    if not person:
        raise HTTPException(status_code=404, detail=f"Person {person_id} not found")
    return person