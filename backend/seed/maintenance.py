"""Discrepancy seeding."""
import random
from datetime import timedelta

from app.core.time import utc_now
from app.models.models import (
    Discrepancy, AircraftStatus, DiscrepancySeverity, DiscrepancyWorkStatus,
)

# ═══════════════════════════════════════════════════════════════════════════════
# Discrepancies  (unchanged)
# ═══════════════════════════════════════════════════════════════════════════════

_NMCM = [
    ("Tail rotor gearbox chip light illuminated; gearbox removed for inspection IAW MRC.",
     "Tail Rotor Gearbox", DiscrepancyWorkStatus.IN_WORK),
    ("Main rotor blade #3 tracking out of limits; blade R&R in progress.",
     "Main Rotor", DiscrepancyWorkStatus.IN_WORK),
    ("AFCS channel 2 inoperative; AFCS computer replacement in work.",
     "AFCS", DiscrepancyWorkStatus.IN_WORK),
    ("Hydraulic system #1 pressure fluctuation; servo valve R&R required.",
     "Hydraulic System 1", DiscrepancyWorkStatus.IN_WORK),
    ("FLIR turret drive motor failure; awaiting depot-level repair authorization.",
     "FLIR", DiscrepancyWorkStatus.IN_WORK),
]
_NMCS = [
    ("Main gearbox input quill shaft awaiting supply delivery (NSN 1650-01-234-5678); EDD unknown.",
     "MGB Input Quill", DiscrepancyWorkStatus.AWP),
    ("Engine #1 compressor blade kit on back-order; aircraft grounded pending receipt.",
     "Engine 1", DiscrepancyWorkStatus.AWP),
]
_PMC = [
    ("FLIR cooldown time excessive (>12 min); aircraft flyable, FLIR capability degraded.",
     "FLIR", DiscrepancyWorkStatus.IN_WORK),
    ("Radar altimeter intermittent above 500 ft; crew to use barometric alt for low-level ops.",
     "Radar Altimeter", DiscrepancyWorkStatus.IN_WORK),
]
_MINOR = [
    ("Interior cabin lighting panel cracked; non-mission-critical, work order submitted.",
     "Cabin Lighting", DiscrepancyWorkStatus.OPEN),
    ("Co-pilot NVG mount wiring chafed; taped and secured, depot repair deferred.",
     "NVG Mount", DiscrepancyWorkStatus.OPEN),
]
# Historical closed discrepancies for FMC aircraft (mix of MAJOR + MINOR)
_CLOSED = [
    ("TACAN intermittent lock loss above FL080; suspected antenna connector. Replaced connector assembly.",
     "TACAN", DiscrepancySeverity.MAJOR,
     "Replaced coax connector P/N 5985-01-137-4321; tested good across full range. Aircraft returned to FMC."),
    ("ICS push-to-talk switch inoperative at HAC station; replaced switch assembly.",
     "ICS", DiscrepancySeverity.MINOR,
     "Replaced PTT switch assembly; comms check completed with all stations. No further discrepancies noted."),
    ("Engine bay drain valve stuck open; valve cleaned and cycled per MRC.",
     "Engine 2", DiscrepancySeverity.MINOR,
     "Cleaned valve seat and cycled three times; valve seats properly. Engine bay inspected — no FOD or residue."),
    ("APU bleed air leak at B-nut; B-nut retorqued and leak check completed.",
     "APU", DiscrepancySeverity.MAJOR,
     "Retorqued B-nut to 65 in-lb per spec; leak check with soap solution — no leaks detected."),
    ("Tail rotor blade erosion strip delaminating at tip; strip replaced IAW depot CMM.",
     "Tail Rotor", DiscrepancySeverity.MINOR,
     "Replaced erosion strip per CMM 67-10-41; blade re-tracked and balanced. In limits."),
]


def seed_discrepancies(db, aircraft_list):
    """
    Open discrepancies aligned with stamped status and three intentional drift cases:
    aircraft_list[4] stamped FMC + open MAJOR → computed PMC;
    aircraft_list[5] stamped FMC + open DOWNING IN_WORK → computed NMCM;
    aircraft_list[7] stamped FMC + open DOWNING AWP → computed NMCS.
    """
    drift_pmc_ac = aircraft_list[4]
    drift_nmcm_ac = aircraft_list[5]
    drift_nmcs_ac = aircraft_list[7]
    maf_counter  = 1
    count_by_sev = {"MINOR": 0, "MAJOR": 0, "DOWNING": 0}

    def _maf():
        nonlocal maf_counter
        m = f"M-2026-{maf_counter:04d}"
        maf_counter += 1
        return m

    def _add(ac, desc, sys, sev, ws, is_open=True, corrective=None):
        days_ago = random.randint(1, 21) if is_open else random.randint(30, 90)
        opened   = utc_now() - timedelta(days=days_ago)
        closed   = (utc_now() - timedelta(days=random.randint(1, days_ago - 1))
                    if not is_open else None)
        db.add(Discrepancy(
            aircraft_id=ac.id,
            description=desc,
            severity=sev,
            work_status=ws,
            maf_number=_maf(),
            system_affected=sys,
            corrective_action=corrective,
            opened_date=opened,
            closed_date=closed,
            is_open=is_open,
        ))
        count_by_sev[sev.value] += 1

    for ac in aircraft_list:
        if ac == drift_pmc_ac:
            desc, sys, ws = _PMC[0]
            _add(ac, desc, sys, DiscrepancySeverity.MAJOR, ws)
        elif ac == drift_nmcm_ac:
            desc, sys, ws = _NMCM[0]
            _add(ac, desc, sys, DiscrepancySeverity.DOWNING, ws)
        elif ac == drift_nmcs_ac:
            desc, sys, ws = _NMCS[0]
            _add(ac, desc, sys, DiscrepancySeverity.DOWNING, ws)
        elif ac.status == AircraftStatus.NMCM:
            desc, sys, ws = random.choice(_NMCM)
            _add(ac, desc, sys, DiscrepancySeverity.DOWNING, ws)
        elif ac.status == AircraftStatus.PMC:
            desc, sys, ws = random.choice(_PMC)
            _add(ac, desc, sys, DiscrepancySeverity.MAJOR, ws)

    # Historical closed discrepancies spread across all aircraft
    closed_per_ac = 2
    for ac in aircraft_list:
        chosen = random.sample(_CLOSED, min(closed_per_ac, len(_CLOSED)))
        for desc, sys, sev, corrective in chosen:
            _add(ac, desc, sys, sev, DiscrepancyWorkStatus.CLOSED,
                 is_open=False, corrective=corrective)

    db.flush()
    total = sum(count_by_sev.values())
    return total, count_by_sev
