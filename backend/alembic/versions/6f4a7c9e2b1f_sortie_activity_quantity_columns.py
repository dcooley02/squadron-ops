"""sortie activity quantity columns

Revision ID: 6f4a7c9e2b1f
Revises: 5e3f8b2c1a4d
Create Date: 2026-05-09 21:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = '6f4a7c9e2b1f'
down_revision: Union[str, None] = '5e3f8b2c1a4d'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('sorties', sa.Column('rounds_fired_20mm',       sa.Integer(), nullable=True))
    op.add_column('sorties', sa.Column('ugr_fired',               sa.Integer(), nullable=True))
    op.add_column('sorties', sa.Column('csw_rounds',              sa.Integer(), nullable=True))
    op.add_column('sorties', sa.Column('csw_rounds_night',        sa.Integer(), nullable=True))
    op.add_column('sorties', sa.Column('landings_day',            sa.Integer(), nullable=True))
    op.add_column('sorties', sa.Column('landings_night',          sa.Integer(), nullable=True))
    op.add_column('sorties', sa.Column('landings_dve_day',        sa.Integer(), nullable=True))
    op.add_column('sorties', sa.Column('landings_dve_night',      sa.Integer(), nullable=True))
    op.add_column('sorties', sa.Column('hoist_streams',           sa.Integer(), nullable=True))
    op.add_column('sorties', sa.Column('hoist_recoveries',        sa.Integer(), nullable=True))
    op.add_column('sorties', sa.Column('amns_iterations',         sa.Integer(), nullable=True))
    op.add_column('sorties', sa.Column('almds_hours',             sa.Float(),   nullable=True))
    op.add_column('sorties', sa.Column('amns_ntrs',               sa.Integer(), nullable=True))
    op.add_column('sorties', sa.Column('strafe_dry_profiles_day',   sa.Integer(), nullable=True))
    op.add_column('sorties', sa.Column('strafe_dry_profiles_night', sa.Integer(), nullable=True))


def downgrade() -> None:
    op.drop_column('sorties', 'strafe_dry_profiles_night')
    op.drop_column('sorties', 'strafe_dry_profiles_day')
    op.drop_column('sorties', 'amns_ntrs')
    op.drop_column('sorties', 'almds_hours')
    op.drop_column('sorties', 'amns_iterations')
    op.drop_column('sorties', 'hoist_recoveries')
    op.drop_column('sorties', 'hoist_streams')
    op.drop_column('sorties', 'landings_dve_night')
    op.drop_column('sorties', 'landings_dve_day')
    op.drop_column('sorties', 'landings_night')
    op.drop_column('sorties', 'landings_day')
    op.drop_column('sorties', 'csw_rounds_night')
    op.drop_column('sorties', 'csw_rounds')
    op.drop_column('sorties', 'ugr_fired')
    op.drop_column('sorties', 'rounds_fired_20mm')
