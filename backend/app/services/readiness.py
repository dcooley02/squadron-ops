"""
WTM capability-area T-rating engine (simplified CHSCWPINST 3500.1F Appendix D).

Ratings derive from anchor-task credit recency (Q/CQ grades) plus optional
Wing Table B-2 currency gates. Compute-on-read — no persisted cache.
"""
from dataclasses import dataclass
from datetime import date, timedelta
from enum import Enum
from typing import Dict, List, Optional, Tuple

from sqlalchemy.orm import Session, joinedload

from app.models.models import (
    CapabilityArea,
    Currency,
    FlightLog,
    Person,
    Role,
    Sortie,
    SortieTaskCredit,
    TaskGrade,
)

QUALIFYING_GRADES = {TaskGrade.Q, TaskGrade.CQ}


class TRating(str, Enum):
    T1 = "T-1"
    T2 = "T-2"
    T3 = "T-3"


@dataclass(frozen=True)
class AreaRule:
    anchor_tasks: Tuple[str, ...]
    t1_recency_days: int = 180
    t2_recency_days: int = 365
    currency_codes: Tuple[str, ...] = ()


AREA_RULES: Dict[CapabilityArea, AreaRule] = {
    CapabilityArea.MOB: AreaRule(
        anchor_tasks=("MOB 203", "MOB 204", "MOB 209"),
        currency_codes=("NIGHT_NVD",),
    ),
    CapabilityArea.FSO: AreaRule(
        anchor_tasks=("FSO 207", "FSO 209"),
        currency_codes=("CSTRS_WINCH",),
    ),
    CapabilityArea.ASU: AreaRule(
        anchor_tasks=("ASU 201", "ASU 207"),
        currency_codes=("CSW", "STRAFE_DRY"),
    ),
    CapabilityArea.SOF: AreaRule(anchor_tasks=("SOF 207",)),
    CapabilityArea.PR: AreaRule(anchor_tasks=("PR 201",)),
    CapabilityArea.STW: AreaRule(anchor_tasks=("STW 210",)),
    CapabilityArea.LOG: AreaRule(anchor_tasks=("LOG 201",)),
    CapabilityArea.MIW: AreaRule(
        anchor_tasks=("MIW 203", "MIW 205"),
        currency_codes=("ALMDS_PILOT",),
    ),
}

AREA_LABELS: Dict[CapabilityArea, str] = {
    CapabilityArea.MOB: "Mobility",
    CapabilityArea.FSO: "Fleet Support Ops",
    CapabilityArea.ASU: "Anti-Surface Warfare",
    CapabilityArea.SOF: "Special Operations Forces",
    CapabilityArea.PR: "Personnel Recovery",
    CapabilityArea.STW: "Strike Warfare",
    CapabilityArea.LOG: "Logistics",
    CapabilityArea.MIW: "Mine Warfare",
}


def _credit_event_date(credit: SortieTaskCredit, sortie: Sortie) -> date:
    if sortie.land_time:
        return sortie.land_time.date()
    if sortie.takeoff_time:
        return sortie.takeoff_time.date()
    return credit.created_at.date()


def _load_person_credits(db: Session, person_id: int) -> List[Tuple[SortieTaskCredit, Sortie]]:
    rows = (
        db.query(SortieTaskCredit, Sortie)
        .join(Sortie, SortieTaskCredit.sortie_id == Sortie.id)
        .join(FlightLog, SortieTaskCredit.flight_log_id == FlightLog.id)
        .filter(
            FlightLog.person_id == person_id,
            Sortie.is_complete.is_(True),
            SortieTaskCredit.grade.in_(QUALIFYING_GRADES),
        )
        .all()
    )
    return list(rows)


def _currency_status(
    currencies_by_code: Dict[str, Currency],
    codes: Tuple[str, ...],
    today: date,
) -> Tuple[bool, bool, List[str]]:
    """Return (all_current, any_expiring_soon, factor strings)."""
    if not codes:
        return True, False, []

    factors: List[str] = []
    all_current = True
    any_expiring = False
    for code in codes:
        curr = currencies_by_code.get(code)
        if curr is None or curr.expires_date is None:
            all_current = False
            factors.append(f"{code} not on record")
            continue
        if curr.expires_date < today:
            all_current = False
            factors.append(f"{code} expired {curr.expires_date.isoformat()}")
        elif curr.expires_date <= today + timedelta(days=14):
            any_expiring = True
            factors.append(f"{code} expires {curr.expires_date.isoformat()}")
    return all_current, any_expiring, factors


def _task_recency_days(
    credits: List[Tuple[SortieTaskCredit, Sortie]],
    task_code: str,
    today: date,
) -> Optional[int]:
    best: Optional[date] = None
    for credit, sortie in credits:
        if credit.task_code != task_code:
            continue
        event_date = _credit_event_date(credit, sortie)
        if best is None or event_date > best:
            best = event_date
    if best is None:
        return None
    return (today - best).days


def rate_person_area(
    person_id: int,
    area: CapabilityArea,
    db: Session,
    today: Optional[date] = None,
    *,
    credits: Optional[List[Tuple[SortieTaskCredit, Sortie]]] = None,
    currencies_by_code: Optional[Dict[str, Currency]] = None,
) -> dict:
    today = today or date.today()
    rule = AREA_RULES[area]

    if credits is None:
        credits = _load_person_credits(db, person_id)
    if currencies_by_code is None:
        currencies_by_code = {
            c.currency_code: c
            for c in db.query(Currency).filter(Currency.person_id == person_id).all()
        }

    anchor_status: List[dict] = []
    all_t1 = True
    any_t2 = False

    for task_code in rule.anchor_tasks:
        days = _task_recency_days(credits, task_code, today)
        if days is None:
            status = "absent"
            all_t1 = False
        elif days <= rule.t1_recency_days:
            status = "current"
            any_t2 = True
        elif days <= rule.t2_recency_days:
            status = "stale"
            all_t1 = False
            any_t2 = True
        else:
            status = "absent"
            all_t1 = False
        anchor_status.append({
            "task_code": task_code,
            "status": status,
            "days_since": days,
        })

    curr_ok, curr_expiring, curr_factors = _currency_status(
        currencies_by_code, rule.currency_codes, today
    )

    factors: List[str] = []
    if not all_t1:
        stale = [a["task_code"] for a in anchor_status if a["status"] == "stale"]
        absent = [a["task_code"] for a in anchor_status if a["status"] == "absent"]
        if stale:
            factors.append(f"Stale anchor tasks: {', '.join(stale)}")
        if absent:
            factors.append(f"No recent credit: {', '.join(absent)}")
    factors.extend(curr_factors)

    if not any_t2:
        rating = TRating.T3
    elif all_t1 and curr_ok and not curr_expiring:
        rating = TRating.T1
    elif all_t1 and curr_ok and curr_expiring:
        rating = TRating.T2
        factors.append("Linked currency expiring within 14 days")
    elif all_t1 and not curr_ok:
        rating = TRating.T2
    else:
        rating = TRating.T2

    return {
        "capability_area": area,
        "label": AREA_LABELS[area],
        "rating": rating.value,
        "contributing_factors": factors,
        "anchor_tasks": anchor_status,
    }


def _worst_rating(ratings: List[str]) -> str:
    order = {TRating.T1.value: 0, TRating.T2.value: 1, TRating.T3.value: 2}
    if not ratings:
        return TRating.T3.value
    return max(ratings, key=lambda r: order.get(r, 2))


def build_person_readiness(db: Session, person: Person, today: Optional[date] = None) -> dict:
    today = today or date.today()
    credits = _load_person_credits(db, person.id)
    currencies_by_code = {
        c.currency_code: c for c in person.currencies
    }
    areas = [
        rate_person_area(
            person.id,
            area,
            db,
            today,
            credits=credits,
            currencies_by_code=currencies_by_code,
        )
        for area in CapabilityArea
    ]
    ratings = [a["rating"] for a in areas]
    return {
        "person_id": person.id,
        "person_name": f"{person.last_name}, {person.first_name}",
        "callsign": person.callsign,
        "role": person.role,
        "overall_rating": _worst_rating(ratings),
        "areas": areas,
    }


def build_squadron_readiness(db: Session, today: Optional[date] = None) -> dict:
    today = today or date.today()
    pilots = (
        db.query(Person)
        .options(joinedload(Person.currencies))
        .filter(Person.is_active.is_(True), Person.role == Role.PILOT)
        .order_by(Person.last_name, Person.first_name)
        .all()
    )

    person_summaries = [build_person_readiness(db, p, today) for p in pilots]

    area_rollups: List[dict] = []
    for area in CapabilityArea:
        counts = {TRating.T1.value: 0, TRating.T2.value: 0, TRating.T3.value: 0}
        pilot_ratings: List[str] = []
        for ps in person_summaries:
            area_row = next(a for a in ps["areas"] if a["capability_area"] == area)
            counts[area_row["rating"]] = counts.get(area_row["rating"], 0) + 1
            pilot_ratings.append(area_row["rating"])
        area_rollups.append({
            "capability_area": area,
            "label": AREA_LABELS[area],
            "squadron_rating": _worst_rating(pilot_ratings),
            "t1_count": counts[TRating.T1.value],
            "t2_count": counts[TRating.T2.value],
            "t3_count": counts[TRating.T3.value],
            "pilots_rated": len(pilots),
        })

    all_ratings = [ps["overall_rating"] for ps in person_summaries]
    return {
        "as_of_date": today,
        "pilots_rated": len(pilots),
        "squadron_overall_rating": _worst_rating(all_ratings),
        "areas": area_rollups,
        "persons": person_summaries,
    }