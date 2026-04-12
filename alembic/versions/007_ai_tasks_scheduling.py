"""ai_tasks_scheduling - ai_tasks表扩展调度字段

Revision ID: 007
Revises: 006
Create Date: 2026-04-12 16:35:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = '007'
down_revision = '006'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column('ai_tasks', sa.Column('schedule_expr', sa.String(100), nullable=True, comment='Cron表达式'))
    op.add_column('ai_tasks', sa.Column('next_run_at', sa.DateTime(timezone=True), nullable=True, comment='下次执行时间'))
    op.add_column('ai_tasks', sa.Column('last_run_at', sa.DateTime(timezone=True), nullable=True, comment='上次执行时间'))
    op.add_column('ai_tasks', sa.Column('run_count', sa.Integer, server_default='0', nullable=False, comment='执行次数'))
    op.add_column('ai_tasks', sa.Column('max_retries', sa.Integer, server_default='3', nullable=False, comment='最大重试次数'))
    op.add_column('ai_tasks', sa.Column('timeout_seconds', sa.Integer, server_default='300', nullable=False, comment='超时时间'))
    op.add_column('ai_tasks', sa.Column('command', sa.String(500), nullable=True, comment='执行命令'))
    op.add_column('ai_tasks', sa.Column('args', postgresql.JSONB, server_default='{}', nullable=True, comment='命令参数'))
    op.add_column('ai_tasks', sa.Column('source_storage_key', sa.String(1024), nullable=True, comment='jobs.json存储键'))
    
    op.create_index('ix_ai_tasks_schedule', 'ai_tasks', ['schedule_expr'])
    op.create_index('ix_ai_tasks_next_run', 'ai_tasks', ['next_run_at'])


def downgrade() -> None:
    op.drop_index('ix_ai_tasks_next_run', table_name='ai_tasks')
    op.drop_index('ix_ai_tasks_schedule', table_name='ai_tasks')
    op.drop_column('ai_tasks', 'source_storage_key')
    op.drop_column('ai_tasks', 'args')
    op.drop_column('ai_tasks', 'command')
    op.drop_column('ai_tasks', 'timeout_seconds')
    op.drop_column('ai_tasks', 'max_retries')
    op.drop_column('ai_tasks', 'run_count')
    op.drop_column('ai_tasks', 'last_run_at')
    op.drop_column('ai_tasks', 'next_run_at')
    op.drop_column('ai_tasks', 'schedule_expr')
