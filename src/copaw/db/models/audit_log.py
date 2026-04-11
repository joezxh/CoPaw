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

    Schema follows ISO 27001 requirements:
    - Who (user_id, user_role)
    - What (action_type, resource_type, resource_id)
    - When (timestamp)
    - Result (action_result)
    - Where (client_ip, client_device)
    - Context (context JSONB — session_id, task_id, agent_id, …)
    - Diff (data_before / data_after for sensitive operations)
    """

    __tablename__ = "audit_logs"
    __table_args__ = (
        Index("idx_audit_logs_timestamp", "timestamp"),
        Index("idx_audit_logs_user_id", "user_id"),
        Index("idx_audit_logs_action_type", "action_type"),
        Index("idx_audit_logs_resource_type", "resource_type"),
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    timestamp: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    user_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )
    user_role: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    action_type: Mapped[str] = mapped_column(
        String(100), nullable=False
    )  # e.g. USER_LOGIN, TASK_CREATE, AGENT_RUN
    resource_type: Mapped[str] = mapped_column(
        String(100), nullable=False
    )  # e.g. user, task, workflow, agent
    resource_id: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)
    action_result: Mapped[Optional[str]] = mapped_column(
        String(20), nullable=True
    )  # success | failure | denied
    client_ip: Mapped[Optional[str]] = mapped_column(
        INET, nullable=True
    )
    client_device: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True)
    context: Mapped[Optional[dict]] = mapped_column(
        JSONB, nullable=True
    )  # session_id, task_id, etc.
    data_before: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True)
    data_after: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True)
    is_sensitive: Mapped[bool] = mapped_column(Boolean, default=False)

    def __repr__(self) -> str:  # pragma: no cover
        return (
            f"<AuditLog id={self.id} action={self.action_type!r}"
            f" result={self.action_result!r}>"
        )
