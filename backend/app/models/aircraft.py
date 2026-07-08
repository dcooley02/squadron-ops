"""SQLAlchemy domain models — aircraft."""
from __future__ import annotations

from sqlalchemy import (
    Column, Integer, String, Float, Enum as SQLEnum, Text,
)
from sqlalchemy.orm import relationship

from app.database import Base
from app.models.enums import *  # noqa: F403

class Aircraft(Base):
    """A single MH-60S airframe, identified by BuNo."""
    __tablename__ = "aircraft"
    id = Column(Integer, primary_key=True)
    bureau_number = Column(String, unique=True, nullable=False, index=True)
    side_number = Column(String)
    type_model_series = Column(String, default="MH-60S", nullable=False)
    total_airframe_hours = Column(Float, default=0.0, nullable=False)
    hours_since_phase = Column(Float, default=0.0, nullable=False)
    phase_interval = Column(Float, default=200.0, nullable=False)
    status = Column(SQLEnum(AircraftStatus), default=AircraftStatus.FMC, nullable=False)
    manual_status_override = Column(SQLEnum(AircraftStatus), nullable=True)
    notes = Column(Text)

    discrepancies = relationship("Discrepancy", back_populates="aircraft", cascade="all, delete-orphan", foreign_keys="Discrepancy.aircraft_id")
    inspections = relationship("AircraftInspection", back_populates="aircraft", cascade="all, delete-orphan")
    sorties = relationship("Sortie", back_populates="aircraft")
    mafs = relationship("Maf", back_populates="aircraft", cascade="all, delete-orphan")
    work_orders = relationship("WorkOrder", back_populates="aircraft", cascade="all, delete-orphan")
    logbook_entries = relationship("AircraftLogbookEntry", back_populates="aircraft", cascade="all, delete-orphan")

# ---------- Qualifications & currencies ----------

