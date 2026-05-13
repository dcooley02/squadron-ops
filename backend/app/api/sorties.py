from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import and_
from datetime import date, datetime, time as dt_time
from typing import List, Optional
from app.database import get_db
from app.models.models import Sortie, FlightLog, SortieTaskCredit, SortieLeg, InstrumentApproach, SortieTmrCode
from app.schemas.sorties import (
    SortieSummary, SortieDetail, FlightLogOut, SortieTaskCreditOut,
    SortieLegRead, InstrumentApproachRead, SortieTmrOut,
)

router = APIRouter(prefix="/api/sorties", tags=["sorties"])


def _summary(s: Sortie) -> SortieSummary:
    return SortieSummary.model_validate({
        "id": s.id,
        "event_code": s.event_code,
        "event_type": s.event_type,
        "aircraft_id": s.aircraft_id,
        "aircraft_side_number": s.aircraft.side_number if s.aircraft else None,
        "brief_time": s.brief_time,
        "takeoff_time": s.takeoff_time,
        "land_time": s.land_time,
        "duration_hours": s.duration_hours,
        "is_complete": s.is_complete,
    })


def _approach_out(appr: InstrumentApproach) -> InstrumentApproachRead:
    return InstrumentApproachRead.model_validate({
        "id": appr.id,
        "approach_type": appr.approach_type.value,
        "actual_or_simulated": appr.actual_or_simulated.value,
        "airport_icao": appr.airport_icao,
        "runway": appr.runway,
        "remarks": appr.remarks,
        "logged_at": appr.logged_at,
    })


def _leg_out(leg: SortieLeg) -> SortieLegRead:
    return SortieLegRead.model_validate({
        "id": leg.id,
        "leg_number": leg.leg_number,
        "departure_location": leg.departure_location,
        "arrival_location": leg.arrival_location,
        "takeoff_time": leg.takeoff_time,
        "land_time": leg.land_time,
        "duration_hours": leg.duration_hours,
    })


def _log_out(fl: FlightLog) -> FlightLogOut:
    return FlightLogOut.model_validate({
        "id": fl.id,
        "person_id": fl.person_id,
        "person_name": f"{fl.person.last_name}, {fl.person.first_name}",
        "crew_position": fl.crew_position,
        "hours_logged": fl.hours_logged,
        "night_hours": fl.night_hours,
        "nvg_hours": fl.nvg_hours,
        "actual_instrument_hours": fl.actual_instrument_hours,
        "sim_instrument_hours": fl.sim_instrument_hours,
        "total_hours": fl.total_hours or fl.hours_logged,
        "first_pilot_hours": fl.first_pilot_hours or 0.0,
        "copilot_hours": fl.copilot_hours or 0.0,
        "ac_commander_hours": fl.ac_commander_hours or 0.0,
        "mission_commander_hours": fl.mission_commander_hours or 0.0,
        "instructor_hours": fl.instructor_hours or 0.0,
        "nvg_unaided_hl_hours": fl.nvg_unaided_hl_hours or 0.0,
        "nvg_unaided_ll_hours": fl.nvg_unaided_ll_hours or 0.0,
        "nvg_tactical_hl_hours": fl.nvg_tactical_hl_hours or 0.0,
        "nvg_tactical_ll_hours": fl.nvg_tactical_ll_hours or 0.0,
        "syllabus_event_completed": fl.syllabus_event_completed,
        "instructor_remarks": fl.instructor_remarks,
        "crew_qual_code": fl.crew_qual_code,
        "special_crew_time_hours": fl.special_crew_time_hours,
        "data_provenance": fl.data_provenance,
        "instrument_approaches": [_approach_out(a) for a in fl.instrument_approaches],
    })


@router.get("", response_model=List[SortieSummary])
def list_sorties(
    date_from: Optional[date] = Query(None, description="Filter sorties on or after this date"),
    date_to: Optional[date] = Query(None, description="Filter sorties on or before this date"),
    is_complete: Optional[bool] = Query(None, description="Filter by completion status"),
    limit: int = Query(100, ge=1, le=500, description="Max results (default 100, max 500)"),
    db: Session = Depends(get_db),
):
    """List sorties with optional date range and completion filters."""
    query = db.query(Sortie).options(joinedload(Sortie.aircraft))

    if date_from is not None:
        query = query.filter(Sortie.takeoff_time >= datetime.combine(date_from, dt_time.min))
    if date_to is not None:
        query = query.filter(Sortie.takeoff_time <= datetime.combine(date_to, dt_time.max))
    if is_complete is not None:
        query = query.filter(Sortie.is_complete == is_complete)

    sorties = query.order_by(Sortie.takeoff_time.desc()).limit(limit).all()
    return [_summary(s) for s in sorties]


def _credit_out(tc: SortieTaskCredit) -> SortieTaskCreditOut:
    person = tc.flight_log.person if tc.flight_log else None
    return SortieTaskCreditOut.model_validate({
        "id": tc.id,
        "task_code": tc.task_code,
        "grade": tc.grade,
        "remarks": tc.remarks,
        "person_id": tc.flight_log.person_id if tc.flight_log else 0,
        "person_name": f"{person.last_name}, {person.first_name}" if person else "Unknown",
    })


@router.get("/{sortie_id}", response_model=SortieDetail)
def get_sortie(sortie_id: int, db: Session = Depends(get_db)):
    """Get one sortie with full hour breakdown, crew, TMR codes, and task credits."""
    s = (
        db.query(Sortie)
        .options(
            joinedload(Sortie.aircraft),
            joinedload(Sortie.flight_logs).joinedload(FlightLog.person),
            joinedload(Sortie.flight_logs).joinedload(FlightLog.instrument_approaches),
            joinedload(Sortie.task_credits)
                .joinedload(SortieTaskCredit.flight_log)
                .joinedload(FlightLog.person),
            joinedload(Sortie.legs),
            joinedload(Sortie.sortie_tmr_codes).joinedload(SortieTmrCode.tmr_code),
        )
        .filter(Sortie.id == sortie_id)
        .first()
    )
    if not s:
        raise HTTPException(status_code=404, detail=f"Sortie {sortie_id} not found")

    tmr_codes_out = [
        SortieTmrOut(
            code=stc.tmr_code.code,
            description=stc.tmr_code.description,
            slot=stc.slot,
            hours=stc.hours,
        )
        for stc in sorted(s.sortie_tmr_codes, key=lambda x: x.slot)
        if stc.tmr_code
    ]

    return SortieDetail.model_validate({
        "id": s.id,
        "event_code": s.event_code,
        "event_type": s.event_type,
        "aircraft_id": s.aircraft_id,
        "aircraft_side_number": s.aircraft.side_number if s.aircraft else None,
        "brief_time": s.brief_time,
        "takeoff_time": s.takeoff_time,
        "land_time": s.land_time,
        "duration_hours": s.duration_hours,
        "is_complete": s.is_complete,
        "debrief_notes": s.debrief_notes,
        "notes": s.notes,
        "flight_mode": s.flight_mode,
        "rounds_fired_20mm": s.rounds_fired_20mm,
        "ugr_fired": s.ugr_fired,
        "csw_rounds": s.csw_rounds,
        "csw_rounds_night": s.csw_rounds_night,
        "landings_day": s.landings_day,
        "landings_night": s.landings_night,
        "landings_dve_day": s.landings_dve_day,
        "landings_dve_night": s.landings_dve_night,
        "hoist_streams": s.hoist_streams,
        "hoist_recoveries": s.hoist_recoveries,
        "amns_iterations": s.amns_iterations,
        "almds_hours": s.almds_hours,
        "amns_ntrs": s.amns_ntrs,
        "strafe_dry_profiles_day": s.strafe_dry_profiles_day,
        "strafe_dry_profiles_night": s.strafe_dry_profiles_night,
        "landings_shipboard_day": s.landings_shipboard_day,
        "landings_shipboard_night": s.landings_shipboard_night,
        "departure_location": s.departure_location,
        "arrival_location": s.arrival_location,
        "legs": [_leg_out(leg) for leg in s.legs],
        "flight_logs": [_log_out(fl) for fl in s.flight_logs],
        "task_credits": [_credit_out(tc) for tc in s.task_credits],
        "tmr_codes": tmr_codes_out,
    })
