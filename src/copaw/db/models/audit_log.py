# -*- coding: utf-8 -*-
"""
AuditLog ORM model (ISO 27001 compliant, append-only by convention).
"""
from __future__ import annotations

import uuid
from datetime import datetime
from typing import Optional

from sqlalchemy import BigInteger, Boolean, DateTime, ForeignKey, Index, String, func
from sqlalchemy.dialects.postgresql import INET, JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from .base import Base, TenantAwareMixin


class AuditLog(Base, TenantAwareMixin):
    """Append-only security/operational audit log.
    
    审计日志表 - 只追加的安全/操作审计日志,符合ISO 27001标准

    Schema follows ISO 27001 requirements:
    - Who (user_id, user_role) - 谁操作的
    - What (action_type, resource_type, resource_id) - 做了什么
    - When (timestamp) - 什么时候
    - Result (action_result) - 结果如何
    - Where (client_ip, client_device) - 从哪里
    - Context (context JSONB — session_id, task_id, agent_id, …) - 上下文
    - Diff (data_before / data_after for sensitive operations) - 数据变更
    """

    __tablename__ = "sys_audit_logs"
    __table_args__ = (
        Index("idx_sys_audit_logs_timestamp", "timestamp"),
        Index("idx_sys_audit_logs_user_id", "user_id"),
        Index("idx_sys_audit_logs_action_type", "action_type"),
        Index("idx_sys_audit_logs_resource_type", "resource_type"),
        {"comment": "审计日志表(ISO 27001合规,只追加)"},
    )

    id: Mapped[int] = mapped_column(
        BigInteger, primary_key=True, autoincrement=True,
        comment="日志ID(自增主键)"
    )
    timestamp: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False,
        comment="操作时间戳"
    )
    user_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("sys_users.id", ondelete="SET NULL"),
        nullable=True,
        comment="操作用户ID"
    )
    user_role: Mapped[Optional[str]] = mapped_column(
        String(100), nullable=True,
        comment="用户角色"
    )
    action_type: Mapped[str] = mapped_column(
        String(100), nullable=False,
        comment="操作类型(如: USER_LOGIN, TASK_CREATE, AGENT_RUN)"
    )
    resource_type: Mapped[str] = mapped_column(
        String(100), nullable=False,
        comment="资源类型(如: user, task, workflow, agent)"
    )
    resource_id: Mapped[Optional[str]] = mapped_column(
        String(200), nullable=True,
        comment="资源ID"
    )
    action_result: Mapped[Optional[str]] = mapped_column(
        String(20), nullable=True,
        comment="操作结果: success(成功) | failure(失败) | denied(拒绝)"
    )
    client_ip: Mapped[Optional[str]] = mapped_column(
        INET, nullable=True,
        comment="客户端IP地址"
    )
    client_device: Mapped[Optional[dict]] = mapped_column(
        JSONB, nullable=True,
        comment="客户端设备信息"
    )
    context: Mapped[Optional[dict]] = mapped_column(
        JSONB, nullable=True,
        comment="操作上下文(包含session_id, task_id等)"
    )
    data_before: Mapped[Optional[dict]] = mapped_column(
        JSONB, nullable=True,
        comment="操作前数据(用于敏感操作审计)"
    )
    data_after: Mapped[Optional[dict]] = mapped_column(
        JSONB, nullable=True,
        comment="操作后数据(用于敏感操作审计)"
    )
    is_sensitive: Mapped[bool] = mapped_column(
        Boolean, default=False,
        comment="是否为敏感操作"
    )

    def __repr__(self) -> str:  # pragma: no cover
        return (
            f"<AuditLog id={self.id} action={self.action_type!r}"
            f" result={self.action_result!r}>"
        )
