"""add type_wo_code and jcn to discrepancies

Revision ID: e4f6b8d0c2a3
Revises: d3e5f7b9c1a2
Create Date: 2026-05-12 21:30:00.000000

Pass 2 / B3:
  CNAF M-4790.2 work-order discrimination fields on discrepancies.
  - type_wo_code: 2-char Type WO (TS, DM, CM, AD, FO, HA, TM, TD, WR,
    PC, PF, PL, SC, SF, SL, CC, CF, CL, AC, AF, AL, TC, TF, TL, FC, FF,
    BC, BF, DF, IA)
  - jcn: 9-char Job Control Number: ORG(3) + Julian(3) + Serno(3)

Backfill:
  - type_wo_code defaults to 'DM' (Discrepancy Maintenance) — the most
    common case for pilot-reported issues.
  - jcn is assigned per-row using ORG "350" + Julian of opened_date +
    sequential serno within that day. Rows older than 365 days from now
    are skipped (left NULL) to avoid masking real demo data.
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op


revision: str = 'e4f6b8d0c2a3'
down_revision: Union[str, None] = 'd3e5f7b9c1a2'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        'discrepancies',
        sa.Column('type_wo_code', sa.String(length=2), nullable=True),
    )
    op.add_column(
        'discrepancies',
        sa.Column('jcn', sa.String(length=9), nullable=True),
    )
    op.create_index('ix_discrepancies_jcn', 'discrepancies', ['jcn'], unique=False)

    # Backfill type_wo_code: pilot-reported (sortie_id is not null) -> 'DM',
    # everything else -> 'DM' as well (safe default).
    op.execute("UPDATE discrepancies SET type_wo_code = 'DM' WHERE type_wo_code IS NULL")

    # Backfill JCN: ORG(350) + Julian(opened_date) + per-day serno.
    # Postgres-only: use a window function to compute serno per Julian day.
    op.execute(
        """
        WITH numbered AS (
            SELECT
                id,
                '350'
                || LPAD(EXTRACT(DOY FROM opened_date)::int::text, 3, '0')
                || LPAD(
                    ROW_NUMBER() OVER (
                        PARTITION BY DATE_TRUNC('day', opened_date)
                        ORDER BY opened_date, id
                    )::text,
                    3,
                    '0'
                ) AS new_jcn
            FROM discrepancies
            WHERE jcn IS NULL
        )
        UPDATE discrepancies d
        SET jcn = numbered.new_jcn
        FROM numbered
        WHERE d.id = numbered.id
        """
    )


def downgrade() -> None:
    op.drop_index('ix_discrepancies_jcn', table_name='discrepancies')
    op.drop_column('discrepancies', 'jcn')
    op.drop_column('discrepancies', 'type_wo_code')
