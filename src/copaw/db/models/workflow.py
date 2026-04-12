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
    
    工作流表 - DAG(有向无环图)工作流定义
    
    ``category`` identifies the workflow type, e.g.:
    - ``"dify"``          — Dify-managed workflow
    - ``"dify_chatflow"`` — Dify conversational workflow
    - ``"dify_agent"``    — Dify agent workflow
    - ``"internal"``      — CoPaw native DAG workflow
    """

    __tablename__ = "ai_workflows"
    __table_args__ = {"comment": "工作流定义表"}

    name: Mapped[str] = mapped_column(
        String(200), nullable=False, index=True,
        comment="工作流名称"
    )
    description: Mapped[Optional[str]] = mapped_column(
        Text, nullable=True,
        comment="工作流描述"
    )
    category: Mapped[Optional[str]] = mapped_column(
        String(100),
        nullable=True,
        index=True,
        comment="工作流类别: 'dify' | 'dify_chatflow' | 'dify_agent' | 'internal'"
    )
    # e.g. 'dify' | 'dify_chatflow' | 'dify_agent' | 'internal'
    definition: Mapped[dict] = mapped_column(
        JSONB, nullable=False, default=dict,
        comment="工作流DAG定义(节点和边的JSON结构)"
    )
    # DAG node/edge definition
    version: Mapped[int] = mapped_column(
        Integer, default=1, nullable=False,
        comment="版本号"
    )
    status: Mapped[str] = mapped_column(
        String(20), default="draft", nullable=False,
        comment="状态: draft(草稿) | active(激活) | archived(归档)"
    )
    creator_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("sys_users.id", ondelete="SET NULL"),
        nullable=True,
        comment="创建者ID"
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
    """Single execution instance of a Workflow.
    
    工作流执行表 - 记录工作流的单次执行实例
    """

    __tablename__ = "ai_workflow_executions"
    __table_args__ = {"comment": "工作流执行记录表"}

    workflow_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("ai_workflows.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="工作流ID"
    )
    triggered_by: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("sys_users.id", ondelete="SET NULL"),
        nullable=True,
        comment="触发者ID"
    )
    status: Mapped[str] = mapped_column(
        String(20), default="pending", nullable=False, index=True,
        comment="执行状态: pending(等待) | running(运行中) | paused(已暂停) | completed(已完成) | failed(失败) | cancelled(已取消)"
    )
    started_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True,
        comment="开始时间"
    )
    completed_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True,
        comment="完成时间"
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False,
        comment="创建时间"
    )
    input_data: Mapped[Optional[dict]] = mapped_column(
        JSONB, nullable=True,
        comment="输入数据"
    )
    output_data: Mapped[Optional[dict]] = mapped_column(
        JSONB, nullable=True,
        comment="输出数据"
    )
    error_message: Mapped[Optional[str]] = mapped_column(
        Text, nullable=True,
        comment="错误信息"
    )
    run_metadata: Mapped[Optional[dict]] = mapped_column(
        JSONB, nullable=True,
        comment="运行元数据"
    )

    workflow: Mapped["Workflow"] = relationship(
        "Workflow", back_populates="executions"
    )

    def __repr__(self) -> str:  # pragma: no cover
        return (
            f"<WorkflowExecution id={self.id} workflow_id={self.workflow_id}"
            f" status={self.status!r}>"
        )
