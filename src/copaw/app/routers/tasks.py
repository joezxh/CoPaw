# -*- coding: utf-8 -*-
"""
Tasks API Router
GET/POST             /api/enterprise/tasks
GET/PUT/DELETE       /api/enterprise/tasks/{id}
PUT                  /api/enterprise/tasks/{id}/status
GET/POST             /api/enterprise/tasks/{id}/comments
"""
from __future__ import annotations

import uuid
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel

from ...db.postgresql import get_db_session
from ...db.models.task import Task
from ...enterprise.task_service import TaskService
from ...enterprise.audit_service import AuditService, AuditAction
from ...enterprise.middleware import get_current_user

router = APIRouter(prefix="/api/enterprise/tasks", tags=["enterprise-tasks"])


class TaskCreateRequest(BaseModel):
    title: str
    description: Optional[str] = None
    priority: str = "medium"
    assignee_id: Optional[str] = None
    assignee_group_id: Optional[str] = None
    department_id: Optional[str] = None
    due_date: Optional[datetime] = None
    parent_task_id: Optional[str] = None
    workflow_id: Optional[str] = None
    metadata: Optional[dict] = None


class TaskUpdateRequest(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    priority: Optional[str] = None
    assignee_id: Optional[str] = None
    due_date: Optional[datetime] = None


class StatusChangeRequest(BaseModel):
    status: str


class CommentCreateRequest(BaseModel):
    content: str


def _task_to_dict(t: Task) -> dict:
    return {
        "id": str(t.id),
        "title": t.title,
        "description": t.description,
        "status": t.status,
        "priority": t.priority,
        "creator_id": str(t.creator_id) if t.creator_id else None,
        "assignee_id": str(t.assignee_id) if t.assignee_id else None,
        "due_date": t.due_date.isoformat() if t.due_date else None,
        "completed_at": t.completed_at.isoformat() if t.completed_at else None,
        "created_at": t.created_at.isoformat(),
        "updated_at": t.updated_at.isoformat(),
    }


@router.get("")
async def list_tasks(
    assignee_id: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    priority: Optional[str] = Query(None),
    workflow_id: Optional[str] = Query(None),
    offset: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=200),
    current_user: dict = Depends(get_current_user),
):
    async with get_db_session() as session:
        tasks, total = await TaskService.list_tasks(
            session,
            assignee_id=uuid.UUID(assignee_id) if assignee_id else None,
            status=status,
            priority=priority,
            workflow_id=uuid.UUID(workflow_id) if workflow_id else None,
            offset=offset,
            limit=limit,
        )
        return {"total": total, "items": [_task_to_dict(t) for t in tasks]}


@router.post("", status_code=201)
async def create_task(
    body: TaskCreateRequest,
    current_user: dict = Depends(get_current_user),
):
    async with get_db_session() as session:
        task = await TaskService.create(
            session,
            title=body.title,
            creator_id=uuid.UUID(current_user["user_id"]),
            description=body.description,
            priority=body.priority,
            assignee_id=uuid.UUID(body.assignee_id) if body.assignee_id else None,
            assignee_group_id=uuid.UUID(body.assignee_group_id) if body.assignee_group_id else None,
            department_id=uuid.UUID(body.department_id) if body.department_id else None,
            due_date=body.due_date,
            parent_task_id=uuid.UUID(body.parent_task_id) if body.parent_task_id else None,
            workflow_id=uuid.UUID(body.workflow_id) if body.workflow_id else None,
            metadata=body.metadata,
        )
        await AuditService.log(
            session,
            action_type=AuditAction.TASK_CREATE,
            resource_type="task",
            resource_id=str(task.id),
            result="success",
            user_id=uuid.UUID(current_user["user_id"]),
            data_after={"title": task.title},
        )
        return _task_to_dict(task)


@router.get("/{task_id}")
async def get_task(task_id: str, current_user: dict = Depends(get_current_user)):
    async with get_db_session() as session:
        task = await session.get(Task, uuid.UUID(task_id))
        if not task:
            raise HTTPException(status_code=404, detail="Task not found")
        return _task_to_dict(task)


@router.put("/{task_id}")
async def update_task(
    task_id: str,
    body: TaskUpdateRequest,
    current_user: dict = Depends(get_current_user),
):
    async with get_db_session() as session:
        task = await session.get(Task, uuid.UUID(task_id))
        if not task:
            raise HTTPException(status_code=404, detail="Task not found")
        if body.title is not None:
            task.title = body.title
        if body.description is not None:
            task.description = body.description
        if body.priority is not None:
            task.priority = body.priority
        if body.assignee_id is not None:
            task.assignee_id = uuid.UUID(body.assignee_id) if body.assignee_id else None
        if body.due_date is not None:
            task.due_date = body.due_date
        await AuditService.log(
            session,
            action_type=AuditAction.TASK_UPDATE,
            resource_type="task",
            resource_id=task_id,
            result="success",
            user_id=uuid.UUID(current_user["user_id"]),
        )
        return _task_to_dict(task)


@router.put("/{task_id}/status")
async def change_task_status(
    task_id: str,
    body: StatusChangeRequest,
    current_user: dict = Depends(get_current_user),
):
    async with get_db_session() as session:
        try:
            task = await TaskService.update_status(
                session, uuid.UUID(task_id), body.status
            )
            await AuditService.log(
                session,
                action_type=AuditAction.TASK_STATUS_CHANGE,
                resource_type="task",
                resource_id=task_id,
                result="success",
                user_id=uuid.UUID(current_user["user_id"]),
                data_after={"status": body.status},
            )
            return _task_to_dict(task)
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc))


@router.delete("/{task_id}")
async def delete_task(task_id: str, current_user: dict = Depends(get_current_user)):
    async with get_db_session() as session:
        task = await session.get(Task, uuid.UUID(task_id))
        if not task:
            raise HTTPException(status_code=404, detail="Task not found")
        await session.delete(task)
        await AuditService.log(
            session,
            action_type=AuditAction.TASK_DELETE,
            resource_type="task",
            resource_id=task_id,
            result="success",
            user_id=uuid.UUID(current_user["user_id"]),
        )
    return {"detail": "Task deleted"}


@router.get("/{task_id}/comments")
async def list_comments(task_id: str, current_user: dict = Depends(get_current_user)):
    from ...db.models.task import TaskComment
    from sqlalchemy import select
    async with get_db_session() as session:
        comments = (
            await session.scalars(
                select(TaskComment)
                .where(TaskComment.task_id == uuid.UUID(task_id))
                .order_by(TaskComment.created_at)
            )
        ).all()
        return [
            {
                "id": str(c.id),
                "content": c.content,
                "author_id": str(c.author_id) if c.author_id else None,
                "created_at": c.created_at.isoformat(),
            }
            for c in comments
        ]


@router.post("/{task_id}/comments", status_code=201)
async def add_comment(
    task_id: str,
    body: CommentCreateRequest,
    current_user: dict = Depends(get_current_user),
):
    async with get_db_session() as session:
        comment = await TaskService.add_comment(
            session,
            task_id=uuid.UUID(task_id),
            author_id=uuid.UUID(current_user["user_id"]),
            content=body.content,
        )
        return {
            "id": str(comment.id),
            "content": comment.content,
            "author_id": str(comment.author_id),
            "created_at": comment.created_at.isoformat(),
        }
