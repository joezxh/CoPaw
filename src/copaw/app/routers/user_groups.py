# -*- coding: utf-8 -*-
"""
UserGroup management API Router
GET/POST             /api/enterprise/groups
GET/PUT/DELETE       /api/enterprise/groups/{id}
GET/POST             /api/enterprise/groups/{id}/members
DELETE               /api/enterprise/groups/{id}/members/{user_id}
"""
from __future__ import annotations

import uuid
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy import select, func, delete as sa_delete

from ...db.postgresql import get_db_session
from ...db.models.user import User, UserGroup, UserGroupMember
from ...enterprise.audit_service import AuditService, AuditAction
from ...enterprise.middleware import get_current_user

router = APIRouter(prefix="/api/enterprise/groups", tags=["enterprise-groups"])


# ── Schemas ──────────────────────────────────────────────────────────────────

class GroupCreateRequest(BaseModel):
    name: str
    description: Optional[str] = None
    department_id: Optional[str] = None


class GroupUpdateRequest(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    department_id: Optional[str] = None


class AddMembersRequest(BaseModel):
    user_ids: list[str]


def _group_to_dict(g: UserGroup) -> dict:
    return {
        "id": str(g.id),
        "name": g.name,
        "description": g.description,
        "department_id": str(g.department_id) if g.department_id else None,
        "created_at": g.created_at.isoformat(),
    }


# ── Routes ───────────────────────────────────────────────────────────────────

@router.get("")
async def list_groups(
    search: Optional[str] = Query(None),
    department_id: Optional[str] = Query(None),
    offset: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    current_user: dict = Depends(get_current_user),
):
    async with get_db_session() as session:
        stmt = select(UserGroup)
        if search:
            stmt = stmt.where(UserGroup.name.ilike(f"%{search}%"))
        if department_id:
            stmt = stmt.where(UserGroup.department_id == uuid.UUID(department_id))

        total = await session.scalar(
            select(func.count()).select_from(stmt.subquery())
        ) or 0
        groups = (
            await session.scalars(
                stmt.order_by(UserGroup.name).offset(offset).limit(limit)
            )
        ).all()
        return {
            "total": total,
            "offset": offset,
            "limit": limit,
            "items": [_group_to_dict(g) for g in groups],
        }


@router.post("", status_code=201)
async def create_group(
    body: GroupCreateRequest,
    current_user: dict = Depends(get_current_user),
):
    async with get_db_session() as session:
        # Check uniqueness
        existing = await session.scalar(
            select(UserGroup).where(UserGroup.name == body.name)
        )
        if existing:
            raise HTTPException(status_code=409, detail=f"Group '{body.name}' already exists")

        group = UserGroup(
            name=body.name,
            description=body.description,
            department_id=uuid.UUID(body.department_id) if body.department_id else None,
        )
        session.add(group)
        await session.flush()
        await AuditService.log(
            session,
            action_type="GROUP_CREATE",
            resource_type="group",
            resource_id=str(group.id),
            result="success",
            user_id=uuid.UUID(current_user["user_id"]),
            data_after={"name": group.name},
        )
        return _group_to_dict(group)


@router.get("/{group_id}")
async def get_group(
    group_id: str,
    current_user: dict = Depends(get_current_user),
):
    async with get_db_session() as session:
        group = await session.get(UserGroup, uuid.UUID(group_id))
        if not group:
            raise HTTPException(status_code=404, detail="Group not found")
        return _group_to_dict(group)


@router.put("/{group_id}")
async def update_group(
    group_id: str,
    body: GroupUpdateRequest,
    current_user: dict = Depends(get_current_user),
):
    async with get_db_session() as session:
        group = await session.get(UserGroup, uuid.UUID(group_id))
        if not group:
            raise HTTPException(status_code=404, detail="Group not found")

        if body.name is not None:
            group.name = body.name
        if body.description is not None:
            group.description = body.description
        if body.department_id is not None:
            group.department_id = (
                uuid.UUID(body.department_id) if body.department_id else None
            )
        await AuditService.log(
            session,
            action_type="GROUP_UPDATE",
            resource_type="group",
            resource_id=group_id,
            result="success",
            user_id=uuid.UUID(current_user["user_id"]),
        )
        return _group_to_dict(group)


@router.delete("/{group_id}")
async def delete_group(
    group_id: str,
    current_user: dict = Depends(get_current_user),
):
    async with get_db_session() as session:
        group = await session.get(UserGroup, uuid.UUID(group_id))
        if not group:
            raise HTTPException(status_code=404, detail="Group not found")
        await session.delete(group)
        await AuditService.log(
            session,
            action_type="GROUP_DELETE",
            resource_type="group",
            resource_id=group_id,
            result="success",
            user_id=uuid.UUID(current_user["user_id"]),
        )
    return {"detail": "Group deleted"}


@router.get("/{group_id}/members")
async def list_members(
    group_id: str,
    current_user: dict = Depends(get_current_user),
):
    async with get_db_session() as session:
        memberships = (
            await session.scalars(
                select(UserGroupMember).where(
                    UserGroupMember.group_id == uuid.UUID(group_id)
                )
            )
        ).all()
        user_ids = [m.user_id for m in memberships]
        if not user_ids:
            return []
        users = (
            await session.scalars(select(User).where(User.id.in_(user_ids)))
        ).all()
        return [
            {
                "id": str(u.id),
                "username": u.username,
                "display_name": u.display_name,
                "email": u.email,
                "status": u.status,
                "joined_at": next(
                    (m.joined_at.isoformat() for m in memberships if m.user_id == u.id),
                    None,
                ),
            }
            for u in users
        ]


@router.post("/{group_id}/members", status_code=201)
async def add_members(
    group_id: str,
    body: AddMembersRequest,
    current_user: dict = Depends(get_current_user),
):
    """Batch add users to a group (idempotent)."""
    async with get_db_session() as session:
        # Verify group exists
        group = await session.get(UserGroup, uuid.UUID(group_id))
        if not group:
            raise HTTPException(status_code=404, detail="Group not found")

        gid = uuid.UUID(group_id)
        added = 0
        for uid_str in body.user_ids:
            uid = uuid.UUID(uid_str)
            exists = await session.scalar(
                select(UserGroupMember).where(
                    UserGroupMember.group_id == gid,
                    UserGroupMember.user_id == uid,
                )
            )
            if not exists:
                session.add(UserGroupMember(group_id=gid, user_id=uid))
                added += 1
        await AuditService.log(
            session,
            action_type="GROUP_MEMBER_ADD",
            resource_type="group",
            resource_id=group_id,
            result="success",
            user_id=uuid.UUID(current_user["user_id"]),
            data_after={"added": added, "users": body.user_ids},
        )
        return {"added": added, "total_requested": len(body.user_ids)}


@router.delete("/{group_id}/members/{user_id}")
async def remove_member(
    group_id: str,
    user_id: str,
    current_user: dict = Depends(get_current_user),
):
    async with get_db_session() as session:
        await session.execute(
            sa_delete(UserGroupMember).where(
                UserGroupMember.group_id == uuid.UUID(group_id),
                UserGroupMember.user_id == uuid.UUID(user_id),
            )
        )
        await AuditService.log(
            session,
            action_type="GROUP_MEMBER_REMOVE",
            resource_type="group",
            resource_id=group_id,
            result="success",
            user_id=uuid.UUID(current_user["user_id"]),
            data_after={"removed_user": user_id},
        )
    return {"detail": "Member removed"}
