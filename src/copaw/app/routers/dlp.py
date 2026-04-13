# -*- coding: utf-8 -*-
"""
DLP API Router
GET/POST/PUT/DELETE /api/enterprise/dlp/rules
GET                 /api/enterprise/dlp/events
GET                 /api/enterprise/dlp/rules/builtin   (内置规则列表)
"""
from __future__ import annotations

import uuid
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy import select, func

from ...db.postgresql import get_db_session
from ...db.models.dlp import DLPRule, DLPEvent
from ...enterprise.middleware import get_current_user
from ...enterprise.dlp_service import _BUILTIN_RULES

router = APIRouter(prefix="/enterprise/dlp", tags=["enterprise-dlp"])


# ── Schemas ──────────────────────────────────────────────────────────────────

class DLPRuleCreateRequest(BaseModel):
    rule_name: str
    description: Optional[str] = None
    pattern_regex: str
    action: str = "alert"  # mask | alert | block
    is_active: bool = True


class DLPRuleUpdateRequest(BaseModel):
    description: Optional[str] = None
    pattern_regex: Optional[str] = None
    action: Optional[str] = None
    is_active: Optional[bool] = None


def _rule_to_dict(r: DLPRule) -> dict:
    return {
        "id": str(r.id),
        "rule_name": r.rule_name,
        "description": r.description,
        "pattern_regex": r.pattern_regex,
        "action": r.action,
        "is_active": r.is_active,
        "is_builtin": r.is_builtin,
        "created_at": r.created_at.isoformat(),
    }


def _event_to_dict(e: DLPEvent) -> dict:
    return {
        "id": str(e.id),
        "rule_name": e.rule_name,
        "action_taken": e.action_taken,
        "content_summary": e.content_summary,
        "user_id": str(e.user_id) if e.user_id else None,
        "context_path": e.context_path,
        "triggered_at": e.triggered_at.isoformat(),
    }


# ── Rule routes ───────────────────────────────────────────────────────────────

@router.get("/rules/builtin")
async def list_builtin_rules(current_user: dict = Depends(get_current_user)):
    """Return the built-in PII rules (read-only, informational)."""
    return [
        {
            "rule_name": r["name"],
            "description": r["description"],
            "action": r["action"],
            "pattern": r["pattern"],
            "is_builtin": True,
        }
        for r in _BUILTIN_RULES
    ]


@router.get("/rules")
async def list_rules(
    is_active: Optional[bool] = Query(None),
    offset: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    current_user: dict = Depends(get_current_user),
):
    async with get_db_session() as session:
        stmt = select(DLPRule)
        if is_active is not None:
            stmt = stmt.where(DLPRule.is_active == is_active)
        total = await session.scalar(
            select(func.count()).select_from(stmt.subquery())
        ) or 0
        rules = (
            await session.scalars(
                stmt.order_by(DLPRule.rule_name).offset(offset).limit(limit)
            )
        ).all()
        return {"total": total, "items": [_rule_to_dict(r) for r in rules]}


@router.post("/rules", status_code=201)
async def create_rule(
    body: DLPRuleCreateRequest,
    current_user: dict = Depends(get_current_user),
):
    import re
    # Validate regex
    try:
        re.compile(body.pattern_regex)
    except re.error as exc:
        raise HTTPException(status_code=400, detail=f"Invalid regex: {exc}")

    if body.action not in ("mask", "alert", "block"):
        raise HTTPException(status_code=400, detail="action must be mask | alert | block")

    async with get_db_session() as session:
        existing = await session.scalar(
            select(DLPRule).where(DLPRule.rule_name == body.rule_name)
        )
        if existing:
            raise HTTPException(status_code=409, detail=f"Rule '{body.rule_name}' already exists")

        rule = DLPRule(
            rule_name=body.rule_name,
            description=body.description,
            pattern_regex=body.pattern_regex,
            action=body.action,
            is_active=body.is_active,
            is_builtin=False,
        )
        session.add(rule)
        await session.flush()
        return _rule_to_dict(rule)


@router.get("/rules/{rule_id}")
async def get_rule(rule_id: str, current_user: dict = Depends(get_current_user)):
    async with get_db_session() as session:
        rule = await session.get(DLPRule, uuid.UUID(rule_id))
        if not rule:
            raise HTTPException(status_code=404, detail="Rule not found")
        return _rule_to_dict(rule)


@router.put("/rules/{rule_id}")
async def update_rule(
    rule_id: str,
    body: DLPRuleUpdateRequest,
    current_user: dict = Depends(get_current_user),
):
    import re
    async with get_db_session() as session:
        rule = await session.get(DLPRule, uuid.UUID(rule_id))
        if not rule:
            raise HTTPException(status_code=404, detail="Rule not found")
        if rule.is_builtin:
            raise HTTPException(status_code=403, detail="Cannot modify built-in rules")

        if body.pattern_regex is not None:
            try:
                re.compile(body.pattern_regex)
            except re.error as exc:
                raise HTTPException(status_code=400, detail=f"Invalid regex: {exc}")
            rule.pattern_regex = body.pattern_regex
        if body.description is not None:
            rule.description = body.description
        if body.action is not None:
            if body.action not in ("mask", "alert", "block"):
                raise HTTPException(status_code=400, detail="Invalid action")
            rule.action = body.action
        if body.is_active is not None:
            rule.is_active = body.is_active
        return _rule_to_dict(rule)


@router.delete("/rules/{rule_id}")
async def delete_rule(rule_id: str, current_user: dict = Depends(get_current_user)):
    async with get_db_session() as session:
        rule = await session.get(DLPRule, uuid.UUID(rule_id))
        if not rule:
            raise HTTPException(status_code=404, detail="Rule not found")
        if rule.is_builtin:
            raise HTTPException(status_code=403, detail="Cannot delete built-in rules")
        await session.delete(rule)
    return {"detail": "Rule deleted"}


# ── Event routes ──────────────────────────────────────────────────────────────

@router.get("/events")
async def list_events(
    rule_name: Optional[str] = Query(None),
    action_taken: Optional[str] = Query(None),
    user_id: Optional[str] = Query(None),
    from_dt: Optional[datetime] = Query(None, alias="from"),
    to_dt: Optional[datetime] = Query(None, alias="to"),
    offset: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=500),
    current_user: dict = Depends(get_current_user),
):
    async with get_db_session() as session:
        stmt = select(DLPEvent)
        if rule_name:
            stmt = stmt.where(DLPEvent.rule_name == rule_name)
        if action_taken:
            stmt = stmt.where(DLPEvent.action_taken == action_taken)
        if user_id:
            stmt = stmt.where(DLPEvent.user_id == uuid.UUID(user_id))
        if from_dt:
            stmt = stmt.where(DLPEvent.triggered_at >= from_dt)
        if to_dt:
            stmt = stmt.where(DLPEvent.triggered_at <= to_dt)

        total = await session.scalar(
            select(func.count()).select_from(stmt.subquery())
        ) or 0
        events = (
            await session.scalars(
                stmt.order_by(DLPEvent.triggered_at.desc()).offset(offset).limit(limit)
            )
        ).all()
        return {"total": total, "items": [_event_to_dict(e) for e in events]}
