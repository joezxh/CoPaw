# -*- coding: utf-8 -*-
"""
AI Memory ORM Models — 向量记忆模型 (pgvector)

定义企业版 PostgreSQL + pgvector 记忆存储表：
- ai_memories: 记忆条目（含向量嵌入）
- ai_memory_tags: 记忆标签关联
- ai_memory_sessions: 记忆会话上下文
- ai_memory_session_links: 会话-记忆关联
"""
from __future__ import annotations

import uuid
from datetime import datetime
from typing import TYPE_CHECKING, List, Optional

from sqlalchemy import (
    BigInteger,
    Boolean,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
    func,
    Index,
)
from sqlalchemy.dialects.postgresql import ARRAY, JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base, TenantAwareMixin, TimestampMixin, UUIDPrimaryKeyMixin

if TYPE_CHECKING:
    from .workspace import Workspace
    from .user import User


class AIMemory(Base, UUIDPrimaryKeyMixin, TimestampMixin, TenantAwareMixin):
    """AI 记忆条目表 — 企业版向量记忆存储"""

    __tablename__ = "ai_memories"
    __table_args__ = (
        Index("ix_ai_memories_tenant", "tenant_id"),
        Index("ix_ai_memories_workspace", "workspace_id"),
        Index("ix_ai_memories_user", "user_id"),
        Index("ix_ai_memories_category", "category"),
        Index("ix_ai_memories_importance", "importance"),
        Index("ix_ai_memories_created", "created_at"),
        Index("ix_ai_memories_tags", "tags", postgresql_using="gin"),
        Index("ix_ai_memories_content_hash", "content_hash"),
        # 向量索引将在 Alembic 迁移中创建 (IVFFlat)
        {"comment": "AI 记忆条目表 — 企业版向量记忆存储"},
    )

    workspace_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("sys_workspaces.id", ondelete="CASCADE"),
        nullable=True,
        comment="所属工作空间 ID"
    )
    user_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("sys_users.id", ondelete="SET NULL"),
        nullable=True,
        comment="所有者用户 ID"
    )
    agent_id: Mapped[Optional[str]] = mapped_column(
        String(100), nullable=True,
        comment="Agent ID"
    )
    content: Mapped[str] = mapped_column(
        Text, nullable=False,
        comment="记忆原文"
    )
    content_hash: Mapped[Optional[str]] = mapped_column(
        String(64), nullable=True,
        comment="SHA-256 内容哈希"
    )
    # embedding 字段使用 pgvector 类型，需要在数据库中启用 vector 扩展
    # 此处声明为 Text，实际使用时由 pgvector.sqlalchemy.Vector 处理
    embedding: Mapped[Optional[str]] = mapped_column(
        Text, nullable=True,
        comment="向量嵌入 (存储为 JSON 数组字符串)"
    )
    embedding_model: Mapped[Optional[str]] = mapped_column(
        String(100), nullable=True,
        comment="嵌入模型名称"
    )
    category: Mapped[Optional[str]] = mapped_column(
        String(50), nullable=True,
        comment="记忆分类"
    )
    importance: Mapped[float] = mapped_column(
        Float, nullable=False, default=0.5,
        comment="重要性评分 [0,1]"
    )
    metadata_: Mapped[Optional[dict]] = mapped_column(
        "metadata", JSONB, nullable=True, default=dict,
        comment="元数据"
    )
    tags: Mapped[list] = mapped_column(
        ARRAY(String), nullable=False, default=list,
        comment="标签"
    )
    access_count: Mapped[int] = mapped_column(
        Integer, nullable=False, default=0,
        comment="访问次数"
    )
    last_accessed_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True,
        comment="最后访问时间"
    )
    archived_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True,
        comment="归档时间"
    )

    # Relationships
    workspace: Mapped[Optional["Workspace"]] = relationship(
        "Workspace", foreign_keys=[workspace_id]
    )
    user: Mapped[Optional["User"]] = relationship(
        "User", foreign_keys=[user_id]
    )
    session_links: Mapped[List["MemorySessionLink"]] = relationship(
        "MemorySessionLink", back_populates="memory", cascade="all, delete-orphan"
    )
    tag_links: Mapped[List["MemoryTag"]] = relationship(
        "MemoryTag", back_populates="memory", cascade="all, delete-orphan"
    )


class MemoryTag(Base, UUIDPrimaryKeyMixin, TimestampMixin, TenantAwareMixin):
    """记忆标签关联表"""

    __tablename__ = "ai_memory_tags"
    __table_args__ = (
        Index("ix_ai_memory_tags_memory", "memory_id"),
        Index("ix_ai_memory_tags_tag", "tag_name"),
        {"comment": "记忆标签关联表"},
    )

    memory_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("ai_memories.id", ondelete="CASCADE"),
        nullable=False,
        comment="记忆条目 ID"
    )
    tag_name: Mapped[str] = mapped_column(
        String(100), nullable=False,
        comment="标签名称"
    )

    memory: Mapped["AIMemory"] = relationship(
        "AIMemory", back_populates="tag_links"
    )


class MemorySession(Base, UUIDPrimaryKeyMixin, TimestampMixin, TenantAwareMixin):
    """记忆会话上下文表"""

    __tablename__ = "ai_memory_sessions"
    __table_args__ = (
        Index("ix_ai_memory_sessions_workspace", "workspace_id"),
        Index("ix_ai_memory_sessions_user", "user_id"),
        Index("ix_ai_memory_sessions_started", "started_at"),
        {"comment": "记忆会话上下文表"},
    )

    workspace_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("sys_workspaces.id", ondelete="CASCADE"),
        nullable=True,
        comment="所属工作空间 ID"
    )
    user_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("sys_users.id", ondelete="SET NULL"),
        nullable=True,
        comment="所有者用户 ID"
    )
    agent_id: Mapped[Optional[str]] = mapped_column(
        String(100), nullable=True,
        comment="Agent ID"
    )
    session_name: Mapped[Optional[str]] = mapped_column(
        String(200), nullable=True,
        comment="会话名称"
    )
    started_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False,
        comment="会话开始时间"
    )
    ended_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True,
        comment="会话结束时间"
    )
    is_active: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=True,
        comment="是否活跃"
    )

    workspace: Mapped[Optional["Workspace"]] = relationship(
        "Workspace", foreign_keys=[workspace_id]
    )
    user: Mapped[Optional["User"]] = relationship(
        "User", foreign_keys=[user_id]
    )
    memory_links: Mapped[List["MemorySessionLink"]] = relationship(
        "MemorySessionLink", back_populates="session", cascade="all, delete-orphan"
    )


class MemorySessionLink(Base, UUIDPrimaryKeyMixin, TimestampMixin, TenantAwareMixin):
    """会话-记忆关联表"""

    __tablename__ = "ai_memory_session_links"
    __table_args__ = (
        Index("ix_ai_memory_links_session", "session_id"),
        Index("ix_ai_memory_links_memory", "memory_id"),
        {"comment": "会话-记忆关联表"},
    )

    session_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("ai_memory_sessions.id", ondelete="CASCADE"),
        nullable=False,
        comment="会话 ID"
    )
    memory_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("ai_memories.id", ondelete="CASCADE"),
        nullable=False,
        comment="记忆条目 ID"
    )
    relevance_score: Mapped[float] = mapped_column(
        Float, nullable=False, default=0.0,
        comment="相关度评分"
    )

    session: Mapped["MemorySession"] = relationship(
        "MemorySession", back_populates="memory_links"
    )
    memory: Mapped["AIMemory"] = relationship(
        "AIMemory", back_populates="session_links"
    )
