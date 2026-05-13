"""add crew_qual_code (A-Z) to flight_logs

Revision ID: d3e5f7b9c1a2
Revises: c2d4f6a8b0e1
Create Date: 2026-05-12 21:00:00.000000

Pass 2 / B2:
  Add a per-crewmember single-letter qualification code (CNAF M-3710.7) to
  flight_logs. Backfill from crew_position with a coarse mapping:
    HAC        -> E (Aircraft Commander)
    H2P        -> A (First Pilot)
    H2P_U      -> B (Copilot / under instruction)
    CREW_CHIEF -> U (Crew Chief)
    AIRCREW    -> W (Helicopter Aircrewman)
    AWS        -> Z (Rescue Swimmer)
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op


revision: str = 'd3e5f7b9c1a2'
down_revision: Union[str, None] = 'c2d4f6a8b0e1'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        'flight_logs',
        sa.Column('crew_qual_code', sa.String(length=1), nullable=True),
    )
    # Backfill from crew_position; cast enum to text for the comparison
    op.execute(
        """
        UPDATE flight_logs SET crew_qual_code = CASE crew_position::text
            WHEN 'HAC'        THEN 'E'
            WHEN 'H2P'        THEN 'A'
            WHEN 'H2P_U'      THEN 'B'
            WHEN 'CREW_CHIEF' THEN 'U'
            WHEN 'AIRCREW'    THEN 'W'
            WHEN 'AWS'        THEN 'Z'
            ELSE NULL
        END
        """
    )


def downgrade() -> None:
    op.drop_column('flight_logs', 'crew_qual_code')
