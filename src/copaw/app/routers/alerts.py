# -*- coding: utf-8 -*-
"""
Alert Rules & Events API Router
GET/POST/PUT/DELETE  /api/enterprise/alerts/rules
GET                  /api/enterprise/alerts/events
POST                 /api/enterprise/alerts/test     (手动触发测试通知)
"""
from __future__ import annotations

import uuid
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy import select, func

from ...db.postgresql import get_db_session
from ...db.models.alert import AlertRule, AlertEvent
from ...enterprise.middleware import get_current_user
from ...enterprise.alert_service import notify

router = APIRouter(prefix="/api/enterprise/alerts", tags=["enterprise-alerts"])


# ── Schemas ──────────────────────────────────────────────────────────────────

class AlertRuleCreateRequest(BaseModel):
    rule_type: str
    description: Optional[str] = None
    threshold: int = 3
    window_seconds: int = 300
    notify_channels: list[str] = []  # wecom | dingtalk | email
    is_active: bool = True


class AlertRuleUpdateRequest(BaseModel):
    description: Optional[str] = None
    threshold: Optional[int] = None
    window_seconds: Optional[int] = None
    notify_channels: Optional[list[str]] = None
    is_active: Optional[bool] = None


class TestNotifyRequest(BaseModel):
    message: str = "CoPaw Alert test notification"


def _rule_to_dict(r: AlertRule) -> dict:
    return {
        "id": str(r.id),
        "rule_type": r.rule_type,
        "description": r.description,
        "threshold": r.threshold,
        "window_seconds": r.window_seconds,
        "notify_channels": r.notify_channels or [],
        "is_active": r.is_active,
        "created_at": r.created_at.isoformat(),
    }


def _event_to_dict(e: AlertEvent) -> dict:
    return {
        "id": str(e.id),
        "rule_type": e.rule_type,
        "triggered_at": e.triggered_at.isoformat(),
        "context": e.context,
        "notify_status": e.notify_status,
    }


# ── Rule routes ───────────────────────────────────────────────────────────────

@router.get("/rules")
async def list_alert_rules(
    is_active: Optional[bool] = Query(None),
    current_user: dict = Depends(get_current_user),
):
    async with get_db_session() as session:
        stmt = select(AlertRule)
        if is_active is not None:
            stmt = stmt.where(AlertRule.is_active == is_active)
        rules = (await session.scalars(stmt.order_by(AlertRule.rule_type))).all()
        return [_rule_to_dict(r) for r in rules]


@router.post("/rules", status_code=201)
async def create_alert_rule(
    body: AlertRuleCreateRequest,
    current_user: dict = Depends(get_current_user),
):
    async with get_db_session() as session:
        existing = await session.scalar(
            select(AlertRule).where(AlertRule.rule_type == body.rule_type)
        )
        if existing:
            raise HTTPException(
                status_code=409, detail=f"Rule type '{body.rule_type}' already exists"
            )
        rule = AlertRule(
            rule_type=body.rule_type,
            description=body.description,
            threshold=body.threshold,
            window_seconds=body.window_seconds,
            notify_channels=body.notify_channels,
            is_active=body.is_active,
        )
        session.add(rule)
        await session.flush()
        return _rule_to_dict(rule)


@router.get("/rules/{rule_id}")
async def get_alert_rule(rule_id: str, current_user: dict = Depends(get_current_user)):
    async with get_db_session() as session:
        rule = await session.get(AlertRule, uuid.UUID(rule_id))
        if not rule:
            raise HTTPException(status_code=404, detail="Rule not found")
        return _rule_to_dict(rule)


@router.put("/rules/{rule_id}")
async def update_alert_rule(
    rule_id: str,
    body: AlertRuleUpdateRequest,
    current_user: dict = Depends(get_current_user),
):
    async with get_db_session() as session:
        rule = await session.get(AlertRule, uuid.UUID(rule_id))
        if not rule:
            raise HTTPException(status_code=404, detail="Rule not found")
        if body.description is not None:
            rule.description = body.description
        if body.threshold is not None:
            rule.threshold = body.threshold
        if body.window_seconds is not None:
            rule.window_seconds = body.window_seconds
        if body.notify_channels is not None:
            rule.notify_channels = body.notify_channels
        if body.is_active is not None:
            rule.is_active = body.is_active
        return _rule_to_dict(rule)


@router.delete("/rules/{rule_id}")
async def delete_alert_rule(rule_id: str, current_user: dict = Depends(get_current_user)):
    async with get_db_session() as session:
        rule = await session.get(AlertRule, uuid.UUID(rule_id))
        if not rule:
            raise HTTPException(status_code=404, detail="Rule not found")
        await session.delete(rule)
    return {"detail": "Rule deleted"}


# ── Event routes ──────────────────────────────────────────────────────────────

@router.get("/events")
async def list_alert_events(
    rule_type: Optional[str] = Query(None),
    from_dt: Optional[datetime] = Query(None, alias="from"),
    to_dt: Optional[datetime] = Query(None, alias="to"),
    offset: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=500),
    current_user: dict = Depends(get_current_user),
):
    async with get_db_session() as session:
        stmt = select(AlertEvent)
        if rule_type:
            stmt = stmt.where(AlertEvent.rule_type == rule_type)
        if from_dt:
            stmt = stmt.where(AlertEvent.triggered_at >= from_dt)
        if to_dt:
            stmt = stmt.where(AlertEvent.triggered_at <= to_dt)

        total = await session.scalar(
            select(func.count()).select_from(stmt.subquery())
        ) or 0
        events = (
            await session.scalars(
                stmt.order_by(AlertEvent.triggered_at.desc()).offset(offset).limit(limit)
            )
        ).all()
        return {"total": total, "items": [_event_to_dict(e) for e in events]}


# ── Test notification ─────────────────────────────────────────────────────────

@router.post("/test")
async def test_notification(
    body: TestNotifyRequest,
    current_user: dict = Depends(get_current_user),
):
    """Send a test notification to all configured channels."""
    await notify(f"[TEST] {body.message}\nSent by: {current_user['username']}")
    return {"detail": "Test notification sent"}
