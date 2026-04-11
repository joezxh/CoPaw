# -*- coding: utf-8 -*-
"""
Enterprise TaskService — stateful task lifecycle management.
"""
from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from ..db.models.task import Task, TaskComment

_VALID_TRANSITIONS: dict[str, set[str]] = {
    "pending":     {"in_progress", "cancelled"},
    "in_progress": {"completed", "blocked", "cancelled"},
    "blocked":     {"in_progress", "cancelled"},
    "completed":   set(),
    "cancelled":   set(),
}


class TaskService:

    @staticmethod
    async def create(
        session: AsyncSession,
        title: str,
        creator_id: uuid.UUID,
        description: Optional[str] = None,
        priority: str = "medium",
        assignee_id: Optional[uuid.UUID] = None,
        assignee_group_id: Optional[uuid.UUID] = None,
        department_id: Optional[uuid.UUID] = None,
        due_date: Optional[datetime] = None,
        parent_task_id: Optional[uuid.UUID] = None,
        workflow_id: Optional[uuid.UUID] = None,
        metadata: Optional[dict] = None,
    ) -> Task:
        task = Task(
            title=title,
            description=description,
            creator_id=creator_id,
            priority=priority,
            assignee_id=assignee_id,
            assignee_group_id=assignee_group_id,
            department_id=department_id,
            due_date=due_date,
            parent_task_id=parent_task_id,
            workflow_id=workflow_id,
            metadata_=metadata or {},
            status="pending",
        )
        session.add(task)
        await session.flush()
        return task

    @staticmethod
    async def update_status(
        session: AsyncSession,
        task_id: uuid.UUID,
        new_status: str,
    ) -> Task:
        task = await session.get(Task, task_id)
        if not task:
            raise ValueError(f"Task {task_id} not found")
        allowed = _VALID_TRANSITIONS.get(task.status, set())
        if new_status not in allowed:
            raise ValueError(
                f"Cannot transition from '{task.status}' to '{new_status}'"
            )
        task.status = new_status
        if new_status == "completed":
            task.completed_at = datetime.now(timezone.utc)
        return task

    @staticmethod
    async def list_tasks(
        session: AsyncSession,
        assignee_id: Optional[uuid.UUID] = None,
        creator_id: Optional[uuid.UUID] = None,
        status: Optional[str] = None,
        priority: Optional[str] = None,
        department_id: Optional[uuid.UUID] = None,
        workflow_id: Optional[uuid.UUID] = None,
        offset: int = 0,
        limit: int = 20,
    ) -> tuple[list[Task], int]:
        stmt = select(Task)
        filters = []
        if assignee_id:
            filters.append(Task.assignee_id == assignee_id)
        if creator_id:
            filters.append(Task.creator_id == creator_id)
        if status:
            filters.append(Task.status == status)
        if priority:
            filters.append(Task.priority == priority)
        if department_id:
            filters.append(Task.department_id == department_id)
        if workflow_id:
            filters.append(Task.workflow_id == workflow_id)
        if filters:
            from sqlalchemy import and_
            stmt = stmt.where(and_(*filters))
        total = await session.scalar(
            select(func.count()).select_from(stmt.subquery())
        ) or 0
        rows = (
            await session.scalars(
                stmt.order_by(Task.created_at.desc()).offset(offset).limit(limit)
            )
        ).all()
        return list(rows), total

    @staticmethod
    async def add_comment(
        session: AsyncSession,
        task_id: uuid.UUID,
        author_id: uuid.UUID,
        content: str,
    ) -> TaskComment:
        comment = TaskComment(
            task_id=task_id, author_id=author_id, content=content
        )
        session.add(comment)
        await session.flush()
        return comment
