"""
Maps a Sortie's actual activity to the Wing Table B-2 currency codes that renew.

PRINCIPLE (B2-1 hours-gate): renewal requires the activity ACTUALLY HAPPENED
(measured by hours or counts logged on the sortie), never inferred from event_type
alone. Every predicate below gates on a specific measured quantity.
"""
from app.models.models import Sortie, FlightMode


def _h(s: Sortie, attr: str) -> float:
    return float(getattr(s, attr, None) or 0)


def _i(s: Sortie, attr: str) -> int:
    return int(getattr(s, attr, None) or 0)


def renews_NIGHT_NVD(s: Sortie) -> bool:
    # 2.0 hrs night/NVD per Wing B-2
    return (_h(s, 'night_hours') + _h(s, 'nvg_hours')) >= 2.0


def renews_NVD_TERF(s: Sortie) -> bool:
    # 2.0 hrs NVD TERF — nvg_hours captures TERF time when terrain-following profile flown
    return _h(s, 'nvg_hours') >= 2.0


def renews_NVD_TERF_INST(s: Sortie) -> bool:
    # 10.0 flight hours total (HAC instructor currency; seldom met in a single sortie)
    return _h(s, 'duration_hours') >= 10.0


def renews_DAY_DVE(s: Sortie) -> bool:
    # 3 day DVE approaches to a landing; per Wing Note 2, NVD DVE also confers Day DVE
    return _i(s, 'landings_dve_day') >= 3 or _i(s, 'landings_dve_night') >= 3


def renews_NVD_DVE(s: Sortie) -> bool:
    # 6 NVD landings
    return _i(s, 'landings_dve_night') >= 6 or _i(s, 'landings_night') >= 6


def renews_STRAFE_DRY(s: Sortie) -> bool:
    # 3 day + 3 night profiles; fire renewal if either threshold met this sortie
    return _i(s, 'strafe_dry_profiles_day') >= 3 or _i(s, 'strafe_dry_profiles_night') >= 3


def renews_STRAFE_LIVE(s: Sortie) -> bool:
    # 300 rounds 20mm OR 9 UGR
    return _i(s, 'rounds_fired_20mm') >= 300 or _i(s, 'ugr_fired') >= 9


def renews_CSW(s: Sortie) -> bool:
    # 400 rounds total, minimum 200 at night
    return _i(s, 'csw_rounds') >= 400 and _i(s, 'csw_rounds_night') >= 200


def renews_ALMDS_PILOT(s: Sortie) -> bool:
    return _h(s, 'almds_hours') >= 1.0


def renews_ALMDS_SO(s: Sortie) -> bool:
    return _h(s, 'almds_hours') >= 1.0


def renews_AMNS_PILOT(s: Sortie) -> bool:
    return _i(s, 'amns_iterations') >= 2


def renews_AMNS_SO(s: Sortie) -> bool:
    return _i(s, 'amns_ntrs') >= 2


def renews_CSTRS_WINCH(s: Sortie) -> bool:
    return _i(s, 'hoist_streams') >= 2


# Currency code → renewal predicate
RENEWAL_RULES: dict = {
    "NIGHT_NVD":     renews_NIGHT_NVD,
    "NVD_TERF":      renews_NVD_TERF,
    "NVD_TERF_INST": renews_NVD_TERF_INST,
    "DAY_DVE":       renews_DAY_DVE,
    "NVD_DVE":       renews_NVD_DVE,
    "STRAFE_DRY":    renews_STRAFE_DRY,
    "STRAFE_LIVE":   renews_STRAFE_LIVE,
    "CSW":           renews_CSW,
    "ALMDS_PILOT":   renews_ALMDS_PILOT,
    "ALMDS_SO":      renews_ALMDS_SO,
    "AMNS_PILOT":    renews_AMNS_PILOT,
    "AMNS_SO":       renews_AMNS_SO,
    "CSTRS_WINCH":   renews_CSTRS_WINCH,
}


def codes_renewed_by(sortie: Sortie, flight_mode: FlightMode,
                     applicable_codes: list) -> set:
    """
    Return the subset of applicable_codes whose renewal predicate fires on this
    sortie. SIM_TOFT callers should pre-filter applicable_codes to sim_eligible
    currencies before calling here.
    """
    return {
        code for code in applicable_codes
        if (rule := RENEWAL_RULES.get(code)) and rule(sortie)
    }
