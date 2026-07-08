"""
WTM capability-area T-rating engine (CHSCWPINST 3500.1F Appendix D aligned).

Table-driven: anchor tasks and per-area T-1/T-2 windows load from the database
(CbrTaskOption.is_anchor_task, CapabilityAreaConfig). Falls back to embedded
defaults when tables are empty (unit tests).
"""
from dataclasses import dataclass
from datetime import date, timedelta
from enum import Enum
from typing import Dict, List, Optional, Tuple

from sqlalchemy.orm import Session, joinedload

from app.catalogs.cbr_enclosure2 import AREA_CONFIG_SPECS, CBR_TASK_SPECS
from app.models.models import (
    CapabilityArea,
    CapabilityAreaConfig,
    CbrTaskOption,
    Currency,
    FlightLog,
    Person,
    Qualification,
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
    min_qual_codes: Tuple[str, ...] = ()


def _catalog_anchors(area: CapabilityArea) -> Tuple[str, ...]:
    return tuple(
        s.code
        for s in CBR_TASK_SPECS
        if s.is_anchor_task and s.capability_area == area
    )


# Fallbacks when DB config/task tables are empty (tests / pre-seed). Single source: catalog.
AREA_RULES: Dict[CapabilityArea, AreaRule] = {
    area: AreaRule(
        anchor_tasks=_catalog_anchors(area),
        t1_recency_days=t1,
        t2_recency_days=t2,
        currency_codes=tuple(currencies),
        min_qual_codes=tuple(quals),
    )
    for area, _label, t1, t2, currencies, quals in AREA_CONFIG_SPECS
}

AREA_LABELS: Dict[CapabilityArea, str] = {
    area: label for area, label, *_rest in AREA_CONFIG_SPECS
}


def _load_area_rule(db: Session, area: CapabilityArea) -> AreaRule:
    cfg = db.query(CapabilityAreaConfig).filter(
        CapabilityAreaConfig.capability_area == area
    ).first()
    anchors = (
        db.query(CbrTaskOption.code)
        .filter(
            CbrTaskOption.capability_area == area,
            CbrTaskOption.is_anchor_task.is_(True),
            CbrTaskOption.is_active.is_(True),
        )
        .order_by(CbrTaskOption.code)
        .all()
    )
    anchor_codes = tuple(a[0] for a in anchors)
    fallback = AREA_RULES[area]
    return AreaRule(
        anchor_tasks=anchor_codes or fallback.anchor_tasks,
        t1_recency_days=cfg.t1_recency_days if cfg else fallback.t1_recency_days,
        t2_recency_days=cfg.t2_recency_days if cfg else fallback.t2_recency_days,
        currency_codes=tuple(cfg.currency_codes or []) if cfg else fallback.currency_codes,
        min_qual_codes=tuple(cfg.min_qual_codes or []) if cfg else fallback.min_qual_codes,
    )


def _area_label(db: Session, area: CapabilityArea) -> str:
    cfg = db.query(CapabilityAreaConfig).filter(
        CapabilityAreaConfig.capability_area == area
    ).first()
    return cfg.label if cfg else AREA_LABELS[area]


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


def _qualification_status(
    db: Session,
    person_id: int,
    qual_codes: Tuple[str, ...],
    today: date,
) -> Tuple[bool, List[str]]:
    if not qual_codes:
        return True, []
    factors: List[str] = []
    quals = {
        q.qual_code: q
        for q in db.query(Qualification).filter(Qualification.person_id == person_id).all()
    }
    ok = True
    for code in qual_codes:
        q = quals.get(code)
        if q is None:
            ok = False
            factors.append(f"Missing qualification {code}")
        elif q.expires_date and q.expires_date < today:
            ok = False
            factors.append(f"{code} qualification expired {q.expires_date.isoformat()}")
    return ok, factors


def _currency_status(
    currencies_by_code: Dict[str, Currency],
    codes: Tuple[str, ...],
    today: date,
) -> Tuple[bool, bool, List[str]]:
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
            days_left = (curr.expires_date - today).days
            factors.append(f"{code} expires in {days_left}d (T-1 gate)")
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


def _classify_anchor(days: Optional[int], t1: int, t2: int) -> str:
    if days is None:
        return "absent"
    if days <= t1:
        return "current"
    if days <= t2:
        return "stale"
    return "absent"


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
    rule = _load_area_rule(db, area)

    if credits is None:
        credits = _load_person_credits(db, person_id)
    if currencies_by_code is None:
        currencies_by_code = {
            c.currency_code: c
            for c in db.query(Currency).filter(Currency.person_id == person_id).all()
        }

    anchor_status: List[dict] = []
    all_t1 = True
    any_in_t2 = False

    for task_code in rule.anchor_tasks:
        days = _task_recency_days(credits, task_code, today)
        status = _classify_anchor(days, rule.t1_recency_days, rule.t2_recency_days)
        if status == "current":
            any_in_t2 = True
        elif status == "stale":
            all_t1 = False
            any_in_t2 = True
        else:
            all_t1 = False
        anchor_status.append({
            "task_code": task_code,
            "status": status,
            "days_since": days,
        })

    qual_ok, qual_factors = _qualification_status(db, person_id, rule.min_qual_codes, today)
    curr_ok, curr_expiring, curr_factors = _currency_status(
        currencies_by_code, rule.currency_codes, today
    )

    factors: List[str] = []
    for a in anchor_status:
        if a["status"] == "stale" and a["days_since"] is not None:
            factors.append(
                f"{a['task_code']}: last credit {a['days_since']}d ago "
                f"(T-1 window {rule.t1_recency_days}d) — stale"
            )
        elif a["status"] == "absent":
            if a["days_since"] is None:
                factors.append(f"{a['task_code']}: no qualifying credit on record")
            else:
                factors.append(
                    f"{a['task_code']}: last credit {a['days_since']}d ago "
                    f"(beyond T-2 window {rule.t2_recency_days}d)"
                )
    factors.extend(qual_factors)
    factors.extend(curr_factors)

    if not any_in_t2:
        rating = TRating.T3
    elif not qual_ok:
        rating = TRating.T3
    elif all_t1 and curr_ok and not curr_expiring:
        rating = TRating.T1
    else:
        rating = TRating.T2
        if all_t1 and curr_expiring:
            factors.append("Linked Table B-2 currency expiring within 14 days — capped at T-2")

    return {
        "capability_area": area,
        "label": _area_label(db, area),
        "rating": rating.value,
        "contributing_factors": factors,
        "anchor_tasks": anchor_status,
        "t1_window_days": rule.t1_recency_days,
        "t2_window_days": rule.t2_recency_days,
    }


def _worst_rating(ratings: List[str]) -> str:
    order = {TRating.T1.value: 0, TRating.T2.value: 1, TRating.T3.value: 2}
    if not ratings:
        return TRating.T3.value
    return max(ratings, key=lambda r: order.get(r, 2))


def build_person_readiness(db: Session, person: Person, today: Optional[date] = None) -> dict:
    today = today or date.today()
    credits = _load_person_credits(db, person.id)
    currencies_by_code = {c.currency_code: c for c in person.currencies}
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


def _rollup_for_persons(
    person_summaries: List[dict],
    today: date,
) -> Tuple[List[dict], str, int]:
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
            "label": next(
                (a["label"] for a in person_summaries[0]["areas"] if a["capability_area"] == area),
                AREA_LABELS[area],
            ) if person_summaries else AREA_LABELS[area],
            "squadron_rating": _worst_rating(pilot_ratings),
            "t1_count": counts[TRating.T1.value],
            "t2_count": counts[TRating.T2.value],
            "t3_count": counts[TRating.T3.value],
            "pilots_rated": len(person_summaries),
        })
    overall = _worst_rating([ps["overall_rating"] for ps in person_summaries])
    return area_rollups, overall, len(person_summaries)


def build_squadron_readiness(db: Session, today: Optional[date] = None) -> dict:
    today = today or date.today()
    pilots = (
        db.query(Person)
        .options(joinedload(Person.currencies))
        .filter(Person.is_active.is_(True), Person.role == Role.PILOT)
        .order_by(Person.last_name, Person.first_name)
        .all()
    )
    aircrew = (
        db.query(Person)
        .options(joinedload(Person.currencies))
        .filter(Person.is_active.is_(True), Person.role == Role.AIRCREW)
        .order_by(Person.last_name, Person.first_name)
        .all()
    )

    person_summaries = [build_person_readiness(db, p, today) for p in pilots]
    aircrew_summaries = [build_person_readiness(db, p, today) for p in aircrew]
    area_rollups, squadron_overall, pilots_rated = _rollup_for_persons(person_summaries, today)
    _, aircrew_overall, _ = _rollup_for_persons(aircrew_summaries, today)

    return {
        "as_of_date": today,
        "pilots_rated": pilots_rated,
        "aircrew_rated": len(aircrew_summaries),
        "squadron_overall_rating": squadron_overall,
        "aircrew_overall_rating": aircrew_overall,
        "areas": area_rollups,
        "persons": person_summaries,
        "aircrew": aircrew_summaries,
    }