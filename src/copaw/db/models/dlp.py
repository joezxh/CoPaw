# -*- coding: utf-8 -*-
"""
DLP ORM models — DLPRule and DLPEvent.
"""
from __future__ import annotations

import uuid
from datetime import datetime
from typing import Optional

from sqlalchemy import Boolean, DateTime, String, Text, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from .base import Base, TenantAwareMixin, UUIDPrimaryKeyMixin


class DLPRule(Base, UUIDPrimaryKeyMixin, TenantAwareMixin):
    """Admin-configurable DLP detection rule.
    
    DLP规则表 - 管理员可配置的数据泄漏防护(DLP)检测规则
    """

    __tablename__ = "sys_dlp_rules"
    __table_args__ = {"comment": "DLP数据泄漏防护规则表"}

    rule_name: Mapped[str] = mapped_column(
        String(100), unique=True, nullable=False,
        comment="规则名称"
    )
    description: Mapped[Optional[str]] = mapped_column(
        String(500), nullable=True,
        comment="规则描述"
    )
    pattern_regex: Mapped[str] = mapped_column(
        Text, nullable=False,
        comment="正则表达式模式(用于匹配敏感数据)"
    )
    # mask | alert | block
    action: Mapped[str] = mapped_column(
        String(20), default="alert", nullable=False,
        comment="执行动作: mask(脱敏) | alert(告警) | block(阻断)"
    )
    is_active: Mapped[bool] = mapped_column(
        Boolean, default=True, nullable=False,
        comment="是否激活"
    )
    is_builtin: Mapped[bool] = mapped_column(
        Boolean, default=False, nullable=False,
        comment="是否为内置规则(内置规则不可删除)"
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False,
        comment="创建时间"
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
        comment="更新时间"
    )

    def __repr__(self) -> str:  # pragma: no cover
        return f"<DLPRule name={self.rule_name!r} action={self.action!r}>"


class DLPEvent(Base, UUIDPrimaryKeyMixin, TenantAwareMixin):
    """Record of a DLP policy violation / match.
    
    DLP事件表 - 记录DLP策略违规/匹配事件
    """

    __tablename__ = "sys_dlp_events"
    __table_args__ = {"comment": "DLP数据泄漏防护事件表"}

    rule_name: Mapped[str] = mapped_column(
        String(100), nullable=False, index=True,
        comment="触发的规则名称"
    )
    # mask | alert | block
    action_taken: Mapped[str] = mapped_column(
        String(20), nullable=False,
        comment="采取的动作: mask(脱敏) | alert(告警) | block(阻断)"
    )
    # Truncated/redacted snippet for audit (never store full sensitive value)
    content_summary: Mapped[Optional[str]] = mapped_column(
        Text, nullable=True,
        comment="内容摘要(截断/编辑,绝不存储完整敏感值)"
    )
    user_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), nullable=True, index=True,
        comment="触发用户ID"
    )
    # e.g. "/api/enterprise/tasks" or "agent:reply"
    context_path: Mapped[Optional[str]] = mapped_column(
        String(200), nullable=True,
        comment="上下文路径(如: \"/api/enterprise/tasks\" 或 \"agent:reply\")"
    )
    triggered_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False, index=True,
        comment="触发时间"
    )

    def __repr__(self) -> str:  # pragma: no cover
        return f"<DLPEvent rule={self.rule_name!r} action={self.action_taken!r}>"
