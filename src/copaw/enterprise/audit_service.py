# -*- coding: utf-8 -*-
"""
Enterprise AuditService — ISO 27001 compliant structured audit logging.

Writes to PostgreSQL audit_logs table (async, batched).
Exposes query helpers for the audit API router.
"""
from __future__ import annotations

import asyncio
import logging
import uuid
from datetime import datetime
from typing import Any, Optional

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from ..db.models.audit_log import AuditLog

logger = logging.getLogger(__name__)

# ── Action type constants ────────────────────────────────────────────────────
class AuditAction:
    USER_LOGIN = "USER_LOGIN"
    USER_LOGOUT = "USER_LOGOUT"
    USER_REGISTER = "USER_REGISTER"
    USER_CREATE = "USER_CREATE"
    USER_UPDATE = "USER_UPDATE"
    USER_DELETE = "USER_DELETE"
    USER_DISABLE = "USER_DISABLE"
    PASSWORD_CHANGE = "PASSWORD_CHANGE"
    MFA_ENABLE = "MFA_ENABLE"
    ROLE_CREATE = "ROLE_CREATE"
    ROLE_UPDATE = "ROLE_UPDATE"
    ROLE_DELETE = "ROLE_DELETE"
    ROLE_ASSIGN = "ROLE_ASSIGN"
    ROLE_REVOKE = "ROLE_REVOKE"
    PERMISSION_ASSIGN = "PERMISSION_ASSIGN"
    TASK_CREATE = "TASK_CREATE"
    TASK_UPDATE = "TASK_UPDATE"
    TASK_DELETE = "TASK_DELETE"
    TASK_STATUS_CHANGE = "TASK_STATUS_CHANGE"
    WORKFLOW_CREATE = "WORKFLOW_CREATE"
    WORKFLOW_RUN = "WORKFLOW_RUN"
    AGENT_RUN = "AGENT_RUN"
    SECRET_ACCESS = "SECRET_ACCESS"
    CONFIG_CHANGE = "CONFIG_CHANGE"


class AuditService:
    """Stateless audit service — session injected per call."""

    @staticmethod
    async def log(
        session: AsyncSession,
        action_type: str,
        resource_type: str,
        result: str = "success",  # success | failure | denied
        user_id: Optional[uuid.UUID] = None,
        user_role: Optional[str] = None,
        resource_id: Optional[str] = None,
        client_ip: Optional[str] = None,
        client_device: Optional[dict] = None,
        context: Optional[dict] = None,
        data_before: Optional[dict] = None,
        data_after: Optional[dict] = None,
        is_sensitive: bool = False,
    ) -> None:
        """Write a single audit log entry (async, within existing transaction)."""
        entry = AuditLog(
            user_id=user_id,
            user_role=user_role,
            action_type=action_type,
            resource_type=resource_type,
            resource_id=resource_id,
            action_result=result,
            client_ip=client_ip,
            client_device=client_device,
            context=context,
            data_before=data_before,
            data_after=data_after,
            is_sensitive=is_sensitive,
        )
        session.add(entry)
        # Caller is responsible for commit (or the session context manager does it)

    # ── Query helpers ────────────────────────────────────────────────────────

    @staticmethod
    async def query_logs(
        session: AsyncSession,
        user_id: Optional[uuid.UUID] = None,
        action_type: Optional[str] = None,
        resource_type: Optional[str] = None,
        result: Optional[str] = None,
        from_dt: Optional[datetime] = None,
        to_dt: Optional[datetime] = None,
        is_sensitive: Optional[bool] = None,
        offset: int = 0,
        limit: int = 50,
    ) -> tuple[list[AuditLog], int]:
        """Return (rows, total_count) with optional filtering."""
        stmt = select(AuditLog)
        count_stmt = select(func.count()).select_from(AuditLog)

        filters = []
        if user_id:
            filters.append(AuditLog.user_id == user_id)
        if action_type:
            filters.append(AuditLog.action_type == action_type)
        if resource_type:
            filters.append(AuditLog.resource_type == resource_type)
        if result:
            filters.append(AuditLog.action_result == result)
        if from_dt:
            filters.append(AuditLog.timestamp >= from_dt)
        if to_dt:
            filters.append(AuditLog.timestamp <= to_dt)
        if is_sensitive is not None:
            filters.append(AuditLog.is_sensitive == is_sensitive)

        if filters:
            from sqlalchemy import and_
            stmt = stmt.where(and_(*filters))
            count_stmt = count_stmt.where(and_(*filters))

        total = await session.scalar(count_stmt) or 0
        rows = (
            await session.scalars(
                stmt.order_by(AuditLog.timestamp.desc()).offset(offset).limit(limit)
            )
        ).all()
        return list(rows), total
