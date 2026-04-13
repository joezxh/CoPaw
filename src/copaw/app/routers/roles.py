# -*- coding: utf-8 -*-
"""
Roles & Permissions management API Router
GET/POST/PUT/DELETE /api/enterprise/roles
GET/PUT             /api/enterprise/roles/{id}/permissions
GET                 /api/enterprise/permissions
POST                /api/enterprise/permissions
"""
from __future__ import annotations

import uuid
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy import select, func, delete
from sqlalchemy.ext.asyncio import AsyncSession

from ...db.postgresql import get_db_session
from ...db.models.role import Role, RolePermission
from ...db.models.permission import Permission
from ...enterprise.rbac_service import RBACService
from ...enterprise.audit_service import AuditService, AuditAction
from ...enterprise.middleware import get_current_user

router = APIRouter(prefix="/enterprise", tags=["enterprise-roles"])


# ── Schemas ──────────────────────────────────────────────────────────────────

class RoleCreateRequest(BaseModel):
    name: str
    description: Optional[str] = None
    parent_role_id: Optional[str] = None
    department_id: Optional[str] = None
    is_system_role: bool = False


class RoleUpdateRequest(BaseModel):
    description: Optional[str] = None
    department_id: Optional[str] = None


class PermissionCreateRequest(BaseModel):
    resource: str
    action: str
    description: Optional[str] = None


class AssignPermissionsRequest(BaseModel):
    permission_ids: list[str]


def _role_to_dict(role: Role) -> dict:
    return {
        "id": str(role.id),
        "name": role.name,
        "description": role.description,
        "level": role.level,
        "parent_role_id": str(role.parent_role_id) if role.parent_role_id else None,
        "department_id": str(role.department_id) if role.department_id else None,
        "is_system_role": role.is_system_role,
        "created_at": role.created_at.isoformat(),
    }


def _perm_to_dict(p: Permission) -> dict:
    return {
        "id": str(p.id),
        "resource": p.resource,
        "action": p.action,
        "description": p.description,
    }


# ── Role routes ───────────────────────────────────────────────────────────────

@router.get("/roles")
async def list_roles(
    search: Optional[str] = Query(None),
    current_user: dict = Depends(get_current_user),
):
    async with get_db_session() as session:
        stmt = select(Role)
        if search:
            stmt = stmt.where(Role.name.ilike(f"%{search}%"))
        roles = (await session.scalars(stmt.order_by(Role.level, Role.name))).all()
        return [_role_to_dict(r) for r in roles]


@router.post("/roles", status_code=201)
async def create_role(
    body: RoleCreateRequest,
    current_user: dict = Depends(get_current_user),
):
    async with get_db_session() as session:
        try:
            role = await RBACService.create_role(
                session,
                name=body.name,
                description=body.description or "",
                parent_role_id=(
                    uuid.UUID(body.parent_role_id) if body.parent_role_id else None
                ),
                department_id=(
                    uuid.UUID(body.department_id) if body.department_id else None
                ),
                is_system_role=body.is_system_role,
            )
            await AuditService.log(
                session,
                action_type=AuditAction.ROLE_CREATE,
                resource_type="role",
                resource_id=str(role.id),
                result="success",
                user_id=uuid.UUID(current_user["user_id"]),
                data_after={"name": role.name},
            )
            return _role_to_dict(role)
        except ValueError as exc:
            raise HTTPException(status_code=409, detail=str(exc))


@router.get("/roles/{role_id}")
async def get_role(
    role_id: str, current_user: dict = Depends(get_current_user)
):
    async with get_db_session() as session:
        role = await session.get(Role, uuid.UUID(role_id))
        if not role:
            raise HTTPException(status_code=404, detail="Role not found")
        return _role_to_dict(role)


@router.put("/roles/{role_id}")
async def update_role(
    role_id: str,
    body: RoleUpdateRequest,
    current_user: dict = Depends(get_current_user),
):
    async with get_db_session() as session:
        role = await session.get(Role, uuid.UUID(role_id))
        if not role:
            raise HTTPException(status_code=404, detail="Role not found")
        if role.is_system_role:
            raise HTTPException(
                status_code=403, detail="Cannot modify system roles"
            )
        if body.description is not None:
            role.description = body.description
        if body.department_id is not None:
            role.department_id = (
                uuid.UUID(body.department_id) if body.department_id else None
            )
        await AuditService.log(
            session,
            action_type=AuditAction.ROLE_UPDATE,
            resource_type="role",
            resource_id=role_id,
            result="success",
            user_id=uuid.UUID(current_user["user_id"]),
        )
        return _role_to_dict(role)


@router.delete("/roles/{role_id}")
async def delete_role(
    role_id: str, current_user: dict = Depends(get_current_user)
):
    async with get_db_session() as session:
        role = await session.get(Role, uuid.UUID(role_id))
        if not role:
            raise HTTPException(status_code=404, detail="Role not found")
        if role.is_system_role:
            raise HTTPException(
                status_code=403, detail="Cannot delete system roles"
            )
        await session.delete(role)
        await AuditService.log(
            session,
            action_type=AuditAction.ROLE_DELETE,
            resource_type="role",
            resource_id=role_id,
            result="success",
            user_id=uuid.UUID(current_user["user_id"]),
        )
    return {"detail": "Role deleted"}


@router.get("/roles/{role_id}/permissions")
async def get_role_permissions(
    role_id: str, current_user: dict = Depends(get_current_user)
):
    async with get_db_session() as session:
        role_perms = (
            await session.scalars(
                select(RolePermission).where(
                    RolePermission.role_id == uuid.UUID(role_id)
                )
            )
        ).all()
        perm_ids = [rp.permission_id for rp in role_perms]
        if not perm_ids:
            return []
        perms = (
            await session.scalars(
                select(Permission).where(Permission.id.in_(perm_ids))
            )
        ).all()
        return [_perm_to_dict(p) for p in perms]


@router.put("/roles/{role_id}/permissions")
async def set_role_permissions(
    role_id: str,
    body: AssignPermissionsRequest,
    current_user: dict = Depends(get_current_user),
):
    async with get_db_session() as session:
        await RBACService.assign_permissions(
            session,
            role_id=uuid.UUID(role_id),
            permission_ids=[uuid.UUID(pid) for pid in body.permission_ids],
        )
        await AuditService.log(
            session,
            action_type=AuditAction.PERMISSION_ASSIGN,
            resource_type="role",
            resource_id=role_id,
            result="success",
            user_id=uuid.UUID(current_user["user_id"]),
            data_after={"permissions": body.permission_ids},
        )
    return {"detail": "Permissions updated"}


# ── Permission routes ─────────────────────────────────────────────────────────

@router.get("/permissions")
async def list_permissions(current_user: dict = Depends(get_current_user)):
    async with get_db_session() as session:
        perms = (await session.scalars(select(Permission))).all()
        return [_perm_to_dict(p) for p in perms]


@router.post("/permissions", status_code=201)
async def create_permission(
    body: PermissionCreateRequest,
    current_user: dict = Depends(get_current_user),
):
    async with get_db_session() as session:
        perm = await RBACService.create_permission(
            session,
            resource=body.resource,
            action=body.action,
            description=body.description or "",
        )
        return _perm_to_dict(perm)
