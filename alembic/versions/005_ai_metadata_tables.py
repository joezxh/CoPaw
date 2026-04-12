"""ai_metadata_tables - 业务元数据表

Revision ID: 005
Revises: 004
Create Date: 2026-04-12 16:25:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = '005'
down_revision = '004'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ai_agent_configs
    op.create_table(
        'ai_agent_configs',
        sa.Column('id', postgresql.UUID(as_uuid=True), server_default=sa.text('gen_random_uuid()'), primary_key=True),
        sa.Column('tenant_id', sa.String(36), server_default='default-tenant', nullable=False),
        sa.Column('workspace_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('agent_id', sa.String(100), nullable=False),
        sa.Column('name', sa.String(200), nullable=False),
        sa.Column('description', sa.Text, nullable=True),
        sa.Column('model_provider', sa.String(100), nullable=True),
        sa.Column('model_name', sa.String(200), nullable=True),
        sa.Column('model_base_url', sa.String(500), nullable=True),
        sa.Column('temperature', sa.Float, nullable=True),
        sa.Column('max_tokens', sa.Integer, nullable=True),
        sa.Column('enabled_channels', postgresql.ARRAY(sa.String), nullable=True),
        sa.Column('memory_backend', sa.String(50), nullable=True),
        sa.Column('memory_max_messages', sa.Integer, nullable=True),
        sa.Column('skills', postgresql.ARRAY(sa.String), nullable=True),
        sa.Column('heartbeat_enabled', sa.Boolean, nullable=True),
        sa.Column('heartbeat_every', sa.String(20), nullable=True),
        sa.Column('storage_key', sa.String(1024), nullable=True),
        sa.Column('content_hash', sa.String(64), nullable=True),
        sa.Column('status', sa.String(20), server_default='active', nullable=False),
        sa.Column('last_synced_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(['workspace_id'], ['sys_workspaces.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['user_id'], ['sys_users.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['tenant_id'], ['sys_tenants.id']),
        comment='Agent 配置元数据表'
    )
    op.create_index('ix_ai_agent_configs_tenant', 'ai_agent_configs', ['tenant_id'])
    op.create_index('ix_ai_agent_configs_workspace', 'ai_agent_configs', ['workspace_id'])
    op.create_index('ix_ai_agent_configs_agent_id', 'ai_agent_configs', ['agent_id'])
    op.create_index('ix_ai_agent_configs_provider', 'ai_agent_configs', ['model_provider'])
    op.create_index('ix_ai_agent_configs_skills', 'ai_agent_configs', ['skills'], postgresql_using='gin')

    # ai_skill_configs
    op.create_table(
        'ai_skill_configs',
        sa.Column('id', postgresql.UUID(as_uuid=True), server_default=sa.text('gen_random_uuid()'), primary_key=True),
        sa.Column('tenant_id', sa.String(36), server_default='default-tenant', nullable=False),
        sa.Column('workspace_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('skill_name', sa.String(200), nullable=False),
        sa.Column('display_name', sa.String(200), nullable=True),
        sa.Column('description', sa.Text, nullable=True),
        sa.Column('version', sa.String(50), server_default='1.0.0', nullable=False),
        sa.Column('source', sa.String(50), nullable=True),
        sa.Column('category', sa.String(50), nullable=True),
        sa.Column('enabled', sa.Boolean, server_default='true', nullable=False),
        sa.Column('channels', postgresql.ARRAY(sa.String), server_default='{}', nullable=False),
        sa.Column('storage_key', sa.String(1024), nullable=True),
        sa.Column('skill_dir_key', sa.String(1024), nullable=True),
        sa.Column('content_hash', sa.String(64), nullable=True),
        sa.Column('last_synced_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(['workspace_id'], ['sys_workspaces.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['user_id'], ['sys_users.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['tenant_id'], ['sys_tenants.id']),
        comment='Skill 配置元数据表'
    )
    op.create_index('ix_ai_skill_configs_tenant', 'ai_skill_configs', ['tenant_id'])
    op.create_index('ix_ai_skill_configs_workspace', 'ai_skill_configs', ['workspace_id'])
    op.create_index('ix_ai_skill_configs_name', 'ai_skill_configs', ['skill_name'])
    op.create_index('ix_ai_skill_configs_source', 'ai_skill_configs', ['source'])

    # ai_conversations
    op.create_table(
        'ai_conversations',
        sa.Column('id', postgresql.UUID(as_uuid=True), server_default=sa.text('gen_random_uuid()'), primary_key=True),
        sa.Column('tenant_id', sa.String(36), server_default='default-tenant', nullable=False),
        sa.Column('workspace_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('agent_id', sa.String(100), nullable=True),
        sa.Column('chat_id', sa.String(100), nullable=False),
        sa.Column('title', sa.String(500), nullable=True),
        sa.Column('message_count', sa.Integer, server_default='0', nullable=False),
        sa.Column('started_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('last_message_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('storage_key', sa.String(1024), nullable=True),
        sa.Column('content_hash', sa.String(64), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(['workspace_id'], ['sys_workspaces.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['user_id'], ['sys_users.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['tenant_id'], ['sys_tenants.id']),
        comment='对话元数据表'
    )
    op.create_index('ix_ai_conversations_tenant', 'ai_conversations', ['tenant_id'])
    op.create_index('ix_ai_conversations_workspace', 'ai_conversations', ['workspace_id'])
    op.create_index('ix_ai_conversations_chat_id', 'ai_conversations', ['chat_id'])
    op.create_index('ix_ai_conversations_agent', 'ai_conversations', ['agent_id'])
    op.create_index('ix_ai_conversations_started', 'ai_conversations', ['started_at'])

    # ai_conversation_messages
    op.create_table(
        'ai_conversation_messages',
        sa.Column('id', postgresql.UUID(as_uuid=True), server_default=sa.text('gen_random_uuid()'), primary_key=True),
        sa.Column('tenant_id', sa.String(36), server_default='default-tenant', nullable=False),
        sa.Column('conversation_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('role', sa.String(20), nullable=False),
        sa.Column('content', sa.Text, nullable=False),
        sa.Column('timestamp', sa.DateTime(timezone=True), nullable=False),
        sa.Column('tool_calls', postgresql.JSONB, nullable=True),
        sa.Column('tool_call_id', sa.String(100), nullable=True),
        sa.Column('token_count', sa.Integer, nullable=True),
        sa.Column('metadata', postgresql.JSONB, nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(['conversation_id'], ['ai_conversations.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['tenant_id'], ['sys_tenants.id']),
        comment='对话消息表'
    )
    op.create_index('ix_ai_conv_msgs_conversation', 'ai_conversation_messages', ['conversation_id'])
    op.create_index('ix_ai_conv_msgs_role', 'ai_conversation_messages', ['role'])
    op.create_index('ix_ai_conv_msgs_tenant', 'ai_conversation_messages', ['tenant_id'])

    # ai_token_usage_stats
    op.create_table(
        'ai_token_usage_stats',
        sa.Column('id', postgresql.UUID(as_uuid=True), server_default=sa.text('gen_random_uuid()'), primary_key=True),
        sa.Column('tenant_id', sa.String(36), server_default='default-tenant', nullable=False),
        sa.Column('workspace_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('agent_id', sa.String(100), nullable=True),
        sa.Column('stat_date', sa.Date, nullable=False),
        sa.Column('prompt_tokens', sa.BigInteger, server_default='0', nullable=False),
        sa.Column('completion_tokens', sa.BigInteger, server_default='0', nullable=False),
        sa.Column('total_tokens', sa.BigInteger, server_default='0', nullable=False),
        sa.Column('request_count', sa.Integer, server_default='0', nullable=False),
        sa.Column('cost_usd', sa.Numeric(10, 6), server_default='0', nullable=False),
        sa.Column('model_provider', sa.String(100), nullable=True),
        sa.Column('model_name', sa.String(200), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(['workspace_id'], ['sys_workspaces.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['user_id'], ['sys_users.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['tenant_id'], ['sys_tenants.id']),
        sa.UniqueConstraint('tenant_id', 'workspace_id', 'agent_id', 'stat_date', 'model_provider', 'model_name', name='uq_token_usage_unique'),
        comment='Token 使用统计表'
    )
    op.create_index('ix_ai_token_usage_tenant', 'ai_token_usage_stats', ['tenant_id'])
    op.create_index('ix_ai_token_usage_date', 'ai_token_usage_stats', ['stat_date'])
    op.create_index('ix_ai_token_usage_workspace', 'ai_token_usage_stats', ['workspace_id'])
    op.create_index('ix_ai_token_usage_agent', 'ai_token_usage_stats', ['agent_id'])

    # ai_memory_documents
    op.create_table(
        'ai_memory_documents',
        sa.Column('id', postgresql.UUID(as_uuid=True), server_default=sa.text('gen_random_uuid()'), primary_key=True),
        sa.Column('tenant_id', sa.String(36), server_default='default-tenant', nullable=False),
        sa.Column('workspace_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('agent_id', sa.String(100), nullable=True),
        sa.Column('doc_type', sa.String(50), nullable=False),
        sa.Column('doc_date', sa.Date, nullable=True),
        sa.Column('title', sa.String(500), nullable=True),
        sa.Column('summary', sa.Text, nullable=True),
        sa.Column('headings', postgresql.ARRAY(sa.String), nullable=True),
        sa.Column('tags', postgresql.ARRAY(sa.String), server_default='{}', nullable=False),
        sa.Column('storage_key', sa.String(1024), nullable=False),
        sa.Column('content_hash', sa.String(64), nullable=True),
        sa.Column('file_size', sa.BigInteger, server_default='0', nullable=False),
        sa.Column('last_synced_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['workspace_id'], ['sys_workspaces.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['user_id'], ['sys_users.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['tenant_id'], ['sys_tenants.id']),
        comment='记忆文档元数据表'
    )
    op.create_index('ix_ai_memory_docs_tenant', 'ai_memory_documents', ['tenant_id'])
    op.create_index('ix_ai_memory_docs_workspace', 'ai_memory_documents', ['workspace_id'])
    op.create_index('ix_ai_memory_docs_type', 'ai_memory_documents', ['doc_type'])
    op.create_index('ix_ai_memory_docs_date', 'ai_memory_documents', ['doc_date'])
    op.create_index('ix_ai_memory_docs_tags', 'ai_memory_documents', ['tags'], postgresql_using='gin')

    # ai_channel_messages
    op.create_table(
        'ai_channel_messages',
        sa.Column('id', postgresql.UUID(as_uuid=True), server_default=sa.text('gen_random_uuid()'), primary_key=True),
        sa.Column('tenant_id', sa.String(36), server_default='default-tenant', nullable=False),
        sa.Column('workspace_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('agent_id', sa.String(100), nullable=True),
        sa.Column('channel_type', sa.String(50), nullable=False),
        sa.Column('channel_id', sa.String(200), nullable=True),
        sa.Column('message_id', sa.String(200), nullable=True),
        sa.Column('direction', sa.String(20), nullable=False),
        sa.Column('content_type', sa.String(50), server_default='text', nullable=False),
        sa.Column('content', sa.Text, nullable=True),
        sa.Column('sender_id', sa.String(200), nullable=True),
        sa.Column('sender_name', sa.String(200), nullable=True),
        sa.Column('is_bot', sa.Boolean, server_default='false', nullable=False),
        sa.Column('reply_to_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('conversation_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('task_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('media_keys', postgresql.ARRAY(sa.String), server_default='{}', nullable=False),
        sa.Column('processing_status', sa.String(20), server_default='pending', nullable=False),
        sa.Column('processed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('dlp_checked', sa.Boolean, server_default='false', nullable=False),
        sa.Column('dlp_violations', postgresql.JSONB, nullable=True),
        sa.Column('timestamp', sa.DateTime(timezone=True), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(['workspace_id'], ['sys_workspaces.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['user_id'], ['sys_users.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['tenant_id'], ['sys_tenants.id']),
        sa.ForeignKeyConstraint(['reply_to_id'], ['ai_channel_messages.id']),
        sa.ForeignKeyConstraint(['conversation_id'], ['ai_conversations.id']),
        sa.ForeignKeyConstraint(['task_id'], ['ai_tasks.id']),
        comment='通道消息表'
    )
    op.create_index('ix_ai_channel_msgs_tenant', 'ai_channel_messages', ['tenant_id'])
    op.create_index('ix_ai_channel_msgs_channel', 'ai_channel_messages', ['channel_type'])
    op.create_index('ix_ai_channel_msgs_workspace', 'ai_channel_messages', ['workspace_id'])
    op.create_index('ix_ai_channel_msgs_timestamp', 'ai_channel_messages', ['timestamp'])
    op.create_index('ix_ai_channel_msgs_sender', 'ai_channel_messages', ['sender_id'])
    op.create_index('ix_ai_channel_msgs_direction', 'ai_channel_messages', ['direction'])
    op.create_index('ix_ai_channel_msgs_processing', 'ai_channel_messages', ['processing_status'])


def downgrade() -> None:
    op.drop_table('ai_channel_messages')
    op.drop_table('ai_memory_documents')
    op.drop_table('ai_token_usage_stats')
    op.drop_table('ai_conversation_messages')
    op.drop_table('ai_conversations')
    op.drop_table('ai_skill_configs')
    op.drop_table('ai_agent_configs')
