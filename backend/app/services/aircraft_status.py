"""
Derives the computed operational status of an aircraft from open discrepancies
and overdue inspections. Manual override takes precedence over everything.

Status priority (high to low):
  NMCS — DOWNING discrepancy awaiting parts
  NMCM — DOWNING discrepancy in work, OR downing inspection overdue
  PMC  — MAJOR discrepancy in work
  FMC  — no disqualifying conditions
"""
from datetime import date
from typing import List

from app.models.models import (
    Aircraft, AircraftInspection, Discrepancy,
    AircraftStatus, DiscrepancySeverity, DiscrepancyWorkStatus,
)


def is_inspection_overdue(insp: AircraftInspection, today: date, current_hours: float) -> bool:
    """Return True if either the date or hours threshold has been exceeded."""
    if insp.next_due_date is not None and today > insp.next_due_date:
        return True
    if insp.next_due_hours is not None and current_hours > insp.next_due_hours:
        return True
    return False


def compute_status(
    aircraft: Aircraft,
    open_discrepancies: List[Discrepancy],
    overdue_inspections: List[AircraftInspection],
) -> AircraftStatus:
    """
    Derive aircraft status from discrepancy and inspection state.

    open_discrepancies — Discrepancy rows where work_status != CLOSED.
    overdue_inspections — AircraftInspection rows already confirmed overdue
                          (call is_inspection_overdue first to filter).
    """
    if aircraft.manual_status_override:
        return aircraft.manual_status_override

    # Any DOWNING discrepancy awaiting supply → NMCS
    if any(
        d.severity == DiscrepancySeverity.DOWNING and d.work_status == DiscrepancyWorkStatus.AWP
        for d in open_discrepancies
    ):
        return AircraftStatus.NMCS

    # Any DOWNING discrepancy otherwise in work → NMCM
    if any(
        d.severity == DiscrepancySeverity.DOWNING and d.work_status != DiscrepancyWorkStatus.CLOSED
        for d in open_discrepancies
    ):
        return AircraftStatus.NMCM

    # Any downing inspection overdue → NMCM
    if any(insp.inspection_type.is_downing_when_overdue for insp in overdue_inspections):
        return AircraftStatus.NMCM

    # Any MAJOR discrepancy open → PMC
    if any(
        d.severity == DiscrepancySeverity.MAJOR and d.work_status != DiscrepancyWorkStatus.CLOSED
        for d in open_discrepancies
    ):
        return AircraftStatus.PMC

    return AircraftStatus.FMC
