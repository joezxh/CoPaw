# -*- coding: utf-8 -*-
"""
CoPaw Enterprise ORM Models
Re-exports all models so Alembic's env.py can import a single target_metadata.
"""
from .base import Base  # noqa: F401 — must be first for metadata

# Import all models to register them with Base.metadata
from .user import User  # noqa: F401
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
from .workspace import Workspace, WorkspaceMember, WorkspaceAgent  # noqa: F401
from .tenant import Tenant  # noqa: F401

# Phase 3: Storage metadata models
from .storage_meta import (  # noqa: F401
    StorageObject,
    AgentConfig,
    SkillConfig,
    Conversation,
    ConversationMessage,
    TokenUsageStat,
    MemoryDocument,
    ChannelMessage,
)

# Phase 3: Memory vector models (pgvector)
from .memory import (  # noqa: F401
    AIMemory,
    MemoryTag,
    MemorySession,
    MemorySessionLink,
)
__all__ = [
    "Base",
    "User",
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
    "DLPRule",
    "DLPEvent",
    "AlertRule",
    "AlertEvent",
    "DifyConnector",
    "Workspace",
    "WorkspaceMember",
    "WorkspaceAgent",
    "Tenant",
    # Phase 3: Storage metadata
    "StorageObject",
    "AgentConfig",
    "SkillConfig",
    "Conversation",
    "ConversationMessage",
    "TokenUsageStat",
    "MemoryDocument",
    "ChannelMessage",
    # Phase 3: Memory vectors
    "AIMemory",
    "MemoryTag",
    "MemorySession",
    "MemorySessionLink",
]
