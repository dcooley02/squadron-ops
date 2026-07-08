"""
Flight completion cascade service.
Handles the full post-flight chain: closing the sortie, updating FlightLogs,
inserting task credits, refreshing currencies, updating aircraft hours,
filing discrepancies, and recording safety reports.

Transaction policy: services flush only; the API route (or caller) commits.
"""
from datetime import date, timedelta
from typing import Optional

from sqlalchemy.orm import Session, joinedload

from app.models.models import (
    Aircraft,
    CbrTaskOption,
    CrewPosition,
    Currency,
    CurrencyType,
    DataProvenance,
    FlightLog,
    FlightMode,
    InstrumentApproach,
    Person,
    SafetyReport,
    Sortie,
    SortieLeg,
    SortieOpsStatus,
    SortieTaskCredit,
    SortieTmrCode,
    TmrCode,
)
from app.schemas.logging import SortieCompletePayload, UnscheduledSortiePayload
from app.services.currency_applicability import currencies_for_person
from app.services.currency_renewal_rules import RENEWAL_RULES
from app.services.maintenance_chain import create_maintenance_chain


def _upsert_currency_typed(
    db: Session,
    person_id: int,
    currency_type: CurrencyType,
    event_date: date,
) -> None:
    """Upsert a Currency row keyed on (person_id, currency_type_id)."""
    expires = event_date + timedelta(days=currency_type.periodicity_days)
    existing = db.query(Currency).filter(
        Currency.person_id == person_id,
        Currency.currency_type_id == currency_type.id,
    ).first()
    if existing:
        if event_date >= existing.last_event_date:
            existing.last_event_date = event_date
            existing.expires_date = expires
    else:
        db.add(Currency(
            person_id=person_id,
            currency_type_id=currency_type.id,
            currency_code=currency_type.code,   # keep for read-side backward compat
            last_event_date=event_date,
            expires_date=expires,
        ))


def complete_sortie(db: Session, sortie_id: int, payload: SortieCompletePayload) -> Sortie:
    """
    Apply the full post-flight cascade for a sortie.

    Locks the sortie row (``SELECT … FOR UPDATE``) so concurrent completes cannot
    double-apply airframe hours. Flushes changes; caller must commit.
    """
    # ── Step 1: lock sortie row and load relationships (single query) ─────────
    # with_for_update(of=Sortie) locks only the sorties row, not joined tables.
    sortie = (
        db.query(Sortie)
        .options(
            joinedload(Sortie.aircraft),
            joinedload(Sortie.flight_logs)
                .joinedload(FlightLog.person)
                .joinedload(Person.qualifications),
            joinedload(Sortie.flight_logs).joinedload(FlightLog.task_credits),
        )
        .filter(Sortie.id == sortie_id)
        .with_for_update(of=Sortie)
        .first()
    )
    if sortie is None:
        raise ValueError(f"Sortie {sortie_id} not found")
    if sortie.is_complete:
        raise ValueError(f"Sortie {sortie_id} is already marked complete")

    # ── Step 2: update sortie fields ──────────────────────────────────────────
    sortie.takeoff_time = payload.actual_takeoff_time
    sortie.land_time = payload.actual_land_time
    sortie.duration_hours = payload.duration_hours
    sortie.debrief_notes = payload.debrief_notes
    # Activity quantities — written through from debrief payload; null stays null.
    sortie.rounds_fired_20mm       = payload.rounds_fired_20mm
    sortie.ugr_fired               = payload.ugr_fired
    sortie.csw_rounds              = payload.csw_rounds
    sortie.csw_rounds_night        = payload.csw_rounds_night
    # Landings: prefer per-crew values on flight_log_actuals; else sortie-level + HAC mirror.
    # Sortie-level totals set after FlightLog updates below.
    sortie.hoist_streams           = payload.hoist_streams
    sortie.hoist_recoveries        = payload.hoist_recoveries
    sortie.amns_iterations         = payload.amns_iterations
    sortie.almds_hours             = payload.almds_hours
    sortie.amns_ntrs               = payload.amns_ntrs
    sortie.strafe_dry_profiles_day   = payload.strafe_dry_profiles_day
    sortie.strafe_dry_profiles_night = payload.strafe_dry_profiles_night
    # Derive location from legs when provided; fall back to direct payload fields
    if payload.legs:
        sortie.departure_location = payload.legs[0].departure_location
        sortie.arrival_location   = payload.legs[-1].arrival_location
    else:
        sortie.departure_location = payload.departure_location
        sortie.arrival_location   = payload.arrival_location
    if payload.flight_mode is not None:
        sortie.flight_mode = payload.flight_mode
    # Mark complete only after validation of payload references succeeds
    # (set after TMR / flight_log / task-credit checks below).

    flight_mode = payload.flight_mode if payload.flight_mode is not None else sortie.flight_mode
    flight_date = payload.actual_takeoff_time.date()

    # Create SortieLeg rows when routing was multi-stop
    for leg_spec in payload.legs:
        db.add(SortieLeg(
            sortie_id=sortie.id,
            leg_number=leg_spec.leg_number,
            departure_location=leg_spec.departure_location,
            arrival_location=leg_spec.arrival_location,
            takeoff_time=leg_spec.takeoff_time,
            land_time=leg_spec.land_time,
            duration_hours=leg_spec.duration_hours,
        ))

    # Create SortieTmrCode junction rows (one per slot, max 3) — unknown codes rejected
    tmr_code_cache: dict[str, TmrCode] = {}
    for tmr_assign in payload.tmr_codes:
        tmr_obj = tmr_code_cache.get(tmr_assign.code)
        if tmr_obj is None:
            tmr_obj = db.query(TmrCode).filter(TmrCode.code == tmr_assign.code).first()
            if tmr_obj is None:
                raise ValueError(f"Unknown TMR code: {tmr_assign.code}")
            tmr_code_cache[tmr_assign.code] = tmr_obj
        db.add(SortieTmrCode(
            sortie_id=sortie.id,
            tmr_code_id=tmr_obj.id,
            slot=tmr_assign.slot,
            hours=tmr_assign.hours,
        ))

    # ── Step 4: update each FlightLog ───────────────────────────────────────────
    log_by_id: dict[int, FlightLog] = {fl.id: fl for fl in sortie.flight_logs}
    for actuals in payload.flight_log_actuals:
        fl = log_by_id.get(actuals.flight_log_id)
        if fl is None:
            raise ValueError(
                f"FlightLog {actuals.flight_log_id} not found on sortie {sortie_id}"
            )
        fl.hours_logged = actuals.hours_logged
        # Environment hours
        fl.night_hours = actuals.night_hours
        fl.nvg_hours = actuals.nvg_hours
        fl.actual_instrument_hours = actuals.actual_instrument_hours
        fl.sim_instrument_hours = actuals.sim_instrument_hours
        # Role hours
        fl.total_hours = actuals.total_hours
        fl.first_pilot_hours = actuals.first_pilot_hours
        fl.copilot_hours = actuals.copilot_hours
        fl.ac_commander_hours = actuals.ac_commander_hours
        fl.mission_commander_hours = actuals.mission_commander_hours
        fl.instructor_hours = actuals.instructor_hours
        # NVG subcategories
        fl.nvg_unaided_hl_hours = actuals.nvg_unaided_hl_hours
        fl.nvg_unaided_ll_hours = actuals.nvg_unaided_ll_hours
        fl.nvg_tactical_hl_hours = actuals.nvg_tactical_hl_hours
        fl.nvg_tactical_ll_hours = actuals.nvg_tactical_ll_hours
        fl.data_provenance = DataProvenance.ENTERED
        if actuals.syllabus_event_completed is not None:
            fl.syllabus_event_completed = actuals.syllabus_event_completed
        if actuals.instructor_remarks is not None:
            fl.instructor_remarks = actuals.instructor_remarks
        fl.special_crew_time_hours = actuals.special_crew_time_hours
        # Per-crew landings (None means "not provided" for rollup logic)
        if actuals.landings_day is not None:
            fl.landings_day = actuals.landings_day
        if actuals.landings_night is not None:
            fl.landings_night = actuals.landings_night
        if actuals.landings_dve_day is not None:
            fl.landings_dve_day = actuals.landings_dve_day
        if actuals.landings_dve_night is not None:
            fl.landings_dve_night = actuals.landings_dve_night
        if actuals.landings_shipboard_day is not None:
            fl.landings_shipboard_day = actuals.landings_shipboard_day
        if actuals.landings_shipboard_night is not None:
            fl.landings_shipboard_night = actuals.landings_shipboard_night
        for appr in actuals.approaches:
            db.add(InstrumentApproach(
                flight_log_id=fl.id,
                sortie_id=sortie.id,
                approach_type=appr.approach_type,
                actual_or_simulated=appr.actual_or_simulated,
                airport_icao=appr.airport_icao,
                runway=appr.runway,
                remarks=appr.remarks,
                logged_at=payload.actual_land_time,
            ))

    # Landings rollup: per-crew when any crewmember provided landing fields
    per_crew_landings = any(
        a.landings_day is not None
        or a.landings_night is not None
        or a.landings_dve_day is not None
        or a.landings_dve_night is not None
        or a.landings_shipboard_day is not None
        or a.landings_shipboard_night is not None
        for a in payload.flight_log_actuals
    )
    if per_crew_landings:
        sortie.landings_day = sum(fl.landings_day or 0 for fl in sortie.flight_logs)
        sortie.landings_night = sum(fl.landings_night or 0 for fl in sortie.flight_logs)
        sortie.landings_dve_day = sum(fl.landings_dve_day or 0 for fl in sortie.flight_logs)
        sortie.landings_dve_night = sum(fl.landings_dve_night or 0 for fl in sortie.flight_logs)
        sortie.landings_shipboard_day = sum(fl.landings_shipboard_day or 0 for fl in sortie.flight_logs) or None
        sortie.landings_shipboard_night = sum(fl.landings_shipboard_night or 0 for fl in sortie.flight_logs) or None
    else:
        # Legacy: sortie-level landings mirrored onto HAC flight log
        sortie.landings_day = payload.landings_day
        sortie.landings_night = payload.landings_night
        sortie.landings_dve_day = payload.landings_dve_day
        sortie.landings_dve_night = payload.landings_dve_night
        sortie.landings_shipboard_day = payload.landings_shipboard_day or None
        sortie.landings_shipboard_night = payload.landings_shipboard_night or None
        _hac = next(
            (fl for fl in sortie.flight_logs if fl.crew_position == CrewPosition.HAC),
            None,
        )
        if _hac is not None:
            _hac.landings_day = payload.landings_day or 0
            _hac.landings_night = payload.landings_night or 0
            _hac.landings_dve_day = payload.landings_dve_day or 0
            _hac.landings_dve_night = payload.landings_dve_night or 0
            _hac.landings_shipboard_day = payload.landings_shipboard_day or 0
            _hac.landings_shipboard_night = payload.landings_shipboard_night or 0

    # Build person_id → flight_log map for task-credit insertion
    log_by_person: dict[int, FlightLog] = {fl.person_id: fl for fl in sortie.flight_logs}

    # ── Step 5: insert SortieTaskCredit rows ────────────────────────────────────
    needed_task_codes = {c.task_code for c in payload.task_credits}
    task_options: dict[str, CbrTaskOption] = {}
    if needed_task_codes:
        task_options = {
            row.code: row
            for row in db.query(CbrTaskOption)
            .filter(CbrTaskOption.code.in_(needed_task_codes))
            .all()
        }

    for credit_spec in payload.task_credits:
        task_opt = task_options.get(credit_spec.task_code)
        if task_opt is None:
            raise ValueError(f"Unknown CBR task code: {credit_spec.task_code}")
        if (
            flight_mode == FlightMode.SIM_TOFT
            and not task_opt.sim_eligible
        ):
            continue  # domain rule: non-sim-eligible tasks skipped on SIM sorties
        for person_id in credit_spec.person_ids:
            fl = log_by_person.get(person_id)
            if fl is None:
                raise ValueError(
                    f"Person {person_id} is not on sortie {sortie_id}; "
                    f"cannot credit task {credit_spec.task_code}"
                )
            # Honour uniqueness: skip if already credited (idempotent re-submit)
            existing = db.query(SortieTaskCredit).filter(
                SortieTaskCredit.flight_log_id == fl.id,
                SortieTaskCredit.task_code == credit_spec.task_code,
            ).first()
            if existing:
                continue
            db.add(SortieTaskCredit(
                sortie_id=sortie.id,
                flight_log_id=fl.id,
                task_code=credit_spec.task_code,
                grade=credit_spec.grade,
                remarks=credit_spec.remarks,
            ))

    # Mark complete only after payload references validated
    sortie.is_complete = True
    sortie.ops_status = SortieOpsStatus.DEBRIEFED
    if payload.flight_mode is not None:
        sortie.flight_mode = payload.flight_mode

    # Flush so we can count credits per log below
    db.flush()

    # Update readiness_credits_count cache on each FlightLog
    for fl in sortie.flight_logs:
        fl.readiness_credits_count = (
            db.query(SortieTaskCredit)
            .filter(SortieTaskCredit.flight_log_id == fl.id)
            .count()
        )

    # ── Step 6: refresh currencies (Wing Table B-2, activity-quantity gated) ────
    for fl in sortie.flight_logs:
        person = fl.person
        if person is None:
            continue
        applicable_types = currencies_for_person(person, db)
        for ct in applicable_types:
            if flight_mode == FlightMode.SIM_TOFT and not ct.sim_eligible:
                continue
            rule = RENEWAL_RULES.get(ct.code)
            if rule and rule(sortie, fl):
                _upsert_currency_typed(db, person.id, ct, flight_date)

    # ── Step 7: update aircraft hours (LIVE only), with row lock ────────────────
    if flight_mode == FlightMode.LIVE and sortie.aircraft_id:
        aircraft = (
            db.query(Aircraft)
            .filter(Aircraft.id == sortie.aircraft_id)
            .with_for_update()
            .first()
        )
        if aircraft is not None:
            aircraft.total_airframe_hours += payload.duration_hours
            aircraft.hours_since_phase += payload.duration_hours
            sortie.aircraft = aircraft

    # ── Step 8: insert new Discrepancy rows ─────────────────────────────────────
    hac_log = next(
        (fl for fl in sortie.flight_logs if fl.crew_position == CrewPosition.HAC), None
    )
    hac_person_id: Optional[int] = hac_log.person_id if hac_log else None

    for disc_spec in payload.new_discrepancies:
        create_maintenance_chain(
            db,
            aircraft_id=sortie.aircraft_id,
            description=disc_spec.description,
            severity=disc_spec.severity,
            system_affected=disc_spec.system_affected,
            notes=disc_spec.notes,
            type_wo_code=disc_spec.type_wo_code or "DM",
            sortie_id=sortie.id,
            reported_by_person_id=hac_person_id,
        )

    # ── Step 9: insert SafetyReport rows ────────────────────────────────────────
    for sr_spec in payload.safety_reports:
        db.add(SafetyReport(
            sortie_id=sortie.id,
            reported_by_person_id=hac_person_id,
            severity=sr_spec.severity,
            category=sr_spec.category,
            description=sr_spec.description,
            actions_taken=sr_spec.actions_taken,
            status="OPEN",
        ))

    # ── Step 10: flush (caller commits) ─────────────────────────────────────────
    db.flush()
    db.refresh(sortie)
    return sortie


def create_and_complete_unscheduled(
    db: Session, payload: UnscheduledSortiePayload
) -> Sortie:
    """
    Create an unscheduled or simulator sortie, optionally running the full
    completion cascade in the same transaction. Flushes only; caller commits.
    """
    from app.models.models import FlightLog as FL

    # Build Sortie
    sortie = Sortie(
        event_type=payload.event_type,
        event_code=payload.event_code,
        aircraft_id=payload.aircraft_id,
        brief_time=payload.brief_time,
        takeoff_time=payload.takeoff_time,
        land_time=payload.land_time,
        duration_hours=payload.duration_hours or 0.0,
        notes=payload.notes,
        flight_mode=payload.flight_mode,
        simulator_id=payload.simulator_id,
        is_complete=False,
    )
    db.add(sortie)
    db.flush()

    # Build FlightLogs
    for slot in payload.crew:
        hours = slot.hours_logged if slot.hours_logged is not None else (payload.duration_hours or 0.0)
        fl = FL(
            sortie_id=sortie.id,
            person_id=slot.person_id,
            crew_position=slot.crew_position,
            hours_logged=hours,
            syllabus_event_completed=slot.syllabus_event_completed,
        )
        db.add(fl)
    db.flush()

    if not payload.immediate_complete:
        db.refresh(sortie)
        return sortie

    # Immediate completion — run the cascade (still flush-only)
    if payload.completion is None:
        raise ValueError("completion payload is required when immediate_complete=True")

    return complete_sortie(db, sortie.id, payload.completion)
