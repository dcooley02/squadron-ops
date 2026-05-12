"""complete per-crewmember hour categories

Revision ID: b1c3e5a7f9d2
Revises: a0f2e4c6b8d0
Create Date: 2026-05-12 12:00:00.000000

Pass 1B:
  a. Add 10 new per-crewmember hour category columns to flight_logs
  b. Backfill role-hour columns from crew_position
  c. Rename instrument_hours -> actual_instrument_hours
  d. Rename instrument_hours_simulated -> sim_instrument_hours
  e. Drop day_hours from flight_logs
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = 'b1c3e5a7f9d2'
down_revision: Union[str, None] = 'a0f2e4c6b8d0'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Step a: Add 10 new columns
    for col in [
        'total_hours',
        'first_pilot_hours',
        'copilot_hours',
        'ac_commander_hours',
        'mission_commander_hours',
        'instructor_hours',
        'nvg_unaided_hl_hours',
        'nvg_unaided_ll_hours',
        'nvg_tactical_hl_hours',
        'nvg_tactical_ll_hours',
    ]:
        op.add_column('flight_logs', sa.Column(col, sa.Float(), nullable=True, server_default='0.0'))

    # Step b: Backfill role-hour columns from crew_position
    # HAC: ac_commander_hours = hours_logged
    op.execute("""
        UPDATE flight_logs SET
            total_hours        = hours_logged,
            ac_commander_hours = hours_logged,
            first_pilot_hours  = 0.0,
            copilot_hours      = 0.0,
            mission_commander_hours = 0.0,
            instructor_hours   = 0.0
        WHERE crew_position = 'HAC'
    """)
    # H2P: copilot_hours = hours_logged
    op.execute("""
        UPDATE flight_logs SET
            total_hours       = hours_logged,
            copilot_hours     = hours_logged,
            first_pilot_hours = 0.0,
            ac_commander_hours = 0.0,
            mission_commander_hours = 0.0,
            instructor_hours  = 0.0
        WHERE crew_position = 'H2P'
    """)
    # H2P_U: copilot_hours = hours_logged
    op.execute("""
        UPDATE flight_logs SET
            total_hours       = hours_logged,
            copilot_hours     = hours_logged,
            first_pilot_hours = 0.0,
            ac_commander_hours = 0.0,
            mission_commander_hours = 0.0,
            instructor_hours  = 0.0
        WHERE crew_position = 'H2P_U'
    """)
    # CREW_CHIEF, AIRCREW, AWS: role hours all 0
    op.execute("""
        UPDATE flight_logs SET
            total_hours       = hours_logged,
            first_pilot_hours = 0.0,
            copilot_hours     = 0.0,
            ac_commander_hours = 0.0,
            mission_commander_hours = 0.0,
            instructor_hours  = 0.0
        WHERE crew_position IN ('CREW_CHIEF', 'AIRCREW', 'AWS')
    """)
    # NVG subcategories: 0 for all (no source data to distribute)
    op.execute("""
        UPDATE flight_logs SET
            nvg_unaided_hl_hours = 0.0,
            nvg_unaided_ll_hours = 0.0,
            nvg_tactical_hl_hours = 0.0,
            nvg_tactical_ll_hours = 0.0
        WHERE nvg_unaided_hl_hours IS NULL
           OR nvg_unaided_ll_hours IS NULL
           OR nvg_tactical_hl_hours IS NULL
           OR nvg_tactical_ll_hours IS NULL
    """)

    # Step c: Rename instrument_hours -> actual_instrument_hours
    op.alter_column('flight_logs', 'instrument_hours', new_column_name='actual_instrument_hours')

    # Step d: Rename instrument_hours_simulated -> sim_instrument_hours
    op.alter_column('flight_logs', 'instrument_hours_simulated', new_column_name='sim_instrument_hours')

    # Step e: Drop day_hours
    op.drop_column('flight_logs', 'day_hours')


def downgrade() -> None:
    # e': Restore day_hours (empty — accept data loss on downgrade)
    op.add_column('flight_logs', sa.Column('day_hours', sa.Float(), nullable=True, server_default='0.0'))

    # d': Rename back
    op.alter_column('flight_logs', 'sim_instrument_hours', new_column_name='instrument_hours_simulated')

    # c': Rename back
    op.alter_column('flight_logs', 'actual_instrument_hours', new_column_name='instrument_hours')

    # a': Drop the 10 new columns
    for col in [
        'total_hours',
        'first_pilot_hours',
        'copilot_hours',
        'ac_commander_hours',
        'mission_commander_hours',
        'instructor_hours',
        'nvg_unaided_hl_hours',
        'nvg_unaided_ll_hours',
        'nvg_tactical_hl_hours',
        'nvg_tactical_ll_hours',
    ]:
        op.drop_column('flight_logs', col)
