"""ai_model_registry - 模型注册表

Revision ID: 008
Revises: 007
Create Date: 2026-04-12 16:40:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = '008'
down_revision = '007'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ai_model_registry
    op.create_table(
        'ai_model_registry',
        sa.Column('id', postgresql.UUID(as_uuid=True), server_default=sa.text('gen_random_uuid()'), primary_key=True),
        sa.Column('tenant_id', sa.String(36), server_default='default-tenant', nullable=False),
        sa.Column('model_name', sa.String(200), nullable=False),
        sa.Column('model_type', sa.String(50), nullable=False),
        sa.Column('architecture', sa.String(100), nullable=True),
        sa.Column('storage_key', sa.String(1024), nullable=True),
        sa.Column('file_size', sa.BigInteger, nullable=True),
        sa.Column('quantization', sa.String(50), nullable=True),
        sa.Column('default_params', postgresql.JSONB, server_default='{}', nullable=True),
        sa.Column('min_gpu_memory', sa.Integer, nullable=True),
        sa.Column('min_ram', sa.Integer, nullable=True),
        sa.Column('is_available', sa.Boolean, server_default='true', nullable=False),
        sa.Column('health_status', sa.String(20), server_default='unknown', nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(['tenant_id'], ['sys_tenants.id']),
        comment='AI 模型注册表'
    )
    op.create_index('ix_ai_model_registry_tenant', 'ai_model_registry', ['tenant_id'])
    op.create_index('ix_ai_model_registry_type', 'ai_model_registry', ['model_type'])

    # ai_inference_tasks
    op.create_table(
        'ai_inference_tasks',
        sa.Column('id', postgresql.UUID(as_uuid=True), server_default=sa.text('gen_random_uuid()'), primary_key=True),
        sa.Column('tenant_id', sa.String(36), server_default='default-tenant', nullable=False),
        sa.Column('model_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('workspace_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('task_type', sa.String(50), nullable=False),
        sa.Column('input_data', postgresql.JSONB, nullable=False),
        sa.Column('output_data', postgresql.JSONB, nullable=True),
        sa.Column('status', sa.String(20), server_default='pending', nullable=False),
        sa.Column('worker_id', sa.String(100), nullable=True),
        sa.Column('prompt_tokens', sa.Integer, server_default='0', nullable=False),
        sa.Column('completion_tokens', sa.Integer, server_default='0', nullable=False),
        sa.Column('error_message', sa.Text, nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('started_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('completed_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['model_id'], ['ai_model_registry.id']),
        sa.ForeignKeyConstraint(['user_id'], ['sys_users.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['workspace_id'], ['sys_workspaces.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['tenant_id'], ['sys_tenants.id']),
        comment='AI 推理任务表'
    )
    op.create_index('ix_ai_inference_tasks_status', 'ai_inference_tasks', ['status'])
    op.create_index('ix_ai_inference_tasks_tenant', 'ai_inference_tasks', ['tenant_id'])

    # ai_skill_registry
    op.create_table(
        'ai_skill_registry',
        sa.Column('id', postgresql.UUID(as_uuid=True), server_default=sa.text('gen_random_uuid()'), primary_key=True),
        sa.Column('tenant_id', sa.String(36), server_default='default-tenant', nullable=False),
        sa.Column('skill_name', sa.String(200), nullable=False),
        sa.Column('version', sa.String(50), nullable=False),
        sa.Column('description', sa.Text, nullable=True),
        sa.Column('storage_key', sa.String(1024), nullable=True),
        sa.Column('is_active', sa.Boolean, server_default='true', nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(['tenant_id'], ['sys_tenants.id']),
        comment='AI 技能注册表'
    )
    op.create_index('ix_ai_skill_registry_tenant', 'ai_skill_registry', ['tenant_id'])
    op.create_index('ix_ai_skill_registry_name', 'ai_skill_registry', ['skill_name'])


def downgrade() -> None:
    op.drop_table('ai_skill_registry')
    op.drop_table('ai_inference_tasks')
    op.drop_table('ai_model_registry')
