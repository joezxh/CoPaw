# -*- coding: utf-8 -*-
"""
Storage Metadata ORM Models — 元数据模型

定义 Phase 3 双轨存储架构中的 PostgreSQL 元数据表：
- storage_objects: 通用文件对象索引
- ai_agent_configs: Agent 配置元数据
- ai_skill_configs: Skill 配置元数据
- ai_conversations: 对话元数据
- ai_conversation_messages: 对话消息
- ai_token_usage_stats: Token 使用统计
- ai_memory_documents: 记忆文档元数据
- ai_channel_messages: 通道消息
"""
from __future__ import annotations

import uuid
from datetime import date, datetime
from typing import TYPE_CHECKING, List, Optional

from sqlalchemy import (
    BigInteger,
    Boolean,
    Date,
    DateTime,
    ForeignKey,
    Integer,
    Numeric,
    String,
    Text,
    UniqueConstraint,
    func,
    Index,
)
from sqlalchemy.dialects.postgresql import ARRAY, JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base, TenantAwareMixin, TimestampMixin, UUIDPrimaryKeyMixin

if TYPE_CHECKING:
    from .workspace import Workspace
    from .user import User


class StorageObject(Base, UUIDPrimaryKeyMixin, TimestampMixin, TenantAwareMixin):
    """通用文件对象索引表 — 所有对象存储文件的统一索引"""

    __tablename__ = "storage_objects"
    __table_args__ = (
        Index("ix_storage_objects_key", "object_key", unique=True,
              postgresql_where="deleted_at IS NULL"),
        Index("ix_storage_objects_tenant", "tenant_id"),
        Index("ix_storage_objects_workspace", "workspace_id"),
        Index("ix_storage_objects_category", "category"),
        Index("ix_storage_objects_tags", "tags", postgresql_using="gin"),
        Index("ix_storage_objects_created", "created_at"),
        {"comment": "通用文件对象索引表 — 所有对象存储文件的统一索引"},
    )

    object_key: Mapped[str] = mapped_column(
        String(1024), nullable=False, unique=False,
        comment="对象存储中的键 (全局唯一)"
    )
    bucket: Mapped[str] = mapped_column(
        String(200), nullable=False, default="copaw-data",
        comment="存储桶名称"
    )
    file_name: Mapped[str] = mapped_column(
        String(500), nullable=False,
        comment="文件名"
    )
    file_ext: Mapped[Optional[str]] = mapped_column(
        String(50), nullable=True,
        comment="扩展名"
    )
    content_type: Mapped[Optional[str]] = mapped_column(
        String(200), nullable=True,
        comment="MIME 类型"
    )
    file_size: Mapped[int] = mapped_column(
        BigInteger, nullable=False, default=0,
        comment="文件大小 (bytes)"
    )
    category: Mapped[str] = mapped_column(
        String(50), nullable=False,
        comment="文件类别: workspace/skill/memory/media/model/config/other"
    )
    version_id: Mapped[Optional[str]] = mapped_column(
        String(200), nullable=True,
        comment="对象版本 ID"
    )
    etag: Mapped[Optional[str]] = mapped_column(
        String(200), nullable=True,
        comment="ETag"
    )
    workspace_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("sys_workspaces.id", ondelete="SET NULL"),
        nullable=True,
        comment="所属工作空间 ID"
    )
    user_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("sys_users.id", ondelete="SET NULL"),
        nullable=True,
        comment="所有者用户 ID"
    )
    search_text: Mapped[Optional[str]] = mapped_column(
        Text, nullable=True,
        comment="全文搜索文本"
    )
    tags: Mapped[list] = mapped_column(
        ARRAY(String), nullable=False, default=list,
        comment="标签"
    )
    custom_metadata: Mapped[Optional[dict]] = mapped_column(
        "custom_metadata", JSONB, nullable=True,
        comment="扩展元数据"
    )
    storage_class: Mapped[str] = mapped_column(
        String(50), nullable=False, default="STANDARD",
        comment="存储类别: STANDARD/INFREQUENT_ACCESS/ARCHIVE"
    )
    content_hash: Mapped[Optional[str]] = mapped_column(
        String(64), nullable=True,
        comment="SHA-256 内容哈希"
    )
    is_latest: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=True,
        comment="是否最新版本"
    )
    deleted_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True,
        comment="软删除时间"
    )

    # Relationships
    workspace: Mapped[Optional["Workspace"]] = relationship(
        "Workspace", foreign_keys=[workspace_id]
    )
    user: Mapped[Optional["User"]] = relationship(
        "User", foreign_keys=[user_id]
    )


class AgentConfig(Base, UUIDPrimaryKeyMixin, TenantAwareMixin):
    """Agent 配置元数据表 — 从 agent.json 抽取的结构化信息"""

    __tablename__ = "ai_agent_configs"
    __table_args__ = (
        Index("ix_ai_agent_configs_tenant", "tenant_id"),
        Index("ix_ai_agent_configs_workspace", "workspace_id"),
        Index("ix_ai_agent_configs_agent_id", "agent_id"),
        Index("ix_ai_agent_configs_provider", "model_provider"),
        Index("ix_ai_agent_configs_skills", "skills", postgresql_using="gin"),
        {"comment": "Agent 配置元数据表 — 从 agent.json 抽取的结构化信息"},
    )

    workspace_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("sys_workspaces.id", ondelete="CASCADE"),
        nullable=False,
        comment="所属工作空间 ID"
    )
    user_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("sys_users.id", ondelete="SET NULL"),
        nullable=True,
        comment="所有者用户 ID"
    )
    agent_id: Mapped[str] = mapped_column(
        String(100), nullable=False,
        comment="Agent ID (对应 agent.json 中的 id)"
    )
    name: Mapped[str] = mapped_column(
        String(200), nullable=False,
        comment="Agent 名称"
    )
    description: Mapped[Optional[str]] = mapped_column(
        Text, nullable=True,
        comment="Agent 描述"
    )
    model_provider: Mapped[Optional[str]] = mapped_column(
        String(100), nullable=True,
        comment="模型提供商"
    )
    model_name: Mapped[Optional[str]] = mapped_column(
        String(200), nullable=True,
        comment="模型名称"
    )
    model_base_url: Mapped[Optional[str]] = mapped_column(
        String(500), nullable=True,
        comment="API 基础URL"
    )
    temperature: Mapped[Optional[float]] = mapped_column(
        nullable=True,
        comment="温度参数"
    )
    max_tokens: Mapped[Optional[int]] = mapped_column(
        Integer, nullable=True,
        comment="最大Token数"
    )
    enabled_channels: Mapped[Optional[list]] = mapped_column(
        ARRAY(String), nullable=True,
        comment="已启用通道列表"
    )
    memory_backend: Mapped[Optional[str]] = mapped_column(
        String(50), nullable=True,
        comment="记忆后端"
    )
    memory_max_messages: Mapped[Optional[int]] = mapped_column(
        Integer, nullable=True,
        comment="最大消息数"
    )
    skills: Mapped[Optional[list]] = mapped_column(
        ARRAY(String), nullable=True,
        comment="已激活技能列表"
    )
    heartbeat_enabled: Mapped[Optional[bool]] = mapped_column(
        Boolean, nullable=True,
        comment="心跳是否启用"
    )
    heartbeat_every: Mapped[Optional[str]] = mapped_column(
        String(20), nullable=True,
        comment="心跳间隔"
    )
    storage_key: Mapped[Optional[str]] = mapped_column(
        String(1024), nullable=True,
        comment="agent.json 在对象存储中的键"
    )
    content_hash: Mapped[Optional[str]] = mapped_column(
        String(64), nullable=True,
        comment="文件内容哈希 (用于变更检测)"
    )
    status: Mapped[str] = mapped_column(
        String(20), nullable=False, default="active",
        comment="状态: active/inactive/archived"
    )
    last_synced_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True,
        comment="最后同步时间"
    )

    workspace: Mapped["Workspace"] = relationship(
        "Workspace", foreign_keys=[workspace_id]
    )
    user: Mapped[Optional["User"]] = relationship(
        "User", foreign_keys=[user_id]
    )


class SkillConfig(Base, UUIDPrimaryKeyMixin, TenantAwareMixin):
    """Skill 配置元数据表 — 从 skill.json 抽取的结构化信息"""

    __tablename__ = "ai_skill_configs"
    __table_args__ = (
        Index("ix_ai_skill_configs_tenant", "tenant_id"),
        Index("ix_ai_skill_configs_workspace", "workspace_id"),
        Index("ix_ai_skill_configs_name", "skill_name"),
        Index("ix_ai_skill_configs_source", "source"),
        {"comment": "Skill 配置元数据表 — 从 skill.json 抽取的结构化信息"},
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
    skill_name: Mapped[str] = mapped_column(
        String(200), nullable=False,
        comment="技能名称"
    )
    display_name: Mapped[Optional[str]] = mapped_column(
        String(200), nullable=True,
        comment="显示名称"
    )
    description: Mapped[Optional[str]] = mapped_column(
        Text, nullable=True,
        comment="技能描述"
    )
    version: Mapped[str] = mapped_column(
        String(50), nullable=False, default="1.0.0",
        comment="技能版本"
    )
    source: Mapped[Optional[str]] = mapped_column(
        String(50), nullable=True,
        comment="来源: builtin/user/plugin"
    )
    category: Mapped[Optional[str]] = mapped_column(
        String(50), nullable=True,
        comment="类别"
    )
    enabled: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=True,
        comment="是否启用"
    )
    channels: Mapped[list] = mapped_column(
        ARRAY(String), nullable=False, default=list,
        comment="绑定通道列表"
    )
    storage_key: Mapped[Optional[str]] = mapped_column(
        String(1024), nullable=True,
        comment="skill.json 在对象存储中的键"
    )
    skill_dir_key: Mapped[Optional[str]] = mapped_column(
        String(1024), nullable=True,
        comment="技能目录在对象存储中的键前缀"
    )
    content_hash: Mapped[Optional[str]] = mapped_column(
        String(64), nullable=True,
        comment="内容哈希"
    )
    last_synced_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True,
        comment="最后同步时间"
    )

    workspace: Mapped[Optional["Workspace"]] = relationship(
        "Workspace", foreign_keys=[workspace_id]
    )
    user: Mapped[Optional["User"]] = relationship(
        "User", foreign_keys=[user_id]
    )


class Conversation(Base, UUIDPrimaryKeyMixin, TenantAwareMixin):
    """对话元数据表 — 从 chats.json 抽取"""

    __tablename__ = "ai_conversations"
    __table_args__ = (
        Index("ix_ai_conversations_tenant", "tenant_id"),
        Index("ix_ai_conversations_workspace", "workspace_id"),
        Index("ix_ai_conversations_chat_id", "chat_id"),
        Index("ix_ai_conversations_agent", "agent_id"),
        Index("ix_ai_conversations_started", "started_at"),
        {"comment": "对话元数据表 — 从 chats.json 抽取"},
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
    chat_id: Mapped[str] = mapped_column(
        String(100), nullable=False,
        comment="原始对话 ID"
    )
    title: Mapped[Optional[str]] = mapped_column(
        String(500), nullable=True,
        comment="对话标题"
    )
    message_count: Mapped[int] = mapped_column(
        Integer, nullable=False, default=0,
        comment="消息数量"
    )
    started_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False,
        comment="对话开始时间"
    )
    last_message_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True,
        comment="最后一条消息时间"
    )
    storage_key: Mapped[Optional[str]] = mapped_column(
        String(1024), nullable=True,
        comment="chats.json 在对象存储中的键"
    )
    content_hash: Mapped[Optional[str]] = mapped_column(
        String(64), nullable=True,
        comment="内容哈希"
    )

    messages: Mapped[List["ConversationMessage"]] = relationship(
        "ConversationMessage", back_populates="conversation", cascade="all, delete-orphan"
    )
    workspace: Mapped[Optional["Workspace"]] = relationship(
        "Workspace", foreign_keys=[workspace_id]
    )
    user: Mapped[Optional["User"]] = relationship(
        "User", foreign_keys=[user_id]
    )


class ConversationMessage(Base, UUIDPrimaryKeyMixin, TenantAwareMixin):
    """对话消息表 — 从 chats.json.messages 逐条抽取"""

    __tablename__ = "ai_conversation_messages"
    __table_args__ = (
        Index("ix_ai_conv_msgs_conversation", "conversation_id"),
        Index("ix_ai_conv_msgs_role", "role"),
        Index("ix_ai_conv_msgs_tenant", "tenant_id"),
        {"comment": "对话消息表 — 从 chats.json.messages 逐条抽取"},
    )

    conversation_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("ai_conversations.id", ondelete="CASCADE"),
        nullable=False,
        comment="所属对话 ID"
    )
    role: Mapped[str] = mapped_column(
        String(20), nullable=False,
        comment="消息角色: user/assistant/system/tool"
    )
    content: Mapped[str] = mapped_column(
        Text, nullable=False,
        comment="消息内容"
    )
    timestamp: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False,
        comment="消息时间戳"
    )
    tool_calls: Mapped[Optional[dict]] = mapped_column(
        JSONB, nullable=True,
        comment="工具调用信息"
    )
    tool_call_id: Mapped[Optional[str]] = mapped_column(
        String(100), nullable=True,
        comment="工具调用响应 ID"
    )
    token_count: Mapped[Optional[int]] = mapped_column(
        Integer, nullable=True,
        comment="消息消耗的 Token 数"
    )
    metadata_: Mapped[Optional[dict]] = mapped_column(
        "metadata", JSONB, nullable=True, default=dict,
        comment="元数据"
    )

    conversation: Mapped["Conversation"] = relationship(
        "Conversation", back_populates="messages"
    )


class TokenUsageStat(Base, UUIDPrimaryKeyMixin, TenantAwareMixin):
    """Token 使用统计表 — 从 token_usage.json 抽取，支持按日/月聚合"""

    __tablename__ = "ai_token_usage_stats"
    __table_args__ = (
        UniqueConstraint(
            "tenant_id", "workspace_id", "agent_id", "stat_date",
            "model_provider", "model_name",
            name="uq_token_usage_unique"
        ),
        Index("ix_ai_token_usage_tenant", "tenant_id"),
        Index("ix_ai_token_usage_date", "stat_date"),
        Index("ix_ai_token_usage_workspace", "workspace_id"),
        Index("ix_ai_token_usage_agent", "agent_id"),
        {"comment": "Token 使用统计表 — 从 token_usage.json 抽取，支持按日/月聚合"},
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
    stat_date: Mapped[date] = mapped_column(
        Date, nullable=False,
        comment="统计日期"
    )
    prompt_tokens: Mapped[int] = mapped_column(
        BigInteger, nullable=False, default=0,
        comment="提示 Token 数"
    )
    completion_tokens: Mapped[int] = mapped_column(
        BigInteger, nullable=False, default=0,
        comment="补全 Token 数"
    )
    total_tokens: Mapped[int] = mapped_column(
        BigInteger, nullable=False, default=0,
        comment="总 Token 数"
    )
    request_count: Mapped[int] = mapped_column(
        Integer, nullable=False, default=0,
        comment="请求次数"
    )
    cost_usd: Mapped[float] = mapped_column(
        Numeric(10, 6), nullable=False, default=0,
        comment="费用 (USD)"
    )
    model_provider: Mapped[Optional[str]] = mapped_column(
        String(100), nullable=True,
        comment="模型提供商"
    )
    model_name: Mapped[Optional[str]] = mapped_column(
        String(200), nullable=True,
        comment="模型名称"
    )

    workspace: Mapped[Optional["Workspace"]] = relationship(
        "Workspace", foreign_keys=[workspace_id]
    )
    user: Mapped[Optional["User"]] = relationship(
        "User", foreign_keys=[user_id]
    )


class MemoryDocument(Base, UUIDPrimaryKeyMixin, TenantAwareMixin):
    """记忆文档元数据表 — 从 memory/*.md 和人格文件抽取"""

    __tablename__ = "ai_memory_documents"
    __table_args__ = (
        Index("ix_ai_memory_docs_tenant", "tenant_id"),
        Index("ix_ai_memory_docs_workspace", "workspace_id"),
        Index("ix_ai_memory_docs_type", "doc_type"),
        Index("ix_ai_memory_docs_date", "doc_date"),
        Index("ix_ai_memory_docs_tags", "tags", postgresql_using="gin"),
        {"comment": "记忆文档元数据表 — 从 memory/*.md 和人格文件抽取"},
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
    doc_type: Mapped[str] = mapped_column(
        String(50), nullable=False,
        comment="文档类型: memory_daily/long_term/personality/soul/profile"
    )
    doc_date: Mapped[Optional[date]] = mapped_column(
        Date, nullable=True,
        comment="记忆日期 (仅 memory_daily)"
    )
    title: Mapped[Optional[str]] = mapped_column(
        String(500), nullable=True,
        comment="文档标题"
    )
    summary: Mapped[Optional[str]] = mapped_column(
        Text, nullable=True,
        comment="内容摘要 (Markdown 前 500 字符)"
    )
    headings: Mapped[Optional[list]] = mapped_column(
        ARRAY(String), nullable=True,
        comment="标题列表 (从 Markdown # 提取)"
    )
    tags: Mapped[list] = mapped_column(
        ARRAY(String), nullable=False, default=list,
        comment="标签"
    )
    storage_key: Mapped[str] = mapped_column(
        String(1024), nullable=False,
        comment="文件在对象存储中的键"
    )
    content_hash: Mapped[Optional[str]] = mapped_column(
        String(64), nullable=True,
        comment="内容哈希"
    )
    file_size: Mapped[int] = mapped_column(
        BigInteger, nullable=False, default=0,
        comment="文件大小"
    )
    last_synced_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True,
        comment="最后同步时间"
    )
    deleted_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True,
        comment="软删除时间"
    )

    workspace: Mapped[Optional["Workspace"]] = relationship(
        "Workspace", foreign_keys=[workspace_id]
    )
    user: Mapped[Optional["User"]] = relationship(
        "User", foreign_keys=[user_id]
    )


class ChannelMessage(Base, UUIDPrimaryKeyMixin, TenantAwareMixin):
    """通道消息表 — 飞书/钉钉等通道消息入库，支持跨节点共享和审计"""

    __tablename__ = "ai_channel_messages"
    __table_args__ = (
        Index("ix_ai_channel_msgs_tenant", "tenant_id"),
        Index("ix_ai_channel_msgs_channel", "channel_type"),
        Index("ix_ai_channel_msgs_workspace", "workspace_id"),
        Index("ix_ai_channel_msgs_timestamp", "timestamp"),
        Index("ix_ai_channel_msgs_sender", "sender_id"),
        Index("ix_ai_channel_msgs_direction", "direction"),
        Index("ix_ai_channel_msgs_processing", "processing_status"),
        {"comment": "通道消息表 — 飞书/钉钉等通道消息入库，支持跨节点共享和审计"},
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
    channel_type: Mapped[str] = mapped_column(
        String(50), nullable=False,
        comment="通道类型: feishu/dingtalk/weixin/telegram/..."
    )
    channel_id: Mapped[Optional[str]] = mapped_column(
        String(200), nullable=True,
        comment="通道会话 ID"
    )
    message_id: Mapped[Optional[str]] = mapped_column(
        String(200), nullable=True,
        comment="原始消息 ID"
    )
    direction: Mapped[str] = mapped_column(
        String(20), nullable=False,
        comment="消息方向: inbound/outbound"
    )
    content_type: Mapped[str] = mapped_column(
        String(50), nullable=False, default="text",
        comment="内容类型: text/markdown/image/file/card"
    )
    content: Mapped[Optional[str]] = mapped_column(
        Text, nullable=True,
        comment="消息正文"
    )
    sender_id: Mapped[Optional[str]] = mapped_column(
        String(200), nullable=True,
        comment="发送者 ID"
    )
    sender_name: Mapped[Optional[str]] = mapped_column(
        String(200), nullable=True,
        comment="发送者名称"
    )
    is_bot: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False,
        comment="是否 Bot 消息"
    )
    reply_to_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("ai_channel_messages.id"),
        nullable=True,
        comment="回复的消息 ID"
    )
    conversation_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("ai_conversations.id"),
        nullable=True,
        comment="关联的对话 ID"
    )
    task_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("ai_tasks.id"),
        nullable=True,
        comment="关联的任务 ID"
    )
    media_keys: Mapped[list] = mapped_column(
        ARRAY(String), nullable=False, default=list,
        comment="媒体文件在对象存储中的键"
    )
    processing_status: Mapped[str] = mapped_column(
        String(20), nullable=False, default="pending",
        comment="处理状态: pending/processed/failed"
    )
    processed_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True,
        comment="处理完成时间"
    )
    dlp_checked: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False,
        comment="是否已进行 DLP 检查"
    )
    dlp_violations: Mapped[Optional[list]] = mapped_column(
        JSONB, nullable=True, default=list,
        comment="DLP 违规记录"
    )
    timestamp: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False,
        comment="消息原始时间戳"
    )

    workspace: Mapped[Optional["Workspace"]] = relationship(
        "Workspace", foreign_keys=[workspace_id]
    )
    user: Mapped[Optional["User"]] = relationship(
        "User", foreign_keys=[user_id]
    )

# ============================================================================
# Registry Models — 注册表模型（Phase 5）
# ============================================================================

class SkillRegistry(Base, UUIDPrimaryKeyMixin, TenantAwareMixin):
    """AI 技能注册表 — 注册所有可用的技能"""

    __tablename__ = "ai_skill_registry"
    __table_args__ = (
        Index("ix_ai_skill_registry_tenant", "tenant_id"),
        Index("ix_ai_skill_registry_name", "skill_name"),
        Index("ix_ai_skill_registry_active", "is_active"),
        {"comment": "AI 技能注册表"},
    )

    skill_name: Mapped[str] = mapped_column(
        String(200), nullable=False,
        comment="技能名称"
    )
    version: Mapped[str] = mapped_column(
        String(50), nullable=False,
        comment="技能版本"
    )
    description: Mapped[Optional[str]] = mapped_column(
        Text, nullable=True,
        comment="技能描述"
    )
    storage_key: Mapped[Optional[str]] = mapped_column(
        String(1024), nullable=True,
        comment="技能目录在对象存储中的键"
    )
    is_active: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=True, server_default="true",
        comment="是否激活"
    )


class ModelRegistry(Base, UUIDPrimaryKeyMixin, TenantAwareMixin):
    """AI 模型注册表 — 注册所有可用的 AI 模型"""

    __tablename__ = "ai_model_registry"
    __table_args__ = (
        Index("ix_ai_model_registry_tenant", "tenant_id"),
        Index("ix_ai_model_registry_type", "model_type"),
        Index("ix_ai_model_registry_available", "is_available"),
        {"comment": "AI 模型注册表"},
    )

    model_name: Mapped[str] = mapped_column(
        String(200), nullable=False,
        comment="模型名称"
    )
    model_type: Mapped[str] = mapped_column(
        String(50), nullable=False,
        comment="模型类型: llm/embedding/vision/tts/stt"
    )
    architecture: Mapped[Optional[str]] = mapped_column(
        String(100), nullable=True,
        comment="模型架构"
    )
    storage_key: Mapped[Optional[str]] = mapped_column(
        String(1024), nullable=True,
        comment="模型文件在对象存储中的键"
    )
    file_size: Mapped[Optional[int]] = mapped_column(
        BigInteger, nullable=True,
        comment="文件大小 (bytes)"
    )
    quantization: Mapped[Optional[str]] = mapped_column(
        String(50), nullable=True,
        comment="量化格式: fp16/int8/int4"
    )
    default_params: Mapped[Optional[dict]] = mapped_column(
        JSONB, server_default="{}", nullable=True,
        comment="默认参数"
    )
    min_gpu_memory: Mapped[Optional[int]] = mapped_column(
        Integer, nullable=True,
        comment="最小GPU内存 (MB)"
    )
    min_ram: Mapped[Optional[int]] = mapped_column(
        Integer, nullable=True,
        comment="最小系统内存 (MB)"
    )
    is_available: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=True, server_default="true",
        comment="是否可用"
    )
    health_status: Mapped[str] = mapped_column(
        String(20), nullable=False, default="unknown", server_default="unknown",
        comment="健康状态: unknown/healthy/unhealthy"
    )


class InferenceTask(Base, UUIDPrimaryKeyMixin, TenantAwareMixin):
    """AI 推理任务表"""

    __tablename__ = "ai_inference_tasks"
    __table_args__ = (
        Index("ix_ai_inference_tasks_status", "status"),
        Index("ix_ai_inference_tasks_tenant", "tenant_id"),
        Index("ix_ai_inference_tasks_model", "model_id"),
        {"comment": "AI 推理任务表"},
    )

    model_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("ai_model_registry.id"),
        nullable=True,
        comment="模型 ID"
    )
    user_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("sys_users.id", ondelete="SET NULL"),
        nullable=True,
        comment="用户 ID"
    )
    workspace_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("sys_workspaces.id", ondelete="SET NULL"),
        nullable=True,
        comment="工作空间 ID"
    )
    task_type: Mapped[str] = mapped_column(
        String(50), nullable=False,
        comment="任务类型: completion/embedding/chat"
    )
    input_data: Mapped[dict] = mapped_column(
        JSONB, nullable=False,
        comment="输入数据"
    )
    output_data: Mapped[Optional[dict]] = mapped_column(
        JSONB, nullable=True,
        comment="输出数据"
    )
    status: Mapped[str] = mapped_column(
        String(20), nullable=False, default="pending", server_default="pending",
        comment="状态: pending/running/completed/failed"
    )
    worker_id: Mapped[Optional[str]] = mapped_column(
        String(100), nullable=True,
        comment="执行Worker ID"
    )
    prompt_tokens: Mapped[int] = mapped_column(
        Integer, nullable=False, default=0, server_default="0",
        comment="Prompt Token数"
    )
    completion_tokens: Mapped[int] = mapped_column(
        Integer, nullable=False, default=0, server_default="0",
        comment="Completion Token数"
    )
    error_message: Mapped[Optional[str]] = mapped_column(
        Text, nullable=True,
        comment="错误信息"
    )
    started_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True,
        comment="开始时间"
    )
    completed_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True,
        comment="完成时间"
    )

    model: Mapped[Optional["ModelRegistry"]] = relationship(
        "ModelRegistry", foreign_keys=[model_id]
    )
    user: Mapped[Optional["User"]] = relationship(
        "User", foreign_keys=[user_id]
    )
    workspace: Mapped[Optional["Workspace"]] = relationship(
        "Workspace", foreign_keys=[workspace_id]
    )
