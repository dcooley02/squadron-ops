"""ORM models package — import submodules so SQLAlchemy mappers register."""
from app.models.enums import *  # noqa: F403
from app.models.person import *  # noqa: F403
from app.models.aircraft import *  # noqa: F403
from app.models.readiness import *  # noqa: F403
from app.models.syllabus import *  # noqa: F403
from app.models.sortie import *  # noqa: F403
from app.models.maintenance import *  # noqa: F403
from app.models.ops import *  # noqa: F403
from app.models.audit import *  # noqa: F403
