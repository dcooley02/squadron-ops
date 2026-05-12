"""wing currency table-driven schema

Revision ID: 5e3f8b2c1a4d
Revises: 4c2e9f1a0b3d
Create Date: 2026-05-09 20:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision: str = '5e3f8b2c1a4d'
down_revision: Union[str, None] = '4c2e9f1a0b3d'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ── New enum type ─────────────────────────────────────────────────────────
    op.execute(
        "CREATE TYPE currencyaudience AS ENUM "
        "('ALL_PILOTS', 'HAC_ONLY', 'AMCM_QUAL_PILOTS', 'ALL_AIRCREWMEN', 'AWS_ONLY', 'HOIST_OP_QUAL')"
    )

    # ── currency_types ────────────────────────────────────────────────────────
    op.create_table(
        'currency_types',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('code', sa.String(), nullable=False),
        sa.Column('name', sa.String(), nullable=False),
        sa.Column('periodicity_days', sa.Integer(), nullable=False),
        sa.Column('requirement_text', sa.Text(), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('sim_eligible', sa.Boolean(), server_default='false', nullable=False),
        sa.Column('sim_notes', sa.Text(), nullable=True),
        sa.Column('min_hours', sa.Float(), nullable=True),
        sa.Column('min_count', sa.Integer(), nullable=True),
        sa.Column('count_unit', sa.String(), nullable=True),
        sa.Column('references', sa.JSON(), nullable=True),
        sa.Column('is_active', sa.Boolean(), server_default='true', nullable=False),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_currency_types_code'), 'currency_types', ['code'], unique=True)

    # ── currency_applicabilities ──────────────────────────────────────────────
    op.create_table(
        'currency_applicabilities',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('currency_type_id', sa.Integer(), nullable=False),
        sa.Column(
            'applies_to',
            postgresql.ENUM(
                'ALL_PILOTS', 'HAC_ONLY', 'AMCM_QUAL_PILOTS',
                'ALL_AIRCREWMEN', 'AWS_ONLY', 'HOIST_OP_QUAL',
                name='currencyaudience',
                create_type=False,
            ),
            nullable=False,
        ),
        sa.Column('required_qualification', sa.String(), nullable=True),
        sa.ForeignKeyConstraint(['currency_type_id'], ['currency_types.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(
        op.f('ix_currency_applicabilities_currency_type_id'),
        'currency_applicabilities',
        ['currency_type_id'],
        unique=False,
    )

    # ── Add currency_type_id FK to existing currencies table ──────────────────
    op.add_column(
        'currencies',
        sa.Column('currency_type_id', sa.Integer(), nullable=True),
    )
    op.create_foreign_key(
        'fk_currencies_currency_type_id',
        'currencies', 'currency_types',
        ['currency_type_id'], ['id'],
    )
    op.create_index(
        op.f('ix_currencies_currency_type_id'),
        'currencies',
        ['currency_type_id'],
        unique=False,
    )


def downgrade() -> None:
    # ── Remove currency_type_id from currencies ───────────────────────────────
    op.drop_index(op.f('ix_currencies_currency_type_id'), table_name='currencies')
    op.drop_constraint('fk_currencies_currency_type_id', 'currencies', type_='foreignkey')
    op.drop_column('currencies', 'currency_type_id')

    # ── Drop currency_applicabilities ─────────────────────────────────────────
    op.drop_index(
        op.f('ix_currency_applicabilities_currency_type_id'),
        table_name='currency_applicabilities',
    )
    op.drop_table('currency_applicabilities')

    # ── Drop currency_types ───────────────────────────────────────────────────
    op.drop_index(op.f('ix_currency_types_code'), table_name='currency_types')
    op.drop_table('currency_types')

    # ── Drop enum ─────────────────────────────────────────────────────────────
    op.execute("DROP TYPE IF EXISTS currencyaudience")
