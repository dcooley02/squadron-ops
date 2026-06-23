"""add per-crew landings columns to flight_logs

Revision ID: a6b8c0d2e4f5
Revises: f5a7c9b0e1d2
Create Date: 2026-05-12 22:30:00.000000

Pass 2 / B1:
  Move landing counts from sortie-level to flight_log-level so the logbook
  can report SHARP-parity per-crewmember landings. The sortie-level columns
  stay (treated as the rollup) and continue to be written by the existing
  completion flow.

Backfill:
  - For each sortie, give the HAC crewmember the entire sortie count.
    HACs sign for landings on the deck in NAVFLIR practice; this preserves
    the squadron-wide totals exactly and is conservative for the demo data.
  - Crewmembers other than HAC get zeros.
  - Sorties with no HAC (rare) fall through to leaving all flight_logs at 0;
    the existing sortie-level counts remain for those rows.
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op


revision: str = 'a6b8c0d2e4f5'
down_revision: Union[str, None] = 'f5a7c9b0e1d2'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

_COLS = [
    'landings_day',
    'landings_night',
    'landings_dve_day',
    'landings_dve_night',
    'landings_shipboard_day',
    'landings_shipboard_night',
]


def upgrade() -> None:
    for col in _COLS:
        op.add_column(
            'flight_logs',
            sa.Column(col, sa.Integer(), nullable=False, server_default='0'),
        )

    # Backfill: give the HAC flight_log the full sortie count.
    op.execute(
        """
        UPDATE flight_logs fl
        SET
            landings_day              = COALESCE(s.landings_day, 0),
            landings_night            = COALESCE(s.landings_night, 0),
            landings_dve_day          = COALESCE(s.landings_dve_day, 0),
            landings_dve_night        = COALESCE(s.landings_dve_night, 0),
            landings_shipboard_day    = COALESCE(s.landings_shipboard_day, 0),
            landings_shipboard_night  = COALESCE(s.landings_shipboard_night, 0)
        FROM sorties s
        WHERE fl.sortie_id = s.id
          AND fl.crew_position = 'HAC'
        """
    )


def downgrade() -> None:
    for col in _COLS:
        op.drop_column('flight_logs', col)
