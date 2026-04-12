"""enterprise_phase_c

Revision ID: 003
Revises: 002
Create Date: 2026-04-11 16:50:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '003'
down_revision = '002'
branch_labels = None
depends_on = None

def upgrade() -> None:
    # Note: sys_tenants table is already created in 001_initial_schema.py
    # Just need to add tenant_id to all core tables
    tables = [
        'sys_alert_rules', 'sys_alert_events', 'sys_audit_logs', 'ai_dify_connectors',
        'sys_dlp_rules', 'sys_dlp_events', 'sys_departments', 'sys_permissions', 'sys_role_permissions',
        'sys_roles', 'sys_user_sessions', 'sys_refresh_tokens', 'ai_tasks', 'ai_task_comments',
        'sys_users', 'sys_user_groups', 'sys_user_group_members', 'sys_user_roles',
        'ai_workflows', 'sys_workspaces', 'sys_workspace_members', 'sys_workspace_agents'
    ]

    for table in tables:
        op.add_column(table, sa.Column('tenant_id', sa.String(length=36), server_default='default-tenant', nullable=True))
        op.create_index(f'ix_{table}_tenant_id', table, ['tenant_id'], unique=False)
        op.create_foreign_key(f'fk_{table}_tenant_id', table, 'sys_tenants', ['tenant_id'], ['id'])


def downgrade() -> None:
    tables = [
        'sys_alert_rules', 'sys_alert_events', 'sys_audit_logs', 'ai_dify_connectors',
        'sys_dlp_rules', 'sys_dlp_events', 'sys_departments', 'sys_permissions', 'sys_role_permissions',
        'sys_roles', 'sys_user_sessions', 'sys_refresh_tokens', 'ai_tasks', 'ai_task_comments',
        'sys_users', 'sys_user_groups', 'sys_user_group_members', 'sys_user_roles',
        'ai_workflows', 'sys_workspaces', 'sys_workspace_members', 'sys_workspace_agents'
    ]

    for table in reversed(tables):
        op.drop_constraint(f'fk_{table}_tenant_id', table, type_='foreignkey')
        op.drop_index(f'ix_{table}_tenant_id', table_name=table)
        op.drop_column(table, 'tenant_id')

    # Note: sys_tenants table is dropped in 001_initial_schema.py downgrade
