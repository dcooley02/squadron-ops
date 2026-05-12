"""
Crew eligibility and sortie fitness scoring for the scheduling subsystem.
"""
from datetime import date, datetime, timedelta
from typing import Optional

from sqlalchemy.orm import Session, joinedload
from sqlalchemy import func

from app.models.models import (
    Person, Sortie, FlightLog, Qualification, Currency, SyllabusEvent,
    Role, CrewPosition, AircraftStatus,
)
from app.schemas.scheduling import EligibleCrewmember, SortieFitness, FitnessWarning


# ─── Low-level helpers ────────────────────────────────────────────────────────

def is_qualified(person: Person, qual_code: str, on_date: date) -> bool:
    """True if person holds qual_code valid on on_date (None expires_date = non-expiring)."""
    for q in person.qualifications:
        if q.qual_code == qual_code:
            if q.expires_date is None or q.expires_date >= on_date:
                return True
    return False


def has_current_currency(person: Person, currency_code: str, on_date: date) -> bool:
    """True if person has a current currency for currency_code on on_date."""
    for c in person.currencies:
        if c.currency_code == currency_code:
            if c.expires_date is None or c.expires_date >= on_date:
                return True
    return False


def hours_flown_last_30_days(db: Session, person_id: int) -> float:
    """Total logged hours for person over the last 30 days of completed sorties."""
    cutoff = datetime.utcnow() - timedelta(days=30)
    result = (
        db.query(func.sum(FlightLog.hours_logged))
        .join(Sortie, FlightLog.sortie_id == Sortie.id)
        .filter(
            FlightLog.person_id == person_id,
            Sortie.is_complete == True,
            Sortie.takeoff_time >= cutoff,
        )
        .scalar()
    )
    return float(result or 0.0)


# ─── Sortie context helpers ───────────────────────────────────────────────────

def _sortie_date(sortie: Sortie) -> date:
    return sortie.takeoff_time.date() if sortie.takeoff_time else date.today()


def _is_night(sortie: Sortie) -> bool:
    if not sortie.takeoff_time:
        return False
    h = sortie.takeoff_time.hour
    return h >= 19 or h < 5


def _requires_nvg(sortie: Sortie) -> bool:
    has_nvg_hours = bool(sortie.nvg_hours and sortie.nvg_hours > 0)
    has_nvg_type = bool(sortie.event_type and "NVG" in sortie.event_type.upper())
    return has_nvg_hours or has_nvg_type


def _currencies_sortie_refreshes(sortie: Sortie) -> set[str]:
    """Return the set of currency codes that flying this sortie would refresh."""
    refreshed: set[str] = set()
    if sortie.nvg_hours and sortie.nvg_hours > 0:
        refreshed.add("NVG")
    if sortie.instrument_hours and sortie.instrument_hours > 0:
        refreshed.add("INSTR")
    if sortie.day_hours and sortie.day_hours > 0:
        refreshed.add("DAY_DL")
    if sortie.night_hours and sortie.night_hours > 0:
        refreshed.add("NIGHT_DL")
    if sortie.event_type and "SAR" in sortie.event_type.upper():
        refreshed.update({"SAR_DAY", "SAR_NIGHT"})
    return refreshed


# ─── Main service functions ───────────────────────────────────────────────────

def get_eligible_crew(
    db: Session,
    sortie: Sortie,
    crew_position: CrewPosition,
) -> list[EligibleCrewmember]:
    """
    Returns a ranked list of persons eligible to fill crew_position on this sortie,
    sorted by score ascending (lower score = higher priority).
    """
    sortie_date = _sortie_date(sortie)
    is_night = _is_night(sortie)
    requires_nvg = _requires_nvg(sortie)

    # Load candidate pool with quals and currencies in one query
    if crew_position in (CrewPosition.HAC, CrewPosition.H2P, CrewPosition.H2P_U):
        role_filter = Role.PILOT
    else:
        role_filter = Role.AIRCREW

    candidates: list[Person] = (
        db.query(Person)
        .options(
            joinedload(Person.qualifications),
            joinedload(Person.currencies),
        )
        .filter(Person.role == role_filter, Person.is_active == True)
        .all()
    )

    # Pre-fetch all syllabus events
    all_syllabus: list[SyllabusEvent] = db.query(SyllabusEvent).all()

    # Pre-fetch completed syllabus events per person (all persons, one query)
    completed_by_person: dict[int, set[str]] = {}
    for person_id, code in (
        db.query(FlightLog.person_id, FlightLog.syllabus_event_completed)
        .filter(FlightLog.syllabus_event_completed.isnot(None))
        .all()
    ):
        completed_by_person.setdefault(person_id, set()).add(code)

    # Pre-fetch hours in last 30 days per person (one query)
    cutoff_dt = datetime.utcnow() - timedelta(days=30)
    hours_rows = (
        db.query(FlightLog.person_id, func.sum(FlightLog.hours_logged))
        .join(Sortie, FlightLog.sortie_id == Sortie.id)
        .filter(Sortie.is_complete == True, Sortie.takeoff_time >= cutoff_dt)
        .group_by(FlightLog.person_id)
        .all()
    )
    hours_by_person: dict[int, float] = {pid: float(h or 0) for pid, h in hours_rows}

    # Compute median hours for this role pool — used for load-leveling reason
    all_hrs = sorted(hours_by_person.get(p.id, 0.0) for p in candidates)
    n_c = len(all_hrs)
    if n_c == 0:
        role_median = 0.0
    elif n_c % 2 == 0:
        role_median = (all_hrs[n_c // 2 - 1] + all_hrs[n_c // 2]) / 2.0
    else:
        role_median = all_hrs[n_c // 2]

    # Currency codes this sortie would refresh (for reason generation)
    refreshed = _currencies_sortie_refreshes(sortie)

    eligible: list[EligibleCrewmember] = []

    for person in candidates:
        reasons: list[str] = []

        # ── Eligibility gate ──────────────────────────────────────────────────
        if crew_position == CrewPosition.HAC:
            if not is_qualified(person, "HAC", sortie_date):
                continue
            if requires_nvg and not has_current_currency(person, "NVG", sortie_date):
                continue
            if is_night and not has_current_currency(person, "NIGHT_DL", sortie_date):
                continue

        elif crew_position == CrewPosition.H2P:
            if not is_qualified(person, "H2P", sortie_date):
                continue
            if requires_nvg and not has_current_currency(person, "NVG", sortie_date):
                continue
            if is_night and not has_current_currency(person, "NIGHT_DL", sortie_date):
                continue

        elif crew_position == CrewPosition.H2P_U:
            has_h2p = is_qualified(person, "H2P", sortie_date)
            # Qualified pilot goes here only on training (event_code present)
            if has_h2p and not sortie.event_code:
                continue
            # NVG/night still applies for H2P_U flying those missions
            if requires_nvg and not has_current_currency(person, "NVG", sortie_date):
                continue
            if is_night and not has_current_currency(person, "NIGHT_DL", sortie_date):
                continue

        # CREW_CHIEF, AIRCREW, AWS: any active aircrew member is eligible

        # ── Scoring ───────────────────────────────────────────────────────────
        completed = completed_by_person.get(person.id, set())
        all_codes = {ev.code for ev in all_syllabus}
        pending = all_codes - completed

        # Syllabus component: 0 if sortie event helps them, 100 otherwise
        if sortie.event_code and sortie.event_code in pending:
            syllabus_bonus = 0.0
            reasons.append(f"Needs {sortie.event_code} for syllabus")
        else:
            syllabus_bonus = 100.0

        # Minimum currency days left (urgency tiebreaker; expired = negative)
        days_list = [
            (c.expires_date - sortie_date).days
            for c in person.currencies
            if c.expires_date is not None
        ]
        min_currency_days = min(days_list) if days_list else 90
        # Currency benefit: expiring within 14 days AND sortie would refresh it
        for c in person.currencies:
            if c.currency_code in refreshed and c.expires_date:
                days_left = (c.expires_date - sortie_date).days
                if 0 <= days_left <= 14:
                    reasons.append(
                        f"{c.currency_code} expires in {days_left}d — this flight refreshes it"
                    )

        # Load-leveling: below squadron median for this role
        hrs_30d = hours_by_person.get(person.id, 0.0)
        if hrs_30d < role_median:
            reasons.append(f"Low hours this month ({hrs_30d:.1f}h)")

        if not reasons:
            reasons.append("Available, qualified")

        # Rank penalty for CREW_CHIEF (prefer AWS1 > AWS2 > AWS3)
        rank_penalty = 0.0
        if crew_position == CrewPosition.CREW_CHIEF:
            rank_penalty = {"AWS1": 0.0, "AWS2": 5.0}.get(person.rank or "", 25.0)

        score = syllabus_bonus + min_currency_days + hrs_30d * 0.5 + rank_penalty

        eligible.append(EligibleCrewmember(
            person_id=person.id,
            last_name=person.last_name,
            first_name=person.first_name,
            callsign=person.callsign,
            rank=person.rank,
            score=score,
            reasons=reasons,
        ))

    eligible.sort(key=lambda e: e.score)
    return eligible


def compute_fitness(db: Session, sortie_id: int) -> Optional[SortieFitness]:
    """
    Returns the fitness assessment for a sortie's currently assigned crew.
    Returns None if the sortie does not exist.
    """
    sortie = (
        db.query(Sortie)
        .options(
            joinedload(Sortie.aircraft),
            joinedload(Sortie.flight_logs).joinedload(FlightLog.person).joinedload(Person.qualifications),
            joinedload(Sortie.flight_logs).joinedload(FlightLog.person).joinedload(Person.currencies),
        )
        .filter(Sortie.id == sortie_id)
        .first()
    )
    if not sortie:
        return None

    warnings: list[FitnessWarning] = []
    sortie_date = _sortie_date(sortie)
    is_night = _is_night(sortie)
    requires_nvg = _requires_nvg(sortie)

    # ── Per-crewmember eligibility checks ─────────────────────────────────────
    for fl in sortie.flight_logs:
        person = fl.person
        pos = fl.crew_position
        target = f"person:{person.id}"

        if pos == CrewPosition.HAC:
            if not is_qualified(person, "HAC", sortie_date):
                warnings.append(FitnessWarning(
                    severity="red",
                    message=f"{person.last_name} lacks a current HAC qualification",
                    target=target,
                ))
            if requires_nvg and not has_current_currency(person, "NVG", sortie_date):
                warnings.append(FitnessWarning(
                    severity="red",
                    message=f"{person.last_name} NVG currency expired/missing (NVG sortie)",
                    target=target,
                ))
            if is_night and not has_current_currency(person, "NIGHT_DL", sortie_date):
                warnings.append(FitnessWarning(
                    severity="red",
                    message=f"{person.last_name} NIGHT_DL currency expired (night sortie)",
                    target=target,
                ))

        elif pos in (CrewPosition.H2P, CrewPosition.H2P_U):
            if not is_qualified(person, "H2P", sortie_date):
                warnings.append(FitnessWarning(
                    severity="red",
                    message=f"{person.last_name} lacks a current H2P qualification",
                    target=target,
                ))
            if requires_nvg and not has_current_currency(person, "NVG", sortie_date):
                warnings.append(FitnessWarning(
                    severity="red",
                    message=f"{person.last_name} NVG currency expired/missing (NVG sortie)",
                    target=target,
                ))
            if is_night and not has_current_currency(person, "NIGHT_DL", sortie_date):
                warnings.append(FitnessWarning(
                    severity="red",
                    message=f"{person.last_name} NIGHT_DL currency expired (night sortie)",
                    target=target,
                ))

    # ── Required slot checks ──────────────────────────────────────────────────
    _REQUIRED_SLOTS: dict[CrewPosition, str] = {
        CrewPosition.HAC: "HAC slot unfilled",
        CrewPosition.CREW_CHIEF: "Crew Chief slot unfilled",
    }
    filled = {fl.crew_position for fl in sortie.flight_logs}
    for req_pos, msg in _REQUIRED_SLOTS.items():
        if req_pos not in filled:
            warnings.append(FitnessWarning(
                severity="red",
                message=msg,
                target=req_pos.value,
            ))

    # ── Aircraft status check ─────────────────────────────────────────────────
    if sortie.aircraft and sortie.aircraft.status in (
        AircraftStatus.NMC, AircraftStatus.NMCM, AircraftStatus.NMCS
    ):
        warnings.append(FitnessWarning(
            severity="red",
            message=(
                f"Aircraft {sortie.aircraft.side_number} is {sortie.aircraft.status.value}"
                " — not mission-capable"
            ),
            target=f"aircraft:{sortie.aircraft.id}",
        ))

    # ── Yellow: no syllabus or currency benefit ───────────────────────────────
    if sortie.flight_logs:
        refreshed = _currencies_sortie_refreshes(sortie)

        # Pre-fetch completed syllabus events for crew members
        crew_ids = [fl.person_id for fl in sortie.flight_logs]
        completed_by_person: dict[int, set[str]] = {}
        for person_id, code in (
            db.query(FlightLog.person_id, FlightLog.syllabus_event_completed)
            .filter(
                FlightLog.person_id.in_(crew_ids),
                FlightLog.syllabus_event_completed.isnot(None),
            )
            .all()
        ):
            completed_by_person.setdefault(person_id, set()).add(code)

        has_benefit = False
        for fl in sortie.flight_logs:
            completed = completed_by_person.get(fl.person_id, set())

            # Syllabus benefit: sortie event is pending for this crew member
            if sortie.event_code and sortie.event_code not in completed:
                has_benefit = True
                break

            # Currency benefit: flying this sortie refreshes an expiring currency
            for c in fl.person.currencies:
                if c.currency_code in refreshed and c.expires_date:
                    days_left = (c.expires_date - sortie_date).days
                    if 0 <= days_left <= 14:
                        has_benefit = True
                        break
            if has_benefit:
                break

        if not has_benefit:
            warnings.append(FitnessWarning(
                severity="yellow",
                message="No syllabus or currency benefit — proficiency only",
                target="sortie",
            ))

    # ── Overall status ────────────────────────────────────────────────────────
    if any(w.severity == "red" for w in warnings):
        overall = "red"
    elif any(w.severity == "yellow" for w in warnings):
        overall = "yellow"
    else:
        overall = "green"

    return SortieFitness(overall_status=overall, warnings=warnings)
