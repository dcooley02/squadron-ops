"""add logbook fields, sortie legs, and instrument approaches

Revision ID: 8c4e6a1f3d2b
Revises: 7b3d5f8c2e1a
Create Date: 2026-05-11 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = '8c4e6a1f3d2b'
down_revision: Union[str, None] = '7b3d5f8c2e1a'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ── New enum types ────────────────────────────────────────────────────────
    op.execute(
        "CREATE TYPE approachtype AS ENUM "
        "('ILS', 'GPS', 'RNAV', 'TACAN', 'VOR', 'PAR', 'ASR', 'ENROUTE')"
    )
    op.execute(
        "CREATE TYPE approachconditions AS ENUM ('ACTUAL', 'SIMULATED')"
    )

    # ── New columns on sorties ────────────────────────────────────────────────
    op.add_column('sorties',
        sa.Column('instrument_hours_simulated', sa.Float(), nullable=False, server_default='0.0'))
    op.add_column('sorties',
        sa.Column('landings_shipboard_day', sa.Integer(), nullable=True))
    op.add_column('sorties',
        sa.Column('landings_shipboard_night', sa.Integer(), nullable=True))
    op.add_column('sorties',
        sa.Column('departure_location', sa.String(16), nullable=True))
    op.add_column('sorties',
        sa.Column('arrival_location', sa.String(16), nullable=True))

    # ── New column on flight_logs ─────────────────────────────────────────────
    op.add_column('flight_logs',
        sa.Column('special_crew_time_hours', sa.Float(), nullable=False, server_default='0.0'))

    # ── sortie_legs table ─────────────────────────────────────────────────────
    op.create_table(
        'sortie_legs',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('sortie_id', sa.Integer(), nullable=False),
        sa.Column('leg_number', sa.Integer(), nullable=False),
        sa.Column('departure_icao', sa.String(16), nullable=False),
        sa.Column('arrival_icao', sa.String(16), nullable=False),
        sa.Column('takeoff_time', sa.DateTime(), nullable=True),
        sa.Column('land_time', sa.DateTime(), nullable=True),
        sa.Column('duration_hours', sa.Float(), nullable=True),
        sa.ForeignKeyConstraint(['sortie_id'], ['sorties.id']),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('sortie_id', 'leg_number', name='uq_sortie_leg_number'),
    )
    op.create_index(op.f('ix_sortie_legs_sortie_id'), 'sortie_legs', ['sortie_id'], unique=False)

    # ── instrument_approaches table ───────────────────────────────────────────
    op.create_table(
        'instrument_approaches',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('flight_log_id', sa.Integer(), nullable=False),
        sa.Column('sortie_id', sa.Integer(), nullable=False),
        sa.Column('approach_type',
                  postgresql.ENUM('ILS', 'GPS', 'RNAV', 'TACAN', 'VOR', 'PAR', 'ASR', 'ENROUTE',
                                  name='approachtype', create_type=False),
                  nullable=False),
        sa.Column('actual_or_simulated',
                  postgresql.ENUM('ACTUAL', 'SIMULATED',
                                  name='approachconditions', create_type=False),
                  nullable=False),
        sa.Column('airport_icao', sa.String(16), nullable=False),
        sa.Column('runway', sa.String(10), nullable=True),
        sa.Column('remarks', sa.Text(), nullable=True),
        sa.Column('logged_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['flight_log_id'], ['flight_logs.id']),
        sa.ForeignKeyConstraint(['sortie_id'], ['sorties.id']),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_instrument_approaches_flight_log_id'),
                    'instrument_approaches', ['flight_log_id'], unique=False)
    op.create_index(op.f('ix_instrument_approaches_sortie_id'),
                    'instrument_approaches', ['sortie_id'], unique=False)


def downgrade() -> None:
    # ── Drop tables ───────────────────────────────────────────────────────────
    op.drop_index(op.f('ix_instrument_approaches_sortie_id'), table_name='instrument_approaches')
    op.drop_index(op.f('ix_instrument_approaches_flight_log_id'), table_name='instrument_approaches')
    op.drop_table('instrument_approaches')

    op.drop_index(op.f('ix_sortie_legs_sortie_id'), table_name='sortie_legs')
    op.drop_table('sortie_legs')

    # ── Drop added columns ────────────────────────────────────────────────────
    op.drop_column('flight_logs', 'special_crew_time_hours')
    op.drop_column('sorties', 'arrival_location')
    op.drop_column('sorties', 'departure_location')
    op.drop_column('sorties', 'landings_shipboard_night')
    op.drop_column('sorties', 'landings_shipboard_day')
    op.drop_column('sorties', 'instrument_hours_simulated')

    # ── Drop enum types ───────────────────────────────────────────────────────
    op.execute("DROP TYPE IF EXISTS approachconditions")
    op.execute("DROP TYPE IF EXISTS approachtype")
