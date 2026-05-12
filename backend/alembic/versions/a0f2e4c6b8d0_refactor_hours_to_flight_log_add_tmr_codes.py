"""refactor hours to flight_log and add TMR code tables

Revision ID: a0f2e4c6b8d0
Revises: 9d5b7e3c1f4a
Create Date: 2026-05-12 00:00:00.000000

Pass 3:
  A. Add per-crewmember hour categories + data_provenance to flight_logs
  B. Create tmr_codes catalog table
  C. Create sortie_tmr_codes junction table
  D. Backfill flight_logs from sortie-level aggregates (proportional split)
  E. Seed starter TMR code catalog
  F. Drop the 5 hour columns from sorties
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = 'a0f2e4c6b8d0'
down_revision: Union[str, None] = '9d5b7e3c1f4a'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


# ── A. New columns on flight_logs ────────────────────────────────────────────

def upgrade() -> None:
    # Step A: per-crewmember hour categories
    op.execute("CREATE TYPE dataprovenance AS ENUM ('ENTERED', 'BACKFILLED', 'SYSTEM_CALCULATED')")
    op.add_column('flight_logs', sa.Column('day_hours', sa.Float(), nullable=False, server_default='0.0'))
    op.add_column('flight_logs', sa.Column('night_hours', sa.Float(), nullable=False, server_default='0.0'))
    op.add_column('flight_logs', sa.Column('nvg_hours', sa.Float(), nullable=False, server_default='0.0'))
    op.add_column('flight_logs', sa.Column('instrument_hours', sa.Float(), nullable=False, server_default='0.0'))
    op.add_column('flight_logs', sa.Column('instrument_hours_simulated', sa.Float(), nullable=False, server_default='0.0'))
    op.add_column('flight_logs', sa.Column(
        'data_provenance',
        postgresql.ENUM('ENTERED', 'BACKFILLED', 'SYSTEM_CALCULATED', name='dataprovenance', create_type=False),
        nullable=False,
        server_default='ENTERED',
    ))

    # Step B: TMR code catalog
    op.create_table(
        'tmr_codes',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('code', sa.String(4), nullable=False),
        sa.Column('fpc', sa.String(1), nullable=False),
        sa.Column('gpc', sa.String(1), nullable=False),
        sa.Column('spc', sa.String(1), nullable=False),
        sa.Column('description', sa.String(), nullable=False),
        sa.Column('capability_area', sa.String(8), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
    )
    op.create_index('ix_tmr_codes_code', 'tmr_codes', ['code'], unique=True)

    # Step C: sortie ↔ TMR junction
    op.create_table(
        'sortie_tmr_codes',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('sortie_id', sa.Integer(), sa.ForeignKey('sorties.id'), nullable=False),
        sa.Column('tmr_code_id', sa.Integer(), sa.ForeignKey('tmr_codes.id'), nullable=False),
        sa.Column('person_id', sa.Integer(), sa.ForeignKey('persons.id'), nullable=True),
        sa.Column('hours', sa.Float(), nullable=True),
    )
    op.create_index('ix_sortie_tmr_codes_sortie_id', 'sortie_tmr_codes', ['sortie_id'])
    op.create_index('ix_sortie_tmr_codes_tmr_code_id', 'sortie_tmr_codes', ['tmr_code_id'])
    op.create_index('ix_sortie_tmr_codes_person_id', 'sortie_tmr_codes', ['person_id'])

    # Step D: backfill per-crewmember hours proportionally from sortie aggregates
    op.execute("""
        UPDATE flight_logs fl
        SET
            day_hours = CASE
                WHEN s.duration_hours > 0
                THEN ROUND(CAST(COALESCE(s.day_hours, 0) * (fl.hours_logged / s.duration_hours) AS numeric), 1)
                ELSE COALESCE(s.day_hours, 0)
            END,
            night_hours = CASE
                WHEN s.duration_hours > 0
                THEN ROUND(CAST(COALESCE(s.night_hours, 0) * (fl.hours_logged / s.duration_hours) AS numeric), 1)
                ELSE COALESCE(s.night_hours, 0)
            END,
            nvg_hours = CASE
                WHEN s.duration_hours > 0
                THEN ROUND(CAST(COALESCE(s.nvg_hours, 0) * (fl.hours_logged / s.duration_hours) AS numeric), 1)
                ELSE COALESCE(s.nvg_hours, 0)
            END,
            instrument_hours = CASE
                WHEN s.duration_hours > 0
                THEN ROUND(CAST(COALESCE(s.instrument_hours, 0) * (fl.hours_logged / s.duration_hours) AS numeric), 1)
                ELSE COALESCE(s.instrument_hours, 0)
            END,
            instrument_hours_simulated = CASE
                WHEN s.duration_hours > 0
                THEN ROUND(CAST(COALESCE(s.instrument_hours_simulated, 0) * (fl.hours_logged / s.duration_hours) AS numeric), 1)
                ELSE COALESCE(s.instrument_hours_simulated, 0)
            END,
            data_provenance = 'BACKFILLED'
        FROM sorties s
        WHERE fl.sortie_id = s.id
          AND s.is_complete = TRUE
    """)

    # Step E: seed starter TMR code catalog (~54 codes)
    tmr_rows = [
        # General Flight (FPC=1)
        ("1A1", "1", "A", "1", "Day, unaugmented flight",        "MOB"),
        ("1A2", "1", "A", "2", "Day, NVD flight",                 "MOB"),
        ("1A3", "1", "A", "3", "Day, formation flight",           "MOB"),
        ("1A4", "1", "A", "4", "Day, low-level flight",           "MOB"),
        ("1A5", "1", "A", "5", "Day, actual IMC",                 "MOB"),
        ("1A6", "1", "A", "6", "Day, simulated IMC",              "MOB"),
        ("1B1", "1", "B", "1", "Night, unaugmented flight",       "MOB"),
        ("1B2", "1", "B", "2", "Night, NVD flight",               "MOB"),
        ("1B3", "1", "B", "3", "Night, formation flight",         "MOB"),
        ("1B4", "1", "B", "4", "Night, low-level NVD",            "MOB"),
        ("1B5", "1", "B", "5", "Night, actual IMC",               "MOB"),
        ("1B6", "1", "B", "6", "Night, simulated IMC",            "MOB"),
        ("1C1", "1", "C", "1", "Simulator — FTD",                 "MOB"),
        ("1C2", "1", "C", "2", "Simulator — TOFT",                "MOB"),
        ("1D1", "1", "D", "1", "HAC check ride",                  "MOB"),
        ("1D2", "1", "D", "2", "NATOPS evaluation flight",        "MOB"),
        # Personnel Recovery / SAR (FPC=2)
        ("2A1", "2", "A", "1", "SAR, day",                        "PR"),
        ("2A2", "2", "A", "2", "SAR, night unaided",              "PR"),
        ("2A3", "2", "A", "3", "SAR, night NVD",                  "PR"),
        ("2B1", "2", "B", "1", "CSAR, day",                       "PR"),
        ("2B2", "2", "B", "2", "CSAR, night NVD",                 "PR"),
        ("2C1", "2", "C", "1", "Hoist operations, day",           "PR"),
        ("2C2", "2", "C", "2", "Hoist operations, night NVD",     "PR"),
        ("2C3", "2", "C", "3", "Rescue swimmer deployment",       "PR"),
        ("2D1", "2", "D", "1", "MEDEVAC, day",                    "PR"),
        ("2D2", "2", "D", "2", "MEDEVAC, night NVD",              "PR"),
        # Strike Warfare / Weapons (FPC=3)
        ("3A1", "3", "A", "1", "Gunnery, M240 day",               "STW"),
        ("3A2", "3", "A", "2", "Gunnery, M240 night NVD",         "STW"),
        ("3A3", "3", "A", "3", "Gunnery, 20mm day",               "STW"),
        ("3B1", "3", "B", "1", "Rocket employment, day",          "STW"),
        ("3B2", "3", "B", "2", "Rocket employment, night",        "STW"),
        ("3C1", "3", "C", "1", "Strafe dry, day",                 "STW"),
        ("3C2", "3", "C", "2", "Strafe dry, night NVD",           "STW"),
        ("3D1", "3", "D", "1", "UGR employment",                  "STW"),
        ("3E1", "3", "E", "1", "CSWS, day",                       "STW"),
        ("3E2", "3", "E", "2", "CSWS, night",                     "STW"),
        ("3F1", "3", "F", "1", "CAS/CASEVAC coordination",        "STW"),
        # Logistics / VERTREP / Shipboard (FPC=4)
        ("4A1", "4", "A", "1", "Shipboard ops, day",              "LOG"),
        ("4A2", "4", "A", "2", "Shipboard ops, night",            "LOG"),
        ("4A3", "4", "A", "3", "Shipboard ops, night NVD",        "LOG"),
        ("4B1", "4", "B", "1", "VERTREP, day",                    "LOG"),
        ("4B2", "4", "B", "2", "VERTREP, night",                  "LOG"),
        ("4C1", "4", "C", "1", "External lift, day",              "LOG"),
        ("4C2", "4", "C", "2", "External lift, night",            "LOG"),
        ("4D1", "4", "D", "1", "Troop transport, day",            "LOG"),
        ("4D2", "4", "D", "2", "Troop transport, night",          "LOG"),
        ("4E1", "4", "E", "1", "VIP transport",                   "LOG"),
        # AMCM (FPC=5)
        ("5A1", "5", "A", "1", "ALMDS operations, day",           "MIW"),
        ("5A2", "5", "A", "2", "ALMDS operations, night",         "MIW"),
        ("5B1", "5", "B", "1", "AMNS operations",                 "MIW"),
        ("5B2", "5", "B", "2", "AMNS NTR employment",             "MIW"),
        ("5C1", "5", "C", "1", "AMCM crew coordination",          "MIW"),
        # Special Operations (FPC=6)
        ("6A1", "6", "A", "1", "SOF insertion, day",              "SOF"),
        ("6A2", "6", "A", "2", "SOF insertion, night NVD",        "SOF"),
        ("6B1", "6", "B", "1", "SOF extraction, day",             "SOF"),
        ("6B2", "6", "B", "2", "SOF extraction, night NVD",       "SOF"),
        # Fleet Support Operations (FPC=7)
        ("7A1", "7", "A", "1", "FSO general support, day",        "FSO"),
        ("7A2", "7", "A", "2", "FSO general support, night",      "FSO"),
        ("7B1", "7", "B", "1", "Anti-surface warfare support",    "ASU"),
        ("7B2", "7", "B", "2", "ASW coordination",                "ASU"),
    ]
    for code, fpc, gpc, spc, description, cap_area in tmr_rows:
        op.execute(
            f"INSERT INTO tmr_codes (code, fpc, gpc, spc, description, capability_area, is_active) "
            f"VALUES ('{code}', '{fpc}', '{gpc}', '{spc}', $${description}$$, '{cap_area}', TRUE)"
        )

    # Step F: drop the 5 sortie-level hour columns (data is now in flight_logs)
    op.drop_column('sorties', 'day_hours')
    op.drop_column('sorties', 'night_hours')
    op.drop_column('sorties', 'nvg_hours')
    op.drop_column('sorties', 'instrument_hours')
    op.drop_column('sorties', 'instrument_hours_simulated')


def downgrade() -> None:
    # Restore 5 sortie-level hour columns (aggregated back from flight_logs)
    op.add_column('sorties', sa.Column('instrument_hours_simulated', sa.Float(), nullable=False, server_default='0.0'))
    op.add_column('sorties', sa.Column('instrument_hours', sa.Float(), nullable=False, server_default='0.0'))
    op.add_column('sorties', sa.Column('nvg_hours', sa.Float(), nullable=False, server_default='0.0'))
    op.add_column('sorties', sa.Column('night_hours', sa.Float(), nullable=False, server_default='0.0'))
    op.add_column('sorties', sa.Column('day_hours', sa.Float(), nullable=False, server_default='0.0'))

    # Re-aggregate from flight_logs into sortie columns
    op.execute("""
        UPDATE sorties s
        SET
            day_hours                  = agg.day_hours,
            night_hours                = agg.night_hours,
            nvg_hours                  = agg.nvg_hours,
            instrument_hours           = agg.instrument_hours,
            instrument_hours_simulated = agg.instrument_hours_simulated
        FROM (
            SELECT
                sortie_id,
                ROUND(CAST(SUM(day_hours) AS numeric), 1)                  AS day_hours,
                ROUND(CAST(SUM(night_hours) AS numeric), 1)                AS night_hours,
                ROUND(CAST(SUM(nvg_hours) AS numeric), 1)                  AS nvg_hours,
                ROUND(CAST(SUM(instrument_hours) AS numeric), 1)           AS instrument_hours,
                ROUND(CAST(SUM(instrument_hours_simulated) AS numeric), 1) AS instrument_hours_simulated
            FROM flight_logs
            GROUP BY sortie_id
        ) agg
        WHERE s.id = agg.sortie_id
    """)

    op.drop_table('sortie_tmr_codes')
    op.drop_index('ix_tmr_codes_code', 'tmr_codes')
    op.drop_table('tmr_codes')

    op.drop_column('flight_logs', 'data_provenance')
    op.drop_column('flight_logs', 'instrument_hours_simulated')
    op.drop_column('flight_logs', 'instrument_hours')
    op.drop_column('flight_logs', 'nvg_hours')
    op.drop_column('flight_logs', 'night_hours')
    op.drop_column('flight_logs', 'day_hours')
    op.execute("DROP TYPE IF EXISTS dataprovenance")
