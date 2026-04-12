"""storage_objects - 通用文件对象索引表

Revision ID: 004
Revises: 003
Create Date: 2026-04-12 16:20:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '004'
down_revision = '003'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        'storage_objects',
        sa.Column('id', postgresql.UUID(as_uuid=True), server_default=sa.text('gen_random_uuid()'), primary_key=True),
        sa.Column('tenant_id', sa.String(36), server_default='default-tenant', nullable=False),
        sa.Column('object_key', sa.String(1024), nullable=False, comment='对象存储中的键'),
        sa.Column('bucket', sa.String(200), server_default='copaw-data', nullable=False, comment='存储桶名称'),
        sa.Column('file_name', sa.String(500), nullable=False, comment='文件名'),
        sa.Column('file_ext', sa.String(50), nullable=True, comment='扩展名'),
        sa.Column('content_type', sa.String(200), nullable=True, comment='MIME 类型'),
        sa.Column('file_size', sa.BigInteger, server_default='0', nullable=False, comment='文件大小'),
        sa.Column('category', sa.String(50), nullable=False, comment='文件类别'),
        sa.Column('version_id', sa.String(200), nullable=True, comment='对象版本ID'),
        sa.Column('etag', sa.String(200), nullable=True, comment='ETag'),
        sa.Column('workspace_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('search_text', sa.Text, nullable=True, comment='全文搜索文本'),
        sa.Column('tags', postgresql.ARRAY(sa.String), server_default='{}', nullable=False, comment='标签'),
        sa.Column('custom_metadata', postgresql.JSONB, nullable=True, comment='扩展元数据'),
        sa.Column('storage_class', sa.String(50), server_default='STANDARD', nullable=False),
        sa.Column('content_hash', sa.String(64), nullable=True, comment='SHA-256内容哈希'),
        sa.Column('is_latest', sa.Boolean, server_default='true', nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True, comment='软删除时间'),
        sa.ForeignKeyConstraint(['workspace_id'], ['sys_workspaces.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['user_id'], ['sys_users.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['tenant_id'], ['sys_tenants.id']),
        comment='通用文件对象索引表'
    )

    # 创建索引
    op.create_index('ix_storage_objects_tenant', 'storage_objects', ['tenant_id'])
    op.create_index('ix_storage_objects_workspace', 'storage_objects', ['workspace_id'])
    op.create_index('ix_storage_objects_category', 'storage_objects', ['category'])
    op.create_index('ix_storage_objects_tags', 'storage_objects', ['tags'], postgresql_using='gin')
    op.create_index('ix_storage_objects_created', 'storage_objects', ['created_at'])
    
    # 唯一索引（partial index）
    op.create_index(
        'ix_storage_objects_key',
        'storage_objects',
        ['object_key'],
        unique=True,
        postgresql_where=sa.text('deleted_at IS NULL')
    )
    
    # 全文搜索索引
    op.execute(
        "CREATE INDEX ix_storage_objects_search ON storage_objects USING GIN("
        "to_tsvector('simple', COALESCE(search_text, ''))"
        ")"
    )


def downgrade() -> None:
    op.drop_index('ix_storage_objects_search', table_name='storage_objects')
    op.drop_index('ix_storage_objects_key', table_name='storage_objects')
    op.drop_index('ix_storage_objects_created', table_name='storage_objects')
    op.drop_index('ix_storage_objects_tags', table_name='storage_objects')
    op.drop_index('ix_storage_objects_category', table_name='storage_objects')
    op.drop_index('ix_storage_objects_workspace', table_name='storage_objects')
    op.drop_index('ix_storage_objects_tenant', table_name='storage_objects')
    op.drop_table('storage_objects')
