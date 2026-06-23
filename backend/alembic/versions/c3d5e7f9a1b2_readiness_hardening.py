"""readiness hardening — area config, anchor tasks

Revision ID: c3d5e7f9a1b2
Revises: b2c4d6e8f0a1
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "c3d5e7f9a1b2"
down_revision: Union[str, None] = "b2c4d6e8f0a1"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

_AREA_CONFIGS = [
    ("MOB", "Mobility", 180, 365, '["NIGHT_NVD"]', "[]"),
    ("FSO", "Fleet Support Ops", 180, 365, '["CSTRS_WINCH"]', "[]"),
    ("ASU", "Anti-Surface Warfare", 180, 365, '["CSW", "STRAFE_DRY"]', "[]"),
    ("SOF", "Special Operations Forces", 180, 365, "[]", "[]"),
    ("PR", "Personnel Recovery", 180, 365, "[]", "[]"),
    ("STW", "Strike Warfare", 180, 365, "[]", "[]"),
    ("LOG", "Logistics", 180, 365, "[]", "[]"),
    ("MIW", "Mine Warfare", 180, 365, '["ALMDS_PILOT"]', "[]"),
]

_ANCHOR_CODES = (
    "MOB 203", "MOB 204", "MOB 209",
    "FSO 207", "FSO 209",
    "ASU 201", "ASU 207",
    "SOF 207",
    "PR 201",
    "STW 210",
    "LOG 201",
    "MIW 203", "MIW 205",
)


def upgrade() -> None:
    cap_area = postgresql.ENUM(name="capabilityarea", create_type=False)
    op.create_table(
        "capability_area_configs",
        sa.Column("capability_area", cap_area, primary_key=True),
        sa.Column("label", sa.String(80), nullable=False),
        sa.Column("t1_recency_days", sa.Integer(), nullable=False, server_default="180"),
        sa.Column("t2_recency_days", sa.Integer(), nullable=False, server_default="365"),
        sa.Column("currency_codes", sa.JSON(), nullable=False, server_default="[]"),
        sa.Column("min_qual_codes", sa.JSON(), nullable=False, server_default="[]"),
    )
    op.add_column(
        "cbr_task_options",
        sa.Column("is_anchor_task", sa.Boolean(), nullable=False, server_default="false"),
    )

    conn = op.get_bind()
    for area, label, t1, t2, currencies, quals in _AREA_CONFIGS:
        conn.execute(
            sa.text(
                "INSERT INTO capability_area_configs "
                "(capability_area, label, t1_recency_days, t2_recency_days, currency_codes, min_qual_codes) "
                "VALUES (:area, :label, :t1, :t2, CAST(:currencies AS json), CAST(:quals AS json))"
            ),
            {"area": area, "label": label, "t1": t1, "t2": t2, "currencies": currencies, "quals": quals},
        )

    for code in _ANCHOR_CODES:
        conn.execute(
            sa.text("UPDATE cbr_task_options SET is_anchor_task = true WHERE code = :code"),
            {"code": code},
        )


def downgrade() -> None:
    op.drop_column("cbr_task_options", "is_anchor_task")
    op.drop_table("capability_area_configs")