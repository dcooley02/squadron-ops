"""SHARP-style gradecard PDF export."""
from __future__ import annotations

from pathlib import Path

from sqlalchemy.orm import Session, joinedload

from app.models.models import Gradecard, GradecardLineItemResult, Person, SyllabusEvent

_TEMPLATE_DIR = Path(__file__).parent.parent / "templates"

FOUR_TIER_LABELS = {
    "UNSAT_1_0": "1.0 Unsat",
    "BELOW_STANDARD_2_0": "2.0 Below Std",
    "STANDARD_3_0": "3.0 Standard",
    "EXCEPTIONAL_4_0": "4.0 Exceptional",
}

SECTION_LABELS = {
    "PLANNING_BRIEFING": "Planning / Briefing",
    "PRELAUNCH": "Prelaunch",
    "ENROUTE": "Enroute",
    "EXECUTION": "Execution",
    "COMMUNICATION": "Communication",
    "GENERAL_FLIGHT_CONDUCT": "General Flight Conduct",
    "DEBRIEF": "Debrief",
}


def render_gradecard_pdf(db: Session, gradecard_id: int) -> bytes:
    gc = (
        db.query(Gradecard)
        .options(
            joinedload(Gradecard.person),
            joinedload(Gradecard.instructor),
            joinedload(Gradecard.syllabus_event),
            joinedload(Gradecard.line_item_results).joinedload(GradecardLineItemResult.line_item),
        )
        .filter(Gradecard.id == gradecard_id)
        .first()
    )
    if gc is None:
        raise ValueError(f"Gradecard {gradecard_id} not found")

    try:
        from jinja2 import Environment, FileSystemLoader
        from weasyprint import HTML as WeasyprintHTML
    except ImportError as exc:
        raise RuntimeError(
            "PDF generation requires weasyprint and Jinja2. "
            "On macOS: brew install pango gdk-pixbuf libffi"
        ) from exc

    event: SyllabusEvent | None = gc.syllabus_event
    sections: dict[str, list] = {}
    for result in sorted(gc.line_item_results, key=lambda r: r.line_item.display_order):
        sec = result.line_item.section.value
        score = ""
        if result.waived:
            score = "WAIVED"
        elif gc.grading_scheme.value == "FOUR_TIER" and result.four_tier_score:
            score = FOUR_TIER_LABELS.get(result.four_tier_score.value, result.four_tier_score.value)
        elif result.completion_status:
            score = result.completion_status.value.replace("_", " ").title()

        sections.setdefault(sec, []).append({
            "name": result.line_item.item_name,
            "critical": result.line_item.is_critical,
            "required": result.line_item.is_required,
            "score": score,
            "remarks": result.remarks or "",
        })

    section_rows = [
        {"key": k, "label": SECTION_LABELS.get(k, k), "items": sections[k]}
        for k in sorted(sections.keys(), key=lambda x: list(SECTION_LABELS).index(x) if x in SECTION_LABELS else 99)
    ]

    student = gc.person
    instructor = gc.instructor
    context = {
        "gradecard_id": gc.id,
        "event_code": event.event_code if event else "—",
        "event_name": event.name if event else "—",
        "student_name": f"{student.last_name}, {student.first_name}" if student else "",
        "student_rank": student.rank if student else "",
        "instructor_name": (
            f"{instructor.last_name}, {instructor.first_name}" if instructor else "—"
        ),
        "card_date": gc.card_date.strftime("%d %b %Y").upper(),
        "overall_status": gc.overall_status.value.replace("_", " "),
        "grading_scheme": gc.grading_scheme.value.replace("_", " "),
        "remarks": gc.remarks or "",
        "sections": section_rows,
    }

    env = Environment(loader=FileSystemLoader(str(_TEMPLATE_DIR)), autoescape=True)
    html = env.get_template("gradecard.html").render(**context)
    return WeasyprintHTML(string=html).write_pdf()