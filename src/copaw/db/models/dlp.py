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
    """Admin-configurable DLP detection rule."""

    __tablename__ = "dlp_rules"

    rule_name: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    description: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    pattern_regex: Mapped[str] = mapped_column(Text, nullable=False)
    # mask | alert | block
    action: Mapped[str] = mapped_column(String(20), default="alert", nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    is_builtin: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    def __repr__(self) -> str:  # pragma: no cover
        return f"<DLPRule name={self.rule_name!r} action={self.action!r}>"


class DLPEvent(Base, UUIDPrimaryKeyMixin, TenantAwareMixin):
    """Record of a DLP policy violation / match."""

    __tablename__ = "dlp_events"

    rule_name: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    # mask | alert | block
    action_taken: Mapped[str] = mapped_column(String(20), nullable=False)
    # Truncated/redacted snippet for audit (never store full sensitive value)
    content_summary: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    user_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), nullable=True, index=True
    )
    # e.g. "/api/enterprise/tasks" or "agent:reply"
    context_path: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)
    triggered_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False, index=True
    )

    def __repr__(self) -> str:  # pragma: no cover
        return f"<DLPEvent rule={self.rule_name!r} action={self.action_taken!r}>"
