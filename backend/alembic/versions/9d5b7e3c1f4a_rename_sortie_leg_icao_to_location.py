"""rename sortie_legs icao columns to location

Revision ID: 9d5b7e3c1f4a
Revises: 8c4e6a1f3d2b
Create Date: 2026-05-11 00:01:00.000000

"""
from typing import Sequence, Union

from alembic import op


# revision identifiers, used by Alembic.
revision: str = '9d5b7e3c1f4a'
down_revision: Union[str, None] = '8c4e6a1f3d2b'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.alter_column('sortie_legs', 'departure_icao', new_column_name='departure_location')
    op.alter_column('sortie_legs', 'arrival_icao', new_column_name='arrival_location')


def downgrade() -> None:
    op.alter_column('sortie_legs', 'departure_location', new_column_name='departure_icao')
    op.alter_column('sortie_legs', 'arrival_location', new_column_name='arrival_icao')
