"""Seed orchestration: wipe + main() entrypoint."""
import os
import sys

# Ensure backend/ is on path when imported as package
_backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _backend_dir not in sys.path:
    sys.path.insert(0, _backend_dir)

from app.database import SessionLocal
from app.models.models import (
    Person, Aircraft, Qualification, Currency, SyllabusEvent,
    GradecardLineItem, Gradecard, GradecardLineItemResult,
    Sortie, FlightLog, Discrepancy, CbrTaskOption, SortieTaskCredit, SafetyReport,
    CurrencyType, CurrencyApplicability,
    InspectionType, AircraftInspection,
    SortieLeg, InstrumentApproach, SortieTmrCode, TmrCode, AuditLog,
    BoardSchedule, BoardType, BoardStatus, WatchbillEntry, WatchbillRole,
    SchedulePublication, SortieOpsStatus,
    QaSignoff, PartsRequest, AircraftLogbookEntry, WorkOrder, Maf, WorkCenter,
    CapabilityAreaConfig,
)

# Import constants first so random.seed(42) applies before other modules use random
import seed.constants  # noqa: F401

from seed.aircraft import seed_aircraft, seed_inspection_types, seed_aircraft_inspections
from seed.cbr import seed_capability_area_configs, seed_cbr_task_options
from seed.maintenance import seed_discrepancies
from seed.ops import seed_watchbill_and_boards, seed_publish_today_schedule
from seed.people import (
    seed_currency_types, seed_persons, seed_qualifications, seed_currencies, _STAFF,
)
from seed.sorties import (
    seed_sorties, seed_instrument_approaches, seed_task_credits,
    seed_safety_reports, seed_future_sorties,
)
from seed.training import seed_syllabus_events, seed_historical_gradecards

# ═══════════════════════════════════════════════════════════════════════════════
# Wipe
# ═══════════════════════════════════════════════════════════════════════════════

def wipe(db):
    db.query(BoardSchedule).delete()
    db.query(WatchbillEntry).delete()
    db.query(SchedulePublication).delete()
    db.query(AuditLog).delete()
    db.query(GradecardLineItemResult).delete()
    db.query(Gradecard).delete()
    db.query(SortieTaskCredit).delete()
    db.query(InstrumentApproach).delete()
    db.query(SortieTmrCode).delete()
    db.query(QaSignoff).delete()
    db.query(PartsRequest).delete()
    db.query(AircraftLogbookEntry).delete()
    db.query(WorkOrder).delete()
    db.query(Maf).delete()
    db.query(WorkCenter).delete()
    db.query(Discrepancy).delete()
    db.query(SafetyReport).delete()
    db.query(FlightLog).delete()
    db.query(SortieLeg).delete()
    db.query(Sortie).delete()
    db.query(TmrCode).delete()
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
    db.query(CapabilityAreaConfig).delete()
    db.commit()

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

        print("Seeding capability area configs...")
        area_config_count = seed_capability_area_configs(db)

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

        print("Seeding watchbill, training boards, and schedule publication...")
        board_count = seed_watchbill_and_boards(db, pilots, aircrew, syllabus_events)
        published_count = seed_publish_today_schedule(db)

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
            f"SDO: {board_count} training boards, {published_count} sorties published for today.\n"
            f"{'─'*60}"
        )

    except Exception:
        db.rollback()
        raise
    finally:
        db.close()
