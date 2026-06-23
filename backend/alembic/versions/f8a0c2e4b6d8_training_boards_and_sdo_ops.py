"""training boards and SDO ops fields

Revision ID: f8a0c2e4b6d8
Revises: e4f6b8d0c2a3
Create Date: 2026-06-22 12:00:00.000000
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "f8a0c2e4b6d8"
down_revision: Union[str, None] = "a6b8c0d2e4f5"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _enums():
    sortie_ops = postgresql.ENUM(
        "PLANNED", "PUBLISHED", "BRIEFED", "MANNED", "AIRBORNE", "RECOVERED", "DEBRIEFED",
        name="sortieopsstatus",
        create_type=False,
    )
    board_type = postgresql.ENUM(
        "HAC_BOARD", "INSTRUCTOR_BOARD", "NATOPS_CHECK", "STAN_EVAL",
        name="boardtype",
        create_type=False,
    )
    board_status = postgresql.ENUM(
        "SCHEDULED", "COMPLETED", "CANCELLED", name="boardstatus", create_type=False
    )
    watchbill_role = postgresql.ENUM(
        "SDO", "ODO", "DUTY_PILOT", "DUTY_AIRCREW", "ALERT",
        name="watchbillrole",
        create_type=False,
    )
    return sortie_ops, board_type, board_status, watchbill_role


def upgrade() -> None:
    bind = op.get_bind()
    for name, values in (
        ("sortieopsstatus", ("PLANNED", "PUBLISHED", "BRIEFED", "MANNED", "AIRBORNE", "RECOVERED", "DEBRIEFED")),
        ("boardtype", ("HAC_BOARD", "INSTRUCTOR_BOARD", "NATOPS_CHECK", "STAN_EVAL")),
        ("boardstatus", ("SCHEDULED", "COMPLETED", "CANCELLED")),
        ("watchbillrole", ("SDO", "ODO", "DUTY_PILOT", "DUTY_AIRCREW", "ALERT")),
    ):
        postgresql.ENUM(*values, name=name).create(bind, checkfirst=True)

    sortie_ops, board_type, board_status, watchbill_role = _enums()

    op.create_table(
        "schedule_publications",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("schedule_date", sa.Date(), nullable=False),
        sa.Column("published_at", sa.DateTime(), nullable=False),
        sa.Column("published_by_person_id", sa.Integer(), nullable=True),
        sa.Column("remarks", sa.Text(), nullable=True),
        sa.ForeignKeyConstraint(["published_by_person_id"], ["persons.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("schedule_date"),
    )
    op.create_index("ix_schedule_publications_schedule_date", "schedule_publications", ["schedule_date"])

    op.create_table(
        "watchbill_entries",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("duty_date", sa.Date(), nullable=False),
        sa.Column("role", watchbill_role, nullable=False),
        sa.Column("person_id", sa.Integer(), nullable=False),
        sa.Column("shift_label", sa.String(length=32), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.ForeignKeyConstraint(["person_id"], ["persons.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("duty_date", "role", name="uq_watchbill_date_role"),
    )
    op.create_index("ix_watchbill_entries_duty_date", "watchbill_entries", ["duty_date"])
    op.create_index("ix_watchbill_entries_person_id", "watchbill_entries", ["person_id"])

    op.create_table(
        "board_schedules",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("board_type", board_type, nullable=False),
        sa.Column("scheduled_at", sa.DateTime(), nullable=False),
        sa.Column("examinee_person_id", sa.Integer(), nullable=False),
        sa.Column("instructor_person_id", sa.Integer(), nullable=True),
        sa.Column("syllabus_event_id", sa.Integer(), nullable=True),
        sa.Column("gradecard_id", sa.Integer(), nullable=True),
        sa.Column("sortie_id", sa.Integer(), nullable=True),
        sa.Column("status", board_status, nullable=False, server_default="SCHEDULED"),
        sa.Column("location", sa.String(length=64), nullable=True),
        sa.Column("remarks", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["examinee_person_id"], ["persons.id"]),
        sa.ForeignKeyConstraint(["gradecard_id"], ["gradecards.id"]),
        sa.ForeignKeyConstraint(["instructor_person_id"], ["persons.id"]),
        sa.ForeignKeyConstraint(["sortie_id"], ["sorties.id"]),
        sa.ForeignKeyConstraint(["syllabus_event_id"], ["syllabus_events.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_board_schedules_scheduled_at", "board_schedules", ["scheduled_at"])
    op.create_index("ix_board_schedules_examinee_person_id", "board_schedules", ["examinee_person_id"])
    op.create_index("ix_board_schedules_instructor_person_id", "board_schedules", ["instructor_person_id"])

    op.add_column(
        "sorties",
        sa.Column("ops_status", sortie_ops, nullable=False, server_default="PLANNED"),
    )
    op.add_column("sorties", sa.Column("mission_summary", sa.Text(), nullable=True))
    op.add_column("sorties", sa.Column("comm_plan", sa.Text(), nullable=True))
    op.add_column("sorties", sa.Column("brief_sheet_notes", sa.Text(), nullable=True))
    op.add_column("sorties", sa.Column("schedule_publication_id", sa.Integer(), nullable=True))
    op.create_foreign_key(
        "fk_sorties_schedule_publication",
        "sorties",
        "schedule_publications",
        ["schedule_publication_id"],
        ["id"],
    )
    op.create_index("ix_sorties_schedule_publication_id", "sorties", ["schedule_publication_id"])


def downgrade() -> None:
    op.drop_index("ix_sorties_schedule_publication_id", table_name="sorties")
    op.drop_constraint("fk_sorties_schedule_publication", "sorties", type_="foreignkey")
    op.drop_column("sorties", "schedule_publication_id")
    op.drop_column("sorties", "brief_sheet_notes")
    op.drop_column("sorties", "comm_plan")
    op.drop_column("sorties", "mission_summary")
    op.drop_column("sorties", "ops_status")

    op.drop_index("ix_board_schedules_instructor_person_id", table_name="board_schedules")
    op.drop_index("ix_board_schedules_examinee_person_id", table_name="board_schedules")
    op.drop_index("ix_board_schedules_scheduled_at", table_name="board_schedules")
    op.drop_table("board_schedules")

    op.drop_index("ix_watchbill_entries_person_id", table_name="watchbill_entries")
    op.drop_index("ix_watchbill_entries_duty_date", table_name="watchbill_entries")
    op.drop_table("watchbill_entries")

    op.drop_index("ix_schedule_publications_schedule_date", table_name="schedule_publications")
    op.drop_table("schedule_publications")

    sa.Enum(name="watchbillrole").drop(op.get_bind(), checkfirst=True)
    sa.Enum(name="boardstatus").drop(op.get_bind(), checkfirst=True)
    sa.Enum(name="boardtype").drop(op.get_bind(), checkfirst=True)
    sa.Enum(name="sortieopsstatus").drop(op.get_bind(), checkfirst=True)