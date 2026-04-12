# -*- coding: utf-8 -*-
"""
Alert ORM models — AlertRule and AlertEvent.
"""
from __future__ import annotations

import uuid
from datetime import datetime
from typing import Optional

from sqlalchemy import Boolean, DateTime, Integer, String, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from .base import Base, TenantAwareMixin, UUIDPrimaryKeyMixin


class AlertRule(Base, UUIDPrimaryKeyMixin, TenantAwareMixin):
    """Configurable anomaly detection rule.
    
    告警规则表 - 可配置的异常检测规则
    
    rule_type examples:
      - login_fail        → threshold repeated login failures
      - permission_change → alert on sensitive role assignments
      - dlp_block         → alert when DLP blocks a message
    notify_channels: JSON list, e.g. ["wecom", "dingtalk", "email"]
    """

    __tablename__ = "sys_alert_rules"
    __table_args__ = {"comment": "告警规则表"}

    rule_type: Mapped[str] = mapped_column(
        String(50), nullable=False, unique=True, index=True,
        comment="规则类型(如: login_fail, permission_change, dlp_block)"
    )
    description: Mapped[Optional[str]] = mapped_column(
        String(300), nullable=True,
        comment="规则描述"
    )
    # Number of occurrences before firing
    threshold: Mapped[int] = mapped_column(
        Integer, default=3, nullable=False,
        comment="触发阈值(达到此次数后告警)"
    )
    # Rolling window in seconds (default 300 = 5 min)
    window_seconds: Mapped[int] = mapped_column(
        Integer, default=300, nullable=False,
        comment="滚动窗口时间(秒,默认300秒=5分钟)"
    )
    # JSON list of channels: ["wecom", "dingtalk", "email"]
    notify_channels: Mapped[Optional[list]] = mapped_column(
        JSONB, nullable=True, default=list,
        comment="通知渠道JSON列表(如: [\"wecom\", \"dingtalk\", \"email\"]"
    )
    is_active: Mapped[bool] = mapped_column(
        Boolean, default=True, nullable=False,
        comment="是否激活"
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False,
        comment="创建时间"
    )

    def __repr__(self) -> str:  # pragma: no cover
        return f"<AlertRule type={self.rule_type!r} threshold={self.threshold}>"


class AlertEvent(Base, UUIDPrimaryKeyMixin, TenantAwareMixin):
    """Persisted record of a triggered alert.
    
    告警事件表 - 记录触发的告警事件
    """

    __tablename__ = "sys_alert_events"
    __table_args__ = {"comment": "告警事件表"}

    rule_type: Mapped[str] = mapped_column(
        String(50), nullable=False, index=True,
        comment="触发的规则类型"
    )
    triggered_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
        index=True,
        comment="触发时间"
    )
    # Structured context dict (username, ip, count, actor_id, etc.)
    context: Mapped[Optional[dict]] = mapped_column(
        JSONB, nullable=True,
        comment="告警上下文(包含username, ip, count, actor_id等)"
    )
    # notify result: sent | failed | suppressed (cooldown)
    notify_status: Mapped[Optional[str]] = mapped_column(
        String(20), nullable=True, default="sent",
        comment="通知状态: sent(已发送) | failed(失败) | suppressed(已抑制/冷却中)"
    )

    def __repr__(self) -> str:  # pragma: no cover
        return f"<AlertEvent rule={self.rule_type!r} at={self.triggered_at!r}>"
