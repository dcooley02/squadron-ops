"""Job Control Number (JCN) generation per CNAF M-4790.2.

A JCN is a 9-character alphanumeric: ORG (3) + Julian day-of-year (3) + serno (3).

ORG is the reporting organisation's UIC suffix; we hard-code "350" as a stand-in
for an HSC squadron. Lift this to a setting when squadron config arrives.
"""
from __future__ import annotations

from datetime import datetime

from sqlalchemy import func
from sqlalchemy.orm import Session

ORG_CODE = "350"


def _julian_day(d: datetime) -> str:
    """Day-of-year as a zero-padded 3-digit string (001-366)."""
    return f"{d.timetuple().tm_yday:03d}"


def assign_jcn(db: Session, *, opened_date: datetime, model) -> str:
    """Return the next JCN for the given day. Caller is responsible for the
    DB commit. The `model` argument is the Discrepancy class (avoids a circular
    import at module load time).
    """
    jul = _julian_day(opened_date)
    prefix = f"{ORG_CODE}{jul}"
    existing_max = (
        db.query(func.max(model.jcn))
        .filter(model.jcn.like(f"{prefix}%"))
        .scalar()
    )
    if existing_max:
        # Extract trailing 3 digits as the serno
        try:
            serno = int(existing_max[-3:]) + 1
        except ValueError:
            serno = 1
    else:
        serno = 1
    return f"{prefix}{serno:03d}"
