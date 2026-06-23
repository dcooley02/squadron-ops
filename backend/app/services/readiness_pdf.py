"""Exportable WTM readiness brief (PDF)."""
from __future__ import annotations

from pathlib import Path

from sqlalchemy.orm import Session

from app.services.readiness import build_squadron_readiness

_TEMPLATE_DIR = Path(__file__).parent.parent / "templates"


def render_readiness_brief_pdf(db: Session) -> bytes:
    data = build_squadron_readiness(db)
    try:
        from jinja2 import Environment, FileSystemLoader
        from weasyprint import HTML as WeasyprintHTML
    except ImportError as exc:
        raise RuntimeError("PDF generation requires weasyprint and Jinja2") from exc

    context = {
        "as_of_date": data["as_of_date"].isoformat(),
        "squadron_overall": data["squadron_overall_rating"],
        "aircrew_overall": data.get("aircrew_overall_rating"),
        "pilots_rated": data["pilots_rated"],
        "aircrew_rated": data.get("aircrew_rated", 0),
        "areas": data["areas"],
        "persons": data["persons"],
        "aircrew": data.get("aircrew", []),
    }
    env = Environment(loader=FileSystemLoader(str(_TEMPLATE_DIR)), autoescape=True)
    html = env.get_template("readiness_brief.html").render(**context)
    return WeasyprintHTML(string=html).write_pdf()