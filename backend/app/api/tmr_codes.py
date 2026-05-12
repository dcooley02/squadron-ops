from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from typing import List

from app.database import get_db
from app.models.models import TmrCode
from app.schemas.logging import TmrCodeOut

router = APIRouter(prefix="/api/tmr-codes", tags=["tmr-codes"])


@router.get("", response_model=List[TmrCodeOut])
def list_tmr_codes(db: Session = Depends(get_db)):
    """Return all active TMR codes sorted by code."""
    return (
        db.query(TmrCode)
        .filter(TmrCode.is_active == True)
        .order_by(TmrCode.code)
        .all()
    )
