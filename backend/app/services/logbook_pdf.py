"""
Server-side PDF generation for the aviator's flight logbook.
Form-faithful to NAVFLIR OPNAV 3760/31 (Level 1 fidelity).

WeasyPrint is a lazy import so the server starts cleanly even when the native
macOS dependencies are not yet installed. The PDF endpoints will raise a
503-style RuntimeError if WeasyPrint is unavailable.

macOS pre-requisite (run once, before pip install weasyprint):
    brew install pango gdk-pixbuf libffi
"""
from __future__ import annotations

from datetime import date as date_type, datetime, time as dt_time
from pathlib import Path
from typing import Optional

from sqlalchemy.orm import Session, joinedload, selectinload

from app.models.models import FlightLog, Person, Sortie
from app.schemas.logging import LogbookFiltersApplied
from app.services.logbook import build_window_totals

_TEMPLATE_DIR = Path(__file__).parent.parent / "templates"
_TEMPLATE_NAME = "logbook.html"
_ENTRIES_PER_PAGE = 19

# Numeric keys tracked for page-level running totals
_TOTAL_KEYS: tuple[str, ...] = (
    "total_hours",
    "first_pilot_hours",
    "copilot_hours",
    "ac_commander_hours",
    "spec_crew_hours",
    "actual_instrument_hours",
    "sim_instrument_hours",
    "night_hours",
    "nvg_hours",
    "landings_day",
    "landings_night",
    "landings_shipboard_day",
    "landings_shipboard_night",
)


# ── Internal helpers ──────────────────────────────────────────────────────────

def _zero_totals() -> dict:
    return dict.fromkeys(_TOTAL_KEYS, 0.0)


def _sum_totals(entries: list[dict]) -> dict:
    result = _zero_totals()
    for e in entries:
        for k in _TOTAL_KEYS:
            result[k] += e.get(k, 0.0)
    return result


def _add_totals(a: dict, b: dict) -> dict:
    return {k: a[k] + b[k] for k in _TOTAL_KEYS}


def _entry_dict(fl: FlightLog) -> dict:
    s = fl.sortie
    ac = s.aircraft
    date_str = s.takeoff_time.strftime("%d %b %Y").upper() if s.takeoff_time else ""
    return {
        "date": date_str,
        "tms": ac.type_model_series if ac else "",
        "buno": ac.bureau_number if ac else "",
        "code": s.event_code or "",
        "qual": fl.crew_qual_code or "",
        "total_hours": fl.total_hours or fl.hours_logged or 0.0,
        "first_pilot_hours": fl.first_pilot_hours or 0.0,
        "copilot_hours": fl.copilot_hours or 0.0,
        "ac_commander_hours": fl.ac_commander_hours or 0.0,
        "spec_crew_hours": fl.special_crew_time_hours or 0.0,
        "actual_instrument_hours": fl.actual_instrument_hours or 0.0,
        "sim_instrument_hours": fl.sim_instrument_hours or 0.0,
        "night_hours": fl.night_hours or 0.0,
        "nvg_hours": fl.nvg_hours or 0.0,
        # Per-crewmember landings (B1): per-aviator NAVFLIR PDF should not
        # show sortie rollups; pull from the flight_log row.
        "landings_day": fl.landings_day or 0,
        "landings_night": fl.landings_night or 0,
        "landings_shipboard_day": fl.landings_shipboard_day or 0,
        "landings_shipboard_night": fl.landings_shipboard_night or 0,
        "approaches": len(fl.instrument_approaches),
        "departure": s.departure_location or "",
        "arrival": s.arrival_location or "",
        # Truncate remarks to fit one table cell
        "remarks": (fl.instructor_remarks or s.debrief_notes or "")[:80],
    }


def _apply_filters(
    logs: list[FlightLog],
    filters: Optional[LogbookFiltersApplied],
) -> list[FlightLog]:
    if not filters:
        return logs
    result = logs
    if filters.date_from:
        cutoff = datetime.combine(date_type.fromisoformat(str(filters.date_from)), dt_time.min)
        result = [fl for fl in result
                  if fl.sortie.takeoff_time and fl.sortie.takeoff_time >= cutoff]
    if filters.date_to:
        cutoff = datetime.combine(date_type.fromisoformat(str(filters.date_to)), dt_time.max)
        result = [fl for fl in result
                  if fl.sortie.takeoff_time and fl.sortie.takeoff_time <= cutoff]
    if filters.aircraft_id is not None:
        result = [fl for fl in result if fl.sortie.aircraft_id == filters.aircraft_id]
    if filters.event_code:
        result = [fl for fl in result if fl.sortie.event_code == filters.event_code]
    if filters.crew_position:
        result = [fl for fl in result if fl.crew_position.value == filters.crew_position]
    if filters.flight_mode:
        result = [fl for fl in result if fl.sortie.flight_mode.value == filters.flight_mode]
    return result


def _paginate(entries: list[dict], per_page: int, window_dict: dict) -> list[dict]:
    """Split entries into pages; attach running totals to each page."""
    total_pages = max(1, (len(entries) + per_page - 1) // per_page) if entries else 1
    pages: list[dict] = []
    brought_forward = _zero_totals()

    for idx in range(total_pages):
        chunk = entries[idx * per_page: (idx + 1) * per_page]
        this_page = _sum_totals(chunk)
        to_date = _add_totals(brought_forward, this_page)
        is_last = idx == total_pages - 1

        pages.append({
            "entries": chunk,
            "page_num": idx + 1,
            "total_pages": total_pages,
            "this_page": this_page,
            "brought_forward": dict(brought_forward),
            "to_date": to_date,
            "is_last": is_last,
            "window_totals": window_dict if is_last else None,
        })
        brought_forward = dict(to_date)

    return pages


# ── Public API ────────────────────────────────────────────────────────────────

def render_logbook_pdf(
    db: Session,
    person_id: int,
    filters: Optional[LogbookFiltersApplied] = None,
    watermark: bool = False,
) -> bytes:
    """
    Render a person's logbook to PDF bytes (NAVFLIR OPNAV 3760/31, Level 1 fidelity).

    - Reuses logbook.compute_totals / build_window_totals — no math reimplemented here.
    - If filters is None or all fields are None, renders the full career logbook.
    - If watermark=True, stamps every page with a filtered-view notice.
    - Paginated at 19 entries per page (NAVFLIR convention).
    - Entries sorted ascending by takeoff_time (paper logbook convention).
    - Four-window totals (career/365d/90d/30d) always computed from ALL career logs,
      regardless of the active filter (matches the JSON logbook endpoint semantics).

    Raises:
        ValueError: person not found.
        RuntimeError: WeasyPrint or Jinja2 not installed (see module docstring).
    """
    try:
        from jinja2 import Environment, FileSystemLoader
        from weasyprint import HTML as WeasyprintHTML  # noqa: N811
    except ImportError as exc:
        raise RuntimeError(
            "PDF generation requires weasyprint and Jinja2. "
            "On macOS, first run:\n"
            "    brew install pango gdk-pixbuf libffi\n"
            "Then:\n"
            "    pip install weasyprint"
        ) from exc

    person = db.query(Person).filter(Person.id == person_id).first()
    if person is None:
        raise ValueError(f"Person {person_id} not found")

    # All completed logs for this person, sorted oldest-first (paper convention).
    all_logs: list[FlightLog] = (
        db.query(FlightLog)
        .join(Sortie, FlightLog.sortie_id == Sortie.id)
        .options(
            joinedload(FlightLog.sortie).joinedload(Sortie.aircraft),
            selectinload(FlightLog.instrument_approaches),
        )
        .filter(
            FlightLog.person_id == person_id,
            Sortie.is_complete == True,
        )
        .order_by(Sortie.takeoff_time.asc(), Sortie.id.asc())
        .all()
    )

    # Window totals always use ALL career logs, same as the JSON endpoint.
    window_dict = build_window_totals(all_logs)

    display_logs = _apply_filters(all_logs, filters)
    entries = [_entry_dict(fl) for fl in display_logs]
    pages = _paginate(entries, _ENTRIES_PER_PAGE, window_dict)

    env = Environment(
        loader=FileSystemLoader(str(_TEMPLATE_DIR)),
        autoescape=True,
    )
    # fmt_num: float → "1.2"; blank_zero=True shows "" for 0.0
    env.filters["fmt_num"] = lambda v, blank_zero=True: (
        "" if (v is None or (blank_zero and float(v) == 0.0)) else f"{float(v):.1f}"
    )
    # fmt_int: int → "3"; blank_zero=True shows "" for 0
    env.filters["fmt_int"] = lambda v, blank_zero=True: (
        "" if (v is None or (blank_zero and int(v) == 0)) else str(int(v))
    )

    template = env.get_template(_TEMPLATE_NAME)
    html_str = template.render(
        person=person,
        pages=pages,
        watermark=watermark,
        generated_at=datetime.utcnow().strftime("%d %b %Y").upper(),
    )

    pdf_bytes = WeasyprintHTML(
        string=html_str,
        base_url=str(_TEMPLATE_DIR),
    ).write_pdf()
    return pdf_bytes
