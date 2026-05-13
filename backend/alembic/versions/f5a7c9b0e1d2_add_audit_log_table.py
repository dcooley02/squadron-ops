"""add audit_log table

Revision ID: f5a7c9b0e1d2
Revises: e4f6b8d0c2a3
Create Date: 2026-05-12 22:00:00.000000

Pass 2 / B5:
  NAMP-style audit trail. Captures every state-changing API call
  (POST/PUT/PATCH/DELETE) so a CO / NATOPS / NAMP inspector can ask
  "who changed what and when".

  Schema notes:
  - actor is a free-form string until auth lands. Once B6 ships it
    will be derived from the JWT subject.
  - request_body is JSONB; large payloads are truncated to ~4KB by the
    middleware before insert.
  - response_status is the HTTP code so failures are visible too.
"""
from typing import Sequence, Union

import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB
from alembic import op


revision: str = 'f5a7c9b0e1d2'
down_revision: Union[str, None] = 'e4f6b8d0c2a3'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'audit_log',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('ts', sa.DateTime(), nullable=False,
                  server_default=sa.func.now()),
        sa.Column('actor', sa.String(length=120), nullable=True),
        sa.Column('method', sa.String(length=8), nullable=False),
        sa.Column('path', sa.String(length=512), nullable=False),
        sa.Column('query_string', sa.String(length=512), nullable=True),
        sa.Column('response_status', sa.Integer(), nullable=False),
        sa.Column('request_body', JSONB(), nullable=True),
        sa.Column('client_host', sa.String(length=64), nullable=True),
        sa.Column('duration_ms', sa.Integer(), nullable=True),
    )
    op.create_index('ix_audit_log_ts', 'audit_log', ['ts'], unique=False)
    op.create_index('ix_audit_log_path', 'audit_log', ['path'], unique=False)


def downgrade() -> None:
    op.drop_index('ix_audit_log_path', table_name='audit_log')
    op.drop_index('ix_audit_log_ts', table_name='audit_log')
    op.drop_table('audit_log')
