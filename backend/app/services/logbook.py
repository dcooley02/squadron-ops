"""
Logbook computation service.
Keeps totals math out of the route handler.
"""
from datetime import datetime, timedelta

_ALL_APPROACH_TYPES = ["ILS", "GPS", "RNAV", "TACAN", "VOR", "PAR", "ASR", "ENROUTE"]


def compute_totals(logs: list) -> dict:
    """
    Aggregate FlightLog rows into a LogbookTotals-compatible dict.
    All hour values come from per-crewmember FlightLog columns.
    Landings remain sortie-level events summed at face value.
    """
    total_hours = 0.0
    night_hours = nvg_hours = instr_actual = instr_sim = 0.0
    fp_hours = cp_hours = hac_hours = mc_hours = instr_role = spec_crew = 0.0
    ldg_day = ldg_night = ldg_dve_day = ldg_dve_night = ldg_ship_day = ldg_ship_night = 0
    approaches_total = 0
    approaches_by_type: dict[str, int] = {t: 0 for t in _ALL_APPROACH_TYPES}
    sortie_ids: set[int] = set()
    provenance_counts: dict[str, int] = {}

    for fl in logs:
        s = fl.sortie

        total_hours  += fl.total_hours or fl.hours_logged
        night_hours  += fl.night_hours or 0.0
        nvg_hours    += fl.nvg_hours or 0.0
        instr_actual += fl.actual_instrument_hours or 0.0
        instr_sim    += fl.sim_instrument_hours or 0.0
        fp_hours     += fl.first_pilot_hours or 0.0
        cp_hours     += fl.copilot_hours or 0.0
        hac_hours    += fl.ac_commander_hours or 0.0
        mc_hours     += fl.mission_commander_hours or 0.0
        instr_role   += fl.instructor_hours or 0.0
        spec_crew    += fl.special_crew_time_hours or 0.0

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

        prov = fl.data_provenance.value if fl.data_provenance else "ENTERED"
        provenance_counts[prov] = provenance_counts.get(prov, 0) + 1

    return {
        "total_hours":                  round(total_hours, 1),
        "night_hours":                  round(night_hours, 1),
        "nvg_hours":                    round(nvg_hours, 1),
        "total_actual_instrument_hours": round(instr_actual, 1),
        "total_sim_instrument_hours":   round(instr_sim, 1),
        "total_first_pilot_hours":      round(fp_hours, 1),
        "total_copilot_hours":          round(cp_hours, 1),
        "total_ac_commander_hours":     round(hac_hours, 1),
        "total_mission_commander_hours": round(mc_hours, 1),
        "total_instructor_hours":       round(instr_role, 1),
        "total_spec_crew_hours":        round(spec_crew, 1),
        "landings_day":                 ldg_day,
        "landings_night":               ldg_night,
        "landings_dve_day":             ldg_dve_day,
        "landings_dve_night":           ldg_dve_night,
        "landings_shipboard_day":       ldg_ship_day,
        "landings_shipboard_night":     ldg_ship_night,
        "approaches_total":             approaches_total,
        "approaches_by_type":           approaches_by_type,
        "sortie_count":                 len(sortie_ids),
        "flight_log_count":             len(logs),
        "data_provenance_breakdown":    provenance_counts,
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
