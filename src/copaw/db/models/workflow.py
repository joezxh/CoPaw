# -*- coding: utf-8 -*-
"""
Workflow and WorkflowExecution ORM models.
Supports Dify workflow categories via the `category` field.
"""
from __future__ import annotations

import uuid
from datetime import datetime
from typing import Optional

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base, TenantAwareMixin, TimestampMixin, UUIDPrimaryKeyMixin


class Workflow(Base, UUIDPrimaryKeyMixin, TimestampMixin, TenantAwareMixin):
    """DAG workflow definition.

    ``category`` identifies the workflow type, e.g.:
    - ``"dify"``          — Dify-managed workflow
    - ``"dify_chatflow"`` — Dify conversational workflow
    - ``"dify_agent"``    — Dify agent workflow
    - ``"internal"``      — CoPaw native DAG workflow
    """

    __tablename__ = "workflows"

    name: Mapped[str] = mapped_column(String(200), nullable=False, index=True)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    category: Mapped[Optional[str]] = mapped_column(
        String(100),
        nullable=True,
        index=True,
    )
    # e.g. 'dify' | 'dify_chatflow' | 'dify_agent' | 'internal'
    definition: Mapped[dict] = mapped_column(
        JSONB, nullable=False, default=dict
    )  # DAG node/edge definition
    version: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    status: Mapped[str] = mapped_column(
        String(20), default="draft", nullable=False
    )  # draft | active | archived
    creator_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )

    creator: Mapped[Optional[object]] = relationship(
        "User", foreign_keys=[creator_id]
    )
    executions: Mapped[list["WorkflowExecution"]] = relationship(
        "WorkflowExecution",
        back_populates="workflow",
        cascade="all, delete-orphan",
    )

    def __repr__(self) -> str:  # pragma: no cover
        return (
            f"<Workflow id={self.id} name={self.name!r}"
            f" category={self.category!r} v{self.version}>"
        )


class WorkflowExecution(Base, UUIDPrimaryKeyMixin, TenantAwareMixin):
    """Single execution instance of a Workflow."""

    __tablename__ = "workflow_executions"

    workflow_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("workflows.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    triggered_by: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )
    status: Mapped[str] = mapped_column(
        String(20), default="pending", nullable=False, index=True
    )  # pending | running | paused | completed | failed | cancelled
    started_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    completed_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    input_data: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True)
    output_data: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True)
    error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    run_metadata: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True)

    workflow: Mapped["Workflow"] = relationship(
        "Workflow", back_populates="executions"
    )

    def __repr__(self) -> str:  # pragma: no cover
        return (
            f"<WorkflowExecution id={self.id} workflow_id={self.workflow_id}"
            f" status={self.status!r}>"
        )
