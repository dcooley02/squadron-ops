"""namp shaped maintenance schema

Revision ID: 7b3d5f8c2e1a
Revises: 6f4a7c9e2b1f
Create Date: 2026-05-09 22:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = '7b3d5f8c2e1a'
down_revision: Union[str, None] = '6f4a7c9e2b1f'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ── 1. Transition discrepancyseverity enum: GROUNDING → DOWNING ────────────
    # Postgres cannot drop enum values; create a new type, migrate, then swap.
    op.execute("CREATE TYPE discrepancyseverity_new AS ENUM ('MINOR', 'MAJOR', 'DOWNING')")
    op.execute("""
        ALTER TABLE discrepancies
            ALTER COLUMN severity TYPE discrepancyseverity_new
            USING (
                CASE severity::text
                    WHEN 'GROUNDING' THEN 'DOWNING'::discrepancyseverity_new
                    ELSE severity::text::discrepancyseverity_new
                END
            )
    """)
    op.execute("DROP TYPE discrepancyseverity")
    op.execute("ALTER TYPE discrepancyseverity_new RENAME TO discrepancyseverity")

    # ── 2. Create DiscrepancyWorkStatus enum and add new columns ───────────────
    op.execute(
        "CREATE TYPE discrepancyworkstatus AS ENUM "
        "('OPEN', 'IN_WORK', 'AWP', 'AWM', 'COMPLETED', 'CLOSED')"
    )
    op.add_column('discrepancies',
        sa.Column('maf_number', sa.String(), nullable=True))
    op.create_index('ix_discrepancies_maf_number', 'discrepancies', ['maf_number'])
    op.add_column('discrepancies',
        sa.Column('work_status',
                  sa.Enum('OPEN', 'IN_WORK', 'AWP', 'AWM', 'COMPLETED', 'CLOSED',
                          name='discrepancyworkstatus'),
                  nullable=False,
                  server_default='OPEN'))
    op.add_column('discrepancies',
        sa.Column('system_affected', sa.String(), nullable=True))
    op.add_column('discrepancies',
        sa.Column('corrective_action', sa.Text(), nullable=True))

    # ── 3. Add manual_status_override to aircraft ──────────────────────────────
    op.add_column('aircraft',
        sa.Column('manual_status_override',
                  sa.Enum('FMC', 'PMC', 'NMC', 'NMCM', 'NMCS', name='aircraftstatus'),
                  nullable=True))

    # ── 4. Create inspection_types table ──────────────────────────────────────
    op.create_table(
        'inspection_types',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('code', sa.String(), nullable=False),
        sa.Column('name', sa.String(), nullable=False),
        sa.Column('periodicity_days', sa.Integer(), nullable=True),
        sa.Column('periodicity_hours', sa.Float(), nullable=True),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('is_downing_when_overdue', sa.Boolean(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_inspection_types_code', 'inspection_types', ['code'], unique=True)

    # ── 5. Create aircraft_inspections table ───────────────────────────────────
    op.create_table(
        'aircraft_inspections',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('aircraft_id', sa.Integer(), nullable=False),
        sa.Column('inspection_type_id', sa.Integer(), nullable=False),
        sa.Column('last_completed_date', sa.Date(), nullable=True),
        sa.Column('last_completed_hours', sa.Float(), nullable=True),
        sa.Column('next_due_date', sa.Date(), nullable=True),
        sa.Column('next_due_hours', sa.Float(), nullable=True),
        sa.Column('last_completion_notes', sa.Text(), nullable=True),
        sa.ForeignKeyConstraint(['aircraft_id'], ['aircraft.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['inspection_type_id'], ['inspection_types.id']),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('aircraft_id', 'inspection_type_id',
                            name='uq_aircraft_inspection_type'),
    )
    op.create_index('ix_aircraft_inspections_aircraft_id', 'aircraft_inspections', ['aircraft_id'])
    op.create_index('ix_aircraft_inspections_inspection_type_id', 'aircraft_inspections', ['inspection_type_id'])


def downgrade() -> None:
    # ── 5. Drop aircraft_inspections ──────────────────────────────────────────
    op.drop_index('ix_aircraft_inspections_inspection_type_id', 'aircraft_inspections')
    op.drop_index('ix_aircraft_inspections_aircraft_id', 'aircraft_inspections')
    op.drop_table('aircraft_inspections')

    # ── 4. Drop inspection_types ───────────────────────────────────────────────
    op.drop_index('ix_inspection_types_code', 'inspection_types')
    op.drop_table('inspection_types')

    # ── 3. Drop manual_status_override ────────────────────────────────────────
    op.drop_column('aircraft', 'manual_status_override')

    # ── 2. Drop new discrepancy columns and work status enum ──────────────────
    op.drop_column('discrepancies', 'corrective_action')
    op.drop_column('discrepancies', 'system_affected')
    op.drop_column('discrepancies', 'work_status')
    op.drop_index('ix_discrepancies_maf_number', 'discrepancies')
    op.drop_column('discrepancies', 'maf_number')
    op.execute("DROP TYPE discrepancyworkstatus")

    # ── 1. Revert severity enum: DOWNING → GROUNDING ──────────────────────────
    op.execute("CREATE TYPE discrepancyseverity_old AS ENUM ('MINOR', 'MAJOR', 'GROUNDING')")
    op.execute("""
        ALTER TABLE discrepancies
            ALTER COLUMN severity TYPE discrepancyseverity_old
            USING (
                CASE severity::text
                    WHEN 'DOWNING' THEN 'GROUNDING'::discrepancyseverity_old
                    ELSE severity::text::discrepancyseverity_old
                END
            )
    """)
    op.execute("DROP TYPE discrepancyseverity")
    op.execute("ALTER TYPE discrepancyseverity_old RENAME TO discrepancyseverity")
