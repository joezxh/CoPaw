# -*- coding: utf-8 -*-
"""
Task and TaskComment ORM models.
"""
from __future__ import annotations

import uuid
from datetime import datetime
from typing import TYPE_CHECKING, List, Optional

from sqlalchemy import DateTime, ForeignKey, String, Text, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base, TenantAwareMixin, TimestampMixin, UUIDPrimaryKeyMixin

if TYPE_CHECKING:
    from .user import User, UserGroup
    from .organization import Department
    from .workflow import Workflow


class Task(Base, UUIDPrimaryKeyMixin, TimestampMixin, TenantAwareMixin):
    """Enterprise task — assignable to users, groups, or departments.
    
    任务表 - 企业任务管理,可分配给用户、用户组或部门
    """

    __tablename__ = "ai_tasks"
    __table_args__ = {"comment": "企业任务表"}

    title: Mapped[str] = mapped_column(
        String(500), nullable=False,
        comment="任务标题"
    )
    description: Mapped[Optional[str]] = mapped_column(
        Text, nullable=True,
        comment="任务详细描述"
    )
    status: Mapped[str] = mapped_column(
        String(20), default="pending", nullable=False, index=True,
        comment="任务状态: pending(待处理) | in_progress(进行中) | completed(已完成) | blocked(受阻) | cancelled(已取消)"
    )
    priority: Mapped[str] = mapped_column(
        String(10), default="medium", nullable=False,
        comment="优先级: high(高) | medium(中) | low(低)"
    )
    creator_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("sys_users.id", ondelete="SET NULL"),
        nullable=True,
        comment="创建者ID"
    )
    assignee_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("sys_users.id", ondelete="SET NULL"),
        nullable=True,
        comment="被分配用户ID"
    )
    assignee_group_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("sys_user_groups.id", ondelete="SET NULL"),
        nullable=True,
        comment="被分配用户组ID"
    )
    department_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("sys_departments.id", ondelete="SET NULL"),
        nullable=True,
        comment="所属部门ID"
    )
    due_date: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True,
        comment="截止日期"
    )
    completed_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True,
        comment="完成时间"
    )
    parent_task_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("ai_tasks.id", ondelete="SET NULL"),
        nullable=True,
        comment="父任务ID(用于实现子任务)"
    )
    workflow_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("ai_workflows.id", ondelete="SET NULL"),
        nullable=True,
        comment="关联的工作流ID"
    )
    metadata_: Mapped[Optional[dict]] = mapped_column(
        "metadata", JSONB, nullable=True,
        comment="任务元数据(JSON格式,存储额外信息)"
    )

    # Relationships
    creator: Mapped[Optional["User"]] = relationship(
        "User", foreign_keys=[creator_id]
    )
    assignee: Mapped[Optional["User"]] = relationship(
        "User", foreign_keys=[assignee_id]
    )
    parent: Mapped[Optional["Task"]] = relationship(
        "Task", remote_side="Task.id", back_populates="subtasks"
    )
    subtasks: Mapped[List["Task"]] = relationship(
        "Task", back_populates="parent"
    )
    comments: Mapped[List["TaskComment"]] = relationship(
        "TaskComment", back_populates="task", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:  # pragma: no cover
        return f"<Task id={self.id} title={self.title[:30]!r} status={self.status!r}>"


class TaskComment(Base, UUIDPrimaryKeyMixin, TenantAwareMixin):
    """Comment on a task.
    
    任务评论表 - 存储对任务的评论和讨论
    """

    __tablename__ = "ai_task_comments"
    __table_args__ = {"comment": "任务评论表"}

    task_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("ai_tasks.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="任务ID"
    )
    author_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("sys_users.id", ondelete="SET NULL"),
        nullable=True,
        comment="评论作者ID"
    )
    content: Mapped[str] = mapped_column(
        Text, nullable=False,
        comment="评论内容"
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False,
        comment="评论创建时间"
    )

    task: Mapped["Task"] = relationship("Task", back_populates="comments")
    author: Mapped[Optional["User"]] = relationship("User", foreign_keys=[author_id])
