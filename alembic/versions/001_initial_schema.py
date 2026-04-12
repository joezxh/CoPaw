# -*- coding: utf-8 -*-
"""
Initial enterprise schema migration.

Creates all core tables:
  sys_users, sys_user_groups, sys_user_group_members,
  sys_departments,
  sys_roles, sys_role_permissions, sys_user_roles,
  sys_permissions,
  sys_user_sessions, sys_refresh_tokens,
  sys_audit_logs,
  ai_tasks, ai_task_comments,
  ai_workflows, ai_workflow_executions
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers
revision = "001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ── Enable pg extensions ───────────────────────────────────────────────
    op.execute('CREATE EXTENSION IF NOT EXISTS "pgcrypto"')

    # ── sys_departments ────────────────────────────────────────────────────
    op.create_table(
        "sys_departments",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            server_default=sa.text("gen_random_uuid()"),
            primary_key=True,
        ),
        sa.Column("name", sa.String(200), nullable=False),
        sa.Column("parent_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("sys_departments.id", ondelete="SET NULL"), nullable=True),
        sa.Column("manager_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("level", sa.Integer, server_default="0", nullable=False),
        sa.Column("description", sa.String(500), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_sys_departments_name", "sys_departments", ["name"])

    # ── sys_users ──────────────────────────────────────────────────────────
    op.create_table(
        "sys_users",
        sa.Column("id", postgresql.UUID(as_uuid=True), server_default=sa.text("gen_random_uuid()"), primary_key=True),
        sa.Column("username", sa.String(100), nullable=False, unique=True),
        sa.Column("email", sa.String(255), nullable=True, unique=True),
        sa.Column("password_hash", sa.String(255), nullable=False),
        sa.Column("password_salt", sa.String(64), nullable=False),
        sa.Column("display_name", sa.String(200), nullable=True),
        sa.Column("department_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("sys_departments.id", ondelete="SET NULL"), nullable=True),
        sa.Column("status", sa.String(20), server_default="active", nullable=False),
        sa.Column("mfa_enabled", sa.Boolean, server_default="false", nullable=False),
        sa.Column("mfa_secret", sa.String(200), nullable=True),
        sa.Column("last_login_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_sys_users_username", "sys_users", ["username"])
    op.create_index("ix_sys_users_email", "sys_users", ["email"])

    # Back-fill FK from sys_departments.manager_id → sys_users.id
    op.create_foreign_key(
        "fk_sys_departments_manager_id", "sys_departments", "sys_users", ["manager_id"], ["id"], ondelete="SET NULL"
    )

    # ── sys_user_groups ────────────────────────────────────────────────────
    op.create_table(
        "sys_user_groups",
        sa.Column("id", postgresql.UUID(as_uuid=True), server_default=sa.text("gen_random_uuid()"), primary_key=True),
        sa.Column("name", sa.String(200), nullable=False, unique=True),
        sa.Column("description", sa.String(500), nullable=True),
        sa.Column("department_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("sys_departments.id", ondelete="SET NULL"), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )

    # ── sys_user_group_members ─────────────────────────────────────────────
    op.create_table(
        "sys_user_group_members",
        sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("sys_users.id", ondelete="CASCADE"), primary_key=True),
        sa.Column("group_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("sys_user_groups.id", ondelete="CASCADE"), primary_key=True),
        sa.Column("joined_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )

    # ── sys_roles ──────────────────────────────────────────────────────────
    op.create_table(
        "sys_roles",
        sa.Column("id", postgresql.UUID(as_uuid=True), server_default=sa.text("gen_random_uuid()"), primary_key=True),
        sa.Column("name", sa.String(100), nullable=False, unique=True),
        sa.Column("description", sa.String(500), nullable=True),
        sa.Column("parent_role_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("sys_roles.id", ondelete="SET NULL"), nullable=True),
        sa.Column("level", sa.Integer, server_default="0", nullable=False),
        sa.Column("department_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("sys_departments.id", ondelete="SET NULL"), nullable=True),
        sa.Column("is_system_role", sa.Boolean, server_default="false", nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_sys_roles_name", "sys_roles", ["name"])

    # ── sys_permissions ────────────────────────────────────────────────────
    op.create_table(
        "sys_permissions",
        sa.Column("id", postgresql.UUID(as_uuid=True), server_default=sa.text("gen_random_uuid()"), primary_key=True),
        sa.Column("resource", sa.String(200), nullable=False),
        sa.Column("action", sa.String(50), nullable=False),
        sa.Column("description", sa.String(500), nullable=True),
    )
    op.create_index("ix_sys_permissions_resource", "sys_permissions", ["resource"])

    # ── sys_role_permissions ───────────────────────────────────────────────
    op.create_table(
        "sys_role_permissions",
        sa.Column("role_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("sys_roles.id", ondelete="CASCADE"), primary_key=True),
        sa.Column("permission_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("sys_permissions.id", ondelete="CASCADE"), primary_key=True),
        sa.Column("granted_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )

    # ── sys_user_roles ─────────────────────────────────────────────────────
    op.create_table(
        "sys_user_roles",
        sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("sys_users.id", ondelete="CASCADE"), primary_key=True),
        sa.Column("role_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("sys_roles.id", ondelete="CASCADE"), primary_key=True),
        sa.Column("assigned_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("assigned_by", postgresql.UUID(as_uuid=True), sa.ForeignKey("sys_users.id", ondelete="SET NULL"), nullable=True),
    )

    # ── sys_user_sessions ──────────────────────────────────────────────────
    op.create_table(
        "sys_user_sessions",
        sa.Column("id", postgresql.UUID(as_uuid=True), server_default=sa.text("gen_random_uuid()"), primary_key=True),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("sys_users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("access_token_jti", sa.String(64), nullable=False, unique=True),
        sa.Column("ip_address", sa.String(45), nullable=True),
        sa.Column("user_agent", sa.String(500), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("revoked", sa.Boolean, server_default="false", nullable=False),
        sa.Column("revoked_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index("ix_sys_user_sessions_user_id", "sys_user_sessions", ["user_id"])
    op.create_index("ix_sys_user_sessions_jti", "sys_user_sessions", ["access_token_jti"])
    op.create_index("ix_sys_user_sessions_expires_at", "sys_user_sessions", ["expires_at"])

    # ── sys_refresh_tokens ─────────────────────────────────────────────────
    op.create_table(
        "sys_refresh_tokens",
        sa.Column("id", postgresql.UUID(as_uuid=True), server_default=sa.text("gen_random_uuid()"), primary_key=True),
        sa.Column("session_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("sys_user_sessions.id", ondelete="CASCADE"), nullable=False),
        sa.Column("token_hash", sa.String(128), nullable=False, unique=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("used", sa.Boolean, server_default="false", nullable=False),
        sa.Column("used_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index("ix_sys_refresh_tokens_session_id", "sys_refresh_tokens", ["session_id"])

    # ── sys_audit_logs ─────────────────────────────────────────────────────
    op.create_table(
        "sys_audit_logs",
        sa.Column("id", sa.BigInteger, primary_key=True, autoincrement=True),
        sa.Column("timestamp", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("sys_users.id", ondelete="SET NULL"), nullable=True),
        sa.Column("user_role", sa.String(100), nullable=True),
        sa.Column("action_type", sa.String(100), nullable=False),
        sa.Column("resource_type", sa.String(100), nullable=False),
        sa.Column("resource_id", sa.String(200), nullable=True),
        sa.Column("action_result", sa.String(20), nullable=True),
        sa.Column("client_ip", postgresql.INET, nullable=True),
        sa.Column("client_device", postgresql.JSONB, nullable=True),
        sa.Column("context", postgresql.JSONB, nullable=True),
        sa.Column("data_before", postgresql.JSONB, nullable=True),
        sa.Column("data_after", postgresql.JSONB, nullable=True),
        sa.Column("is_sensitive", sa.Boolean, server_default="false", nullable=False),
    )
    op.create_index("idx_sys_audit_logs_timestamp", "sys_audit_logs", ["timestamp"])
    op.create_index("idx_sys_audit_logs_user_id", "sys_audit_logs", ["user_id"])
    op.create_index("idx_sys_audit_logs_action_type", "sys_audit_logs", ["action_type"])
    op.create_index("idx_sys_audit_logs_resource_type", "sys_audit_logs", ["resource_type"])

    # ── ai_workflows ───────────────────────────────────────────────────────
    op.create_table(
        "ai_workflows",
        sa.Column("id", postgresql.UUID(as_uuid=True), server_default=sa.text("gen_random_uuid()"), primary_key=True),
        sa.Column("name", sa.String(200), nullable=False),
        sa.Column("description", sa.Text, nullable=True),
        sa.Column("category", sa.String(100), nullable=True),
        sa.Column("definition", postgresql.JSONB, nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.Column("version", sa.Integer, server_default="1", nullable=False),
        sa.Column("status", sa.String(20), server_default="draft", nullable=False),
        sa.Column("creator_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("sys_users.id", ondelete="SET NULL"), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_ai_workflows_name", "ai_workflows", ["name"])
    op.create_index("ix_ai_workflows_category", "ai_workflows", ["category"])

    # ── ai_workflow_executions ─────────────────────────────────────────────
    op.create_table(
        "ai_workflow_executions",
        sa.Column("id", postgresql.UUID(as_uuid=True), server_default=sa.text("gen_random_uuid()"), primary_key=True),
        sa.Column("workflow_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("ai_workflows.id", ondelete="CASCADE"), nullable=False),
        sa.Column("triggered_by", postgresql.UUID(as_uuid=True), sa.ForeignKey("sys_users.id", ondelete="SET NULL"), nullable=True),
        sa.Column("status", sa.String(20), server_default="pending", nullable=False),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("input_data", postgresql.JSONB, nullable=True),
        sa.Column("output_data", postgresql.JSONB, nullable=True),
        sa.Column("error_message", sa.Text, nullable=True),
        sa.Column("run_metadata", postgresql.JSONB, nullable=True),
    )
    op.create_index("ix_ai_workflow_executions_workflow_id", "ai_workflow_executions", ["workflow_id"])
    op.create_index("ix_ai_workflow_executions_status", "ai_workflow_executions", ["status"])

    # ── ai_tasks ───────────────────────────────────────────────────────────
    op.create_table(
        "ai_tasks",
        sa.Column("id", postgresql.UUID(as_uuid=True), server_default=sa.text("gen_random_uuid()"), primary_key=True),
        sa.Column("title", sa.String(500), nullable=False),
        sa.Column("description", sa.Text, nullable=True),
        sa.Column("status", sa.String(20), server_default="pending", nullable=False),
        sa.Column("priority", sa.String(10), server_default="medium", nullable=False),
        sa.Column("creator_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("sys_users.id", ondelete="SET NULL"), nullable=True),
        sa.Column("assignee_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("sys_users.id", ondelete="SET NULL"), nullable=True),
        sa.Column("assignee_group_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("sys_user_groups.id", ondelete="SET NULL"), nullable=True),
        sa.Column("department_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("sys_departments.id", ondelete="SET NULL"), nullable=True),
        sa.Column("due_date", sa.DateTime(timezone=True), nullable=True),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("parent_task_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("ai_tasks.id", ondelete="SET NULL"), nullable=True),
        sa.Column("workflow_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("ai_workflows.id", ondelete="SET NULL"), nullable=True),
        sa.Column("metadata", postgresql.JSONB, nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_ai_tasks_status", "ai_tasks", ["status"])
    op.create_index("ix_ai_tasks_assignee_id", "ai_tasks", ["assignee_id"])

    # ── ai_task_comments ───────────────────────────────────────────────────
    op.create_table(
        "ai_task_comments",
        sa.Column("id", postgresql.UUID(as_uuid=True), server_default=sa.text("gen_random_uuid()"), primary_key=True),
        sa.Column("task_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("ai_tasks.id", ondelete="CASCADE"), nullable=False),
        sa.Column("author_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("sys_users.id", ondelete="SET NULL"), nullable=True),
        sa.Column("content", sa.Text, nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_ai_task_comments_task_id", "ai_task_comments", ["task_id"])

    # ── sys_workspaces ─────────────────────────────────────────────────────
    op.create_table(
        "sys_workspaces",
        sa.Column("id", postgresql.UUID(as_uuid=True), server_default=sa.text("gen_random_uuid()"), primary_key=True),
        sa.Column("name", sa.String(200), nullable=False),
        sa.Column("description", sa.String(500), nullable=True),
        sa.Column("is_default", sa.Boolean, server_default="false", nullable=False),
        sa.Column("owner_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("sys_users.id", ondelete="SET NULL"), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )

    # ── sys_workspace_members ──────────────────────────────────────────────
    op.create_table(
        "sys_workspace_members",
        sa.Column("workspace_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("sys_workspaces.id", ondelete="CASCADE"), primary_key=True),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("sys_users.id", ondelete="CASCADE"), primary_key=True),
        sa.Column("role", sa.String(50), server_default="viewer", nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )

    # ── sys_workspace_agents ───────────────────────────────────────────────
    op.create_table(
        "sys_workspace_agents",
        sa.Column("workspace_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("sys_workspaces.id", ondelete="CASCADE"), primary_key=True),
        sa.Column("agent_id", sa.String(100), primary_key=True),
        sa.Column("visibility", sa.String(50), server_default="PRIVATE", nullable=False),
    )

    # ── sys_tenants ────────────────────────────────────────────────────────
    op.create_table(
        "sys_tenants",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("name", sa.String(100), nullable=False),
        sa.Column("domain", sa.String(100), nullable=True, unique=True),
        sa.Column("is_active", sa.Boolean, server_default="true", nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=True),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
    )


def downgrade() -> None:
    op.drop_table("ai_task_comments")
    op.drop_table("ai_tasks")
    op.drop_table("ai_workflow_executions")
    op.drop_table("ai_workflows")
    op.drop_table("sys_audit_logs")
    op.drop_table("sys_refresh_tokens")
    op.drop_table("sys_user_sessions")
    op.drop_table("sys_user_roles")
    op.drop_table("sys_role_permissions")
    op.drop_table("sys_permissions")
    op.drop_table("sys_roles")
    op.drop_table("sys_user_group_members")
    op.drop_table("sys_user_groups")
    op.drop_table("sys_users")
    op.drop_table("sys_departments")
    op.drop_table("sys_workspace_agents")
    op.drop_table("sys_workspace_members")
    op.drop_table("sys_workspaces")
    op.drop_table("sys_tenants")
