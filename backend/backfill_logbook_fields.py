"""
Backfill logbook fields for the existing database after migration 8c4e6a1f3d2b.

Run from the backend/ directory:  python backfill_logbook_fields.py

NOTE (Pass 3): instrument_hours and instrument_hours_simulated moved from Sortie
to FlightLog in migration a0f2e4c6b8d0. That migration already backfilled those
FlightLog columns proportionally from the then-existing Sortie aggregates.
This script now checks FlightLog.instrument_hours instead of Sortie.instrument_hours
when deciding whether to seed InstrumentApproach rows.

Backfill rules
--------------
Sortie.landings_shipboard_day / _night: 0 (no ship ops in existing seed data)
Sortie.departure_location / arrival_location: "KNKX" (NAS North Island home field)
FlightLog.special_crew_time_hours: 0.0 (no data to derive from)

InstrumentApproach rows:
  For each FlightLog where:
    - the FlightLog has instrument_hours > 0
    - crew_position is HAC, H2P, or H2P_U
  Insert 1-3 InstrumentApproach rows using a mix of ILS/GPS/RNAV/TACAN/VOR.
  All marked ACTUAL (all are LIVE sorties).

SortieLeg rows: none (existing seed data is single-leg point-to-point).
"""
import random
import sys
import os

random.seed(99)  # deterministic but different from seed.py's seed(42)

sys.path.insert(0, os.path.dirname(__file__))

from datetime import datetime
from app.database import SessionLocal
from app.models.models import (
    Sortie, FlightLog, InstrumentApproach,
    FlightMode, CrewPosition, ApproachType, ApproachConditions,
)


_APPROACH_TYPE_POOL = [
    ApproachType.ILS, ApproachType.GPS, ApproachType.RNAV,
    ApproachType.TACAN, ApproachType.VOR,
]

_APPROACH_AIRPORTS = ["KNKX", "KNZY", "KSEE", "KMYF", "KCRQ"]

_PILOT_POSITIONS = {CrewPosition.HAC, CrewPosition.H2P, CrewPosition.H2P_U}


def backfill(db):
    sorties = db.query(Sortie).all()
    print(f"Found {len(sorties)} sorties to backfill.")

    sortie_updated = 0
    log_updated = 0
    approaches_inserted = 0

    for s in sorties:
        # ── Sortie-level fields ────────────────────────────────────────────────
        changed = False

        if s.departure_location is None:
            s.departure_location = "KNKX"
            changed = True
        if s.arrival_location is None:
            s.arrival_location = "KNKX"
            changed = True
        if s.landings_shipboard_day is None:
            s.landings_shipboard_day = 0
            changed = True
        if s.landings_shipboard_night is None:
            s.landings_shipboard_night = 0
            changed = True

        if changed:
            sortie_updated += 1

        # ── FlightLog-level fields and InstrumentApproach rows ─────────────────
        for fl in s.flight_logs:
            if fl.special_crew_time_hours is None or fl.special_crew_time_hours == 0.0:
                fl.special_crew_time_hours = 0.0
                log_updated += 1

            # instrument_hours is now per-crewmember on FlightLog (Pass 3)
            if not (fl.instrument_hours or 0.0) > 0:
                continue
            if fl.crew_position not in _PILOT_POSITIONS:
                continue

            # Only insert if no approaches exist yet (idempotent)
            existing = (
                db.query(InstrumentApproach)
                .filter(InstrumentApproach.flight_log_id == fl.id)
                .count()
            )
            if existing > 0:
                continue

            n = random.randint(1, 3)
            for _ in range(n):
                db.add(InstrumentApproach(
                    flight_log_id=fl.id,
                    sortie_id=s.id,
                    approach_type=random.choice(_APPROACH_TYPE_POOL),
                    actual_or_simulated=ApproachConditions.ACTUAL,
                    airport_icao=random.choice(_APPROACH_AIRPORTS),
                    runway=None,
                    remarks=None,
                    logged_at=s.land_time or s.takeoff_time or datetime.utcnow(),
                ))
                approaches_inserted += 1

    db.flush()
    return sortie_updated, log_updated, approaches_inserted


def main():
    db = SessionLocal()
    try:
        print("Starting logbook backfill...")
        sortie_updated, log_updated, approaches_inserted = backfill(db)
        db.commit()
        print(
            f"Done.\n"
            f"  Sorties updated:          {sortie_updated}\n"
            f"  FlightLogs touched:       {log_updated}\n"
            f"  InstrumentApproach rows:  {approaches_inserted}"
        )
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    main()
