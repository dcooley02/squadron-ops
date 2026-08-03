"""Syllabus events/line items and historical gradecards."""
import random

from app.models.models import (
    SyllabusEvent, GradecardLineItem, Gradecard, GradecardLineItemResult,
    CrewPosition, GradecardStatus, CompletionStatus, FourTierScore,
)

from seed.constants import GS, ST
from seed.swtp_catalog import _SWTP_EVENTS, _get_line_items

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
