"""
Populates the database with realistic HSC squadron demo data.
Run from the backend/ directory:  python seed.py

Batch 3b: replaced placeholder syllabus events (FAM-101 etc.) with real SWTP
event codes from COMHELSEACOMBATWING 3502.8 / 3502.8 IC1. Descriptions are
paraphrased — not verbatim from the source document.

Legacy code mapping (old placeholders → new SWTP codes):
  FAM-101 / FAM-102 / FAM-103  → P200 / P201  (Pilot INTRO L2)
  TAC-201  (Tactical Intro)     → P214          (RWT, ASU L2)
  TAC-202  (Tactical Day)       → P211          (PGM & Strafe, ASU L2)
  TAC-203  (Tactical Night)     → P314          (RWT, ASU L3)
  SAR-301  (SAR Day)            → P225          (Deliberate CSAR Overland)
  SAR-302  (SAR Night)          → P226          (Overwater CSAR Simulator)
  OL-401   (Overland Intro)     → P234          (Overland SOF Support)

AMCM code-collision note: where PILOT_AMCM shares an event number with
PILOT_CORE (e.g. both have P211, P291), the AMCM version uses a _AMCM suffix
on both SyllabusEvent.code and .event_code (e.g. "P211_AMCM").
"""
import random
import sys
import os
from datetime import date, datetime, timedelta

random.seed(42)

sys.path.insert(0, os.path.dirname(__file__))

from passlib.hash import bcrypt as bc
from app.database import SessionLocal
from app.models.models import (
    Person, Aircraft, Qualification, Currency, SyllabusEvent,
    GradecardLineItem, Gradecard, GradecardLineItemResult,
    Sortie, FlightLog, Discrepancy, CbrTaskOption, SortieTaskCredit, SafetyReport,
    CurrencyType, CurrencyApplicability,
    InspectionType, AircraftInspection,
    SortieLeg, InstrumentApproach,
    Role, CrewPosition, AircraftStatus, DiscrepancySeverity, DiscrepancyWorkStatus,
    FlightMode, CapabilityArea, TaskGrade, CrewScope,
    SyllabusLevel, SyllabusStage, SyllabusTrack, EventVenue,
    GradingScheme, GradecardSection, LineItemRole,
    GradecardStatus, CompletionStatus, FourTierScore,
    CurrencyAudience, ApproachType, ApproachConditions,
)

DEMO_PW = bc.hash("demo1234")
TODAY = date.today()

GCS = GradecardSection
LIR = LineItemRole
GS  = GradingScheme
SL  = SyllabusLevel
SS  = SyllabusStage
ST  = SyllabusTrack
EV  = EventVenue


# ═══════════════════════════════════════════════════════════════════════════════
# SWTP Event Catalog
# Columns: (code, event_code, name, track, level, stage, series,
#            venue, time_h, min_inst, grading_scheme, is_stan_eval)
# ═══════════════════════════════════════════════════════════════════════════════

_SWTP_EVENTS = [
    # ── PILOT_CORE L2 INTRO (series 200) ──────────────────────────────────────
    ("L200",  "L200",  "Basic Mission Planning",          ST.PILOT_CORE, SL.L2, SS.INTRO, 200, EV.LAB,      None, 3, GS.COMPLETION, False),
    ("L201",  "L201",  "Basic Briefing and Debriefing",   ST.PILOT_CORE, SL.L2, SS.INTRO, 200, EV.LAB,      None, 3, GS.COMPLETION, False),
    ("L202",  "L202",  "Threat Study",                    ST.PILOT_CORE, SL.L2, SS.INTRO, 200, EV.LAB,      None, 5, GS.COMPLETION, False),
    ("L203",  "L203",  "Event 0",                         ST.PILOT_CORE, SL.L2, SS.INTRO, 200, EV.LAB,      None, 5, GS.COMPLETION, False),
    ("P200",  "P200",  "PGM/SACT",                        ST.PILOT_CORE, SL.L2, SS.INTRO, 200, EV.TOFT,     2.0,  4, GS.COMPLETION, False),
    ("P201",  "P201",  "Night Routes and Landings",        ST.PILOT_CORE, SL.L2, SS.INTRO, 200, EV.AIRCRAFT, 2.0,  3, GS.COMPLETION, False),
    # ── PILOT_CORE L2 ASU (series 210) ────────────────────────────────────────
    ("P211",  "P211",  "PGM and Strafe Employment",        ST.PILOT_CORE, SL.L2, SS.ASU,   210, EV.TOFT,     2.0,  2, GS.COMPLETION, False),
    ("P212",  "P212",  "Aerial Gunnery",                   ST.PILOT_CORE, SL.L2, SS.ASU,   210, EV.AIRCRAFT, 2.0,  3, GS.COMPLETION, False),
    ("P214",  "P214",  "Restricted Waters Transit",        ST.PILOT_CORE, SL.L2, SS.ASU,   210, EV.AIRCRAFT, 2.0,  2, GS.COMPLETION, False),
    ("P215",  "P215",  "Armed Reconnaissance",             ST.PILOT_CORE, SL.L2, SS.ASU,   210, EV.AIRCRAFT, 2.0,  2, GS.COMPLETION, False),
    # ── PILOT_CORE L2 CSAR (series 220) ───────────────────────────────────────
    ("P221",  "P221",  "Immediate CSAR Overland Escorted", ST.PILOT_CORE, SL.L2, SS.CSAR,  220, EV.TOFT,     2.0,  2, GS.COMPLETION, False),
    ("P223",  "P223",  "Overwater CSAR Escorted",          ST.PILOT_CORE, SL.L2, SS.CSAR,  220, EV.TOFT,     2.0,  2, GS.COMPLETION, False),
    ("P225",  "P225",  "Deliberate CSAR Overland Unescorted", ST.PILOT_CORE, SL.L2, SS.CSAR, 220, EV.AIRCRAFT, 2.0, 3, GS.COMPLETION, False),
    ("P226",  "P226",  "Overwater CSAR Simulator Unescorted", ST.PILOT_CORE, SL.L2, SS.CSAR, 220, EV.TOFT,   2.0,  2, GS.COMPLETION, False),
    # ── PILOT_CORE L2 SOF_LOG (series 230) ────────────────────────────────────
    ("P231",  "P231",  "Combat Logistics",                 ST.PILOT_CORE, SL.L2, SS.SOF_LOG, 230, EV.TOFT,   2.0,  2, GS.COMPLETION, False),
    ("P232",  "P232",  "Overwater SOF Support",            ST.PILOT_CORE, SL.L2, SS.SOF_LOG, 230, EV.TOFT,   2.0,  2, GS.COMPLETION, False),
    ("P233",  "P233",  "HVBSS",                            ST.PILOT_CORE, SL.L2, SS.SOF_LOG, 230, EV.AIRCRAFT,2.0,  3, GS.COMPLETION, False),
    ("P234",  "P234",  "Overland SOF Support",             ST.PILOT_CORE, SL.L2, SS.SOF_LOG, 230, EV.AIRCRAFT,2.0,  2, GS.COMPLETION, False),
    # ── PILOT_CORE L2 STAN_EVAL (series 290) ──────────────────────────────────
    ("P290",  "P290",  "Oral Board",                       ST.PILOT_CORE, SL.L2, SS.STAN_EVAL, 290, EV.BOARD,   None, 5, GS.FOUR_TIER,  True),
    ("P291",  "P291",  "STAN/EVAL",                        ST.PILOT_CORE, SL.L2, SS.STAN_EVAL, 290, EV.AIRCRAFT, 2.0,  5, GS.FOUR_TIER,  True),
    ("L290",  "L290",  "Instructor Development",           ST.PILOT_CORE, SL.L2, SS.STAN_EVAL, 290, EV.LAB,      None, 5, GS.COMPLETION, False),
    ("P292",  "P292",  "Basic Instructional Techniques",   ST.PILOT_CORE, SL.L2, SS.STAN_EVAL, 290, EV.AIRCRAFT, 2.0,  4, GS.COMPLETION, False),
    ("P293",  "P293",  "Scenario Instructional Techniques",ST.PILOT_CORE, SL.L2, SS.STAN_EVAL, 290, EV.TOFT,     2.0,  4, GS.COMPLETION, False),
    # ── PILOT_CORE L3 INTRO (series 300) ──────────────────────────────────────
    ("L300",  "L300",  "Advanced Mission Planning",        ST.PILOT_CORE, SL.L3, SS.INTRO, 300, EV.LAB,      None, 4, GS.COMPLETION, False),
    ("L301",  "L301",  "Advanced Briefing and Debriefing", ST.PILOT_CORE, SL.L3, SS.INTRO, 300, EV.LAB,      None, 4, GS.COMPLETION, False),
    ("P300",  "P300",  "PGM/SACT",                         ST.PILOT_CORE, SL.L3, SS.INTRO, 300, EV.AIRCRAFT, 2.0,  4, GS.COMPLETION, False),
    # ── PILOT_CORE L3 ASU (series 310) ────────────────────────────────────────
    ("P314",  "P314",  "Restricted Waters Transit",        ST.PILOT_CORE, SL.L3, SS.ASU,   310, EV.AIRCRAFT, 2.0,  3, GS.COMPLETION, False),
    ("P315",  "P315",  "SCAR",                             ST.PILOT_CORE, SL.L3, SS.ASU,   310, EV.AIRCRAFT, 2.0,  3, GS.COMPLETION, False),
    # ── PILOT_CORE L3 CSAR (series 320) ───────────────────────────────────────
    ("P323",  "P323",  "Overwater CSAR Escorted",          ST.PILOT_CORE, SL.L3, SS.CSAR,  320, EV.AIRCRAFT, 2.0,  3, GS.COMPLETION, False),
    ("P325",  "P325",  "Deliberate CSAR Overland Unescorted", ST.PILOT_CORE, SL.L3, SS.CSAR, 320, EV.AIRCRAFT, 2.0, 3, GS.COMPLETION, False),
    ("P326",  "P326",  "Overwater CSAR Simulator Unescorted", ST.PILOT_CORE, SL.L3, SS.CSAR, 320, EV.TOFT,   2.0,  3, GS.COMPLETION, False),
    # ── PILOT_CORE L3 SOF_LOG (series 330) ────────────────────────────────────
    ("P331",  "P331",  "Combat Logistics",                 ST.PILOT_CORE, SL.L3, SS.SOF_LOG, 330, EV.AIRCRAFT,2.0,  3, GS.COMPLETION, False),
    ("P333",  "P333",  "HVBSS",                            ST.PILOT_CORE, SL.L3, SS.SOF_LOG, 330, EV.AIRCRAFT,2.0,  3, GS.COMPLETION, False),
    ("P334",  "P334",  "Overland SOF Support",             ST.PILOT_CORE, SL.L3, SS.SOF_LOG, 330, EV.AIRCRAFT,2.0,  3, GS.COMPLETION, False),
    # ── PILOT_CORE L3 STAN_EVAL (series 390) ──────────────────────────────────
    ("P390",  "P390",  "Oral Board",                       ST.PILOT_CORE, SL.L3, SS.STAN_EVAL, 390, EV.BOARD,   None, 5, GS.FOUR_TIER,  True),
    ("P391",  "P391",  "STAN/EVAL",                        ST.PILOT_CORE, SL.L3, SS.STAN_EVAL, 390, EV.AIRCRAFT, 2.0,  5, GS.FOUR_TIER,  True),
    ("L390",  "L390",  "Instructor Development",           ST.PILOT_CORE, SL.L3, SS.STAN_EVAL, 390, EV.LAB,      None, 5, GS.COMPLETION, False),
    ("P392",  "P392",  "Instructional Techniques",         ST.PILOT_CORE, SL.L3, SS.STAN_EVAL, 390, EV.AIRCRAFT, 2.0,  4, GS.COMPLETION, False),
    # ── PILOT_AMCM L2 AMCM_INTRO ──────────────────────────────────────────────
    ("L203_AMCM", "L203_AMCM", "AMCM Mission Planning",          ST.PILOT_AMCM, SL.L2, SS.AMCM_INTRO, None, EV.LAB,  None, None, GS.COMPLETION, False),
    ("L204_AMCM", "L204_AMCM", "AMCM Mission Planning Practical",ST.PILOT_AMCM, SL.L2, SS.AMCM_INTRO, None, EV.LAB,  None, None, GS.COMPLETION, False),
    # ── PILOT_AMCM L2 ALMDS (series 210) ──────────────────────────────────────
    ("P210",      "P210",      "ALMDS Search and Reacquisition",  ST.PILOT_AMCM, SL.L2, SS.ALMDS,      210,  EV.TOFT, 2.0,  None, GS.COMPLETION, False),
    ("P211_AMCM", "P211_AMCM", "ALMDS Day Search and Reacquisition", ST.PILOT_AMCM, SL.L2, SS.ALMDS,   210,  EV.TOFT, 1.5,  None, GS.COMPLETION, False),
    ("P212_AMCM", "P212_AMCM", "ALMDS Night Search and Reacquisition",ST.PILOT_AMCM, SL.L2, SS.ALMDS,  210,  EV.TOFT, 1.5,  None, GS.COMPLETION, False),
    # ── PILOT_AMCM L2 AMNS (series 220) ───────────────────────────────────────
    ("P220",      "P220",      "AMNS Mission",                    ST.PILOT_AMCM, SL.L2, SS.AMNS,       220,  EV.TOFT, 1.5,  None, GS.COMPLETION, False),
    ("P221_AMCM", "P221_AMCM", "AMNS Day",                        ST.PILOT_AMCM, SL.L2, SS.AMNS,       220,  EV.TOFT, 1.5,  None, GS.COMPLETION, False),
    ("P222_AMCM", "P222_AMCM", "AMNS Night",                      ST.PILOT_AMCM, SL.L2, SS.AMNS,       220,  EV.TOFT, 1.5,  None, GS.COMPLETION, False),
    # ── PILOT_AMCM L2 STAN_EVAL (series 290) ──────────────────────────────────
    ("P291_AMCM", "P291_AMCM", "STAN/EVAL ALMDS or AMNS",         ST.PILOT_AMCM, SL.L2, SS.STAN_EVAL,  290,  EV.AIRCRAFT, 2.0, None, GS.FOUR_TIER,  True),
    ("L290_AMCM", "L290_AMCM", "Instructor Under Training Lab",   ST.PILOT_AMCM, SL.L2, SS.STAN_EVAL,  290,  EV.LAB,      None, None, GS.COMPLETION, False),
    ("P292_AMCM", "P292_AMCM", "Simulator Operations",            ST.PILOT_AMCM, SL.L2, SS.STAN_EVAL,  290,  EV.TOFT,     2.0,  None, GS.COMPLETION, False),
    # ── AIRCREW_CORE L2 INTRO/LAB (series 200) ────────────────────────────────
    ("L200_AW",  "L200_AW",  "Crew Served Weapons",              ST.AIRCREW_CORE, SL.L2, SS.INTRO, 200, EV.LAB, None, None, GS.COMPLETION, False),
    ("L201_AW",  "L201_AW",  "Individual Service Weapons",       ST.AIRCREW_CORE, SL.L2, SS.INTRO, 200, EV.LAB, None, None, GS.COMPLETION, False),
    ("L202_AW",  "L202_AW",  "Electronic Kneeboard",             ST.AIRCREW_CORE, SL.L2, SS.INTRO, 200, EV.LAB, None, None, GS.COMPLETION, False),
    ("L203_AW",  "L203_AW",  "Rescue Element Procedures",        ST.AIRCREW_CORE, SL.L2, SS.INTRO, 200, EV.LAB, None, None, GS.COMPLETION, False),
    # ── AIRCREW_CORE L2 ASU (series 210) ──────────────────────────────────────
    ("A212",  "A212",  "Weapons Employment M240D",               ST.AIRCREW_CORE, SL.L2, SS.ASU,    210, EV.TOFT,     1.0, None, GS.COMPLETION, False),
    ("A213",  "A213",  "Weapons Employment GAU21",               ST.AIRCREW_CORE, SL.L2, SS.ASU,    210, EV.TOFT,     1.0, None, GS.COMPLETION, False),
    # ── AIRCREW_CORE L2 CSAR (series 220) ─────────────────────────────────────
    ("A221",  "A221",  "Overland Hoist Operator",                ST.AIRCREW_CORE, SL.L2, SS.CSAR,   220, EV.TOFT,     2.0, None, GS.COMPLETION, False),
    ("A222",  "A222",  "Overland CSAR Rescue Element",           ST.AIRCREW_CORE, SL.L2, SS.CSAR,   220, EV.TOFT,     2.0, None, GS.COMPLETION, False),
    ("A223",  "A223",  "Overwater Hoist Operator",               ST.AIRCREW_CORE, SL.L2, SS.CSAR,   220, EV.TOFT,     2.0, None, GS.COMPLETION, False),
    ("A224",  "A224",  "Overwater CSAR Swimmer",                 ST.AIRCREW_CORE, SL.L2, SS.CSAR,   220, EV.TOFT,     2.0, None, GS.COMPLETION, False),
    # ── AIRCREW_CORE L2 SOF_LOG (series 230) ──────────────────────────────────
    ("A232",  "A232",  "Overwater SOF",                          ST.AIRCREW_CORE, SL.L2, SS.SOF_LOG, 230, EV.TOFT,    2.0, None, GS.COMPLETION, False),
    ("A233",  "A233",  "HVBSS",                                  ST.AIRCREW_CORE, SL.L2, SS.SOF_LOG, 230, EV.AIRCRAFT, 2.0, None, GS.COMPLETION, False),
    ("A234",  "A234",  "Overland SOF",                           ST.AIRCREW_CORE, SL.L2, SS.SOF_LOG, 230, EV.TOFT,    2.0, None, GS.COMPLETION, False),
    # ── AIRCREW_CORE L2 STAN_EVAL (series 290) ────────────────────────────────
    ("A291",  "A291",  "STAN EVAL",                              ST.AIRCREW_CORE, SL.L2, SS.STAN_EVAL, 290, EV.AIRCRAFT, 2.0, None, GS.FOUR_TIER, True),
    # ── AIRCREW_CORE L3 ────────────────────────────────────────────────────────
    ("A301",  "A301",  "Advanced Mission Systems",               ST.AIRCREW_CORE, SL.L3, SS.INTRO,    300, EV.AIRCRAFT, 2.0, None, GS.COMPLETION, False),
    ("A314",  "A314",  "Restricted Waters Transit",              ST.AIRCREW_CORE, SL.L3, SS.ASU,      310, EV.AIRCRAFT, 2.0, None, GS.COMPLETION, False),
    ("A315",  "A315",  "SCAR Crew",                              ST.AIRCREW_CORE, SL.L3, SS.ASU,      310, EV.AIRCRAFT, 2.0, None, GS.COMPLETION, False),
    ("A323",  "A323",  "Overwater CSAR Escorted",                ST.AIRCREW_CORE, SL.L3, SS.CSAR,     320, EV.AIRCRAFT, 2.0, None, GS.COMPLETION, False),
    ("A325",  "A325",  "Deliberate CSAR Overland Unescorted",    ST.AIRCREW_CORE, SL.L3, SS.CSAR,     320, EV.AIRCRAFT, 2.0, None, GS.COMPLETION, False),
    ("A326",  "A326",  "Overwater CSAR Simulator Unescorted",    ST.AIRCREW_CORE, SL.L3, SS.CSAR,     320, EV.TOFT,     2.0, None, GS.COMPLETION, False),
    ("A331",  "A331",  "Combat Logistics",                       ST.AIRCREW_CORE, SL.L3, SS.SOF_LOG,  330, EV.AIRCRAFT, 2.0, None, GS.COMPLETION, False),
    ("A333",  "A333",  "HVBSS",                                  ST.AIRCREW_CORE, SL.L3, SS.SOF_LOG,  330, EV.AIRCRAFT, 2.0, None, GS.COMPLETION, False),
    ("A334",  "A334",  "Overland SOF Support",                   ST.AIRCREW_CORE, SL.L3, SS.SOF_LOG,  330, EV.AIRCRAFT, 2.0, None, GS.COMPLETION, False),
    ("A390",  "A390",  "Oral Board",                             ST.AIRCREW_CORE, SL.L3, SS.STAN_EVAL, 390, EV.BOARD,   None, None, GS.FOUR_TIER, True),
    ("A391",  "A391",  "STAN EVAL",                              ST.AIRCREW_CORE, SL.L3, SS.STAN_EVAL, 390, EV.AIRCRAFT, 2.0, None, GS.FOUR_TIER, True),
    ("L390_AW","L390_AW","Instructor Development",               ST.AIRCREW_CORE, SL.L3, SS.STAN_EVAL, 390, EV.LAB,     None, None, GS.COMPLETION, False),
    ("A392",  "A392",  "Instructional Techniques",               ST.AIRCREW_CORE, SL.L3, SS.STAN_EVAL, 390, EV.AIRCRAFT, 2.0, None, GS.COMPLETION, False),
    # ── AIRCREW_AMCM L2 ────────────────────────────────────────────────────────
    ("L301_AW_AMCM", "L301_AW_AMCM", "CSTRS-T Operator",        ST.AIRCREW_AMCM, SL.L2, SS.AMCM_INTRO, None, EV.LAB,    None, None, GS.COMPLETION, False),
    ("L302_AW_AMCM", "L302_AW_AMCM", "ALMDS WTT Operator",      ST.AIRCREW_AMCM, SL.L2, SS.AMCM_INTRO, None, EV.LAB,    None, None, GS.COMPLETION, False),
    ("L303_AW_AMCM", "L303_AW_AMCM", "AMNS WTT Operator",       ST.AIRCREW_AMCM, SL.L2, SS.AMCM_INTRO, None, EV.LAB,    None, None, GS.COMPLETION, False),
    ("A310",  "A310",  "ALMDS Search",                           ST.AIRCREW_AMCM, SL.L2, SS.ALMDS,      None, EV.TOFT,    2.0, None, GS.COMPLETION, False),
    ("A320",  "A320",  "AMNS Mission",                           ST.AIRCREW_AMCM, SL.L2, SS.AMNS,       None, EV.TOFT,    2.0, None, GS.COMPLETION, False),
    ("A390_AMCM","A390_AMCM","ALMDS STAN EVAL",                  ST.AIRCREW_AMCM, SL.L2, SS.STAN_EVAL,  None, EV.AIRCRAFT, 2.0, None, GS.FOUR_TIER, True),
    ("A391_AMCM","A391_AMCM","AMNS STAN EVAL",                   ST.AIRCREW_AMCM, SL.L2, SS.STAN_EVAL,  None, EV.AIRCRAFT, 2.0, None, GS.FOUR_TIER, True),
]


# ═══════════════════════════════════════════════════════════════════════════════
# Line Item Templates
# ═══════════════════════════════════════════════════════════════════════════════

# MOP text for FOUR_TIER critical items (paraphrased — not verbatim from 3502.8)
_MOPS = {
    "Mission System Set-Up": (
        "Completes system initialization but requires instructor prompting for at least one critical step, or completes steps out of the correct sequence, degrading readiness.",
        "Independently completes all mission system initialization steps in the correct sequence without prompting, within the required time window.",
    ),
    "Asset Integration": (
        "Asset integration calls are late, out of sequence, or omitted at one or more critical mission phases, degrading package coordination.",
        "Calls for asset integration at each planned decision point using correct terminology; package elements coordinate without confusion or requery.",
    ),
    "ALR": (
        "Operates within ALR limits but does not take advantage of lower-risk corridors when mission permits, or fails to apply maximum-allowed ALR when threat dictates, unnecessarily increasing force exposure.",
        "Consistently applies ALR appropriate to the threat environment; never exceeds maximum ALR; uses reduced ALR when mission permits to minimize unnecessary exposure.",
    ),
    "Package Decision Making": (
        "Makes package decisions that increase risk to force or compromise mission objectives without adequate consideration of threat, fuel state, or environmental constraints.",
        "Makes sound, timely package decisions that account for threat, fuel, and environmental factors; adapts the plan appropriately when conditions change.",
    ),
    "Asset Management": (
        "Allows package fuel or ordnance to approach minimums without prior adjustment; fails to account for asset losses or degraded states during mission execution.",
        "Proactively tracks package fuel and ordnance states; adjusts asset employment before minimums are reached; accounts for all losses and capability degradation.",
    ),
    "Weapon Preflight": (
        "Completes weapon preflight but misses one or more critical inspection steps, requiring crew prompting to identify and correct the discrepancy prior to flight.",
        "Independently completes all weapon preflight inspection items in the correct sequence; identifies and corrects any discrepancies without prompting.",
    ),
    "Safety of Flight": (
        "Maintains basic cabin safety but requires prompting on at least one safety-critical procedure, or briefly creates an unsafe condition requiring crew intervention.",
        "Proactively manages cabin safety throughout all flight phases; no unsafe conditions created; effective crew coordination and hazard communication maintained.",
    ),
    "Weapon Employment": (
        "Weapon employment remains within ROE but is below standard on targeting accuracy, trigger discipline, or engagement criteria; does not independently recognize and call out violations.",
        "Employs weapons accurately within engagement criteria; independently verifies ROE compliance before each engagement; calls ceasefire correctly and immediately when appropriate.",
    ),
    "ALMDS/AMNS System Proficiency": (
        "Operates the system but requires instructor intervention on at least one critical initialization step or misidentifies system states, reducing mission effectiveness.",
        "Independently operates all system functions correctly; completes initialization, sweep execution, and contact reporting without instructor prompting.",
    ),
}


# Execution items per event: list of (name, is_critical) tuples
_EXEC: dict[str, list[tuple[str, bool]]] = {
    # PILOT_CORE L2 INTRO
    "P200":       [("PGM Employment", False), ("Strafe Employment", False), ("CSW Pattern Execution", False), ("SACT", False)],
    "P201":       [("Night Currency Profile", False), ("Unaided Low-Level Transit", False), ("Night Deck Landing", False)],
    # PILOT_CORE L2 ASU
    "P211":       [("PGM Employment", False), ("Strafe Employment", False), ("CSW Pattern Execution", False)],
    "P212":       [("Aerial Gunnery Pattern", False), ("Target Acquisition", False), ("Ammunition Management", False)],
    "P214":       [("Mission Display Management", False), ("PGM Employment", False), ("Asset Integration", True), ("Contingency Management", False), ("SACT", False)],
    "P215":       [("Reconnaissance Pattern", False), ("Target Reporting", False), ("Threat Awareness", False)],
    # PILOT_CORE L2 CSAR
    "P221":       [("Hoist Procedures", False), ("Survivor Recovery", False), ("Survivor Authentication", False), ("Tactical Pickup Zone", False)],
    "P223":       [("Overwater CSAR Pattern", False), ("Hoist Procedures", False), ("Survivor Recovery", False)],
    "P225":       [("Hoist Procedures", False), ("Survivor Recovery", False), ("Survivor Authentication", False), ("Tactical Pickup Zone", False), ("Contingency Management", False)],
    "P226":       [("TOFT CSAR Scenario", False), ("Simulated Hoist Procedures", False), ("Survivor Recovery Procedures", False)],
    # PILOT_CORE L2 SOF_LOG
    "P231":       [("Combat Logistics Pattern", False), ("Cargo Management", False), ("Route Planning Execution", False)],
    "P232":       [("Overwater SOF Pattern", False), ("SPIE / Fast-Rope Coordination", False), ("Comms and Encryption Setup", False)],
    "P233":       [("HVBSS Approach", False), ("Boarding Team Coordination", False), ("Stabilized Hover Maintenance", False)],
    "P234":       [("LZ Survey", False), ("Insertion Execution", False), ("Extraction Execution", False)],
    # PILOT_CORE L2 STAN_EVAL
    "P291":       [("Mission System Set-Up", True), ("Asset Integration", True), ("Package Decision Making", True), ("Asset Management", True)],
    "P292":       [("Demonstration Technique", False), ("Guided Practice", False), ("Error Correction", False), ("Performance Debrief", False)],
    "P293":       [("Scenario Setup", False), ("Student Monitoring", False), ("Intervention Technique", False), ("Debrief Facilitation", False)],
    # PILOT_CORE L3
    "P300":       [("PGM Employment", False), ("SACT", False), ("Multi-ship Coordination", False)],
    "P314":       [("RWT Pattern Execution", False), ("Asset Integration", True), ("Contingency Management", False), ("SACT", False)],
    "P315":       [("SCAR Pattern", False), ("Strike Coordination", False), ("Target Handoff", False)],
    "P323":       [("Overwater CSAR Pattern", False), ("Hoist Procedures", False), ("Survivor Recovery", False)],
    "P325":       [("Deliberate CSAR Planning", False), ("Hoist Procedures", False), ("Survivor Recovery", False), ("Contingency Management", False)],
    "P326":       [("TOFT CSAR Scenario", False), ("Simulated Hoist Procedures", False), ("Survivor Recovery Procedures", False)],
    "P331":       [("Combat Logistics Pattern", False), ("Multi-ship Coordination", False), ("Cargo Management", False)],
    "P333":       [("HVBSS Approach", False), ("Boarding Team Coordination", False), ("Stabilized Hover Maintenance", False)],
    "P334":       [("LZ Survey", False), ("Insertion Execution", False), ("Extraction Execution", False)],
    "P391":       [("Mission System Set-Up", True), ("Asset Integration", True), ("Package Decision Making", True), ("Asset Management", True)],
    "P392":       [("Advanced Demonstration", False), ("Student Performance Evaluation", False), ("Error Correction", False), ("Gradecard Completion", False)],
    # PILOT_AMCM
    "P210":       [("ALMDS Search Pattern", False), ("Lane Coverage", False), ("System Management", False)],
    "P211_AMCM":  [("ALMDS Day Search", False), ("Contact Reacquisition", False), ("System Checks", False)],
    "P212_AMCM":  [("ALMDS Night Search", False), ("Night Contact Reacquisition", False), ("NVG Integration", False)],
    "P220":       [("AMNS Mission Planning", False), ("Sweep Pattern Execution", False), ("System Management", False)],
    "P221_AMCM":  [("AMNS Day Mission", False), ("Sweep Pattern", False), ("System Checks", False)],
    "P222_AMCM":  [("AMNS Night Mission", False), ("Night System Operation", False), ("NVG Integration", False)],
    "P291_AMCM":  [("ALMDS/AMNS System Proficiency", True), ("Asset Integration", True), ("Mission Execution", False)],
    "P292_AMCM":  [("Simulator Operations", False), ("System Management", False), ("Emergency Procedure Execution", False)],
    # AIRCREW_CORE L2
    "A212":       [("M240D Employment", False), ("Weapon Clearance Procedures", False), ("Target Engagement", False)],
    "A213":       [("GAU21 Employment", False), ("Weapon Clearance Procedures", False), ("Target Engagement", False)],
    "A221":       [("Hoist Operator Procedures", False), ("Verbal Communication", False), ("Emergency Recovery", False)],
    "A222":       [("Rescue Element Procedures", False), ("CSAR Execution", False), ("Survivor Authentication", False), ("Emergency Recovery", False)],
    "A223":       [("Overwater Hoist Procedures", False), ("Comm Relay", False), ("Survivor Approach", False)],
    "A224":       [("CSAR Swimmer Deployment", False), ("Water Approach", False), ("Survivor Assist Procedures", False)],
    "A232":       [("SOF Insertion Procedures", False), ("SPIE / Fast-Rope Execution", False)],
    "A233":       [("HVBSS Procedures", False), ("Boarding Team Coordination", False), ("Cabin Safety", False)],
    "A234":       [("LZ Survey Procedures", False), ("SOF Coordination", False), ("Insertion Execution", False)],
    "A291":       [("Weapon Employment", True), ("Emergency Procedures", False)],
    # AIRCREW_CORE L3
    "A301":       [("Advanced System Operations", False), ("Multi-ship Coordination", False)],
    "A314":       [("RWT Crew Coordination", False), ("Asset Integration", True), ("Contingency Management", False)],
    "A315":       [("SCAR Crew Coordination", False), ("Target Reporting", False)],
    "A323":       [("Overwater CSAR Crew Coordination", False), ("Hoist Execution", False)],
    "A325":       [("Deliberate CSAR Crew Coordination", False), ("Hoist Execution", False), ("Contingency Management", False)],
    "A326":       [("TOFT CSAR Crew Execution", False), ("Simulated Hoist Procedures", False)],
    "A331":       [("Combat Logistics Crew Coordination", False), ("Cargo Management", False)],
    "A333":       [("HVBSS Crew Coordination", False), ("Boarding Assist Procedures", False)],
    "A334":       [("SOF Insertion Crew Coordination", False), ("LZ Survey", False)],
    "A391":       [("Weapon Employment", True), ("Mission Execution", False)],
    "A392":       [("Advanced Demonstration", False), ("Student Performance Evaluation", False), ("Error Correction", False)],
    # AIRCREW_AMCM
    "A310":       [("ALMDS Search Pattern", False), ("Contact Report", False), ("System Management", False)],
    "A320":       [("AMNS Mission Execution", False), ("Sweep Pattern", False), ("System Management", False)],
    "A390_AMCM":  [("ALMDS/AMNS System Proficiency", True), ("Mission Execution", False)],
    "A391_AMCM":  [("ALMDS/AMNS System Proficiency", True), ("Mission Execution", False)],
}

# BOARD / LAB events get minimal templates (no flight sections)
_BOARD_EVENTS = {"P290", "P390", "A390"}
_LAB_PREFIXES  = {"L"}  # any event whose code starts with L


def _mop(name: str, is_four_tier: bool, is_critical: bool):
    if not is_four_tier or not is_critical:
        return None, None
    pair = _MOPS.get(name, (None, None))
    return pair


def _pilot_items(event_code: str, is_four_tier: bool, is_instr: bool) -> list[dict]:
    exec_raw = _EXEC.get(event_code, [("Mission Execution", False)])
    exec_role = LIR.I if is_instr else LIR.P
    items = []
    order = 1

    def _add(sec, name, role=LIR.P, crit=False, req=True):
        nonlocal order
        bs, std = _mop(name, is_four_tier, crit)
        items.append(dict(section=sec, item_name=name, role=role,
                          is_critical=crit, is_required=req,
                          display_order=order, mop_below_standard=bs, mop_standard=std))
        order += 1

    # PLANNING_BRIEFING
    _add(GCS.PLANNING_BRIEFING, "Briefing Standards")
    _add(GCS.PLANNING_BRIEFING, "Mission Products")
    _add(GCS.PLANNING_BRIEFING, "Admin / Environmentals")
    _add(GCS.PLANNING_BRIEFING, "TAC Admin", req=False)
    _add(GCS.PLANNING_BRIEFING, "Mission Execution Planning")
    _add(GCS.PLANNING_BRIEFING, "Contingency Planning")
    # PRELAUNCH
    _add(GCS.PRELAUNCH, "Mission System Setup")
    _add(GCS.PRELAUNCH, "Navigation System Setup")
    _add(GCS.PRELAUNCH, "Comm Checks")
    # ENROUTE
    _add(GCS.ENROUTE, "Combat / FENCE Checks")
    _add(GCS.ENROUTE, "Navigation")
    _add(GCS.ENROUTE, "Range Procedures")
    # EXECUTION (event-specific)
    for name, crit in exec_raw:
        _add(GCS.EXECUTION, name, role=exec_role, crit=crit)
    # COMMUNICATION
    _add(GCS.COMMUNICATION, "Terminology and Brevity")
    _add(GCS.COMMUNICATION, "ICS Comms")
    _add(GCS.COMMUNICATION, "Section Comms")
    _add(GCS.COMMUNICATION, "External Comms")
    # GENERAL_FLIGHT_CONDUCT
    _add(GCS.GENERAL_FLIGHT_CONDUCT, "Safety of Flight")
    _add(GCS.GENERAL_FLIGHT_CONDUCT, "Aircraft Handling")
    _add(GCS.GENERAL_FLIGHT_CONDUCT, "ALR", crit=is_four_tier)
    _add(GCS.GENERAL_FLIGHT_CONDUCT, "ROE / Training Rule Adherence")
    _add(GCS.GENERAL_FLIGHT_CONDUCT, "Situational Awareness")
    _add(GCS.GENERAL_FLIGHT_CONDUCT, "Tactical Decision Making")
    _add(GCS.GENERAL_FLIGHT_CONDUCT, "CRM Effectiveness")
    # DEBRIEF
    _add(GCS.DEBRIEF, "Debrief")
    _add(GCS.DEBRIEF, "Shot Validation / Assessment", req=False)
    return items


def _aircrew_items(event_code: str, is_four_tier: bool) -> list[dict]:
    exec_raw = _EXEC.get(event_code, [("Mission Execution", False)])
    items = []
    order = 1

    def _add(sec, name, crit=False, req=True):
        nonlocal order
        bs, std = _mop(name, is_four_tier, crit)
        items.append(dict(section=sec, item_name=name, role=LIR.P,
                          is_critical=crit, is_required=req,
                          display_order=order, mop_below_standard=bs, mop_standard=std))
        order += 1

    # PLANNING_BRIEFING
    _add(GCS.PLANNING_BRIEFING, "Briefing Standards")
    _add(GCS.PLANNING_BRIEFING, "Mission Products")
    _add(GCS.PLANNING_BRIEFING, "Cabin / Equipment Brief")
    _add(GCS.PLANNING_BRIEFING, "Gunner / RE / EPA Brief")
    # PRELAUNCH
    _add(GCS.PRELAUNCH, "Weapon Preflight", crit=is_four_tier)
    _add(GCS.PRELAUNCH, "Ammo Preflight", crit=is_four_tier)
    _add(GCS.PRELAUNCH, "DMS / TAC-TAB / FIST Setup")
    _add(GCS.PRELAUNCH, "Cabin Prep / Setup")
    # ENROUTE
    _add(GCS.ENROUTE, "Combat Checks")
    _add(GCS.ENROUTE, "Ranging Exercise / Test Fire", crit=is_four_tier)
    _add(GCS.ENROUTE, "Route Lookout", crit=is_four_tier)
    # EXECUTION (event-specific)
    for name, crit in exec_raw:
        _add(GCS.EXECUTION, name, crit=crit)
    # COMMUNICATION
    _add(GCS.COMMUNICATION, "Terminology and Brevity", crit=is_four_tier)
    _add(GCS.COMMUNICATION, "ICS Comms")
    # GENERAL_FLIGHT_CONDUCT
    _add(GCS.GENERAL_FLIGHT_CONDUCT, "Safety of Flight", crit=is_four_tier)
    _add(GCS.GENERAL_FLIGHT_CONDUCT, "Cabin Management", crit=is_four_tier)
    _add(GCS.GENERAL_FLIGHT_CONDUCT, "Weapon Management", crit=is_four_tier)
    _add(GCS.GENERAL_FLIGHT_CONDUCT, "Crew Coordination")
    # DEBRIEF
    _add(GCS.DEBRIEF, "Preparation")
    _add(GCS.DEBRIEF, "Training Objective Accomplishment")
    _add(GCS.DEBRIEF, "Reconstruction")
    _add(GCS.DEBRIEF, "Mission / Self Analysis")
    return items


def _lab_items(event_code: str) -> list[dict]:
    return [
        dict(section=GCS.PLANNING_BRIEFING, item_name="Study Preparation",     role=LIR.P, is_critical=False, is_required=True,  display_order=1, mop_below_standard=None, mop_standard=None),
        dict(section=GCS.PLANNING_BRIEFING, item_name="Resource Review",        role=LIR.P, is_critical=False, is_required=True,  display_order=2, mop_below_standard=None, mop_standard=None),
        dict(section=GCS.EXECUTION,         item_name="Academic Review",         role=LIR.P, is_critical=False, is_required=True,  display_order=3, mop_below_standard=None, mop_standard=None),
        dict(section=GCS.EXECUTION,         item_name="Practical Exercise",      role=LIR.P, is_critical=False, is_required=False, display_order=4, mop_below_standard=None, mop_standard=None),
        dict(section=GCS.EXECUTION,         item_name="Knowledge Assessment",    role=LIR.P, is_critical=False, is_required=True,  display_order=5, mop_below_standard=None, mop_standard=None),
        dict(section=GCS.DEBRIEF,           item_name="Learning Objectives Met", role=LIR.P, is_critical=False, is_required=True,  display_order=6, mop_below_standard=None, mop_standard=None),
        dict(section=GCS.DEBRIEF,           item_name="Action Items",            role=LIR.P, is_critical=False, is_required=False, display_order=7, mop_below_standard=None, mop_standard=None),
    ]


def _board_items(event_code: str) -> list[dict]:
    return [
        dict(section=GCS.PLANNING_BRIEFING, item_name="Oral Board Preparation",  role=LIR.P, is_critical=False, is_required=True,  display_order=1, mop_below_standard=None, mop_standard=None),
        dict(section=GCS.PLANNING_BRIEFING, item_name="Study Materials Review",  role=LIR.P, is_critical=False, is_required=True,  display_order=2, mop_below_standard=None, mop_standard=None),
        dict(section=GCS.EXECUTION,         item_name="Systems Knowledge",        role=LIR.P, is_critical=True,  is_required=True,  display_order=3,
             mop_below_standard="Demonstrates partial systems knowledge; answers are incomplete or require significant instructor prompting on required topics.",
             mop_standard="Demonstrates thorough systems knowledge; answers all required questions independently and correctly."),
        dict(section=GCS.EXECUTION,         item_name="Emergency Procedures Knowledge", role=LIR.P, is_critical=True, is_required=True, display_order=4,
             mop_below_standard="Identifies the correct EP but misses one or more critical steps or performs steps out of sequence without prompting.",
             mop_standard="Correctly recites and sequences all required EP steps without prompting; identifies critical action items immediately."),
        dict(section=GCS.EXECUTION,         item_name="Tactical Knowledge",       role=LIR.P, is_critical=False, is_required=True,  display_order=5, mop_below_standard=None, mop_standard=None),
        dict(section=GCS.EXECUTION,         item_name="Mission Planning Application", role=LIR.P, is_critical=False, is_required=True, display_order=6, mop_below_standard=None, mop_standard=None),
        dict(section=GCS.DEBRIEF,           item_name="Overall Assessment",       role=LIR.P, is_critical=False, is_required=True,  display_order=7, mop_below_standard=None, mop_standard=None),
        dict(section=GCS.DEBRIEF,           item_name="Action Items",             role=LIR.P, is_critical=False, is_required=False, display_order=8, mop_below_standard=None, mop_standard=None),
    ]


def _get_line_items(event_code: str, venue: EventVenue, grading_scheme: GradingScheme, track: SyllabusTrack) -> list[dict]:
    """Return the appropriate line item list for an event."""
    is_four_tier = (grading_scheme == GS.FOUR_TIER)
    if venue == EV.LAB:
        return _lab_items(event_code)
    if venue == EV.BOARD:
        return _board_items(event_code)
    is_instr = event_code in {"P292", "P293", "P392", "P292_AMCM", "A392"}
    if track in (ST.AIRCREW_CORE, ST.AIRCREW_AMCM):
        return _aircrew_items(event_code, is_four_tier)
    return _pilot_items(event_code, is_four_tier, is_instr)


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
# Wing Table B-2 Currency Types
# ═══════════════════════════════════════════════════════════════════════════════

_CA = CurrencyAudience

_CURRENCY_TYPES = [
    dict(
        code="NIGHT_NVD", name="Night/NVD",
        periodicity_days=45, requirement_text="2.0 hrs night/NVD",
        min_hours=2.0, sim_eligible=False,
        references=["3710.7G Table B-2"],
        applicability=[(_CA.ALL_PILOTS, None)],
    ),
    dict(
        code="NVD_TERF", name="NVD TERF (Terrain Following)",
        periodicity_days=30, requirement_text="2.0 hrs NVD TERF",
        min_hours=2.0, sim_eligible=False,
        references=["3710.7G Table B-2"],
        applicability=[(_CA.ALL_PILOTS, None)],
    ),
    dict(
        code="NVD_TERF_INST", name="NVD TERF Instructor",
        periodicity_days=45, requirement_text="10.0 flight hours",
        min_hours=10.0, sim_eligible=False,
        references=["3710.7G Table B-2 Note 1"],
        applicability=[(_CA.HAC_ONLY, None)],
    ),
    dict(
        code="DAY_DVE", name="Day DVE Approaches",
        periodicity_days=60,
        requirement_text="3 day DVE approaches to a landing",
        min_count=3, count_unit="approaches", sim_eligible=False,
        description="NVD DVE approaches confer Day DVE approaches per Wing Note 2.",
        references=["3710.7G Table B-2 Note 2"],
        applicability=[(_CA.ALL_PILOTS, None)],
    ),
    dict(
        code="NVD_DVE", name="NVD DVE Approaches",
        periodicity_days=30, requirement_text="6 NVD landings",
        min_count=6, count_unit="landings", sim_eligible=False,
        references=["3710.7G Table B-2 Note 2"],
        applicability=[(_CA.ALL_PILOTS, None)],
    ),
    dict(
        code="STRAFE_DRY", name="Strafe Dry Fire",
        periodicity_days=90, requirement_text="3 day and 3 night profiles",
        min_count=6, count_unit="profiles", sim_eligible=True,
        sim_notes="May be conducted in Aircraft, TOFT or WTT per Wing Note 3. Night must be conducted wearing NVDs.",
        references=["3710.7G Table B-2 Note 3"],
        applicability=[(_CA.ALL_PILOTS, None)],
    ),
    dict(
        code="STRAFE_LIVE", name="Strafe Live Fire",
        periodicity_days=90,
        requirement_text="300×20mm or 9 UGR; day or night",
        min_count=300, count_unit="rounds 20mm OR 9 UGR", sim_eligible=False,
        description="Annual evaluation required regardless of 90-day currency. Annual eval shall be completed post-FRS training.",
        references=["3710.7G Table B-2 Note 4"],
        applicability=[(_CA.ALL_PILOTS, None)],
    ),
    dict(
        code="CSW", name="Crew-Served Weapons",
        periodicity_days=90, requirement_text="400 rounds (min 200 night)",
        min_count=400, count_unit="rounds (min 200 night)", sim_eligible=False,
        references=["3710.7G Table B-2"],
        applicability=[(_CA.ALL_PILOTS, None), (_CA.ALL_AIRCREWMEN, None)],
    ),
    dict(
        code="ALMDS_PILOT", name="ALMDS (Pilot)",
        periodicity_days=180, requirement_text="1.0 hour",
        min_hours=1.0, sim_eligible=False,
        description="PAC shall be up night couplers. Not required to be accomplished in AMCM-configured aircraft.",
        references=["3710.7G Table B-2 Note 5"],
        applicability=[(_CA.AMCM_QUAL_PILOTS, None)],
    ),
    dict(
        code="ALMDS_SO", name="ALMDS (Sensor Operator)",
        periodicity_days=180, requirement_text="1.0 hour",
        min_hours=1.0, sim_eligible=False,
        references=["3710.7G Table B-2"],
        applicability=[(_CA.AWS_ONLY, "AMCM_SO")],
    ),
    dict(
        code="AMNS_PILOT", name="AMNS (Pilot)",
        periodicity_days=180,
        requirement_text="2 simulated or actual NVD iterations",
        min_count=2, count_unit="iterations", sim_eligible=True,
        references=["3710.7G Table B-2"],
        applicability=[(_CA.AMCM_QUAL_PILOTS, None)],
    ),
    dict(
        code="AMNS_SO", name="AMNS (Sensor Operator)",
        periodicity_days=180,
        requirement_text="2 NTR vs 2 mines, day or night",
        min_count=2, count_unit="NTRs", sim_eligible=True,
        sim_notes="May be completed in the WTT per Wing Note 6",
        references=["3710.7G Table B-2 Note 6"],
        applicability=[(_CA.AWS_ONLY, "AMCM_SO")],
    ),
    dict(
        code="CSTRS_WINCH", name="CSTRS Winch Operator",
        periodicity_days=180, requirement_text="2 stream/recovery",
        min_count=2, count_unit="stream/recovery", sim_eligible=False,
        description="The shore-based CSTRS-T may be applied for non-consecutive 180-day periods.",
        references=["3710.7G Table B-2 Note 7"],
        applicability=[(_CA.HOIST_OP_QUAL, None)],
    ),
]


def seed_currency_types(db):
    ct_count = 0
    ca_count = 0
    for entry in _CURRENCY_TYPES:
        applicability = entry.pop("applicability")
        ct = CurrencyType(**entry)
        db.add(ct)
        db.flush()
        for audience, req_qual in applicability:
            db.add(CurrencyApplicability(
                currency_type_id=ct.id,
                applies_to=audience,
                required_qualification=req_qual,
            ))
            ca_count += 1
        ct_count += 1
    db.flush()
    return ct_count, ca_count


# ═══════════════════════════════════════════════════════════════════════════════
# Wipe
# ═══════════════════════════════════════════════════════════════════════════════

def wipe(db):
    db.query(GradecardLineItemResult).delete()
    db.query(Gradecard).delete()
    db.query(SortieTaskCredit).delete()
    db.query(Discrepancy).delete()
    db.query(SafetyReport).delete()
    db.query(FlightLog).delete()
    db.query(Sortie).delete()
    db.query(AircraftInspection).delete()
    db.query(InspectionType).delete()
    db.query(GradecardLineItem).delete()
    db.query(SyllabusEvent).delete()
    db.query(Currency).delete()
    db.query(CurrencyApplicability).delete()
    db.query(CurrencyType).delete()
    db.query(Qualification).delete()
    db.query(Aircraft).delete()
    db.query(Person).delete()
    db.query(CbrTaskOption).delete()
    db.commit()


# ═══════════════════════════════════════════════════════════════════════════════
# Aircraft
# ═══════════════════════════════════════════════════════════════════════════════

_AC_STATUSES = [
    AircraftStatus.FMC, AircraftStatus.FMC, AircraftStatus.FMC,
    AircraftStatus.FMC, AircraftStatus.FMC,
    AircraftStatus.PMC,
    AircraftStatus.NMCM,
    AircraftStatus.NMCS,
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
# Persons
# ═══════════════════════════════════════════════════════════════════════════════

_PILOTS = [
    ("Mitchell",  "James",    "LCDR", "VIPER"),
    ("Torres",    "Maria",    "LCDR", "GHOST"),
    ("Navarro",   "Carlos",   "LCDR", "RAZOR"),
    ("Bennett",   "Sarah",    "LT",   "HAMMER"),
    ("Collins",   "Derek",    "LT",   "ATLAS"),
    ("Walsh",     "Patrick",  "LT",   "FANG"),
    ("Nguyen",    "Linh",     "LT",   "NOVA"),
    ("Reyes",     "Marcus",   "LT",   "DUKE"),
    ("Foster",    "Amanda",   "LT",   "DAGGER"),
    ("Holloway",  "Tyler",    "LTJG", "SLICK"),
    ("Park",      "Jenna",    "LTJG", "SPARK"),
    ("Graham",    "Ethan",    "LTJG", "ROOK"),
]

_AIRCREW = [
    ("Davis",    "Aaron",  "AWS1"),
    ("Simmons",  "Brian",  "AWS2"),
    ("Ramos",    "Elena",  "AWS1"),
    ("Knight",   "Kevin",  "AWS3"),
    ("Larson",   "Tasha",  "AWS2"),
    ("Fleming",  "Jason",  "AWS3"),
    ("Ortega",   "Rosa",   "AWS1"),
    ("Hughes",   "Miles",  "AWS2"),
]

_STAFF = [
    ("Anderson",  "Robert",  "LCDR", Role.SDO,           None),
    ("Cooper",    "Lisa",    "LT",   Role.TRAINING_O,    None),
    ("Morgan",    "David",   "LCDR", Role.MAINT_CONTROL, None),
    ("Hawkins",   "Charles", "CDR",  Role.CO_XO,         None),
    ("admin",     "admin",   "",     Role.ADMIN,         None),
]


def seed_persons(db):
    pilots, aircrew = [], []

    for last, first, rank, callsign in _PILOTS:
        p = Person(
            last_name=last, first_name=first, rank=rank, callsign=callsign,
            role=Role.PILOT,
            username=f"{last.lower()}.{first.lower()}",
            password_hash=DEMO_PW, is_active=True,
        )
        db.add(p)
        pilots.append(p)

    for last, first, rank in _AIRCREW:
        p = Person(
            last_name=last, first_name=first, rank=rank, callsign=None,
            role=Role.AIRCREW,
            username=f"{last.lower()}.{first.lower()}",
            password_hash=DEMO_PW, is_active=True,
        )
        db.add(p)
        aircrew.append(p)

    for last, first, rank, role, callsign in _STAFF:
        username = "admin" if role == Role.ADMIN else f"{last.lower()}.{first.lower()}"
        p = Person(
            last_name=last, first_name=first, rank=rank, callsign=callsign,
            role=role, username=username,
            password_hash=DEMO_PW, is_active=True,
        )
        db.add(p)

    db.flush()
    return pilots, aircrew


# ═══════════════════════════════════════════════════════════════════════════════
# Qualifications & Currencies  (unchanged from batch-2)
# ═══════════════════════════════════════════════════════════════════════════════

def seed_qualifications(db, pilots, aircrew):
    hac_pilots = []
    count = 0

    for pilot in pilots:
        rank = pilot.rank
        db.add(Qualification(person_id=pilot.id, qual_code="H2P",
                             qualified_date=TODAY - timedelta(days=random.randint(180, 1500))))
        count += 1

        hac_p = 0.85 if rank == "LCDR" else (0.60 if rank == "LT" else 0.15)
        if random.random() < hac_p:
            db.add(Qualification(person_id=pilot.id, qual_code="HAC",
                                 qualified_date=TODAY - timedelta(days=random.randint(90, 800))))
            hac_pilots.append(pilot)
            count += 1

        if random.random() < 0.70:
            db.add(Qualification(person_id=pilot.id, qual_code="NVG",
                                 qualified_date=TODAY - timedelta(days=random.randint(60, 600))))
            count += 1

        special_p = 0.60 if rank == "LCDR" else 0.20
        if random.random() < special_p:
            code = random.choice(["FCP", "NSI", "INSTR"])
            db.add(Qualification(person_id=pilot.id, qual_code=code,
                                 qualified_date=TODAY - timedelta(days=random.randint(60, 600))))
            count += 1

    for ac in aircrew:
        db.add(Qualification(person_id=ac.id, qual_code="AIRCREW_QUAL",
                             qualified_date=TODAY - timedelta(days=random.randint(90, 1000))))
        count += 1
        if random.random() < 0.50:
            db.add(Qualification(person_id=ac.id, qual_code="AWS_QUAL",
                                 qualified_date=TODAY - timedelta(days=random.randint(90, 800))))
            count += 1
        # AMCM_SO qual → unlocks ALMDS_SO and AMNS_SO currencies (B4a-1)
        if ac.last_name in ("Davis", "Ortega"):
            db.add(Qualification(person_id=ac.id, qual_code="AMCM_SO",
                                 qualified_date=TODAY - timedelta(days=random.randint(60, 400))))
            count += 1
        # HOIST_OP_QUAL → unlocks CSTRS_WINCH currency (B4a-1)
        if ac.last_name in ("Davis", "Ramos"):
            db.add(Qualification(person_id=ac.id, qual_code="HOIST_OP_QUAL",
                                 qualified_date=TODAY - timedelta(days=random.randint(60, 400))))
            count += 1

    db.flush()
    return hac_pilots, count


def seed_currencies(db, persons, currency_types=None):
    """
    Create a Currency row for each Wing Table B-2 type that applies to each active
    person (based on their role + quals). Randomize last_event_date within
    1.5× the periodicity window to produce a mix of current and lapsed currencies.

    `currency_types` is accepted but unused — currencies_for_person does its own
    DB query so the rows must already exist (seed_currency_types must run first).
    """
    from app.services.currency_applicability import currencies_for_person

    rows = []
    for person in persons:
        if not person.is_active:
            continue
        applicable = currencies_for_person(person, db)
        for ct in applicable:
            days_ago = random.randint(0, int(ct.periodicity_days * 1.5))
            last = TODAY - timedelta(days=days_ago)
            expires = last + timedelta(days=ct.periodicity_days)
            rows.append(Currency(
                person_id=person.id,
                currency_type_id=ct.id,
                currency_code=ct.code,   # backward compat for any frontend still using it
                last_event_date=last,
                expires_date=expires,
            ))
    db.add_all(rows)
    db.flush()
    return rows


# ═══════════════════════════════════════════════════════════════════════════════
# Syllabus Events + Line Items
# ═══════════════════════════════════════════════════════════════════════════════

def seed_syllabus_events(db):
    event_objs = []
    total_items = 0
    by_track: dict[str, int] = {}

    for (code, event_code, name, track, level, stage, series,
         venue, time_h, min_inst, grading, is_stan) in _SWTP_EVENTS:

        ev = SyllabusEvent(
            code=code,
            event_code=event_code,
            name=name,
            track=track,
            level=level,
            stage=stage,
            series=series,
            aircraft_or_sim=venue,
            time_hours=time_h,
            min_instructor_level=min_inst,
            grading_scheme=grading,
            is_stan_eval=is_stan,
        )
        db.add(ev)
        db.flush()

        items = _get_line_items(event_code, venue, grading, track)
        # De-dup by item_name only (not section) since some line items canonically
        # belong to one section but were redundantly included in per-event EXECUTION
        # lists. Prefer is_critical=True; break ties by canonical section priority.
        _SECTION_PRIORITY = [
            "PRELAUNCH", "GENERAL_FLIGHT_CONDUCT", "COMMUNICATION",
            "DEBRIEF", "EXECUTION", "ENROUTE", "PLANNING_BRIEFING",
        ]
        def _sec_rank(sec) -> int:
            s = sec if isinstance(sec, str) else sec.value
            return _SECTION_PRIORITY.index(s) if s in _SECTION_PRIORITY else 99

        seen: dict = {}
        for li in items:
            key = li["item_name"]
            if key not in seen:
                seen[key] = li
                continue
            existing = seen[key]
            if li.get("is_critical") and not existing.get("is_critical"):
                seen[key] = li
                continue
            if existing.get("is_critical") and not li.get("is_critical"):
                continue
            if _sec_rank(li["section"]) < _sec_rank(existing["section"]):
                seen[key] = li
        deduped = list(seen.values())
        for item in deduped:
            db.add(GradecardLineItem(syllabus_event_id=ev.id, **item))
        total_items += len(deduped)
        event_objs.append(ev)
        tkey = track.value
        by_track[tkey] = by_track.get(tkey, 0) + 1

    db.flush()
    return event_objs, total_items, by_track


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
                days_ago = random.randint(0, max(1, it.periodicity_days // 3))
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


# ═══════════════════════════════════════════════════════════════════════════════
# CBR Task Options  (unchanged from batch-2)
# ═══════════════════════════════════════════════════════════════════════════════

_CBR_TASKS = [
    ("MOB 201", CapabilityArea.MOB, "NATOPS Check — Aircrew demonstrate proficiency per NATOPS procedures; evaluated by designated check aircrewman.", CrewScope.INDIVIDUAL, False, 1.5, [], "Aircrew demonstrate NATOPS-standard emergency procedures and systems knowledge.", "Complete all required EP demonstrations; verbal/written exam as required by NATOPS."),
    ("MOB 202", CapabilityArea.MOB, "Emergency Procedure Training — Crew execute simulated emergency procedures in flight or simulator.", CrewScope.CREW, True, 0.5, [], "Crew correctly identify, communicate, and execute all assigned EP scenarios.", "Execute each EP per NATOPS checklist; HAC grades crew actions on task/condition/standard."),
    ("MOB 203", CapabilityArea.MOB, "Basic Flight / FAM / FCF — Crew demonstrate basic airmanship during familiarization, proficiency, or functional check flight.", CrewScope.CREW, False, 1.5, [], "Crew maintain aircraft control within NATOPS limits throughout all maneuvers.", "Complete all planned profiles; no deviations outside NATOPS limits; HAC debriefs crew."),
    ("MOB 204", CapabilityArea.MOB, "Night Flight — Crew demonstrate proficiency during unaided or NVG night operations.", CrewScope.CREW, False, 2.0, ["MOB 203"], "Crew maintain situational awareness and aircraft control during night operations.", "Complete all planned night profiles; NVG goggle ops IAW NATOPS Chapter 7 if applicable."),
    ("MOB 205", CapabilityArea.MOB, "Air-Capable Ship Recovery Day — Pilot demonstrates proficiency in day shipboard approaches and deck landings.", CrewScope.INDIVIDUAL, False, 0.5, [], "Pilot executes stabilized approach to within NATOPS tolerances on each approach.", "Minimum 6 approaches; grade each approach per NATOPS T&R; HAC certifies completion."),
    ("MOB 209", CapabilityArea.MOB, "Instrument Check — Aircrew demonstrate proficiency in IMC and instrument approach procedures.", CrewScope.INDIVIDUAL, True, 1.0, [], "Aircrew fly all assigned instrument approach categories within NATOPS tolerances.", "Complete ILS, RNAV, and partial-panel approaches; HAC or IP grades each approach."),
    ("MOB 211", CapabilityArea.MOB, "Terminal Area Operations — Crew demonstrate proficiency in confined area and pinnacle landing operations.", CrewScope.CREW, False, 0.5, [], "Crew completes terminal area profiles without exceeding aircraft or site limitations.", "Conduct minimum one confined area approach/departure; crew brief/debrief required."),
    ("MOB 214", CapabilityArea.MOB, "Formation Flight — Crew demonstrate proficiency in multi-aircraft formation operations.", CrewScope.CREW, False, 0.5, [], "Crew maintains assigned position within NATOPS formation parameters throughout flight.", "Lead and wing phases; all crew demonstrate comm discipline and position awareness."),
    ("FSO 207", CapabilityArea.FSO, "Live Hoist — Crew execute external rescue hoist operations with a live swimmer or load.", CrewScope.CREW, False, 0.5, [], "Crew successfully deploys/recovers load or SAR swimmer within NATOPS weight and speed limits.", "Minimum two hoist cycles with live load; AWS grades hook-up procedure and crew coordination."),
    ("FSO 208", CapabilityArea.FSO, "Hoist Training — Crew execute hoist training with a dummy load or training device.", CrewScope.CREW, False, 0.5, [], "Crew demonstrates correct hoist procedures and emergency actions with training load.", "Demonstrate hook-up, hoist operation, and recovery; practice emergency jettison procedure."),
    ("FSO 209", CapabilityArea.FSO, "Search and Rescue — Crew execute a search pattern and execute survivor recovery in a SAR scenario.", CrewScope.CREW, False, 1.0, [], "Crew locates simulated survivor within planned search area and executes recovery.", "Execute assigned search pattern; demonstrate datum run procedures; recover survivor via hoist."),
    ("ASU 201", CapabilityArea.ASU, "CSW Pattern — Pilot/crew execute a coordinated surface warfare engagement pattern against a surface target.", CrewScope.INDIVIDUAL, False, 0.5, [], "Crew executes coordinated search/strike pattern and correctly employs sensors against surface targets.", "Complete all assigned CSW pattern phases; sensor employment grades per ASU T&R criteria."),
    ("ASU 206", CapabilityArea.ASU, "MTS Employment — Aircrew employ the Multi-spectral Targeting System against surface targets.", CrewScope.INDIVIDUAL, True, 0.5, [], "AWS/aircrew acquires and tracks assigned targets with MTS within ASU engagement criteria.", "Demonstrate MTS initialization, target acquisition, tracking, and handoff; debrief grade assigned."),
    ("ASU 207", CapabilityArea.ASU, "SCAR — Crew execute a Strike Coordination and Reconnaissance mission in support of surface forces.", CrewScope.CREW, True, 0.5, [], "Crew successfully coordinates with surface units and provides reconnaissance products.", "Complete full SCAR profile; comm plan executed; crew debrief includes target product assessment."),
    ("SOF 207", CapabilityArea.SOF, "SOF Insertion/Extraction — Crew insert or extract special operations forces via fast-rope, SPIE, or hover delivery.", CrewScope.CREW, False, 0.5, [], "Crew successfully inserts/extracts SOF element within time and accuracy parameters.", "Execute insertion or extraction IAW SOF T&R criteria; HAC grades crew coordination and airspeed control."),
    ("PR 201", CapabilityArea.PR, "Combat Search and Rescue — Crew executes recovery of isolated personnel in a contested environment.", CrewScope.CREW, False, 0.5, [], "Crew establishes comm with isolated personnel, executes recovery under threat environment constraints.", "Authentication, comm relay, threat assessment, and survivor recovery completed per PR T&R criteria."),
    ("STW 210", CapabilityArea.STW, "Large Force Exercise — Crew participates in a large force strike exercise with multi-unit coordination.", CrewScope.CREW, False, 0.5, [], "Crew integrates with strike package within EMCON and timing parameters.", "Complete all assigned LFE tasking; mission commander debrief; T/M/S grades assigned per exercise criteria."),
    ("LOG 201", CapabilityArea.LOG, "Day VERTREP — Crew execute vertical replenishment operations transferring cargo between ships.", CrewScope.CREW, False, 0.5, [], "Crew completes all assigned VERTREP cycles within weight limits and ship course/speed parameters.", "Demonstrate cargo hook-up, transfer, and release procedures; AWS grades sling load operations."),
    ("MIW 203", CapabilityArea.MIW, "ALMDS Simulator Day — Aircrew demonstrate proficiency with the Airborne Laser Mine Detection System in a simulator.", CrewScope.INDIVIDUAL, True, 0.5, [], "Aircrew demonstrates ALMDS system initialization, sweep pattern execution, and contact classification.", "Complete simulator ALMDS profile; system setup, sweep pattern, and contact report graded per MIW T&R."),
    ("MIW 205", CapabilityArea.MIW, "ALMDS Employment Day — Crew employ ALMDS in flight against a real or simulated minefield during daylight.", CrewScope.INDIVIDUAL, False, 0.5, [], "Crew successfully executes ALMDS lane sweep and generates contact report within time parameters.", "Execute full ALMDS lane; report contacts per MIW T&R criteria; post-mission data download graded."),
]


def seed_cbr_task_options(db):
    count = 0
    for code, area, desc, scope, sim_elig, min_hrs, confers, moe, mop in _CBR_TASKS:
        db.add(CbrTaskOption(code=code, capability_area=area, description=desc, crew_scope=scope,
                             sim_eligible=sim_elig, min_time_hours=min_hrs, confers_codes=confers,
                             moe_notes=moe, mop_notes=mop, is_active=True))
        count += 1
    db.flush()
    return count


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
    "INTRO":     ["MOB 203", "MOB 211"],
    "PROFICIENCY": ["MOB 203", "MOB 211", "MOB 202"],
    "ASU":       ["MOB 203", "ASU 201", "ASU 207", "MOB 202"],
    "CSAR":      ["FSO 209", "FSO 207", "FSO 208", "MOB 203", "PR 201"],
    "SOF":       ["SOF 207", "MOB 203"],
    "AMCM":      ["MIW 203", "MIW 205", "MOB 203"],
    "STAN_EVAL": ["MOB 203", "MOB 202"],
    "TRAINING":  ["MOB 203"],
    "FCF":       ["MOB 203", "MOB 202"],
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
                    day_hours=day_h,
                    night_hours=night_h,
                    nvg_hours=nvg_h,
                    instrument_hours=instr_h,
                    instrument_hours_simulated=instr_sim_h,
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


# ═══════════════════════════════════════════════════════════════════════════════
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
    fmc_aircraft = [ac for ac in aircraft_list if ac.status == AircraftStatus.FMC]
    minor_two    = random.sample(fmc_aircraft, min(2, len(fmc_aircraft)))
    maf_counter  = 1
    count_by_sev = {"MINOR": 0, "MAJOR": 0, "DOWNING": 0}

    def _maf():
        nonlocal maf_counter
        m = f"M-2026-{maf_counter:04d}"
        maf_counter += 1
        return m

    def _add(ac, desc, sys, sev, ws, is_open=True, corrective=None):
        days_ago = random.randint(1, 21) if is_open else random.randint(30, 90)
        opened   = datetime.utcnow() - timedelta(days=days_ago)
        closed   = (datetime.utcnow() - timedelta(days=random.randint(1, days_ago - 1))
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
        if ac.status == AircraftStatus.NMCM:
            desc, sys, ws = random.choice(_NMCM)
            _add(ac, desc, sys, DiscrepancySeverity.DOWNING, ws)
        elif ac.status == AircraftStatus.NMCS:
            desc, sys, ws = random.choice(_NMCS)
            _add(ac, desc, sys, DiscrepancySeverity.DOWNING, ws)
        elif ac.status == AircraftStatus.PMC:
            desc, sys, ws = random.choice(_PMC)
            # ~20% chance to escalate PMC MAJOR to DOWNING for demo variety
            sev = DiscrepancySeverity.DOWNING if random.random() < 0.20 else DiscrepancySeverity.MAJOR
            _add(ac, desc, sys, sev, ws)
        elif ac in minor_two:
            desc, sys, ws = random.choice(_MINOR)
            _add(ac, desc, sys, DiscrepancySeverity.MINOR, ws)

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


# ═══════════════════════════════════════════════════════════════════════════════
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


# ═══════════════════════════════════════════════════════════════════════════════
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
        status="CLOSED", closed_at=datetime.utcnow() - timedelta(days=random.randint(1, 5)),
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


# ═══════════════════════════════════════════════════════════════════════════════
# Historical Gradecards
# ═══════════════════════════════════════════════════════════════════════════════

def seed_historical_gradecards(db, all_logs):
    """
    For each historical sortie that references a SWTP event, generate a
    gradecard for the trainee pilot (H2P_U preferred, else H2P) or for the
    first aircrew member on aircrew-track events.
    Outcome distribution: 60% pass, 25% conditional/incomplete, 10% in-progress,
    5% no card.
    """
    from app.models.models import SyllabusEvent as SE, GradecardLineItem as GLI

    event_cache: dict[str, tuple] = {}  # event_code → (SE, list[GLI])

    status_counts: dict[str, int] = {
        "COMPLETE": 0, "PASS": 0, "CONDITIONAL_PASS": 0,
        "INCOMPLETE": 0, "IN_PROGRESS": 0, "UNSAT": 0,
    }
    count = 0

    for sortie, logs, _instr_h in all_logs:
        ec = sortie.event_code
        if not ec:
            continue

        if ec not in event_cache:
            evt = db.query(SE).filter(SE.event_code == ec).first()
            if evt is None or evt.grading_scheme is None:
                event_cache[ec] = (None, [])
                continue
            items = (db.query(GLI)
                     .filter(GLI.syllabus_event_id == evt.id)
                     .order_by(GLI.display_order)
                     .all())
            event_cache[ec] = (evt, items)

        evt, items = event_cache.get(ec, (None, []))
        if evt is None or not items:
            continue

        is_aircrew_track = evt.track in (ST.AIRCREW_CORE, ST.AIRCREW_AMCM)

        if is_aircrew_track:
            ui_log = next((fl for fl in logs if fl.crew_position in
                           (CrewPosition.AIRCREW, CrewPosition.AWS, CrewPosition.CREW_CHIEF)), None)
        else:
            ui_log = next((fl for fl in logs if fl.crew_position == CrewPosition.H2P_U), None)
            if ui_log is None:
                ui_log = next((fl for fl in logs if fl.crew_position == CrewPosition.H2P), None)

        if ui_log is None:
            continue

        roll = random.random()
        if roll < 0.05:
            continue  # 5%: no card filed

        hac_log     = next((fl for fl in logs if fl.crew_position == CrewPosition.HAC), None)
        instructor_id = hac_log.person_id if hac_log else None
        card_date   = sortie.land_time.date() if sortie.land_time else sortie.takeoff_time.date()
        is_four_tier = (evt.grading_scheme == GS.FOUR_TIER)

        if is_four_tier:
            # FOUR_TIER: 70% PASS / 20% CONDITIONAL_PASS / 10% UNSAT (no IN_PROGRESS)
            # Thresholds are over the 95% of events that get a card filed.
            if roll < 0.145:    # ~10% of filed cards
                outcome = "conditional"
                status  = GradecardStatus.UNSAT
            elif roll < 0.335:  # ~20% of filed cards
                outcome = "conditional"
                status  = GradecardStatus.CONDITIONAL_PASS
            else:               # ~70% of filed cards
                outcome = "pass"
                status  = GradecardStatus.PASS
        else:
            # COMPLETION: 80% COMPLETE / 8% INCOMPLETE / 12% IN_PROGRESS
            if roll < 0.164:    # ~12% of filed cards
                outcome = "in_progress"
                status  = GradecardStatus.IN_PROGRESS
            elif roll < 0.24:   # ~8% of filed cards
                outcome = "conditional"
                status  = GradecardStatus.INCOMPLETE
            else:               # ~80% of filed cards
                outcome = "pass"
                status  = GradecardStatus.COMPLETE

        gc = Gradecard(
            person_id=ui_log.person_id,
            syllabus_event_id=evt.id,
            sortie_id=sortie.id,
            flight_log_id=ui_log.id,
            instructor_person_id=instructor_id,
            card_date=card_date,
            grading_scheme=evt.grading_scheme,
            overall_status=status,
            remarks=None,
        )
        db.add(gc)
        db.flush()

        # Build results consistent with chosen outcome
        midpoint = len(items) // 2  # for conditional: item at midpoint gets degraded score
        for i, li in enumerate(items):
            if outcome == "in_progress" and i >= midpoint and li.is_required:
                continue  # leave second half of required items unscored

            if is_four_tier:
                if outcome == "pass":
                    score = FourTierScore.STANDARD_3_0
                elif outcome == "conditional":
                    # One non-critical item at the midpoint gets BELOW_STANDARD
                    score = (FourTierScore.BELOW_STANDARD_2_0
                             if i == midpoint and not li.is_critical
                             else FourTierScore.STANDARD_3_0)
                else:
                    score = FourTierScore.STANDARD_3_0  # scored items in in-progress are passing
                cs = None
            else:
                score = None
                if outcome == "pass":
                    cs = CompletionStatus.COMPLETE
                elif outcome == "conditional":
                    cs = (CompletionStatus.INCOMPLETE
                          if i == midpoint and li.is_required
                          else CompletionStatus.COMPLETE)
                else:
                    cs = CompletionStatus.COMPLETE  # scored items in in-progress are complete

            db.add(GradecardLineItemResult(
                gradecard_id=gc.id, line_item_id=li.id,
                waived=False, completion_status=cs, four_tier_score=score,
            ))

        # Credit the flight log for passing cards
        if status in (GradecardStatus.PASS, GradecardStatus.COMPLETE):
            ui_log.syllabus_event_completed = evt.event_code

        db.flush()
        status_counts[status.value] += 1
        count += 1

    return count, status_counts


# ═══════════════════════════════════════════════════════════════════════════════
# Future Scheduled Sorties (9 planned, using SWTP event codes)
# ═══════════════════════════════════════════════════════════════════════════════

def seed_future_sorties(db, aircraft_list, hac_pilots, all_pilots, aircrew_list):
    """9 planned sorties spread over the next 6 days."""
    from app.models.models import Currency

    fmc    = [ac for ac in aircraft_list if ac.status == AircraftStatus.FMC]
    pmc    = [ac for ac in aircraft_list if ac.status == AircraftStatus.PMC]
    nmcm   = next((ac for ac in aircraft_list if ac.status == AircraftStatus.NMCM), fmc[0])
    pmc_ac = pmc[0] if pmc else fmc[0]

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
            Currency.currency_code == "NVG",
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
             day_h, night_h, nvg_h, instr_h, dur, notes, crew):
        nonlocal sortie_count, log_count
        to_dt = datetime(flight_date.year, flight_date.month, flight_date.day, to_hour, 0)
        s = Sortie(
            event_type=event_type, event_code=event_code, aircraft_id=ac.id,
            brief_time=to_dt - timedelta(hours=1, minutes=30), takeoff_time=to_dt,
            land_time=to_dt + timedelta(hours=dur), duration_hours=dur,
            day_hours=day_h, night_hours=night_h, nvg_hours=nvg_h, instrument_hours=instr_h,
            is_complete=False, flight_mode=FlightMode.LIVE, notes=notes,
        )
        db.add(s)
        db.flush()
        for person, position in crew:
            db.add(FlightLog(sortie_id=s.id, person_id=person.id,
                             crew_position=position, hours_logged=dur))
            log_count += 1
        sortie_count += 1
        return s

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


# ═══════════════════════════════════════════════════════════════════════════════
# Main
# ═══════════════════════════════════════════════════════════════════════════════

def main():
    db = SessionLocal()
    try:
        print("Wiping existing data...")
        wipe(db)

        print("Seeding aircraft...")
        aircraft_list = seed_aircraft(db)

        print("Seeding persons...")
        pilots, aircrew = seed_persons(db)

        print("Seeding qualifications...")
        hac_pilots, qual_count = seed_qualifications(db, pilots, aircrew)

        print("Seeding Wing Table B-2 currency types...")
        ct_count, ca_count = seed_currency_types(db)

        print("Seeding currencies (Wing Table B-2, per-person)...")
        currency_rows = seed_currencies(db, pilots + aircrew)

        print("Seeding SWTP syllabus events and line items...")
        syllabus_events, line_item_count, by_track = seed_syllabus_events(db)

        print("Seeding CBR task options...")
        task_option_count = seed_cbr_task_options(db)

        print("Seeding inspection types...")
        inspection_types = seed_inspection_types(db)

        print("Seeding aircraft inspections...")
        insp_count = seed_aircraft_inspections(db, aircraft_list, inspection_types)

        print("Seeding historical sorties and flight logs...")
        sortie_count, log_count, all_logs = seed_sorties(db, aircraft_list, hac_pilots, pilots, aircrew)

        print("Seeding instrument approaches...")
        approach_count = seed_instrument_approaches(db, all_logs)

        print("Seeding discrepancies...")
        discrepancy_count, disc_by_sev = seed_discrepancies(db, aircraft_list)

        print("Seeding historical task credits...")
        task_credit_count = seed_task_credits(db, all_logs)

        print("Seeding safety reports...")
        safety_report_count = seed_safety_reports(db, all_logs, pilots)

        print("Seeding historical gradecards...")
        gradecard_count, gc_status_counts = seed_historical_gradecards(db, all_logs)

        print("Seeding future scheduled sorties...")
        sched_count, sched_log_count = seed_future_sorties(db, aircraft_list, hac_pilots, pilots, aircrew)

        db.commit()

        n_persons = len(pilots) + len(aircrew) + len(_STAFF)
        print(
            f"\n{'─'*60}\n"
            f"Seeded {len(aircraft_list)} aircraft, {n_persons} persons, "
            f"{qual_count} quals, {len(currency_rows)} currency rows "
            f"({ct_count} types, {ca_count} applicability rows).\n"
            f"Inspections: {len(inspection_types)} types, {insp_count} aircraft_inspection rows.\n"
            f"Syllabus: {len(syllabus_events)} events "
            f"({', '.join(f'{k}={v}' for k, v in sorted(by_track.items()))}), "
            f"{line_item_count} line items.\n"
            f"CBR: {task_option_count} task options.\n"
            f"Sorties: {sortie_count} historical + {sched_count} scheduled = "
            f"{sortie_count + sched_count} total, "
            f"{log_count + sched_log_count} flight_logs, "
            f"{approach_count} instrument_approaches.\n"
            f"Discrepancies: {discrepancy_count} total "
            f"({', '.join(f'{k}={v}' for k, v in disc_by_sev.items() if v)}), "
            f"task_credits: {task_credit_count}, "
            f"safety_reports: {safety_report_count}.\n"
            f"Gradecards: {gradecard_count} total "
            f"({', '.join(f'{k}={v}' for k, v in gc_status_counts.items() if v)}).\n"
            f"{'─'*60}"
        )

    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    main()
