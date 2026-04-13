# -*- coding: utf-8 -*-
"""
Remove user group module and related tables.

This migration:
1. Drops the assignee_group_id foreign key and column from ai_tasks
2. Drops the sys_user_group_members association table
3. Drops the sys_user_groups table

The Department model already provides hierarchical organization management
with tree structure support, making UserGroup redundant.
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers
revision = "004"
down_revision = "003"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Remove assignee_group_id from ai_tasks (foreign key dependency)
    op.drop_constraint(
        "ai_tasks_assignee_group_id_fkey",
        "ai_tasks",
        type_="foreignkey"
    )
    op.drop_column("ai_tasks", "assignee_group_id")
    
    # Drop user group association table
    op.drop_table("sys_user_group_members")
    
    # Drop user group table
    op.drop_table("sys_user_groups")


def downgrade() -> None:
    # Recreate sys_user_groups table
    op.create_table(
        "sys_user_groups",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            sa.server_default=sa.text("gen_random_uuid()"),
            primary_key=True,
        ),
        sa.Column("name", sa.String(200), nullable=False, unique=True),
        sa.Column("description", sa.String(500), nullable=True),
        sa.Column(
            "department_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("sys_departments.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
    )
    
    # Recreate sys_user_group_members association table
    op.create_table(
        "sys_user_group_members",
        sa.Column(
            "user_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("sys_users.id", ondelete="CASCADE"),
            primary_key=True,
        ),
        sa.Column(
            "group_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("sys_user_groups.id", ondelete="CASCADE"),
            primary_key=True,
        ),
        sa.Column(
            "joined_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
    )
    
    # Restore assignee_group_id column in ai_tasks
    op.add_column(
        "ai_tasks",
        sa.Column(
            "assignee_group_id",
            postgresql.UUID(as_uuid=True),
            nullable=True,
        ),
    )
    op.create_foreign_key(
        "ai_tasks_assignee_group_id_fkey",
        "ai_tasks",
        "sys_user_groups",
        ["assignee_group_id"],
        ["id"],
        ondelete="SET NULL",
    )
