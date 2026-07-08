"""SQLAlchemy domain models — maintenance / 4790 chain."""
from __future__ import annotations

from sqlalchemy import (
    Column, Integer, String, DateTime, Date, Float, Boolean,
    ForeignKey, Enum as SQLEnum, Text, UniqueConstraint,
)
from sqlalchemy.orm import relationship

from app.database import Base
from app.core.time import utc_now
from app.models.enums import *  # noqa: F403

class Discrepancy(Base):
    """An open or closed maintenance issue against an aircraft."""
    __tablename__ = "discrepancies"
    id = Column(Integer, primary_key=True)
    aircraft_id = Column(Integer, ForeignKey("aircraft.id"), nullable=False, index=True)
    description = Column(Text, nullable=False)
    severity = Column(SQLEnum(DiscrepancySeverity), default=DiscrepancySeverity.MINOR, nullable=False)
    opened_date = Column(DateTime, default=utc_now, nullable=False)
    closed_date = Column(DateTime)
    is_open = Column(Boolean, default=True, nullable=False, index=True)
    notes = Column(Text)
    # Batch 5a NAMP fields
    maf_number = Column(String, nullable=True, index=True)
    work_status = Column(SQLEnum(DiscrepancyWorkStatus), default=DiscrepancyWorkStatus.OPEN, nullable=False)
    system_affected = Column(String, nullable=True)
    corrective_action = Column(Text, nullable=True)
    # CNAF M-4790.2 work-order discrimination (denormalized for legacy reads)
    type_wo_code = Column(String(2), nullable=True)
    jcn = Column(String(9), nullable=True, index=True)

    # New in flight-logging
    sortie_id = Column(Integer, ForeignKey("sorties.id"), nullable=True, index=True)
    reported_by_person_id = Column(Integer, ForeignKey("persons.id"), nullable=True)

    aircraft = relationship("Aircraft", back_populates="discrepancies", foreign_keys=[aircraft_id])
    sortie = relationship("Sortie", back_populates="discrepancies_filed", foreign_keys=[sortie_id])
    reported_by = relationship("Person", back_populates="discrepancies_reported", foreign_keys=[reported_by_person_id])
    maf_record = relationship("Maf", back_populates="discrepancy", uselist=False)
    work_order = relationship("WorkOrder", back_populates="discrepancy", uselist=False)

class WorkCenter(Base):
    """Maintenance work center routing per 4790 job control."""
    __tablename__ = "work_centers"
    id = Column(Integer, primary_key=True)
    code = Column(String(8), unique=True, nullable=False, index=True)
    name = Column(String(80), nullable=False)
    description = Column(Text, nullable=True)

    work_orders = relationship("WorkOrder", back_populates="work_center")

class Maf(Base):
    """Maintenance Action Form — first-class 4790.2 record."""
    __tablename__ = "mafs"
    id = Column(Integer, primary_key=True)
    maf_number = Column(String(20), unique=True, nullable=False, index=True)
    aircraft_id = Column(Integer, ForeignKey("aircraft.id"), nullable=False, index=True)
    discrepancy_id = Column(Integer, ForeignKey("discrepancies.id"), nullable=True, unique=True, index=True)
    reported_by_person_id = Column(Integer, ForeignKey("persons.id"), nullable=True)
    system_affected = Column(String, nullable=True)
    severity = Column(SQLEnum(DiscrepancySeverity), nullable=False)
    status = Column(SQLEnum(MafStatus), default=MafStatus.OPEN, nullable=False)
    opened_date = Column(DateTime, default=utc_now, nullable=False)
    closed_date = Column(DateTime, nullable=True)
    notes = Column(Text, nullable=True)

    aircraft = relationship("Aircraft", back_populates="mafs")
    discrepancy = relationship("Discrepancy", back_populates="maf_record", foreign_keys=[discrepancy_id])
    work_orders = relationship("WorkOrder", back_populates="maf")

class WorkOrder(Base):
    """Job control work order — JCN, type WO, work center routing."""
    __tablename__ = "work_orders"
    id = Column(Integer, primary_key=True)
    jcn = Column(String(9), unique=True, nullable=False, index=True)
    type_wo_code = Column(String(2), nullable=False, default="DM")
    aircraft_id = Column(Integer, ForeignKey("aircraft.id"), nullable=False, index=True)
    maf_id = Column(Integer, ForeignKey("mafs.id"), nullable=True, index=True)
    discrepancy_id = Column(Integer, ForeignKey("discrepancies.id"), nullable=True, unique=True, index=True)
    work_center_id = Column(Integer, ForeignKey("work_centers.id"), nullable=True, index=True)
    status = Column(SQLEnum(DiscrepancyWorkStatus), default=DiscrepancyWorkStatus.OPEN, nullable=False)
    corrective_action = Column(Text, nullable=True)
    opened_date = Column(DateTime, default=utc_now, nullable=False)
    assigned_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)

    aircraft = relationship("Aircraft", back_populates="work_orders")
    maf = relationship("Maf", back_populates="work_orders")
    discrepancy = relationship("Discrepancy", back_populates="work_order", foreign_keys=[discrepancy_id])
    work_center = relationship("WorkCenter", back_populates="work_orders")
    qa_signoffs = relationship("QaSignoff", back_populates="work_order", cascade="all, delete-orphan")
    parts_requests = relationship("PartsRequest", back_populates="work_order", cascade="all, delete-orphan")

class QaSignoff(Base):
    """QA inspector signoff on a work order before safe-for-flight release."""
    __tablename__ = "qa_signoffs"
    id = Column(Integer, primary_key=True)
    work_order_id = Column(Integer, ForeignKey("work_orders.id"), nullable=False, index=True)
    aircraft_id = Column(Integer, ForeignKey("aircraft.id"), nullable=False, index=True)
    inspector_person_id = Column(Integer, ForeignKey("persons.id"), nullable=False)
    signed_at = Column(DateTime, default=utc_now, nullable=False)
    notes = Column(Text, nullable=True)
    release_eligible = Column(Boolean, default=True, nullable=False)

    work_order = relationship("WorkOrder", back_populates="qa_signoffs")
    inspector = relationship("Person", foreign_keys=[inspector_person_id])

class PartsRequest(Base):
    """Parts requisition linked to AWP work orders (BCM when on shelf)."""
    __tablename__ = "parts_requests"
    id = Column(Integer, primary_key=True)
    work_order_id = Column(Integer, ForeignKey("work_orders.id"), nullable=False, index=True)
    nsn = Column(String(20), nullable=True)
    part_name = Column(String(120), nullable=False)
    qty_ordered = Column(Integer, default=1, nullable=False)
    status = Column(SQLEnum(PartsRequestStatus), default=PartsRequestStatus.REQUESTED, nullable=False)
    expected_delivery_date = Column(Date, nullable=True)
    bcm_on_shelf = Column(Boolean, default=False, nullable=False)

    work_order = relationship("WorkOrder", back_populates="parts_requests")

class AircraftLogbookEntry(Base):
    """Aircraft logbook: ASR, MSR, equipment history per 4790."""
    __tablename__ = "aircraft_logbook_entries"
    id = Column(Integer, primary_key=True)
    aircraft_id = Column(Integer, ForeignKey("aircraft.id"), nullable=False, index=True)
    entry_type = Column(SQLEnum(LogbookEntryType), nullable=False)
    entry_date = Column(DateTime, default=utc_now, nullable=False)
    hours_at_entry = Column(Float, nullable=True)
    title = Column(String(120), nullable=False)
    description = Column(Text, nullable=True)
    work_order_id = Column(Integer, ForeignKey("work_orders.id"), nullable=True, index=True)
    sortie_id = Column(Integer, ForeignKey("sorties.id"), nullable=True, index=True)
    created_by_person_id = Column(Integer, ForeignKey("persons.id"), nullable=True)

    aircraft = relationship("Aircraft", back_populates="logbook_entries")
    work_order = relationship("WorkOrder")
    sortie = relationship("Sortie")
    created_by = relationship("Person", foreign_keys=[created_by_person_id])

# ---------- Inspection catalog ----------

class InspectionType(Base):
    """Catalog of recurring maintenance inspection definitions."""
    __tablename__ = "inspection_types"
    id = Column(Integer, primary_key=True)
    code = Column(String, unique=True, nullable=False, index=True)
    name = Column(String, nullable=False)
    periodicity_days = Column(Integer, nullable=True)
    periodicity_hours = Column(Float, nullable=True)
    description = Column(Text, nullable=True)
    is_downing_when_overdue = Column(Boolean, default=True, nullable=False)

    inspections = relationship("AircraftInspection", back_populates="inspection_type")

class AircraftInspection(Base):
    """Per-aircraft tracking row — one per (aircraft, inspection_type)."""
    __tablename__ = "aircraft_inspections"
    __table_args__ = (
        UniqueConstraint("aircraft_id", "inspection_type_id", name="uq_aircraft_inspection_type"),
    )
    id = Column(Integer, primary_key=True)
    aircraft_id = Column(Integer, ForeignKey("aircraft.id", ondelete="CASCADE"), nullable=False, index=True)
    inspection_type_id = Column(Integer, ForeignKey("inspection_types.id"), nullable=False, index=True)
    last_completed_date = Column(Date, nullable=True)
    last_completed_hours = Column(Float, nullable=True)
    next_due_date = Column(Date, nullable=True)
    next_due_hours = Column(Float, nullable=True)
    last_completion_notes = Column(Text, nullable=True)

    aircraft = relationship("Aircraft", back_populates="inspections")
    inspection_type = relationship("InspectionType", back_populates="inspections")

# ---------- Gradecard templates ----------

