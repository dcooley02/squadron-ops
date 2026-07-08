"""SQLAlchemy domain models — boards, schedule publication, watchbill."""
from __future__ import annotations

from sqlalchemy import (
    Column, Integer, String, DateTime, Date, ForeignKey, Enum as SQLEnum, Text, UniqueConstraint,
)
from sqlalchemy.orm import relationship

from app.database import Base
from app.core.time import utc_now
from app.models.enums import *  # noqa: F403

class BoardSchedule(Base):
    """Scheduled training board or check ride."""
    __tablename__ = "board_schedules"

    id = Column(Integer, primary_key=True)
    board_type = Column(SQLEnum(BoardType), nullable=False)
    scheduled_at = Column(DateTime, nullable=False, index=True)
    examinee_person_id = Column(Integer, ForeignKey("persons.id"), nullable=False, index=True)
    instructor_person_id = Column(Integer, ForeignKey("persons.id"), nullable=True, index=True)
    syllabus_event_id = Column(Integer, ForeignKey("syllabus_events.id"), nullable=True, index=True)
    gradecard_id = Column(Integer, ForeignKey("gradecards.id"), nullable=True, index=True)
    sortie_id = Column(Integer, ForeignKey("sorties.id"), nullable=True, index=True)
    status = Column(SQLEnum(BoardStatus), default=BoardStatus.SCHEDULED, nullable=False)
    location = Column(String(64), nullable=True)
    remarks = Column(Text, nullable=True)
    created_at = Column(DateTime, default=utc_now, nullable=False)

    examinee = relationship("Person", foreign_keys=[examinee_person_id])
    instructor = relationship("Person", foreign_keys=[instructor_person_id])
    syllabus_event = relationship("SyllabusEvent")
    gradecard = relationship("Gradecard")
    sortie = relationship("Sortie")

# ---------- SDO schedule publishing (Phase 5) ----------

class SchedulePublication(Base):
    """Locked flight schedule for a given ops day."""
    __tablename__ = "schedule_publications"

    id = Column(Integer, primary_key=True)
    schedule_date = Column(Date, unique=True, nullable=False, index=True)
    published_at = Column(DateTime, nullable=False)
    published_by_person_id = Column(Integer, ForeignKey("persons.id"), nullable=True)
    remarks = Column(Text, nullable=True)

    published_by = relationship("Person")
    sorties = relationship("Sortie", back_populates="schedule_publication")

class WatchbillEntry(Base):
    """Duty roster assignment for a given day."""
    __tablename__ = "watchbill_entries"
    __table_args__ = (
        UniqueConstraint("duty_date", "role", name="uq_watchbill_date_role"),
    )

    id = Column(Integer, primary_key=True)
    duty_date = Column(Date, nullable=False, index=True)
    role = Column(SQLEnum(WatchbillRole), nullable=False)
    person_id = Column(Integer, ForeignKey("persons.id"), nullable=False, index=True)
    shift_label = Column(String(32), nullable=True)
    notes = Column(Text, nullable=True)

    person = relationship("Person")

# ---------- Audit log ----------

