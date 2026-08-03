"""Historical and future sorties, approaches, task credits, safety reports."""
import random
from datetime import datetime, timedelta

from app.models.models import (
    Sortie, FlightLog, InstrumentApproach, SortieTaskCredit, SafetyReport,
    CrewPosition, AircraftStatus, FlightMode, TaskGrade,
    ApproachType, ApproachConditions, SortieOpsStatus, Currency,
)

from seed.constants import TODAY
from app.core.time import utc_now

# ═══════════════════════════════════════════════════════════════════════════════
# Event-type lookup for historical sorties
# (drives currency refresh logic via "SAR" in event_type check)
# ═══════════════════════════════════════════════════════════════════════════════

_EVENT_TYPE_MAP: dict[str, str] = {
    "L200": "LAB", "L201": "LAB", "L202": "LAB", "L203": "LAB",
    "P200": "INTRO", "P201": "INTRO",
    "P211": "ASU", "P212": "ASU", "P214": "ASU", "P215": "ASU",
    "P221": "CSAR", "P223": "CSAR", "P225": "CSAR", "P226": "CSAR",
    "P231": "SOF", "P232": "SOF", "P233": "SOF", "P234": "SOF",
    "P290": "ORAL_BOARD", "P291": "STAN_EVAL", "L290": "LAB", "P292": "TRAINING", "P293": "TRAINING",
    "L300": "LAB", "L301": "LAB", "P300": "INTRO",
    "P314": "ASU", "P315": "ASU",
    "P323": "CSAR", "P325": "CSAR", "P326": "CSAR",
    "P331": "SOF", "P333": "SOF", "P334": "SOF",
    "P390": "ORAL_BOARD", "P391": "STAN_EVAL", "L390": "LAB", "P392": "TRAINING",
    "L203_AMCM": "LAB", "L204_AMCM": "LAB",
    "P210": "AMCM", "P211_AMCM": "AMCM", "P212_AMCM": "AMCM",
    "P220": "AMCM", "P221_AMCM": "AMCM", "P222_AMCM": "AMCM",
    "P291_AMCM": "STAN_EVAL", "L290_AMCM": "LAB", "P292_AMCM": "AMCM",
    "L200_AW": "LAB", "L201_AW": "LAB", "L202_AW": "LAB", "L203_AW": "LAB",
    "A212": "ASU", "A213": "ASU",
    "A221": "CSAR", "A222": "CSAR", "A223": "CSAR", "A224": "CSAR",
    "A232": "SOF", "A233": "SOF", "A234": "SOF",
    "A291": "STAN_EVAL",
    "A301": "INTRO",
    "A314": "ASU", "A315": "ASU",
    "A323": "CSAR", "A325": "CSAR", "A326": "CSAR",
    "A331": "SOF", "A333": "SOF", "A334": "SOF",
    "A390": "ORAL_BOARD", "A391": "STAN_EVAL", "L390_AW": "LAB", "A392": "TRAINING",
    "L301_AW_AMCM": "LAB", "L302_AW_AMCM": "LAB", "L303_AW_AMCM": "LAB",
    "A310": "AMCM", "A320": "AMCM",
    "A390_AMCM": "STAN_EVAL", "A391_AMCM": "STAN_EVAL",
}

# Weighted historical event pool: ~50% L2, ~30% L3, ~10% AMCM, ~10% non-syllabus
_HIST_POOL = (
    ["P200", "P201", "P211", "P212", "P214", "P215",
     "P221", "P223", "P225", "P231", "P233", "P234"] * 4
    + ["A212", "A213", "A221", "A222", "A223", "A232", "A233", "A234"] * 3
    + ["P300", "P314", "P315", "P323", "P325", "P331", "P333", "P334"] * 2
    + ["A314", "A315", "A323", "A325", "A331", "A333"] * 2
    + ["P210", "P211_AMCM", "P220", "A310", "A320"]
    + ["P291", "P391", "A291"]
    + [None, None, None]        # PROFICIENCY / FCF
)

# ═══════════════════════════════════════════════════════════════════════════════
# Historical Sorties & Flight Logs
# ═══════════════════════════════════════════════════════════════════════════════

_NOTES = [
    "NVG low-level transit and approach; crew coordination good.",
    "FLIR checks and hoist training IAW NATOPS.",
    "CSAR pattern work, multiple datum runs.",
    "Touch-and-go ops at KNFG; AFCS check normal.",
    "FCF post-phase check; all systems normal.",
    "NVG CSAR scenario with SAR swimmer deployment.",
    "Dual-pilot instrument approaches at KNZY.",
    "ASU low-level with FLIR; NVG comms check.",
    "Proficiency hoist and forward-area landing zone survey.",
    "Night CSAR pattern; multiple simulated survivor contacts.",
    "Shipboard landing qualifications; 12 traps completed.",
    "Overland nap-of-earth transit; FLIR tracking exercise.",
]

# CBR task codes likely credited per event_type
_EVENT_TASK_MAP: dict[str, list[str]] = {
    "INTRO":       ["MOB 203", "MOB 211", "MOB 216"],
    "PROFICIENCY": ["MOB 203", "MOB 211", "MOB 202", "MOB 207"],
    "ASU":         ["MOB 203", "ASU 201", "ASU 207", "ASU 209", "MOB 202"],
    "CSAR":        ["FSO 209", "FSO 207", "FSO 208", "MOB 203", "PR 201", "PR 206"],
    "SOF":         ["SOF 207", "SOF 208", "MOB 203"],
    "AMCM":        ["MIW 203", "MIW 205", "MIW 207", "MOB 203"],
    "STAN_EVAL":   ["MOB 203", "MOB 202", "MOB 209"],
    "TRAINING":    ["MOB 203", "MOB 206"],
    "FCF":         ["MOB 203", "MOB 202"],
    "VERTREP":     ["LOG 201", "LOG 205", "MOB 203"],
    "STRIKE":      ["STW 210", "STW 206", "MOB 203"],
}

_GRADE_POOL = [TaskGrade.Q] * 70 + [TaskGrade.CQ] * 20 + [TaskGrade.NO] * 6 + [TaskGrade.NG] * 4


def _generate_activity(event_type: str, event_code: str | None, day_hours: float, night_hours: float, nvg_hours: float) -> dict:
    """Return plausible activity quantity kwargs for a completed historical sortie."""
    activity: dict = {}
    et = (event_type or "").upper()
    ec = (event_code or "").upper()
    has_night = night_hours > 0 or nvg_hours > 0

    activity["landings_day"]   = random.randint(2, 6) if day_hours > 0 else 0
    activity["landings_night"] = random.randint(1, 4) if has_night else 0

    if et in ("CSAR", "SAR") or ec.startswith("P22") or ec.startswith("A22"):
        activity["hoist_streams"]    = random.randint(1, 4)
        activity["hoist_recoveries"] = random.randint(1, 3)
        if has_night and random.random() < 0.4:
            activity["landings_dve_night"] = random.randint(1, 2)
        elif day_hours > 0 and random.random() < 0.3:
            activity["landings_dve_day"] = random.randint(1, 2)

    if et in ("ASU", "STW", "SOF") or ec.startswith("P21") or ec.startswith("P31") or ec.startswith("A21") or ec.startswith("A31"):
        if random.random() < 0.4:
            total_csw = random.choice([200, 300, 400, 600])
            activity["csw_rounds"] = total_csw
            if has_night and random.random() < 0.5:
                activity["csw_rounds_night"] = random.randint(100, total_csw // 2)
        if random.random() < 0.25:
            activity["rounds_fired_20mm"] = random.choice([100, 200, 300])

    if et == "AMCM" or "_AMCM" in ec or ec.startswith("P21") and "AMCM" in ec:
        if random.random() < 0.5:
            activity["amns_iterations"] = random.randint(1, 4)
            activity["amns_ntrs"]       = random.randint(0, 2)
        else:
            activity["almds_hours"] = round(random.uniform(0.5, 1.5), 1)

    return activity


def _make_times(flight_date, to_hour):
    duration = round(random.uniform(1.5, 3.0), 1)
    takeoff_dt = datetime(flight_date.year, flight_date.month, flight_date.day, to_hour, 0)
    brief_dt   = takeoff_dt - timedelta(hours=1, minutes=30)
    land_dt    = takeoff_dt + timedelta(hours=duration)
    return brief_dt, takeoff_dt, land_dt, duration


def _allot(takeoff_dt, duration):
    hour = takeoff_dt.hour
    is_night = hour >= 19 or hour < 5
    if is_night:
        night_h = round(duration, 1)
        day_h   = 0.0
        nvg_h   = round(duration * random.uniform(0.5, 1.0), 1)
    else:
        day_h   = round(duration, 1)
        night_h = 0.0
        nvg_h   = 0.0
    instr_h = round(duration * random.uniform(0.05, 0.20), 1) if random.random() < 0.25 else 0.0
    return day_h, night_h, nvg_h, instr_h


def seed_sorties(db, aircraft_list, hac_pilots, all_pilots, aircrew_list):
    flyable = [ac for ac in aircraft_list if ac.status in (AircraftStatus.FMC, AircraftStatus.PMC)]
    hacs = hac_pilots if hac_pilots else all_pilots

    sortie_count = 0
    log_count    = 0
    all_logs     = []
    start = TODAY - timedelta(weeks=6)
    day   = start

    while day < TODAY:
        if day.weekday() < 5:
            n = random.randint(2, 4)
            to_hours = sorted(random.sample(range(6, 22), n))

            for to_hour in to_hours:
                ac         = random.choice(flyable)
                event_code = random.choice(_HIST_POOL)
                event_type = _EVENT_TYPE_MAP.get(event_code, "PROFICIENCY") if event_code else (
                    "FCF" if random.random() < 0.15 else "PROFICIENCY"
                )

                brief_dt, takeoff_dt, land_dt, dur = _make_times(day, to_hour)
                day_h, night_h, nvg_h, instr_h     = _allot(takeoff_dt, dur)
                activity = _generate_activity(event_type, event_code, day_h, night_h, nvg_h)

                # instrument_hours_simulated: LIVE with actual instrument time gets ~0 (real IMC);
                # a small fraction is a safety-pilot sim pass — approximate as 0 in seed.
                instr_sim_h = 0.0

                sortie = Sortie(
                    event_type=event_type,
                    event_code=event_code,
                    aircraft_id=ac.id,
                    brief_time=brief_dt,
                    takeoff_time=takeoff_dt,
                    land_time=land_dt,
                    duration_hours=dur,
                    landings_shipboard_day=0,
                    landings_shipboard_night=0,
                    departure_location="KNKX",
                    arrival_location="KNKX",
                    is_complete=True,
                    flight_mode=FlightMode.LIVE,
                    notes=random.choice(_NOTES),
                    **activity,
                )
                db.add(sortie)
                db.flush()

                hac    = random.choice(hacs)
                others = [p for p in all_pilots if p.id != hac.id]
                p2     = random.choice(others)
                p2_pos = CrewPosition.H2P_U if p2.rank == "LTJG" else CrewPosition.H2P

                is_aircrew_event = event_type in ("CSAR", "SOF", "AMCM", "ASU")
                p2_syl = None  # gradecard seeding will credit syllabus events

                logs = [
                    FlightLog(sortie_id=sortie.id, person_id=hac.id,
                              crew_position=CrewPosition.HAC, hours_logged=dur),
                    FlightLog(sortie_id=sortie.id, person_id=p2.id,
                              crew_position=p2_pos, hours_logged=dur,
                              syllabus_event_completed=p2_syl),
                ]

                n_crew = random.randint(0, 2)
                for crewman in random.sample(aircrew_list, min(n_crew, len(aircrew_list))):
                    pos = (CrewPosition.CREW_CHIEF if crewman.rank == "AWS1"
                           else random.choice([CrewPosition.AIRCREW, CrewPosition.AWS]))
                    logs.append(FlightLog(sortie_id=sortie.id, person_id=crewman.id,
                                         crew_position=pos, hours_logged=dur))

                for lg in logs:
                    db.add(lg)
                db.flush()

                all_logs.append((sortie, logs, instr_h))
                log_count    += len(logs)
                sortie_count += 1

        day += timedelta(days=1)

    return sortie_count, log_count, all_logs

# Instrument Approaches  (seeded for historical sorties with instrument time)
# ═══════════════════════════════════════════════════════════════════════════════

_APPROACH_TYPE_POOL = [
    ApproachType.ILS, ApproachType.GPS, ApproachType.RNAV,
    ApproachType.TACAN, ApproachType.VOR,
]

_APPROACH_AIRPORTS = ["KNKX", "KNZY", "KSEE", "KMYF", "KCRQ"]


def seed_instrument_approaches(db, all_logs):
    """
    Seed InstrumentApproach rows for completed historical sorties that have
    instrument_hours > 0.  1–3 approaches per eligible flight log (pilots only).
    All are ACTUAL (LIVE sorties, zero simulated in the historical seed).
    """
    count = 0
    pilot_positions = {CrewPosition.HAC, CrewPosition.H2P, CrewPosition.H2P_U}

    for sortie, logs, instr_h in all_logs:
        if instr_h <= 0:
            continue
        n_approaches = random.randint(1, 3)
        for fl in logs:
            if fl.crew_position not in pilot_positions:
                continue
            for _ in range(n_approaches):
                db.add(InstrumentApproach(
                    flight_log_id=fl.id,
                    sortie_id=sortie.id,
                    approach_type=random.choice(_APPROACH_TYPE_POOL),
                    actual_or_simulated=ApproachConditions.ACTUAL,
                    airport_icao=random.choice(_APPROACH_AIRPORTS),
                    runway=None,
                    remarks=None,
                    logged_at=sortie.land_time or sortie.takeoff_time,
                ))
                count += 1

    db.flush()
    return count

# Task Credits
# ═══════════════════════════════════════════════════════════════════════════════

def seed_task_credits(db, all_logs):
    count = 0
    for sortie, logs, _instr_h in all_logs:
        task_pool = _EVENT_TASK_MAP.get(sortie.event_type or "", ["MOB 203"])
        for fl in logs:
            if random.random() > 0.30:
                continue
            n_credits   = random.randint(1, min(3, len(task_pool)))
            chosen_codes = random.sample(task_pool, n_credits)
            for code in chosen_codes:
                db.add(SortieTaskCredit(sortie_id=sortie.id, flight_log_id=fl.id,
                                        task_code=code, grade=random.choice(_GRADE_POOL)))
                count += 1
    db.flush()
    return count

# Safety Reports  (unchanged)
# ═══════════════════════════════════════════════════════════════════════════════

def seed_safety_reports(db, all_logs, all_pilots):
    count = 0
    if not all_logs or not all_pilots:
        return count

    s1, logs1, _ = random.choice(all_logs)
    hac1 = next((fl for fl in logs1 if fl.crew_position == CrewPosition.HAC), logs1[0])
    db.add(SafetyReport(
        sortie_id=s1.id, reported_by_person_id=hac1.person_id,
        severity="HAZARD", category="FOD",
        description="Post-recovery FOD sweep identified two loose screws (approx 3/8\") on the flight deck adjacent to the port sponson. Screws appear to have backed out from the deck grating panel; lock washers found nearby. No aircraft or personnel damage.",
        actions_taken="Screws and washers removed and secured. Maintenance notified; deck grating inspected and all remaining fasteners torque-checked. Crew reminded of post-recovery FOD walk procedures.",
        status="CLOSED", closed_at=utc_now() - timedelta(days=random.randint(1, 5)),
    ))
    count += 1

    s2, logs2, _ = random.choice(all_logs)
    while s2.id == s1.id:
        s2, logs2, _ = random.choice(all_logs)
    hac2 = next((fl for fl in logs2 if fl.crew_position == CrewPosition.HAC), logs2[0])
    db.add(SafetyReport(
        sortie_id=s2.id, reported_by_person_id=hac2.person_id,
        severity="INCIDENT", category="BIRDSTRIKE",
        description="Bird strike on transit at approximately 800 ft MSL, 120 KIAS. Single medium-sized bird (likely seagull) impacted the port chin bubble; no observable aircraft damage at strike. Returned to field for post-flight inspection.",
        actions_taken="Post-flight inspection completed by QAR; no structural damage noted. Chin bubble exterior cleaned; feather debris removed. Wildlife hazard report filed with base ops. Aircraft returned to FMC status following inspection.",
        status="UNDER_REVIEW",
    ))
    count += 1

    db.flush()
    return count

# Future Scheduled Sorties (9 planned, using SWTP event codes)
# ═══════════════════════════════════════════════════════════════════════════════

def seed_future_sorties(db, aircraft_list, hac_pilots, all_pilots, aircrew_list):
    """Planned sorties for today through the next 6 days."""
    from app.models.models import Currency

    fmc    = [ac for ac in aircraft_list if ac.status == AircraftStatus.FMC]
    pmc    = [ac for ac in aircraft_list if ac.status == AircraftStatus.PMC]
    nmcm   = next((ac for ac in aircraft_list if ac.status == AircraftStatus.NMCM), fmc[0])
    pmc_ac = pmc[0] if pmc else fmc[0]

    day0 = TODAY
    day1 = TODAY + timedelta(days=1)
    day2 = TODAY + timedelta(days=2)
    day3 = TODAY + timedelta(days=3)
    day4 = TODAY + timedelta(days=4)
    day5 = TODAY + timedelta(days=5)
    day6 = TODAY + timedelta(days=6)

    nvg_hac = None
    for pilot in hac_pilots:
        cur = db.query(Currency).filter(
            Currency.person_id == pilot.id,
            Currency.currency_code == "NIGHT_NVD",
            Currency.expires_date >= day2,
            Currency.expires_date <= day2 + timedelta(days=5),
        ).first()
        if cur:
            nvg_hac = pilot
            break
    if nvg_hac is None:
        nvg_hac = hac_pilots[0] if hac_pilots else all_pilots[0]

    ltjg_pilots   = [p for p in all_pilots if p.rank == "LTJG"]
    lt_lc_pilots  = [p for p in all_pilots if p.rank in ("LT", "LCDR")]
    aws1_crew     = [c for c in aircrew_list if c.rank == "AWS1"]

    def _hac(n=0):   return hac_pilots[n % len(hac_pilots)]
    def _h2p(ex, n=0):
        pool = [p for p in lt_lc_pilots if p.id not in ex] or lt_lc_pilots or all_pilots
        return pool[n % len(pool)]
    def _h2p_u(n=0): pool = ltjg_pilots or all_pilots; return pool[n % len(pool)]
    def _cc(n=0):    pool = aws1_crew or aircrew_list; return pool[n % len(pool)]

    sortie_count = 0
    log_count    = 0

    def _add(flight_date, to_hour, event_type, event_code, ac,
             day_h, night_h, nvg_h, instr_h, dur, notes, crew,
             flight_mode=FlightMode.LIVE):
        nonlocal sortie_count, log_count
        to_dt = datetime(flight_date.year, flight_date.month, flight_date.day, to_hour, 0)
        s = Sortie(
            event_type=event_type, event_code=event_code, aircraft_id=ac.id,
            brief_time=to_dt - timedelta(hours=1, minutes=30), takeoff_time=to_dt,
            land_time=to_dt + timedelta(hours=dur), duration_hours=dur,
            is_complete=False, flight_mode=flight_mode, notes=notes,
            mission_summary=notes,
            ops_status=SortieOpsStatus.PLANNED,
        )
        db.add(s)
        db.flush()
        for person, position in crew:
            db.add(FlightLog(sortie_id=s.id, person_id=person.id,
                             crew_position=position, hours_logged=dur))
            log_count += 1
        sortie_count += 1
        return s

    h0 = _hac(0); p0 = _h2p({h0.id}, 0); c0 = _cc(0)
    _add(day0, 9,  "PROFICIENCY", None, fmc[0], 1.5, 0.0, 0.0, 0.0, 1.5,
         "Morning proficiency — day VFR pattern and deck-landing reps.",
         [(h0, CrewPosition.HAC), (p0, CrewPosition.H2P), (c0, CrewPosition.CREW_CHIEF)])

    h0b = _hac(1); u0b = _h2p_u(1)
    _add(day0, 14, "INTRO", "P201", fmc[1], 2.0, 0.0, 0.0, 0.0, 2.0,
         "P201 intro syllabus event — systems and weapons brief to follow.",
         [(h0b, CrewPosition.HAC), (u0b, CrewPosition.H2P_U)])

    h1 = _hac(0); u1 = _h2p_u(0); c1 = _cc(0)
    _add(day1, 9,  "INTRO", "P200", fmc[0], 2.0, 0.0, 0.0, 0.0, 2.0,
         "P200 PGM/SACT intro — systems check and weapons familiarization.",
         [(h1, CrewPosition.HAC), (u1, CrewPosition.H2P_U), (c1, CrewPosition.CREW_CHIEF)])

    h2 = _hac(1)
    _add(day1, 13, "PROFICIENCY", None, fmc[1], 1.5, 0.0, 0.0, 0.0, 1.5,
         "Proficiency currency flight — remaining crew TBD.",
         [(h2, CrewPosition.HAC)])

    p3 = _h2p({nvg_hac.id}, 0); ac3 = aircrew_list[0] if aircrew_list else None
    crew3 = [(nvg_hac, CrewPosition.HAC), (p3, CrewPosition.H2P)]
    if ac3: crew3.append((ac3, CrewPosition.AWS))
    _add(day2, 20, "ASU", "P211", fmc[2 % len(fmc)], 0.0, 2.0, 2.0, 0.0, 2.0,
         "P211 PGM and Strafe NVG night — low-level transit and FLIR targeting.", crew3)

    h4 = _hac(2 % len(hac_pilots)); p4 = _h2p({h4.id}, 1); c4 = _cc(1 % len(aws1_crew or [None]))
    _add(day3, 9,  "CSAR", "P225", fmc[3 % len(fmc)], 2.5, 0.0, 0.0, 0.0, 2.5,
         "P225 Deliberate CSAR Overland — datum runs and hoist survivor drills.",
         [(h4, CrewPosition.HAC), (p4, CrewPosition.H2P), (c4, CrewPosition.CREW_CHIEF)])

    h4s = _hac(3 % len(hac_pilots)); u4s = _h2p_u(0)
    _add(day3, 15, "INTRO", "P200", fmc[4 % len(fmc)], 2.0, 0.0, 0.0, 0.0, 2.0,
         "P200 PGM/SACT TOFT sim — sim-eligible currencies only; aircraft hours not incremented.",
         [(h4s, CrewPosition.HAC), (u4s, CrewPosition.H2P_U)],
         flight_mode=FlightMode.SIM_TOFT)

    h5 = _hac(3 % len(hac_pilots)); p5 = _h2p({h5.id}, 2)
    _add(day4, 10, "PROFICIENCY", None, fmc[4 % len(fmc)], 2.0, 0.0, 0.0, 0.0, 2.0,
         "Proficiency currency — hoist and deck-landing ops.",
         [(h5, CrewPosition.HAC), (p5, CrewPosition.H2P)])

    h6 = _hac(4 % len(hac_pilots)); p6 = _h2p({h6.id}, 3)
    _add(day4, 14, "FCF", None, nmcm, 1.5, 0.0, 0.0, 0.0, 1.5,
         "FCF tentatively scheduled; contingent on maintenance completion.",
         [(h6, CrewPosition.HAC), (p6, CrewPosition.H2P)])

    h7 = _hac(0); u7 = _h2p_u(1 % len(ltjg_pilots or [None])); c7 = _cc(2 % len(aws1_crew or [None]))
    _add(day5, 8,  "INTRO", "P201", fmc[0], 2.0, 0.0, 0.0, 0.0, 2.0,
         "P201 Night Routes and Landings — navigation and radio procedures.",
         [(h7, CrewPosition.HAC), (u7, CrewPosition.H2P_U), (c7, CrewPosition.CREW_CHIEF)])

    h8 = _hac(1 % len(hac_pilots)); p8 = _h2p({h8.id}, 4)
    ac8 = aircrew_list[1] if len(aircrew_list) > 1 else aircrew_list[0]
    _add(day5, 13, "ASU", "P214", fmc[1], 2.5, 0.0, 0.0, 0.0, 2.5,
         "P214 Restricted Waters Transit — FLIR targeting and deconfliction exercise.",
         [(h8, CrewPosition.HAC), (p8, CrewPosition.H2P), (ac8, CrewPosition.AIRCREW)])

    h9 = _hac(2 % len(hac_pilots)); u9 = _h2p_u(2 % len(ltjg_pilots or [None]))
    ac9 = aircrew_list[2] if len(aircrew_list) > 2 else aircrew_list[0]
    _add(day6, 9,  "CSAR", "P226", pmc_ac, 2.0, 0.0, 0.0, 0.0, 2.0,
         "P226 Overwater CSAR Simulator — FLIR capability degraded on PMC aircraft.",
         [(h9, CrewPosition.HAC), (u9, CrewPosition.H2P_U), (ac9, CrewPosition.AWS)])

    db.flush()
    return sortie_count, log_count
