"""Backward-compatible model imports.

Prefer ``from app.models import Person`` going forward. This module re-exports
all domain models so existing ``from app.models.models import ...`` keeps working.
"""
from app.models.enums import *  # noqa: F403
from app.models.person import *  # noqa: F403
from app.models.aircraft import *  # noqa: F403
from app.models.readiness import *  # noqa: F403
from app.models.syllabus import *  # noqa: F403
from app.models.sortie import *  # noqa: F403
from app.models.maintenance import *  # noqa: F403
from app.models.ops import *  # noqa: F403
from app.models.audit import *  # noqa: F403
