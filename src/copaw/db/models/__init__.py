# -*- coding: utf-8 -*-
"""
CoPaw Enterprise ORM Models
Re-exports all models so Alembic's env.py can import a single target_metadata.
"""
from .base import Base  # noqa: F401 — must be first for metadata

# Import all models to register them with Base.metadata
from .user import User, UserGroup, UserGroupMember  # noqa: F401
from .role import Role, RolePermission, UserRole  # noqa: F401
from .permission import Permission  # noqa: F401
from .organization import Department  # noqa: F401
from .session import UserSession, RefreshToken  # noqa: F401
from .audit_log import AuditLog  # noqa: F401
from .task import Task, TaskComment  # noqa: F401
from .workflow import Workflow, WorkflowExecution  # noqa: F401
from .dlp import DLPRule, DLPEvent  # noqa: F401
from .alert import AlertRule, AlertEvent  # noqa: F401
from .dify import DifyConnector  # noqa: F401
__all__ = [
    "Base",
    "User",
    "UserGroup",
    "UserGroupMember",
    "Role",
    "RolePermission",
    "UserRole",
    "Permission",
    "Department",
    "UserSession",
    "RefreshToken",
    "AuditLog",
    "Task",
    "TaskComment",
    "Workflow",
    "WorkflowExecution",
]
