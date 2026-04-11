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

    rule_type examples:
      - login_fail        → threshold repeated login failures
      - permission_change → alert on sensitive role assignments
      - dlp_block         → alert when DLP blocks a message
    notify_channels: JSON list, e.g. ["wecom", "dingtalk", "email"]
    """

    __tablename__ = "alert_rules"

    rule_type: Mapped[str] = mapped_column(
        String(50), nullable=False, unique=True, index=True
    )
    description: Mapped[Optional[str]] = mapped_column(String(300), nullable=True)
    # Number of occurrences before firing
    threshold: Mapped[int] = mapped_column(Integer, default=3, nullable=False)
    # Rolling window in seconds (default 300 = 5 min)
    window_seconds: Mapped[int] = mapped_column(Integer, default=300, nullable=False)
    # JSON list of channels: ["wecom", "dingtalk", "email"]
    notify_channels: Mapped[Optional[list]] = mapped_column(
        JSONB, nullable=True, default=list
    )
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    def __repr__(self) -> str:  # pragma: no cover
        return f"<AlertRule type={self.rule_type!r} threshold={self.threshold}>"


class AlertEvent(Base, UUIDPrimaryKeyMixin, TenantAwareMixin):
    """Persisted record of a triggered alert."""

    __tablename__ = "alert_events"

    rule_type: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    triggered_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
        index=True,
    )
    # Structured context dict (username, ip, count, actor_id, etc.)
    context: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True)
    # notify result: sent | failed | suppressed (cooldown)
    notify_status: Mapped[Optional[str]] = mapped_column(
        String(20), nullable=True, default="sent"
    )

    def __repr__(self) -> str:  # pragma: no cover
        return f"<AlertEvent rule={self.rule_type!r} at={self.triggered_at!r}>"
