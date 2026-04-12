"""ai_memories_pgvector - 记忆向量表 + pgvector扩展

Revision ID: 006
Revises: 005
Create Date: 2026-04-12 16:30:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = '006'
down_revision = '005'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # 启用 pgvector 扩展
    op.execute('CREATE EXTENSION IF NOT EXISTS vector')

    # ai_memories
    op.create_table(
        'ai_memories',
        sa.Column('id', postgresql.UUID(as_uuid=True), server_default=sa.text('gen_random_uuid()'), primary_key=True),
        sa.Column('tenant_id', sa.String(36), server_default='default-tenant', nullable=False),
        sa.Column('workspace_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('agent_id', sa.String(100), nullable=True),
        sa.Column('content', sa.Text, nullable=False),
        sa.Column('content_hash', sa.String(64), nullable=True),
        sa.Column('embedding', sa.Text, nullable=True, comment='向量嵌入 (JSON数组字符串)'),
        sa.Column('embedding_model', sa.String(100), nullable=True),
        sa.Column('category', sa.String(50), nullable=True),
        sa.Column('importance', sa.Float, server_default='0.5', nullable=False),
        sa.Column('metadata', postgresql.JSONB, nullable=True),
        sa.Column('tags', postgresql.ARRAY(sa.String), server_default='{}', nullable=False),
        sa.Column('access_count', sa.Integer, server_default='0', nullable=False),
        sa.Column('last_accessed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('archived_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['workspace_id'], ['sys_workspaces.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['user_id'], ['sys_users.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['tenant_id'], ['sys_tenants.id']),
        comment='AI 记忆条目表'
    )
    
    # 索引
    op.create_index('ix_ai_memories_tenant', 'ai_memories', ['tenant_id'])
    op.create_index('ix_ai_memories_workspace', 'ai_memories', ['workspace_id'])
    op.create_index('ix_ai_memories_user', 'ai_memories', ['user_id'])
    op.create_index('ix_ai_memories_category', 'ai_memories', ['category'])
    op.create_index('ix_ai_memories_importance', 'ai_memories', ['importance'])
    op.create_index('ix_ai_memories_created', 'ai_memories', ['created_at'])
    op.create_index('ix_ai_memories_tags', 'ai_memories', ['tags'], postgresql_using='gin')
    op.create_index('ix_ai_memories_content_hash', 'ai_memories', ['content_hash'])
    
    # 向量索引 (IVFFlat)
    op.execute(
        "CREATE INDEX ix_ai_memories_embedding ON ai_memories "
        "USING ivfflat (embedding vector_cosine_ops) WITH (lists = 100)"
    )

    # ai_memory_tags
    op.create_table(
        'ai_memory_tags',
        sa.Column('id', postgresql.UUID(as_uuid=True), server_default=sa.text('gen_random_uuid()'), primary_key=True),
        sa.Column('tenant_id', sa.String(36), server_default='default-tenant', nullable=False),
        sa.Column('memory_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('tag_name', sa.String(100), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(['memory_id'], ['ai_memories.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['tenant_id'], ['sys_tenants.id']),
        comment='记忆标签关联表'
    )
    op.create_index('ix_ai_memory_tags_memory', 'ai_memory_tags', ['memory_id'])
    op.create_index('ix_ai_memory_tags_tag', 'ai_memory_tags', ['tag_name'])

    # ai_memory_sessions
    op.create_table(
        'ai_memory_sessions',
        sa.Column('id', postgresql.UUID(as_uuid=True), server_default=sa.text('gen_random_uuid()'), primary_key=True),
        sa.Column('tenant_id', sa.String(36), server_default='default-tenant', nullable=False),
        sa.Column('workspace_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('agent_id', sa.String(100), nullable=True),
        sa.Column('session_name', sa.String(200), nullable=True),
        sa.Column('started_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('ended_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('is_active', sa.Boolean, server_default='true', nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(['workspace_id'], ['sys_workspaces.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['user_id'], ['sys_users.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['tenant_id'], ['sys_tenants.id']),
        comment='记忆会话上下文表'
    )
    op.create_index('ix_ai_memory_sessions_workspace', 'ai_memory_sessions', ['workspace_id'])
    op.create_index('ix_ai_memory_sessions_user', 'ai_memory_sessions', ['user_id'])
    op.create_index('ix_ai_memory_sessions_started', 'ai_memory_sessions', ['started_at'])

    # ai_memory_session_links
    op.create_table(
        'ai_memory_session_links',
        sa.Column('id', postgresql.UUID(as_uuid=True), server_default=sa.text('gen_random_uuid()'), primary_key=True),
        sa.Column('tenant_id', sa.String(36), server_default='default-tenant', nullable=False),
        sa.Column('session_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('memory_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('relevance_score', sa.Float, server_default='0.0', nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(['session_id'], ['ai_memory_sessions.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['memory_id'], ['ai_memories.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['tenant_id'], ['sys_tenants.id']),
        comment='会话-记忆关联表'
    )
    op.create_index('ix_ai_memory_links_session', 'ai_memory_session_links', ['session_id'])
    op.create_index('ix_ai_memory_links_memory', 'ai_memory_session_links', ['memory_id'])


def downgrade() -> None:
    op.drop_table('ai_memory_session_links')
    op.drop_table('ai_memory_sessions')
    op.drop_table('ai_memory_tags')
    op.drop_index('ix_ai_memories_embedding', table_name='ai_memories')
    op.drop_table('ai_memories')
    op.execute('DROP EXTENSION IF EXISTS vector')
