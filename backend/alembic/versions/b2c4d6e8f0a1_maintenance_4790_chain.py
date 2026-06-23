"""maintenance 4790 chain — MAF, work orders, logbook

Revision ID: b2c4d6e8f0a1
Revises: f8a0c2e4b6d8
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "b2c4d6e8f0a1"
down_revision: Union[str, None] = "f8a0c2e4b6d8"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _create_enums():
    for name, values in (
        ("mafstatus", ("OPEN", "IN_WORK", "COMPLETED", "CLOSED")),
        ("partsrequeststatus", ("REQUESTED", "ORDERED", "RECEIVED", "BCM")),
        ("logbookentrytype", ("ASR", "MSR", "EQUIPMENT_CHANGE", "QA_RELEASE", "PHASE_INSPECTION", "DISCREPANCY")),
    ):
        postgresql.ENUM(*values, name=name).create(op.get_bind(), checkfirst=True)


def upgrade() -> None:
    _create_enums()
    disc_ws = postgresql.ENUM(name="discrepancyworkstatus", create_type=False)
    disc_sev = postgresql.ENUM(name="discrepancyseverity", create_type=False)
    maf_status = postgresql.ENUM("OPEN", "IN_WORK", "COMPLETED", "CLOSED", name="mafstatus", create_type=False)
    parts_status = postgresql.ENUM("REQUESTED", "ORDERED", "RECEIVED", "BCM", name="partsrequeststatus", create_type=False)
    log_type = postgresql.ENUM(
        "ASR", "MSR", "EQUIPMENT_CHANGE", "QA_RELEASE", "PHASE_INSPECTION", "DISCREPANCY",
        name="logbookentrytype", create_type=False,
    )

    op.create_table(
        "work_centers",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("code", sa.String(8), nullable=False),
        sa.Column("name", sa.String(80), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
    )
    op.create_index("ix_work_centers_code", "work_centers", ["code"], unique=True)

    op.create_table(
        "mafs",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("maf_number", sa.String(20), nullable=False),
        sa.Column("aircraft_id", sa.Integer(), sa.ForeignKey("aircraft.id"), nullable=False),
        sa.Column("discrepancy_id", sa.Integer(), sa.ForeignKey("discrepancies.id"), nullable=True),
        sa.Column("reported_by_person_id", sa.Integer(), sa.ForeignKey("persons.id"), nullable=True),
        sa.Column("system_affected", sa.String(), nullable=True),
        sa.Column("severity", disc_sev, nullable=False),
        sa.Column("status", maf_status, nullable=False),
        sa.Column("opened_date", sa.DateTime(), nullable=False),
        sa.Column("closed_date", sa.DateTime(), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
    )
    op.create_index("ix_mafs_maf_number", "mafs", ["maf_number"], unique=True)
    op.create_index("ix_mafs_aircraft_id", "mafs", ["aircraft_id"])
    op.create_index("ix_mafs_discrepancy_id", "mafs", ["discrepancy_id"], unique=True)

    op.create_table(
        "work_orders",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("jcn", sa.String(9), nullable=False),
        sa.Column("type_wo_code", sa.String(2), nullable=False),
        sa.Column("aircraft_id", sa.Integer(), sa.ForeignKey("aircraft.id"), nullable=False),
        sa.Column("maf_id", sa.Integer(), sa.ForeignKey("mafs.id"), nullable=True),
        sa.Column("discrepancy_id", sa.Integer(), sa.ForeignKey("discrepancies.id"), nullable=True),
        sa.Column("work_center_id", sa.Integer(), sa.ForeignKey("work_centers.id"), nullable=True),
        sa.Column("status", disc_ws, nullable=False),
        sa.Column("corrective_action", sa.Text(), nullable=True),
        sa.Column("opened_date", sa.DateTime(), nullable=False),
        sa.Column("assigned_at", sa.DateTime(), nullable=True),
        sa.Column("completed_at", sa.DateTime(), nullable=True),
    )
    op.create_index("ix_work_orders_jcn", "work_orders", ["jcn"], unique=True)
    op.create_index("ix_work_orders_aircraft_id", "work_orders", ["aircraft_id"])
    op.create_index("ix_work_orders_discrepancy_id", "work_orders", ["discrepancy_id"], unique=True)

    op.create_table(
        "qa_signoffs",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("work_order_id", sa.Integer(), sa.ForeignKey("work_orders.id"), nullable=False),
        sa.Column("aircraft_id", sa.Integer(), sa.ForeignKey("aircraft.id"), nullable=False),
        sa.Column("inspector_person_id", sa.Integer(), sa.ForeignKey("persons.id"), nullable=False),
        sa.Column("signed_at", sa.DateTime(), nullable=False),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("release_eligible", sa.Boolean(), nullable=False, server_default="true"),
    )
    op.create_index("ix_qa_signoffs_work_order_id", "qa_signoffs", ["work_order_id"])

    op.create_table(
        "parts_requests",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("work_order_id", sa.Integer(), sa.ForeignKey("work_orders.id"), nullable=False),
        sa.Column("nsn", sa.String(20), nullable=True),
        sa.Column("part_name", sa.String(120), nullable=False),
        sa.Column("qty_ordered", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("status", parts_status, nullable=False),
        sa.Column("expected_delivery_date", sa.Date(), nullable=True),
        sa.Column("bcm_on_shelf", sa.Boolean(), nullable=False, server_default="false"),
    )
    op.create_index("ix_parts_requests_work_order_id", "parts_requests", ["work_order_id"])

    op.create_table(
        "aircraft_logbook_entries",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("aircraft_id", sa.Integer(), sa.ForeignKey("aircraft.id"), nullable=False),
        sa.Column("entry_type", log_type, nullable=False),
        sa.Column("entry_date", sa.DateTime(), nullable=False),
        sa.Column("hours_at_entry", sa.Float(), nullable=True),
        sa.Column("title", sa.String(120), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("work_order_id", sa.Integer(), sa.ForeignKey("work_orders.id"), nullable=True),
        sa.Column("sortie_id", sa.Integer(), sa.ForeignKey("sorties.id"), nullable=True),
        sa.Column("created_by_person_id", sa.Integer(), sa.ForeignKey("persons.id"), nullable=True),
    )
    op.create_index("ix_aircraft_logbook_entries_aircraft_id", "aircraft_logbook_entries", ["aircraft_id"])

    # Seed work centers
    op.execute(
        sa.text(
            "INSERT INTO work_centers (code, name, description) VALUES "
            "('AF', 'Airframes', 'Structural and airframe systems'), "
            "('AV', 'Avionics', 'Communications, navigation, mission systems'), "
            "('PP', 'Powerplant', 'Engines, transmission, rotors'), "
            "('QA', 'Quality Assurance', 'Inspection and release'), "
            "('SE', 'Support Equipment', 'Ground support and SE')"
        )
    )

    # Backfill MAF + work order from existing discrepancies
    conn = op.get_bind()
    discs = conn.execute(
        sa.text(
            "SELECT id, aircraft_id, maf_number, jcn, type_wo_code, severity, system_affected, "
            "work_status, corrective_action, opened_date, closed_date, reported_by_person_id, notes "
            "FROM discrepancies WHERE maf_number IS NOT NULL"
        )
    ).fetchall()

    for row in discs:
        maf_status_val = "CLOSED" if row.closed_date else (
            "COMPLETED" if row.work_status == "COMPLETED" else (
                "IN_WORK" if row.work_status in ("IN_WORK", "AWP", "AWM") else "OPEN"
            )
        )
        maf_id = conn.execute(
            sa.text(
                "INSERT INTO mafs (maf_number, aircraft_id, discrepancy_id, reported_by_person_id, "
                "system_affected, severity, status, opened_date, closed_date, notes) "
                "VALUES (:maf_number, :aircraft_id, :disc_id, :reporter, :system, :severity, "
                ":status, :opened, :closed, :notes) RETURNING id"
            ),
            {
                "maf_number": row.maf_number,
                "aircraft_id": row.aircraft_id,
                "disc_id": row.id,
                "reporter": row.reported_by_person_id,
                "system": row.system_affected,
                "severity": row.severity,
                "status": maf_status_val,
                "opened": row.opened_date,
                "closed": row.closed_date,
                "notes": row.notes,
            },
        ).scalar()
        if row.jcn:
            conn.execute(
                sa.text(
                    "INSERT INTO work_orders (jcn, type_wo_code, aircraft_id, maf_id, discrepancy_id, "
                    "status, corrective_action, opened_date, completed_at) "
                    "VALUES (:jcn, :type_wo, :aircraft_id, :maf_id, :disc_id, :status, :corrective, "
                    ":opened, :completed)"
                ),
                {
                    "jcn": row.jcn,
                    "type_wo": row.type_wo_code or "DM",
                    "aircraft_id": row.aircraft_id,
                    "maf_id": maf_id,
                    "disc_id": row.id,
                    "status": row.work_status,
                    "corrective": row.corrective_action,
                    "opened": row.opened_date,
                    "completed": row.closed_date,
                },
            )


def downgrade() -> None:
    op.drop_table("aircraft_logbook_entries")
    op.drop_table("parts_requests")
    op.drop_table("qa_signoffs")
    op.drop_table("work_orders")
    op.drop_table("mafs")
    op.drop_table("work_centers")
    for name in ("logbookentrytype", "partsrequeststatus", "mafstatus"):
        postgresql.ENUM(name=name).drop(op.get_bind(), checkfirst=True)