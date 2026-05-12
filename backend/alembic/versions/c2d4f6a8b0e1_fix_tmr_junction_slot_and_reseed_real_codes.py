"""fix_tmr_junction_slot_and_reseed_real_codes

Replace per-crewmember TMR junction (person_id) with per-sortie slot (1-3),
and replace fabricated 60-code catalog with the real 78 codes from
CNAF M-3710.7 Appendix D Figure D-1.

Revision ID: c2d4f6a8b0e1
Revises: b1c3e5a7f9d2
Create Date: 2026-05-12

"""
from alembic import op
import sqlalchemy as sa
from typing import Union

# revision identifiers, used by Alembic.
revision: str = 'c2d4f6a8b0e1'
down_revision: Union[str, None] = 'b1c3e5a7f9d2'
branch_labels = None
depends_on = None


_TMR_CODES = [
    ('1A1', 'TRNG SYL/EXC F/FN',                         '1', 'A', '1'),
    ('1A2', 'TRNG SYL/EXC INST',                         '1', 'A', '2'),
    ('1A3', 'TRNG SYL/EXC FCLP/CAL',                     '1', 'A', '3'),
    ('1A4', 'TRNG SYL/EXC CQ',                           '1', 'A', '4'),
    ('1A5', 'TRNG SYL/EXC TRANS',                        '1', 'A', '5'),
    ('1A6', 'TRNG SYL/EXC AIR CMBT',                     '1', 'A', '6'),
    ('1A7', 'TRNG SYL/EXC ATCK',                         '1', 'A', '7'),
    ('1A8', 'TRNG SYL/EXC ASW',                          '1', 'A', '8'),
    ('1A9', 'TRNG SYL/EXC SP EQUIP',                     '1', 'A', '9'),
    ('1A0', 'TRNG SYL/EXC UNSAT FLT',                    '1', 'A', '0'),
    ('1B1', 'TRNG IUT F/F/N',                            '1', 'B', '1'),
    ('1B2', 'TRNG IUT INST',                             '1', 'B', '2'),
    ('1B3', 'TRNG IUT FCLP/CAL',                         '1', 'B', '3'),
    ('1B4', 'TRNG IUT CQ',                               '1', 'B', '4'),
    ('1B5', 'TRNG IUT TRANS',                            '1', 'B', '5'),
    ('1B6', 'TRNG IUT AIR CMBT',                         '1', 'B', '6'),
    ('1B7', 'TRNG IUT ATCK',                             '1', 'B', '7'),
    ('1B8', 'TRNG IUT ASW',                              '1', 'B', '8'),
    ('1B9', 'TRNG IUT SP EQUIP',                         '1', 'B', '9'),
    ('1B0', 'TRNG IUT UNSAT FLT',                        '1', 'B', '0'),
    ('1C1', 'TRNG NAV F/F/N',                            '1', 'C', '1'),
    ('1C2', 'TRNG NAV INST',                             '1', 'C', '2'),
    ('1C3', 'TRNG NAV FCLP/CAL',                         '1', 'C', '3'),
    ('1C4', 'TRNG NAV CQ',                               '1', 'C', '4'),
    ('1C5', 'TRNG NAV TRANS',                            '1', 'C', '5'),
    ('1C6', 'TRNG NAV AIR CMBT',                         '1', 'C', '6'),
    ('1C7', 'TRNG NAV ATCK',                             '1', 'C', '7'),
    ('1C8', 'TRNG NAV ASW',                              '1', 'C', '8'),
    ('1C9', 'TRNG NAV SP EQUIP',                         '1', 'C', '9'),
    ('1C0', 'TRNG NAV UNSAT FLT',                        '1', 'C', '0'),
    ('1E1', 'TRNG DNA SYLLABUS F/F/N',                   '1', 'E', '1'),
    ('1E2', 'TRNG DNA SYLLABUS INST',                    '1', 'E', '2'),
    ('1E5', 'TRNG DNA SYLLABUS TRANS',                   '1', 'E', '5'),
    ('1E7', 'TRNG DNA SYLLABUS ATCK',                    '1', 'E', '7'),
    ('1E9', 'TRNG DNA SYLLABUS SP EQUIP',                '1', 'E', '9'),
    ('1E0', 'TRNG DNA SYL UNSAT FLT',                   '1', 'E', '0'),
    ('1F1', 'TRNG DNA NON-SYL F/F/N',                   '1', 'F', '1'),
    ('1F2', 'TRNG DNA NON-SYL INST',                    '1', 'F', '2'),
    ('1F5', 'TRNG DNA NON-SYL TRANS',                   '1', 'F', '5'),
    ('1F9', 'TRNG DNA NON-SYL SP EQUIP',                '1', 'F', '9'),
    ('1F0', 'TRNG DNA NON-SYL UNSAT FLT',               '1', 'F', '0'),
    ('1H1', 'TRNG OTHER US SVC F/F/N',                  '1', 'H', '1'),
    ('1H9', 'TRNG OTHER US SVC SP EQUIP',               '1', 'H', '9'),
    ('1I1', 'TRNG FOREIGN F/F/N',                       '1', 'I', '1'),
    ('1I9', 'TRNG FOREIGN SP EQUIP',                    '1', 'I', '9'),
    ('2J1', 'SVC FERRY FLEET FUND',                     '2', 'J', '1'),
    ('2J2', 'SVC FERRY OTHER FUND',                     '2', 'J', '2'),
    ('2K1', 'SVC FCF FLEET FUND',                       '2', 'K', '1'),
    ('2K2', 'SVC FCF OTHER FUND',                       '2', 'K', '2'),
    ('2K3', 'SVC FCF OBSERVER',                         '2', 'K', '3'),
    ('2K9', 'SVC FCF OTHER',                            '2', 'K', '9'),
    ('2L1', 'SVC OT&E',                                 '2', 'L', '1'),
    ('2L2', 'SVC ORI',                                  '2', 'L', '2'),
    ('2L3', 'SVC INSTRUMENT CHECK',                     '2', 'L', '3'),
    ('2L4', 'SVC NATOPS CHECK',                         '2', 'L', '4'),
    ('2L5', 'SVC INSTRUCTOR STAN/TPT TRAIN/QUAL EVAL',  '2', 'L', '5'),
    ('2L7', 'SVC ORDNANCE EVAL',                        '2', 'L', '7'),
    ('2M1', 'SVC PUBLIC RELATIONS',                     '2', 'M', '1'),
    ('2M2', 'SVC OBSERVATION',                          '2', 'M', '2'),
    ('2M3', 'SVC TROOP MOVEMENT',                       '2', 'M', '3'),
    ('2M9', 'SVC SAR',                                  '2', 'M', '9'),
    ('2N1', 'ABORT GROUND-EXTERNAL CAUSE',              '2', 'N', '1'),
    ('2N2', 'ABORT GROUND-MATERIAL CAUSE',              '2', 'N', '2'),
    ('2N3', 'ABORT GROUND-OPERATOR CAUSE',              '2', 'N', '3'),
    ('2N4', 'ABORT GROUND-WEATHER',                     '2', 'N', '4'),
    ('2O1', 'CANCEL EXTERNAL CAUSE',                    '2', 'O', '1'),
    ('2O2', 'CANCEL MATERIAL CAUSE',                    '2', 'O', '2'),
    ('2O3', 'CANCEL OPERATOR CAUSE',                    '2', 'O', '3'),
    ('2O4', 'CANCEL WEATHER',                           '2', 'O', '4'),
    ('2P1', 'UTILITY ADMIN TRANSPORT',                  '2', 'P', '1'),
    ('2P2', 'UTILITY PROFICIENCY',                      '2', 'P', '2'),
    ('2P3', 'UTILITY DV TRANSPORT',                     '2', 'P', '3'),
    ('2P9', 'UTILITY OTHER',                            '2', 'P', '9'),
    ('2R1', 'LOGISTICS SCHED TRANSPORT',                '2', 'R', '1'),
    ('2R2', 'LOGISTICS SPECIAL TRANSPORT',              '2', 'R', '2'),
    ('2R3', 'ADMIN TRANSPORT NON-SCHED',                '2', 'R', '3'),
    ('3S1', 'OPS CAS ASSIGNED PRE-TAKEOFF',             '3', 'S', '1'),
    ('3S2', 'OPS CAS ASSIGNED POST-TAKEOFF',            '3', 'S', '2'),
    ('3U5', 'OPS AMCM MINE NEUTRALIZE',                 '3', 'U', '5'),
    ('3V4', 'OPS AMCM MINE SEARCH',                     '3', 'V', '4'),
]


def upgrade() -> None:
    # ── Step a: remove fabricated test rows for sortie 97 ────────────────────────
    op.execute("DELETE FROM sortie_tmr_codes WHERE sortie_id = 97")

    # ── Step b: restructure sortie_tmr_codes ─────────────────────────────────────
    # Drop index and FK on person_id, then drop the column
    op.drop_index('ix_sortie_tmr_codes_person_id', table_name='sortie_tmr_codes')
    op.drop_constraint('sortie_tmr_codes_person_id_fkey',
                       'sortie_tmr_codes', type_='foreignkey')
    op.drop_column('sortie_tmr_codes', 'person_id')

    # Add slot column (DEFAULT 1 satisfies NOT NULL during DDL; table is empty)
    op.add_column(
        'sortie_tmr_codes',
        sa.Column('slot', sa.Integer(), nullable=False, server_default='1'),
    )
    # Remove the server default — callers must supply slot explicitly
    op.alter_column('sortie_tmr_codes', 'slot', server_default=None)

    op.create_check_constraint(
        'sortie_tmr_codes_slot_check',
        'sortie_tmr_codes',
        'slot BETWEEN 1 AND 3',
    )
    op.create_unique_constraint(
        'sortie_tmr_codes_sortie_slot_unique',
        'sortie_tmr_codes',
        ['sortie_id', 'slot'],
    )

    # ── Steps c–d: replace catalog with real Appendix D codes ────────────────────
    op.execute("TRUNCATE TABLE tmr_codes RESTART IDENTITY CASCADE")

    insert_sql = sa.text(
        "INSERT INTO tmr_codes (code, fpc, gpc, spc, description, is_active) "
        "VALUES (:code, :fpc, :gpc, :spc, :description, TRUE)"
    )
    conn = op.get_bind()
    for code, description, fpc, gpc, spc in _TMR_CODES:
        conn.execute(insert_sql, {
            'code': code, 'fpc': fpc, 'gpc': gpc,
            'spc': spc, 'description': description,
        })


def downgrade() -> None:
    """
    Downgrade does not restore the fabricated TMR descriptions from the prior pass.
    The catalog will be empty after downgrade. Re-run seed.py or this migration's
    upgrade to restore real descriptions.
    """
    # Remove slot constraints and column
    op.drop_constraint('sortie_tmr_codes_sortie_slot_unique',
                       'sortie_tmr_codes', type_='unique')
    op.drop_constraint('sortie_tmr_codes_slot_check',
                       'sortie_tmr_codes', type_='check')
    op.drop_column('sortie_tmr_codes', 'slot')

    # Restore person_id as nullable FK
    op.add_column(
        'sortie_tmr_codes',
        sa.Column('person_id', sa.Integer(), nullable=True),
    )
    op.create_foreign_key(
        'sortie_tmr_codes_person_id_fkey',
        'sortie_tmr_codes', 'persons',
        ['person_id'], ['id'],
    )
    op.create_index(
        'ix_sortie_tmr_codes_person_id',
        'sortie_tmr_codes', ['person_id'],
    )

    # Truncate catalog — fabricated data not restored
    op.execute("TRUNCATE TABLE tmr_codes RESTART IDENTITY CASCADE")
