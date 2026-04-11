# -*- coding: utf-8 -*-
"""
Enterprise WorkflowService — Workflow CRUD + execution management.
Supports Dify categories: 'dify' | 'dify_chatflow' | 'dify_agent' | 'internal'
"""
from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from ..db.models.workflow import Workflow, WorkflowExecution

_DIFY_CATEGORIES = {"dify", "dify_chatflow", "dify_agent", "internal"}


class WorkflowService:

    @staticmethod
    async def create(
        session: AsyncSession,
        name: str,
        creator_id: uuid.UUID,
        category: str = "internal",
        description: Optional[str] = None,
        definition: Optional[dict] = None,
    ) -> Workflow:
        if category not in _DIFY_CATEGORIES:
            raise ValueError(
                f"Invalid category '{category}'. "
                f"Must be one of: {sorted(_DIFY_CATEGORIES)}"
            )
        wf = Workflow(
            name=name,
            description=description,
            category=category,
            definition=definition or {},
            creator_id=creator_id,
            status="draft",
        )
        session.add(wf)
        await session.flush()
        return wf

    @staticmethod
    async def update(
        session: AsyncSession,
        workflow_id: uuid.UUID,
        name: Optional[str] = None,
        description: Optional[str] = None,
        definition: Optional[dict] = None,
        status: Optional[str] = None,
        category: Optional[str] = None,
    ) -> Workflow:
        wf = await session.get(Workflow, workflow_id)
        if not wf:
            raise ValueError(f"Workflow {workflow_id} not found")
        if name is not None:
            wf.name = name
        if description is not None:
            wf.description = description
        if definition is not None:
            wf.definition = definition
            wf.version = wf.version + 1
        if status is not None:
            wf.status = status
        if category is not None:
            if category not in _DIFY_CATEGORIES:
                raise ValueError(f"Invalid category '{category}'")
            wf.category = category
        return wf

    @staticmethod
    async def list_workflows(
        session: AsyncSession,
        category: Optional[str] = None,
        status: Optional[str] = None,
        creator_id: Optional[uuid.UUID] = None,
        offset: int = 0,
        limit: int = 20,
    ) -> tuple[list[Workflow], int]:
        stmt = select(Workflow)
        filters = []
        if category:
            filters.append(Workflow.category == category)
        if status:
            filters.append(Workflow.status == status)
        if creator_id:
            filters.append(Workflow.creator_id == creator_id)
        if filters:
            from sqlalchemy import and_
            stmt = stmt.where(and_(*filters))
        total = await session.scalar(
            select(func.count()).select_from(stmt.subquery())
        ) or 0
        rows = (
            await session.scalars(
                stmt.order_by(Workflow.created_at.desc()).offset(offset).limit(limit)
            )
        ).all()
        return list(rows), total

    @staticmethod
    async def start_execution(
        session: AsyncSession,
        workflow_id: uuid.UUID,
        triggered_by: uuid.UUID,
        input_data: Optional[dict] = None,
    ) -> WorkflowExecution:
        wf = await session.get(Workflow, workflow_id)
        if not wf:
            raise ValueError(f"Workflow {workflow_id} not found")
        if wf.status != "active":
            raise ValueError(f"Workflow is not active (status={wf.status})")

        execution = WorkflowExecution(
            workflow_id=workflow_id,
            triggered_by=triggered_by,
            status="running",
            started_at=datetime.now(timezone.utc),
            input_data=input_data or {},
        )
        session.add(execution)
        await session.flush()
        return execution

    @staticmethod
    async def complete_execution(
        session: AsyncSession,
        execution_id: uuid.UUID,
        output_data: Optional[dict] = None,
        error_message: Optional[str] = None,
    ) -> WorkflowExecution:
        execution = await session.get(WorkflowExecution, execution_id)
        if not execution:
            raise ValueError(f"Execution {execution_id} not found")
        now = datetime.now(timezone.utc)
        execution.completed_at = now
        execution.output_data = output_data
        execution.error_message = error_message
        execution.status = "failed" if error_message else "completed"
        return execution
