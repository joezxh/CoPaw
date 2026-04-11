"""enterprise_phase_a

Revision ID: 002
Revises: 001
Create Date: 2026-04-11 16:30:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '002'
down_revision: Union[str, None] = '001'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Modify users.mfa_secret to Text for AES-256-GCM encryption
    op.alter_column('users', 'mfa_secret',
               existing_type=sa.VARCHAR(length=200),
               type_=sa.Text(),
               existing_nullable=True)

    # 2. Create dlp_rules table
    op.create_table('dlp_rules',
        sa.Column('rule_name', sa.String(length=100), nullable=False),
        sa.Column('description', sa.String(length=500), nullable=True),
        sa.Column('pattern_regex', sa.Text(), nullable=False),
        sa.Column('action', sa.String(length=20), nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=False),
        sa.Column('is_builtin', sa.Boolean(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('rule_name')
    )

    # 3. Create dlp_events table
    op.create_table('dlp_events',
        sa.Column('rule_name', sa.String(length=100), nullable=False),
        sa.Column('action_taken', sa.String(length=20), nullable=False),
        sa.Column('content_summary', sa.Text(), nullable=True),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('context_path', sa.String(length=200), nullable=True),
        sa.Column('triggered_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_dlp_events_rule_name'), 'dlp_events', ['rule_name'], unique=False)
    op.create_index(op.f('ix_dlp_events_triggered_at'), 'dlp_events', ['triggered_at'], unique=False)
    op.create_index(op.f('ix_dlp_events_user_id'), 'dlp_events', ['user_id'], unique=False)

    # 4. Create alert_rules table
    op.create_table('alert_rules',
        sa.Column('rule_type', sa.String(length=50), nullable=False),
        sa.Column('description', sa.String(length=300), nullable=True),
        sa.Column('threshold', sa.Integer(), nullable=False),
        sa.Column('window_seconds', sa.Integer(), nullable=False),
        sa.Column('notify_channels', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_alert_rules_rule_type'), 'alert_rules', ['rule_type'], unique=True)

    # 5. Create alert_events table
    op.create_table('alert_events',
        sa.Column('rule_type', sa.String(length=50), nullable=False),
        sa.Column('triggered_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('context', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('notify_status', sa.String(length=20), nullable=True),
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_alert_events_rule_type'), 'alert_events', ['rule_type'], unique=False)
    op.create_index(op.f('ix_alert_events_triggered_at'), 'alert_events', ['triggered_at'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_alert_events_triggered_at'), table_name='alert_events')
    op.drop_index(op.f('ix_alert_events_rule_type'), table_name='alert_events')
    op.drop_table('alert_events')

    op.drop_index(op.f('ix_alert_rules_rule_type'), table_name='alert_rules')
    op.drop_table('alert_rules')

    op.drop_index(op.f('ix_dlp_events_user_id'), table_name='dlp_events')
    op.drop_index(op.f('ix_dlp_events_triggered_at'), table_name='dlp_events')
    op.drop_index(op.f('ix_dlp_events_rule_name'), table_name='dlp_events')
    op.drop_table('dlp_events')

    op.drop_table('dlp_rules')

    op.alter_column('users', 'mfa_secret',
               existing_type=sa.Text(),
               type_=sa.VARCHAR(length=200),
               existing_nullable=True)
