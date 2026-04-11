"""enterprise_phase_c

Revision ID: 003_enterprise_phase_c
Revises: 002_enterprise_phase_a
Create Date: 2026-04-11 16:50:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '003_enterprise_phase_c'
down_revision = '002_enterprise_phase_a'
branch_labels = None
depends_on = None

def upgrade() -> None:
    # 1. Create tenants table
    op.create_table('tenants',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('name', sa.String(length=100), nullable=False),
        sa.Column('domain', sa.String(length=100), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('domain')
    )

    # 2. Add tenant_id to all core tables
    tables = [
        'alert_rules', 'alert_events', 'audit_logs', 'dify_connectors',
        'dlp_rules', 'dlp_events', 'departments', 'permissions', 'role_permissions',
        'roles', 'user_sessions', 'refresh_tokens', 'tasks', 'task_comments',
        'users', 'user_groups', 'user_group_members', 'workflows', 'workflow_phases',
        'workflow_connections'
    ]

    for table in tables:
        op.add_column(table, sa.Column('tenant_id', sa.String(length=36), server_default='default-tenant', nullable=True))
        op.create_index(f'ix_{table}_tenant_id', table, ['tenant_id'], unique=False)
        op.create_foreign_key(f'fk_{table}_tenant_id', table, 'tenants', ['tenant_id'], ['id'])


def downgrade() -> None:
    tables = [
        'alert_rules', 'alert_events', 'audit_logs', 'dify_connectors',
        'dlp_rules', 'dlp_events', 'departments', 'permissions', 'role_permissions',
        'roles', 'user_sessions', 'refresh_tokens', 'tasks', 'task_comments',
        'users', 'user_groups', 'user_group_members', 'workflows', 'workflow_phases',
        'workflow_connections'
    ]

    for table in reversed(tables):
        op.drop_constraint(f'fk_{table}_tenant_id', table, type_='foreignkey')
        op.drop_index(f'ix_{table}_tenant_id', table_name=table)
        op.drop_column(table, 'tenant_id')

    op.drop_table('tenants')
