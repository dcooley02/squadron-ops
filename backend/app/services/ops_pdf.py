"""SDO brief sheet and daily ATO PDF exports."""
from __future__ import annotations

from datetime import date
from pathlib import Path

from sqlalchemy.orm import Session, joinedload

from app.models.models import FlightLog, Sortie
from app.services.ops_day import build_day_ops

_TEMPLATE_DIR = Path(__file__).parent.parent / "templates"


def render_brief_sheet_pdf(db: Session, sortie_id: int) -> bytes:
    sortie = (
        db.query(Sortie)
        .options(
            joinedload(Sortie.aircraft),
            joinedload(Sortie.flight_logs).joinedload(FlightLog.person),
        )
        .filter(Sortie.id == sortie_id)
        .first()
    )
    if sortie is None:
        raise ValueError(f"Sortie {sortie_id} not found")

    try:
        from jinja2 import Environment, FileSystemLoader
        from weasyprint import HTML as WeasyprintHTML
    except ImportError as exc:
        raise RuntimeError("PDF generation requires weasyprint and Jinja2") from exc

    crew = [
        {
            "position": fl.crew_position.value.replace("_", " "),
            "name": f"{fl.person.last_name}, {fl.person.first_name}" if fl.person else "",
        }
        for fl in sortie.flight_logs
    ]
    context = {
        "event_code": sortie.event_code or "—",
        "event_type": sortie.event_type or "—",
        "aircraft": sortie.aircraft.side_number if sortie.aircraft else "—",
        "brief_time": sortie.brief_time.strftime("%H%M") if sortie.brief_time else "—",
        "takeoff_time": sortie.takeoff_time.strftime("%H%M") if sortie.takeoff_time else "—",
        "mission_summary": sortie.mission_summary or sortie.notes or "—",
        "comm_plan": sortie.comm_plan or "See SPINS / daily freq card",
        "brief_notes": sortie.brief_sheet_notes or "",
        "ops_status": sortie.ops_status.value if sortie.ops_status else "PLANNED",
        "crew": crew,
    }

    env = Environment(loader=FileSystemLoader(str(_TEMPLATE_DIR)), autoescape=True)
    html = env.get_template("brief_sheet.html").render(**context)
    return WeasyprintHTML(string=html).write_pdf()


def render_ato_pdf(db: Session, ops_date: date) -> bytes:
    day = build_day_ops(db, ops_date)

    try:
        from jinja2 import Environment, FileSystemLoader
        from weasyprint import HTML as WeasyprintHTML
    except ImportError as exc:
        raise RuntimeError("PDF generation requires weasyprint and Jinja2") from exc

    sortie_rows = []
    for s in day["sorties"]:
        takeoff = s["takeoff_time"].strftime("%H%M") if s["takeoff_time"] else "—"
        crew_str = ", ".join(
            f"{c['crew_position']}: {c['person_name']}" for c in s["crew"]
        ) or "TBD"
        sortie_rows.append({
            "event_code": s["event_code"] or "—",
            "aircraft": s["aircraft_side_number"] or "—",
            "takeoff": takeoff,
            "status": s["ops_status"],
            "mission": (s["mission_summary"] or s["event_type"] or "—")[:80],
            "crew": crew_str,
        })

    context = {
        "ops_date": ops_date.strftime("%d %b %Y").upper(),
        "is_published": day["is_published"],
        "sortie_count": day["sortie_count"],
        "airborne_count": day["airborne_count"],
        "watchbill": day["watchbill"],
        "sorties": sortie_rows,
        "publication_remarks": (
            day["publication"]["remarks"] if day.get("publication") else None
        ),
    }

    env = Environment(loader=FileSystemLoader(str(_TEMPLATE_DIR)), autoescape=True)
    html = env.get_template("ato_day.html").render(**context)
    return WeasyprintHTML(string=html).write_pdf()