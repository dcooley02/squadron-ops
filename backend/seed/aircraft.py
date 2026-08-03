"""Aircraft, inspection types, and aircraft inspections."""
import random
from datetime import timedelta

from app.models.models import Aircraft, AircraftStatus, InspectionType, AircraftInspection

from seed.constants import TODAY

# ═══════════════════════════════════════════════════════════════════════════════
# Aircraft
# ═══════════════════════════════════════════════════════════════════════════════

# Stamped statuses: 3 true FMC, 3 FMC with intentional drift (PMC/NMCM/NMCS),
# 1 PMC, 1 NMCM — targets ~50% computed FMC with 3 drift demos.
_AC_STATUSES = [
    AircraftStatus.FMC, AircraftStatus.FMC, AircraftStatus.FMC, AircraftStatus.FMC,
    AircraftStatus.FMC, AircraftStatus.FMC,
    AircraftStatus.PMC,
    AircraftStatus.FMC,  # drift_nmcs_ac: stamped FMC + DOWNING AWP → computed NMCS
]


def seed_aircraft(db):
    result = []
    for i in range(8):
        ac = Aircraft(
            bureau_number=f"16805{i + 1}",
            side_number=str(610 + i),
            type_model_series="MH-60S",
            total_airframe_hours=round(random.uniform(3000, 8000), 1),
            hours_since_phase=round(random.uniform(20, 180), 1),
            phase_interval=200.0,
            status=_AC_STATUSES[i],
        )
        db.add(ac)
        result.append(ac)
    db.flush()
    return result

# ═══════════════════════════════════════════════════════════════════════════════
# Inspection Types + Aircraft Inspections  (Batch 5a)
# ═══════════════════════════════════════════════════════════════════════════════

_INSPECTION_TYPES = [
    dict(code="DAILY",    name="Daily Inspection",    periodicity_days=1,    periodicity_hours=None, is_downing_when_overdue=False,
         description="Pre- or post-flight daily inspection per MRC workpackage."),
    dict(code="7_DAY",    name="7-Day Inspection",    periodicity_days=7,    periodicity_hours=None, is_downing_when_overdue=False,
         description="Weekly recurring inspection items per MRC."),
    dict(code="14_DAY",   name="14-Day Inspection",   periodicity_days=14,   periodicity_hours=None, is_downing_when_overdue=False,
         description="Bi-weekly inspection per MRC workpackage."),
    dict(code="28_DAY",   name="28-Day Inspection",   periodicity_days=28,   periodicity_hours=None, is_downing_when_overdue=True,
         description="28-day calendar inspection; aircraft grounded if overdue."),
    dict(code="56_DAY",   name="56-Day Inspection",   periodicity_days=56,   periodicity_hours=None, is_downing_when_overdue=True,
         description="56-day calendar inspection; aircraft grounded if overdue."),
    dict(code="PHASE",    name="Phase Inspection",    periodicity_days=None, periodicity_hours=200.0, is_downing_when_overdue=True,
         description="200-hour phase inspection; aircraft grounded when hours exceeded."),
    dict(code="CALENDAR", name="Annual Inspection",   periodicity_days=365,  periodicity_hours=None, is_downing_when_overdue=True,
         description="Annual calendar inspection per NAMP requirements."),
]


def seed_inspection_types(db):
    types = []
    for entry in _INSPECTION_TYPES:
        it = InspectionType(**entry)
        db.add(it)
        types.append(it)
    db.flush()
    return types


def seed_aircraft_inspections(db, aircraft_list, inspection_types):
    """
    Create one AircraftInspection row per (aircraft, inspection_type).
    PHASE rows are derived from existing aircraft.hours_since_phase.
    Calendar rows are status-driven (deterministic):
      NMCM  → shortest-periodicity inspection is slightly overdue (1-10 days); rest current
      FMC/PMC/NMCS → all calendar inspections current
    """
    count = 0

    phase_it = next(it for it in inspection_types if it.code == "PHASE")
    # Sort calendar types shortest-periodicity first — most likely to lapse
    calendar_types = sorted(
        [it for it in inspection_types if it.code != "PHASE"],
        key=lambda it: it.periodicity_days,
    )

    for ac in aircraft_list:
        # ── PHASE (hours-based, unchanged) ────────────────────────────────────
        last_completed_hours = round(ac.total_airframe_hours - ac.hours_since_phase, 1)
        next_due_hours = round(last_completed_hours + phase_it.periodicity_hours, 1)
        days_ago = random.randint(5, 90)
        last_date = TODAY - timedelta(days=days_ago)
        db.add(AircraftInspection(
            aircraft_id=ac.id,
            inspection_type_id=phase_it.id,
            last_completed_date=last_date,
            last_completed_hours=last_completed_hours,
            next_due_date=None,
            next_due_hours=next_due_hours,
        ))
        count += 1

        # ── Calendar (status-driven) ───────────────────────────────────────────
        is_nmcm = ac.status == AircraftStatus.NMCM
        overdue_picked = False  # exactly one overdue per NMCM aircraft

        for it in calendar_types:
            should_be_overdue = is_nmcm and not overdue_picked
            if should_be_overdue:
                overdue_by = random.randint(1, 10)
                days_ago = it.periodicity_days + overdue_by
                overdue_picked = True
            else:
                # Keep calendar inspections comfortably current for flyable aircraft.
                days_ago = random.randint(0, max(1, it.periodicity_days // 5))
            last_date = TODAY - timedelta(days=days_ago)
            next_date = last_date + timedelta(days=it.periodicity_days)
            db.add(AircraftInspection(
                aircraft_id=ac.id,
                inspection_type_id=it.id,
                last_completed_date=last_date,
                last_completed_hours=None,
                next_due_date=next_date,
                next_due_hours=None,
            ))
            count += 1

    db.flush()
    return count
