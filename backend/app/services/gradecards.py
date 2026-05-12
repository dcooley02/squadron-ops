"""
Gradecard business logic.
`compute_overall_status` derives the overall card result from line item scores
per the rules in COMHELSEACOMBATWING 3502.8.
`credit_syllabus_for_gradecard` stamps flight_log.syllabus_event_completed when
a card reaches PASS/COMPLETE — must be called inside the same open transaction.
"""
from typing import List

from sqlalchemy.orm import Session

from app.models.models import (
    GradingScheme, GradecardStatus, CompletionStatus,
    FourTierScore, GradecardLineItem, FlightLog, SyllabusEvent,
)
from app.schemas.syllabus import GradecardLineItemResultIn


def compute_overall_status(
    grading_scheme: GradingScheme,
    line_items: List[GradecardLineItem],
    results: List[GradecardLineItemResultIn],
) -> GradecardStatus:
    """
    Derive overall_status from the submitted line item results.

    line_items: template rows (provides is_required, is_critical per line)
    results:    submitted GradecardLineItemResultIn payloads from the POST body
    """
    result_by_id = {r.line_item_id: r for r in results}

    if grading_scheme == GradingScheme.COMPLETION:
        required = [li for li in line_items if li.is_required]
        for li in required:
            r = result_by_id.get(li.id)
            if r is None or (not r.waived and r.completion_status is None):
                return GradecardStatus.IN_PROGRESS
            if not r.waived and r.completion_status == CompletionStatus.INCOMPLETE:
                return GradecardStatus.INCOMPLETE
        return GradecardStatus.COMPLETE

    # FOUR_TIER — three descending-priority passes
    # Pass 1: any UNSAT caps the card immediately
    for li in line_items:
        r = result_by_id.get(li.id)
        if r and not r.waived and r.four_tier_score == FourTierScore.UNSAT_1_0:
            return GradecardStatus.UNSAT

    # Pass 2: any BELOW_STANDARD (critical or non-critical) → Conditional Pass
    for li in line_items:
        r = result_by_id.get(li.id)
        if r and not r.waived and r.four_tier_score == FourTierScore.BELOW_STANDARD_2_0:
            return GradecardStatus.CONDITIONAL_PASS

    # Pass 3: check all required items are scored (≥ STANDARD)
    required = [li for li in line_items if li.is_required]
    for li in required:
        r = result_by_id.get(li.id)
        if r is None or (not r.waived and r.four_tier_score is None):
            return GradecardStatus.IN_PROGRESS

    return GradecardStatus.PASS


def credit_syllabus_for_gradecard(gradecard: object, db: Session) -> None:
    """
    If the gradecard reached PASS (FOUR_TIER) or COMPLETE (COMPLETION) and is
    linked to a flight_log_id, write the event_code back to
    flight_log.syllabus_event_completed.

    Must be called before the final db.commit() in the same transaction — any
    failure here will cause the caller's transaction to roll back the entire
    gradecard creation.
    """
    is_credit_worthy = (
        (gradecard.grading_scheme == GradingScheme.FOUR_TIER
         and gradecard.overall_status == GradecardStatus.PASS)
        or
        (gradecard.grading_scheme == GradingScheme.COMPLETION
         and gradecard.overall_status == GradecardStatus.COMPLETE)
    )
    if not is_credit_worthy or not gradecard.flight_log_id:
        return

    event = db.query(SyllabusEvent).filter(
        SyllabusEvent.id == gradecard.syllabus_event_id
    ).first()
    if event is None or event.event_code is None:
        return

    fl = db.query(FlightLog).filter(
        FlightLog.id == gradecard.flight_log_id
    ).first()
    if fl is not None:
        fl.syllabus_event_completed = event.event_code
