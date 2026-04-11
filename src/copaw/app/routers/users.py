# -*- coding: utf-8 -*-
"""
Users management API Router
GET    /api/enterprise/users
POST   /api/enterprise/users
GET    /api/enterprise/users/{user_id}
PUT    /api/enterprise/users/{user_id}
DELETE /api/enterprise/users/{user_id}
GET    /api/enterprise/users/{user_id}/roles
PUT    /api/enterprise/users/{user_id}/roles
"""
from __future__ import annotations

import uuid
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from ...db.postgresql import get_db_session
from ...db.models.user import User
from ...enterprise.auth_service import hash_password
from ...enterprise.rbac_service import RBACService
from ...enterprise.audit_service import AuditService, AuditAction
from ...enterprise.middleware import get_current_user

router = APIRouter(prefix="/api/enterprise/users", tags=["enterprise-users"])


# ── Schemas ──────────────────────────────────────────────────────────────────

class UserCreateRequest(BaseModel):
    username: str
    password: str
    email: Optional[str] = None
    display_name: Optional[str] = None
    department_id: Optional[str] = None
    status: str = "active"


class UserUpdateRequest(BaseModel):
    email: Optional[str] = None
    display_name: Optional[str] = None
    department_id: Optional[str] = None
    status: Optional[str] = None


class AssignRolesRequest(BaseModel):
    role_ids: list[str]


def _user_to_dict(user: User) -> dict:
    return {
        "id": str(user.id),
        "username": user.username,
        "email": user.email,
        "display_name": user.display_name,
        "department_id": str(user.department_id) if user.department_id else None,
        "status": user.status,
        "mfa_enabled": user.mfa_enabled,
        "last_login_at": user.last_login_at.isoformat() if user.last_login_at else None,
        "created_at": user.created_at.isoformat(),
    }


# ── Routes ───────────────────────────────────────────────────────────────────

@router.get("")
async def list_users(
    search: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    department_id: Optional[str] = Query(None),
    offset: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=200),
    current_user: dict = Depends(get_current_user),
):
    async with get_db_session() as session:
        stmt = select(User)
        if search:
            stmt = stmt.where(
                User.username.ilike(f"%{search}%") | User.email.ilike(f"%{search}%")
            )
        if status:
            stmt = stmt.where(User.status == status)
        if department_id:
            stmt = stmt.where(User.department_id == uuid.UUID(department_id))

        total = await session.scalar(
            select(func.count()).select_from(stmt.subquery())
        ) or 0
        users = (
            await session.scalars(
                stmt.order_by(User.created_at.desc()).offset(offset).limit(limit)
            )
        ).all()

        return {
            "total": total,
            "offset": offset,
            "limit": limit,
            "items": [_user_to_dict(u) for u in users],
        }


@router.post("", status_code=201)
async def create_user(
    body: UserCreateRequest,
    current_user: dict = Depends(get_current_user),
):
    from ...enterprise.auth_service import AuthService
    async with get_db_session() as session:
        try:
            user = await AuthService.register(
                session,
                username=body.username,
                password=body.password,
                email=body.email,
                display_name=body.display_name,
            )
            if body.department_id:
                user.department_id = uuid.UUID(body.department_id)
            user.status = body.status
            await AuditService.log(
                session,
                action_type=AuditAction.USER_CREATE,
                resource_type="user",
                resource_id=str(user.id),
                result="success",
                user_id=uuid.UUID(current_user["user_id"]),
                data_after={"username": user.username},
            )
            return _user_to_dict(user)
        except ValueError as exc:
            raise HTTPException(status_code=409, detail=str(exc))


@router.get("/{user_id}")
async def get_user(
    user_id: str,
    current_user: dict = Depends(get_current_user),
):
    async with get_db_session() as session:
        user = await session.get(User, uuid.UUID(user_id))
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        return _user_to_dict(user)


@router.put("/{user_id}")
async def update_user(
    user_id: str,
    body: UserUpdateRequest,
    current_user: dict = Depends(get_current_user),
):
    async with get_db_session() as session:
        user = await session.get(User, uuid.UUID(user_id))
        if not user:
            raise HTTPException(status_code=404, detail="User not found")

        before = {
            "email": user.email,
            "display_name": user.display_name,
            "status": user.status,
        }
        if body.email is not None:
            user.email = body.email
        if body.display_name is not None:
            user.display_name = body.display_name
        if body.department_id is not None:
            user.department_id = (
                uuid.UUID(body.department_id) if body.department_id else None
            )
        if body.status is not None:
            user.status = body.status

        await AuditService.log(
            session,
            action_type=AuditAction.USER_UPDATE,
            resource_type="user",
            resource_id=user_id,
            result="success",
            user_id=uuid.UUID(current_user["user_id"]),
            data_before=before,
            data_after={"email": user.email, "status": user.status},
        )
        return _user_to_dict(user)


@router.delete("/{user_id}")
async def disable_user(
    user_id: str,
    current_user: dict = Depends(get_current_user),
):
    """Soft-delete: sets status=disabled (does not delete the row)."""
    async with get_db_session() as session:
        user = await session.get(User, uuid.UUID(user_id))
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        user.status = "disabled"
        await AuditService.log(
            session,
            action_type=AuditAction.USER_DISABLE,
            resource_type="user",
            resource_id=user_id,
            result="success",
            user_id=uuid.UUID(current_user["user_id"]),
        )
    return {"detail": "User disabled"}


@router.get("/{user_id}/roles")
async def get_user_roles(
    user_id: str,
    current_user: dict = Depends(get_current_user),
):
    async with get_db_session() as session:
        roles = await RBACService.get_user_roles(session, uuid.UUID(user_id))
        return [
            {"id": str(r.id), "name": r.name, "level": r.level}
            for r in roles
        ]


@router.put("/{user_id}/roles")
async def assign_roles(
    user_id: str,
    body: AssignRolesRequest,
    current_user: dict = Depends(get_current_user),
):
    async with get_db_session() as session:
        uid = uuid.UUID(user_id)
        # Remove all existing roles first
        from sqlalchemy import delete as sa_delete
        from ...db.models.role import UserRole
        await session.execute(
            sa_delete(UserRole).where(UserRole.user_id == uid)
        )
        # Assign new roles
        for rid in body.role_ids:
            await RBACService.assign_role_to_user(
                session,
                user_id=uid,
                role_id=uuid.UUID(rid),
                assigned_by=uuid.UUID(current_user["user_id"]),
            )
        await AuditService.log(
            session,
            action_type=AuditAction.ROLE_ASSIGN,
            resource_type="user",
            resource_id=user_id,
            result="success",
            user_id=uuid.UUID(current_user["user_id"]),
            data_after={"roles": body.role_ids},
        )
    return {"detail": "Roles assigned"}
