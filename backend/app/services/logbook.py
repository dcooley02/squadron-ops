"""
Logbook computation service.
Keeps totals math out of the route handler.
"""
from datetime import datetime, timedelta

_ALL_APPROACH_TYPES = ["ILS", "GPS", "RNAV", "TACAN", "VOR", "PAR", "ASR", "ENROUTE"]


def compute_totals(logs: list) -> dict:
    """
    Aggregate FlightLog rows into a LogbookTotals-compatible dict.

    Hours allocation: each log's contribution to day/night/NVG/instrument is
    scaled by (hours_logged / sortie.duration_hours). This handles partial-flight
    cases correctly. Landings are sortie-level events summed at face value.
    """
    total_hours = 0.0
    day_hours = night_hours = nvg_hours = instr_actual = instr_sim = 0.0
    ldg_day = ldg_night = ldg_dve_day = ldg_dve_night = ldg_ship_day = ldg_ship_night = 0
    approaches_total = 0
    approaches_by_type: dict[str, int] = {t: 0 for t in _ALL_APPROACH_TYPES}
    sortie_ids: set[int] = set()

    for fl in logs:
        s = fl.sortie
        dur = s.duration_hours or 0.0
        ratio = fl.hours_logged / dur if dur > 0 else 1.0

        total_hours  += fl.hours_logged
        day_hours    += (s.day_hours or 0.0) * ratio
        night_hours  += (s.night_hours or 0.0) * ratio
        nvg_hours    += (s.nvg_hours or 0.0) * ratio
        instr_actual += (s.instrument_hours or 0.0) * ratio
        instr_sim    += (s.instrument_hours_simulated or 0.0) * ratio

        ldg_day       += s.landings_day or 0
        ldg_night     += s.landings_night or 0
        ldg_dve_day   += s.landings_dve_day or 0
        ldg_dve_night += s.landings_dve_night or 0
        ldg_ship_day  += s.landings_shipboard_day or 0
        ldg_ship_night += s.landings_shipboard_night or 0

        for appr in fl.instrument_approaches:
            approaches_total += 1
            t = appr.approach_type.value
            if t in approaches_by_type:
                approaches_by_type[t] += 1

        sortie_ids.add(s.id)

    return {
        "total_hours":               round(total_hours, 1),
        "day_hours":                 round(day_hours, 1),
        "night_hours":               round(night_hours, 1),
        "nvg_hours":                 round(nvg_hours, 1),
        "instrument_hours_actual":   round(instr_actual, 1),
        "instrument_hours_simulated": round(instr_sim, 1),
        "landings_day":              ldg_day,
        "landings_night":            ldg_night,
        "landings_dve_day":          ldg_dve_day,
        "landings_dve_night":        ldg_dve_night,
        "landings_shipboard_day":    ldg_ship_day,
        "landings_shipboard_night":  ldg_ship_night,
        "approaches_total":          approaches_total,
        "approaches_by_type":        approaches_by_type,
        "sortie_count":              len(sortie_ids),
        "flight_log_count":          len(logs),
    }


def build_window_totals(all_logs: list) -> dict:
    """
    Compute the four fixed-window totals (career / 365d / 90d / 30d).
    Windows are always relative to now — independent of any user filter.
    """
    now = datetime.utcnow()

    def _after(cutoff):
        return [
            fl for fl in all_logs
            if fl.sortie.takeoff_time and fl.sortie.takeoff_time >= cutoff
        ]

    return {
        "career":    compute_totals(all_logs),
        "last_365d": compute_totals(_after(now - timedelta(days=365))),
        "last_90d":  compute_totals(_after(now - timedelta(days=90))),
        "last_30d":  compute_totals(_after(now - timedelta(days=30))),
    }
