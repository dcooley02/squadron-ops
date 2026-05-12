"""
Determines which Wing Table B-2 currency types apply to a given person
based on their role and earned qualifications.
"""
from sqlalchemy.orm import Session, joinedload

from app.models.models import (
    CurrencyType, CurrencyApplicability, CurrencyAudience, Role,
)


def currencies_for_person(person, db: Session) -> list:
    """Return all active CurrencyType rows that apply to this person."""
    quals = {q.qual_code for q in person.qualifications}
    is_pilot = person.role in (Role.PILOT, Role.CO_XO)
    is_aircrew = person.role == Role.AIRCREW

    def _matches(app: CurrencyApplicability) -> bool:
        audience = app.applies_to
        req_qual = app.required_qualification

        if audience == CurrencyAudience.ALL_PILOTS:
            if not is_pilot:
                return False
        elif audience == CurrencyAudience.HAC_ONLY:
            if not is_pilot or "HAC" not in quals:
                return False
        elif audience == CurrencyAudience.AMCM_QUAL_PILOTS:
            if not is_pilot or not any("AMCM" in q for q in quals):
                return False
        elif audience == CurrencyAudience.ALL_AIRCREWMEN:
            if not is_aircrew:
                return False
        elif audience == CurrencyAudience.AWS_ONLY:
            if not is_aircrew:
                return False
        elif audience == CurrencyAudience.HOIST_OP_QUAL:
            hoist_quals = {"HOIST_OP", "HOIST_OPERATOR", "RESCUE_SWIMMER", "HOIST_OP_QUAL"}
            if not (quals & hoist_quals):
                return False

        if req_qual and req_qual not in quals:
            return False
        return True

    all_types = (
        db.query(CurrencyType)
        .options(joinedload(CurrencyType.applicability))
        .filter(CurrencyType.is_active.is_(True))
        .all()
    )
    return [ct for ct in all_types if any(_matches(a) for a in ct.applicability)]
