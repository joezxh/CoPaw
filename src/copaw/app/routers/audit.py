# -*- coding: utf-8 -*-
"""
Audit Log Query API Router
GET /api/enterprise/audit
"""
from __future__ import annotations

from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, Query
import uuid

from ...db.postgresql import get_db_session
from ...enterprise.audit_service import AuditService
from ...enterprise.middleware import get_current_user

router = APIRouter(prefix="/api/enterprise/audit", tags=["enterprise-audit"])


@router.get("")
async def query_audit_logs(
    user_id: Optional[str] = Query(None),
    action_type: Optional[str] = Query(None),
    resource_type: Optional[str] = Query(None),
    result: Optional[str] = Query(None),
    from_dt: Optional[datetime] = Query(None, alias="from"),
    to_dt: Optional[datetime] = Query(None, alias="to"),
    is_sensitive: Optional[bool] = Query(None),
    offset: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=500),
    current_user: dict = Depends(get_current_user),
):
    """Query audit logs with rich filtering. Returns paginated results."""
    async with get_db_session() as session:
        rows, total = await AuditService.query_logs(
            session,
            user_id=uuid.UUID(user_id) if user_id else None,
            action_type=action_type,
            resource_type=resource_type,
            result=result,
            from_dt=from_dt,
            to_dt=to_dt,
            is_sensitive=is_sensitive,
            offset=offset,
            limit=limit,
        )
        items = [
            {
                "id": r.id,
                "timestamp": r.timestamp.isoformat(),
                "user_id": str(r.user_id) if r.user_id else None,
                "user_role": r.user_role,
                "action_type": r.action_type,
                "resource_type": r.resource_type,
                "resource_id": r.resource_id,
                "action_result": r.action_result,
                "client_ip": str(r.client_ip) if r.client_ip else None,
                "is_sensitive": r.is_sensitive,
                "context": r.context,
            }
            for r in rows
        ]
        return {"total": total, "offset": offset, "limit": limit, "items": items}
