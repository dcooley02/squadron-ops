"""syllabus event extensions and gradecard tables

Revision ID: 4c2e9f1a0b3d
Revises: 790f9729d5e5
Create Date: 2026-05-09 16:30:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision: str = '4c2e9f1a0b3d'
down_revision: Union[str, None] = '790f9729d5e5'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ── Create new PostgreSQL enum types ──────────────────────────────────────
    op.execute("CREATE TYPE syllabuslevel AS ENUM ('2', '3', '4', '5')")
    op.execute("CREATE TYPE syllabusstage AS ENUM ('INTRO', 'ASU', 'CSAR', 'SOF_LOG', 'STAN_EVAL', 'AMCM_INTRO', 'ALMDS', 'AMNS')")
    op.execute("CREATE TYPE syllabustrack AS ENUM ('PILOT_CORE', 'PILOT_AMCM', 'AIRCREW_CORE', 'AIRCREW_AMCM')")
    op.execute("CREATE TYPE eventvenue AS ENUM ('AIRCRAFT', 'TOFT', 'LAB', 'BOARD')")
    op.execute("CREATE TYPE gradingscheme AS ENUM ('COMPLETION', 'FOUR_TIER')")
    op.execute("CREATE TYPE gradecardsection AS ENUM ('PLANNING_BRIEFING', 'PRELAUNCH', 'ENROUTE', 'EXECUTION', 'COMMUNICATION', 'GENERAL_FLIGHT_CONDUCT', 'DEBRIEF')")
    op.execute("CREATE TYPE lineitemrole AS ENUM ('D', 'I', 'P')")
    op.execute("CREATE TYPE gradecardstatus AS ENUM ('COMPLETE', 'INCOMPLETE', 'PASS', 'CONDITIONAL_PASS', 'UNSAT', 'IN_PROGRESS')")
    op.execute("CREATE TYPE completionstatus AS ENUM ('COMPLETE', 'INCOMPLETE')")
    op.execute("CREATE TYPE fourtierscore AS ENUM ('UNSAT_1_0', 'BELOW_STANDARD_2_0', 'STANDARD_3_0', 'EXCEPTIONAL_4_0')")

    # ── syllabus_events: rename legacy stage, add SWTP columns ───────────────
    op.alter_column('syllabus_events', 'stage', new_column_name='stage_legacy')

    op.add_column('syllabus_events', sa.Column('level', postgresql.ENUM('2', '3', '4', '5', name='syllabuslevel', create_type=False), nullable=True))
    op.add_column('syllabus_events', sa.Column('stage', postgresql.ENUM('INTRO', 'ASU', 'CSAR', 'SOF_LOG', 'STAN_EVAL', 'AMCM_INTRO', 'ALMDS', 'AMNS', name='syllabusstage', create_type=False), nullable=True))
    op.add_column('syllabus_events', sa.Column('series', sa.Integer(), nullable=True))
    op.add_column('syllabus_events', sa.Column('track', postgresql.ENUM('PILOT_CORE', 'PILOT_AMCM', 'AIRCREW_CORE', 'AIRCREW_AMCM', name='syllabustrack', create_type=False), nullable=True))
    op.add_column('syllabus_events', sa.Column('event_code', sa.String(), nullable=True))
    op.add_column('syllabus_events', sa.Column('min_instructor_level', sa.Integer(), nullable=True))
    op.add_column('syllabus_events', sa.Column('aircraft_or_sim', postgresql.ENUM('AIRCRAFT', 'TOFT', 'LAB', 'BOARD', name='eventvenue', create_type=False), nullable=True))
    op.add_column('syllabus_events', sa.Column('time_hours', sa.Float(), nullable=True))
    op.add_column('syllabus_events', sa.Column('is_stan_eval', sa.Boolean(), server_default='false', nullable=False))
    op.add_column('syllabus_events', sa.Column('grading_scheme', postgresql.ENUM('COMPLETION', 'FOUR_TIER', name='gradingscheme', create_type=False), nullable=True))
    op.add_column('syllabus_events', sa.Column('prerequisites_text', sa.Text(), nullable=True))
    op.add_column('syllabus_events', sa.Column('force_composition', sa.Text(), nullable=True))
    op.add_column('syllabus_events', sa.Column('recommended_soe', sa.Text(), nullable=True))
    op.add_column('syllabus_events', sa.Column('unsat_criteria', sa.Text(), nullable=True))
    op.add_column('syllabus_events', sa.Column('references', sa.JSON(), nullable=True))
    op.create_index(op.f('ix_syllabus_events_event_code'), 'syllabus_events', ['event_code'], unique=False)

    # ── Create gradecard_line_items ───────────────────────────────────────────
    op.create_table(
        'gradecard_line_items',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('syllabus_event_id', sa.Integer(), nullable=False),
        sa.Column('section', postgresql.ENUM('PLANNING_BRIEFING', 'PRELAUNCH', 'ENROUTE', 'EXECUTION', 'COMMUNICATION', 'GENERAL_FLIGHT_CONDUCT', 'DEBRIEF', name='gradecardsection', create_type=False), nullable=False),
        sa.Column('item_name', sa.String(), nullable=False),
        sa.Column('role', postgresql.ENUM('D', 'I', 'P', name='lineitemrole', create_type=False), nullable=False),
        sa.Column('is_critical', sa.Boolean(), nullable=False),
        sa.Column('is_required', sa.Boolean(), nullable=False),
        sa.Column('display_order', sa.Integer(), nullable=False),
        sa.Column('mop_below_standard', sa.Text(), nullable=True),
        sa.Column('mop_standard', sa.Text(), nullable=True),
        sa.ForeignKeyConstraint(['syllabus_event_id'], ['syllabus_events.id']),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_gradecard_line_items_syllabus_event_id'), 'gradecard_line_items', ['syllabus_event_id'], unique=False)

    # ── Create gradecards ─────────────────────────────────────────────────────
    op.create_table(
        'gradecards',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('person_id', sa.Integer(), nullable=False),
        sa.Column('syllabus_event_id', sa.Integer(), nullable=False),
        sa.Column('sortie_id', sa.Integer(), nullable=True),
        sa.Column('flight_log_id', sa.Integer(), nullable=True),
        sa.Column('instructor_person_id', sa.Integer(), nullable=True),
        sa.Column('card_date', sa.Date(), nullable=False),
        sa.Column('grading_scheme', postgresql.ENUM('COMPLETION', 'FOUR_TIER', name='gradingscheme', create_type=False), nullable=False),
        sa.Column('overall_status', postgresql.ENUM('COMPLETE', 'INCOMPLETE', 'PASS', 'CONDITIONAL_PASS', 'UNSAT', 'IN_PROGRESS', name='gradecardstatus', create_type=False), nullable=False),
        sa.Column('remarks', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['flight_log_id'], ['flight_logs.id']),
        sa.ForeignKeyConstraint(['instructor_person_id'], ['persons.id']),
        sa.ForeignKeyConstraint(['person_id'], ['persons.id']),
        sa.ForeignKeyConstraint(['sortie_id'], ['sorties.id']),
        sa.ForeignKeyConstraint(['syllabus_event_id'], ['syllabus_events.id']),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_gradecards_person_id'), 'gradecards', ['person_id'], unique=False)
    op.create_index(op.f('ix_gradecards_syllabus_event_id'), 'gradecards', ['syllabus_event_id'], unique=False)
    op.create_index(op.f('ix_gradecards_sortie_id'), 'gradecards', ['sortie_id'], unique=False)
    op.create_index(op.f('ix_gradecards_flight_log_id'), 'gradecards', ['flight_log_id'], unique=False)

    # ── Create gradecard_line_item_results ────────────────────────────────────
    op.create_table(
        'gradecard_line_item_results',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('gradecard_id', sa.Integer(), nullable=False),
        sa.Column('line_item_id', sa.Integer(), nullable=False),
        sa.Column('waived', sa.Boolean(), nullable=False),
        sa.Column('completion_status', postgresql.ENUM('COMPLETE', 'INCOMPLETE', name='completionstatus', create_type=False), nullable=True),
        sa.Column('four_tier_score', postgresql.ENUM('UNSAT_1_0', 'BELOW_STANDARD_2_0', 'STANDARD_3_0', 'EXCEPTIONAL_4_0', name='fourtierscore', create_type=False), nullable=True),
        sa.Column('remarks', sa.Text(), nullable=True),
        sa.ForeignKeyConstraint(['gradecard_id'], ['gradecards.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['line_item_id'], ['gradecard_line_items.id']),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_gradecard_line_item_results_gradecard_id'), 'gradecard_line_item_results', ['gradecard_id'], unique=False)
    op.create_index(op.f('ix_gradecard_line_item_results_line_item_id'), 'gradecard_line_item_results', ['line_item_id'], unique=False)


def downgrade() -> None:
    # ── Drop result / gradecard / line-item tables (dependency order) ─────────
    op.drop_index(op.f('ix_gradecard_line_item_results_line_item_id'), table_name='gradecard_line_item_results')
    op.drop_index(op.f('ix_gradecard_line_item_results_gradecard_id'), table_name='gradecard_line_item_results')
    op.drop_table('gradecard_line_item_results')

    op.drop_index(op.f('ix_gradecards_flight_log_id'), table_name='gradecards')
    op.drop_index(op.f('ix_gradecards_sortie_id'), table_name='gradecards')
    op.drop_index(op.f('ix_gradecards_syllabus_event_id'), table_name='gradecards')
    op.drop_index(op.f('ix_gradecards_person_id'), table_name='gradecards')
    op.drop_table('gradecards')

    op.drop_index(op.f('ix_gradecard_line_items_syllabus_event_id'), table_name='gradecard_line_items')
    op.drop_table('gradecard_line_items')

    # ── Remove new columns from syllabus_events ───────────────────────────────
    op.drop_index(op.f('ix_syllabus_events_event_code'), table_name='syllabus_events')
    op.drop_column('syllabus_events', 'references')
    op.drop_column('syllabus_events', 'unsat_criteria')
    op.drop_column('syllabus_events', 'recommended_soe')
    op.drop_column('syllabus_events', 'force_composition')
    op.drop_column('syllabus_events', 'prerequisites_text')
    op.drop_column('syllabus_events', 'grading_scheme')
    op.drop_column('syllabus_events', 'is_stan_eval')
    op.drop_column('syllabus_events', 'time_hours')
    op.drop_column('syllabus_events', 'aircraft_or_sim')
    op.drop_column('syllabus_events', 'min_instructor_level')
    op.drop_column('syllabus_events', 'event_code')
    op.drop_column('syllabus_events', 'track')
    op.drop_column('syllabus_events', 'series')
    op.drop_column('syllabus_events', 'stage')
    op.drop_column('syllabus_events', 'level')
    op.alter_column('syllabus_events', 'stage_legacy', new_column_name='stage')

    # ── Drop enum types (after all columns/tables that reference them) ────────
    op.execute("DROP TYPE IF EXISTS fourtierscore")
    op.execute("DROP TYPE IF EXISTS completionstatus")
    op.execute("DROP TYPE IF EXISTS gradecardstatus")
    op.execute("DROP TYPE IF EXISTS lineitemrole")
    op.execute("DROP TYPE IF EXISTS gradecardsection")
    op.execute("DROP TYPE IF EXISTS gradingscheme")
    op.execute("DROP TYPE IF EXISTS eventvenue")
    op.execute("DROP TYPE IF EXISTS syllabustrack")
    op.execute("DROP TYPE IF EXISTS syllabusstage")
    op.execute("DROP TYPE IF EXISTS syllabuslevel")
