"""permission_enhancement - 权限系统增强

Revision ID: 009
Revises: 008
Create Date: 2026-04-13 02:00:00.000000

增强 Permission 表，新增细粒度权限控制字段
创建 AuditLog 审计日志表
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = '009'
down_revision = '008'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ==========================================
    # 1. 增强 sys_permissions 表
    # ==========================================
    
    # 新增 permission_code 字段（权限码）
    op.add_column(
        'sys_permissions',
        sa.Column('permission_code', sa.String(100), nullable=True)
    )
    
    # 先为现有数据生成 permission_code
    op.execute("""
        UPDATE sys_permissions 
        SET permission_code = resource || ':' || action
        WHERE permission_code IS NULL
    """)
    
    # 现在设置为 NOT NULL 并添加唯一索引
    op.alter_column(
        'sys_permissions',
        'permission_code',
        existing_type=sa.String(100),
        nullable=False
    )
    op.create_index(
        'ix_sys_permissions_permission_code',
        'sys_permissions',
        ['permission_code'],
        unique=True
    )
    
    # 新增 resource_path 字段（前端路由映射）
    op.add_column(
        'sys_permissions',
        sa.Column('resource_path', sa.String(200), nullable=True,
                  comment='前端路由路径(如: /agent-config)')
    )
    
    # 新增 permission_type 字段（权限类型）
    op.add_column(
        'sys_permissions',
        sa.Column('permission_type', sa.String(20), nullable=False,
                  server_default='menu',
                  comment='权限类型: menu|api|button|data')
    )
    
    # 新增 parent_id 字段（权限层次结构）
    op.add_column(
        'sys_permissions',
        sa.Column('parent_id', postgresql.UUID(as_uuid=True), nullable=True)
    )
    op.create_foreign_key(
        'fk_sys_permissions_parent',
        'sys_permissions', 'sys_permissions',
        ['parent_id'], ['id'],
        ondelete='SET NULL'
    )
    
    # 新增 sort_order 字段
    op.add_column(
        'sys_permissions',
        sa.Column('sort_order', sa.Integer(), nullable=False,
                  server_default='0',
                  comment='排序顺序')
    )
    
    # 新增 icon 字段
    op.add_column(
        'sys_permissions',
        sa.Column('icon', sa.String(100), nullable=True,
                  comment='图标标识')
    )
    
    # 新增 is_visible 字段
    op.add_column(
        'sys_permissions',
        sa.Column('is_visible', sa.Boolean(), nullable=False,
                  server_default='true',
                  comment='是否在菜单中可见')
    )
    
    # 新增 created_by 字段
    op.add_column(
        'sys_permissions',
        sa.Column('created_by', postgresql.UUID(as_uuid=True), nullable=True)
    )
    op.create_foreign_key(
        'fk_sys_permissions_created_by',
        'sys_permissions', 'sys_users',
        ['created_by'], ['id'],
        ondelete='SET NULL'
    )
    
    # 更新字段注释
    op.execute("""
        COMMENT ON COLUMN sys_permissions.resource IS '资源标识(如: agent, skill, model)'
    """)
    
    # ==========================================
    # 2. 创建 sys_audit_logs 表（如果不存在）
    # ==========================================
    
    # 检查表是否已存在
    connection = op.get_bind()
    inspector = sa.inspect(connection)
    
    if 'sys_audit_logs' not in inspector.get_table_names():
        # 表不存在，创建它
        op.create_table(
            'sys_audit_logs',
            sa.Column('id', postgresql.UUID(as_uuid=True),
                      server_default=sa.text('gen_random_uuid()'),
                      primary_key=True),
            sa.Column('tenant_id', sa.String(36),
                      server_default='default-tenant',
                      nullable=False),
            sa.Column('user_id', postgresql.UUID(as_uuid=True),
                      nullable=True),
            sa.Column('username', sa.String(100), nullable=True,
                      comment='操作用户名'),
            sa.Column('operation_type', sa.String(50), nullable=False,
                      comment='操作类型: create|update|delete|read|login|logout'),
            sa.Column('operation_module', sa.String(50), nullable=True,
                      comment='操作模块: user|role|permission|agent|skill'),
            sa.Column('operation_desc', sa.Text, nullable=True,
                      comment='操作描述'),
            sa.Column('request_method', sa.String(10), nullable=True,
                      comment='HTTP方法: GET|POST|PUT|DELETE'),
            sa.Column('request_url', sa.String(500), nullable=True,
                      comment='请求URL'),
            sa.Column('request_params', postgresql.JSONB, nullable=True,
                      comment='请求参数'),
            sa.Column('request_ip', sa.String(50), nullable=True,
                      comment='请求IP地址'),
            sa.Column('user_agent', sa.String(500), nullable=True,
                      comment='用户代理'),
            sa.Column('response_status', sa.Integer, nullable=True,
                      comment='响应状态码'),
            sa.Column('response_time_ms', sa.Integer, nullable=True,
                      comment='响应时间(毫秒)'),
            sa.Column('old_data', postgresql.JSONB, nullable=True,
                      comment='变更前数据'),
            sa.Column('new_data', postgresql.JSONB, nullable=True,
                      comment='变更后数据'),
            sa.Column('created_at', sa.DateTime(timezone=True),
                      server_default=sa.func.now(),
                      nullable=False),
            sa.ForeignKeyConstraint(['tenant_id'], ['sys_tenants.id']),
            sa.ForeignKeyConstraint(['user_id'], ['sys_users.id'], ondelete='SET NULL'),
            comment='审计日志表'
        )
        
        # 创建索引
        op.create_index(
            'ix_sys_audit_logs_tenant',
            'sys_audit_logs',
            ['tenant_id']
        )
        op.create_index(
            'idx_audit_operation',
            'sys_audit_logs',
            ['operation_type', 'operation_module']
        )
        op.create_index(
            'idx_audit_user',
            'sys_audit_logs',
            ['user_id', 'created_at']
        )
        op.create_index(
            'ix_sys_audit_logs_created_at',
            'sys_audit_logs',
            ['created_at']
        )
    else:
        print("⚠️  sys_audit_logs 表已存在，跳过创建")


def downgrade() -> None:
    # 删除 sys_audit_logs 表
    op.drop_index('ix_sys_audit_logs_created_at', table_name='sys_audit_logs')
    op.drop_index('idx_audit_user', table_name='sys_audit_logs')
    op.drop_index('idx_audit_operation', table_name='sys_audit_logs')
    op.drop_index('ix_sys_audit_logs_tenant', table_name='sys_audit_logs')
    op.drop_table('sys_audit_logs')
    
    # 删除 sys_permissions 新增字段
    op.drop_constraint('fk_sys_permissions_created_by', 'sys_permissions', type_='foreignkey')
    op.drop_column('sys_permissions', 'created_by')
    op.drop_column('sys_permissions', 'is_visible')
    op.drop_column('sys_permissions', 'icon')
    op.drop_column('sys_permissions', 'sort_order')
    op.drop_constraint('fk_sys_permissions_parent', 'sys_permissions', type_='foreignkey')
    op.drop_column('sys_permissions', 'parent_id')
    op.drop_column('sys_permissions', 'permission_type')
    op.drop_column('sys_permissions', 'resource_path')
    op.drop_index('ix_sys_permissions_permission_code', table_name='sys_permissions')
    op.drop_column('sys_permissions', 'permission_code')
