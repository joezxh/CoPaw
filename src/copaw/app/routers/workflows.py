# -*- coding: utf-8 -*-
"""
Workflows API Router
GET/POST/PUT/DELETE  /api/enterprise/workflows
POST                 /api/enterprise/workflows/{id}/execute
GET                  /api/enterprise/workflows/{id}/executions
"""
from __future__ import annotations

import uuid
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel

from ...db.postgresql import get_db_session
from ...db.models.workflow import Workflow, WorkflowExecution
from ...enterprise.workflow_service import WorkflowService
from ...enterprise.audit_service import AuditService, AuditAction
from ...enterprise.middleware import get_current_user
from sqlalchemy import select

router = APIRouter(prefix="/api/enterprise/workflows", tags=["enterprise-workflows"])


class WorkflowCreateRequest(BaseModel):
    name: str
    category: str = "internal"       # dify | dify_chatflow | dify_agent | internal
    description: Optional[str] = None
    definition: Optional[dict] = None


class WorkflowUpdateRequest(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    definition: Optional[dict] = None
    status: Optional[str] = None
    category: Optional[str] = None


class ExecuteRequest(BaseModel):
    input_data: Optional[dict] = None


def _wf_to_dict(wf: Workflow) -> dict:
    return {
        "id": str(wf.id),
        "name": wf.name,
        "category": wf.category,
        "description": wf.description,
        "version": wf.version,
        "status": wf.status,
        "creator_id": str(wf.creator_id) if wf.creator_id else None,
        "definition": wf.definition,
        "created_at": wf.created_at.isoformat(),
        "updated_at": wf.updated_at.isoformat(),
    }


def _exec_to_dict(e: WorkflowExecution) -> dict:
    return {
        "id": str(e.id),
        "workflow_id": str(e.workflow_id),
        "triggered_by": str(e.triggered_by) if e.triggered_by else None,
        "status": e.status,
        "input_data": e.input_data,
        "output_data": e.output_data,
        "started_at": e.started_at.isoformat() if e.started_at else None,
        "completed_at": e.completed_at.isoformat() if e.completed_at else None,
        "error_message": e.error_message,
        "created_at": e.created_at.isoformat(),
    }


@router.get("")
async def list_workflows(
    category: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    offset: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=200),
    current_user: dict = Depends(get_current_user),
):
    async with get_db_session() as session:
        wfs, total = await WorkflowService.list_workflows(
            session, category=category, status=status, offset=offset, limit=limit
        )
        return {"total": total, "items": [_wf_to_dict(w) for w in wfs]}


@router.post("", status_code=201)
async def create_workflow(
    body: WorkflowCreateRequest,
    current_user: dict = Depends(get_current_user),
):
    async with get_db_session() as session:
        try:
            wf = await WorkflowService.create(
                session,
                name=body.name,
                creator_id=uuid.UUID(current_user["user_id"]),
                category=body.category,
                description=body.description,
                definition=body.definition,
            )
            await AuditService.log(
                session,
                action_type=AuditAction.WORKFLOW_CREATE,
                resource_type="workflow",
                resource_id=str(wf.id),
                result="success",
                user_id=uuid.UUID(current_user["user_id"]),
                data_after={"name": wf.name, "category": wf.category},
            )
            return _wf_to_dict(wf)
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc))


@router.get("/{workflow_id}")
async def get_workflow(workflow_id: str, current_user: dict = Depends(get_current_user)):
    async with get_db_session() as session:
        wf = await session.get(Workflow, uuid.UUID(workflow_id))
        if not wf:
            raise HTTPException(status_code=404, detail="Workflow not found")
        return _wf_to_dict(wf)


@router.put("/{workflow_id}")
async def update_workflow(
    workflow_id: str,
    body: WorkflowUpdateRequest,
    current_user: dict = Depends(get_current_user),
):
    async with get_db_session() as session:
        try:
            wf = await WorkflowService.update(
                session,
                workflow_id=uuid.UUID(workflow_id),
                name=body.name,
                description=body.description,
                definition=body.definition,
                status=body.status,
                category=body.category,
            )
            return _wf_to_dict(wf)
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc))


@router.delete("/{workflow_id}")
async def delete_workflow(workflow_id: str, current_user: dict = Depends(get_current_user)):
    async with get_db_session() as session:
        wf = await session.get(Workflow, uuid.UUID(workflow_id))
        if not wf:
            raise HTTPException(status_code=404, detail="Workflow not found")
        await session.delete(wf)
    return {"detail": "Workflow deleted"}


@router.post("/{workflow_id}/execute", status_code=202)
async def execute_workflow(
    workflow_id: str,
    body: ExecuteRequest,
    current_user: dict = Depends(get_current_user),
):
    async with get_db_session() as session:
        try:
            execution = await WorkflowService.start_execution(
                session,
                workflow_id=uuid.UUID(workflow_id),
                triggered_by=uuid.UUID(current_user["user_id"]),
                input_data=body.input_data,
            )
            await AuditService.log(
                session,
                action_type=AuditAction.WORKFLOW_RUN,
                resource_type="workflow",
                resource_id=workflow_id,
                result="success",
                user_id=uuid.UUID(current_user["user_id"]),
                context={"execution_id": str(execution.id)},
            )
            return _exec_to_dict(execution)
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc))


@router.get("/{workflow_id}/executions")
async def list_executions(
    workflow_id: str,
    status: Optional[str] = Query(None),
    offset: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=200),
    current_user: dict = Depends(get_current_user),
):
    async with get_db_session() as session:
        stmt = select(WorkflowExecution).where(
            WorkflowExecution.workflow_id == uuid.UUID(workflow_id)
        )
        if status:
            stmt = stmt.where(WorkflowExecution.status == status)
        execs = (
            await session.scalars(
                stmt.order_by(WorkflowExecution.created_at.desc())
                .offset(offset)
                .limit(limit)
            )
        ).all()
        return [_exec_to_dict(e) for e in execs]
