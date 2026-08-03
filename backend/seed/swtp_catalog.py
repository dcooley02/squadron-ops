"""SWTP event catalog and gradecard line-item templates."""
from app.models.models import EventVenue, GradingScheme, SyllabusTrack

from seed.constants import GCS, LIR, GS, SL, SS, ST, EV

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

