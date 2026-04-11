# -*- coding: utf-8 -*-
"""
Departments (org hierarchy) API Router — pure PostgreSQL, recursive CTE.
GET/POST/PUT/DELETE /api/enterprise/departments
GET                 /api/enterprise/departments/{id}/members
GET                 /api/enterprise/departments/tree
"""
from __future__ import annotations

import uuid
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession

from ...db.postgresql import get_db_session
from ...db.models.organization import Department
from ...db.models.user import User
from ...enterprise.middleware import get_current_user

router = APIRouter(prefix="/api/enterprise/departments", tags=["enterprise-departments"])


# ── Schemas ──────────────────────────────────────────────────────────────────

class DeptCreateRequest(BaseModel):
    name: str
    parent_id: Optional[str] = None
    manager_id: Optional[str] = None
    description: Optional[str] = None


class DeptUpdateRequest(BaseModel):
    name: Optional[str] = None
    parent_id: Optional[str] = None
    manager_id: Optional[str] = None
    description: Optional[str] = None


def _dept_to_dict(d: Department) -> dict:
    return {
        "id": str(d.id),
        "name": d.name,
        "parent_id": str(d.parent_id) if d.parent_id else None,
        "manager_id": str(d.manager_id) if d.manager_id else None,
        "level": d.level,
        "description": d.description,
        "created_at": d.created_at.isoformat(),
    }


# ── Routes ───────────────────────────────────────────────────────────────────

@router.get("/tree")
async def get_tree(current_user: dict = Depends(get_current_user)):
    """Return the full department tree using a recursive CTE."""
    async with get_db_session() as session:
        # PostgreSQL recursive CTE — returns all departments with full path
        cte_sql = text("""
            WITH RECURSIVE dept_tree AS (
                SELECT id, name, parent_id, manager_id, level, description,
                       created_at, ARRAY[id::text] AS path
                FROM departments
                WHERE parent_id IS NULL
              UNION ALL
                SELECT d.id, d.name, d.parent_id, d.manager_id, d.level,
                       d.description, d.created_at,
                       dt.path || d.id::text
                FROM departments d
                JOIN dept_tree dt ON d.parent_id = dt.id
            )
            SELECT * FROM dept_tree ORDER BY path;
        """)
        result = await session.execute(cte_sql)
        rows = result.mappings().all()
        return [dict(r) for r in rows]


@router.get("")
async def list_departments(
    parent_id: Optional[str] = Query(None),
    current_user: dict = Depends(get_current_user),
):
    async with get_db_session() as session:
        stmt = select(Department)
        if parent_id:
            stmt = stmt.where(Department.parent_id == uuid.UUID(parent_id))
        elif parent_id == "":
            stmt = stmt.where(Department.parent_id.is_(None))
        depts = (await session.scalars(stmt.order_by(Department.level, Department.name))).all()
        return [_dept_to_dict(d) for d in depts]


@router.post("", status_code=201)
async def create_department(
    body: DeptCreateRequest,
    current_user: dict = Depends(get_current_user),
):
    async with get_db_session() as session:
        level = 0
        if body.parent_id:
            parent = await session.get(Department, uuid.UUID(body.parent_id))
            if parent:
                level = parent.level + 1

        dept = Department(
            name=body.name,
            parent_id=uuid.UUID(body.parent_id) if body.parent_id else None,
            manager_id=uuid.UUID(body.manager_id) if body.manager_id else None,
            level=level,
            description=body.description,
        )
        session.add(dept)
        await session.flush()
        return _dept_to_dict(dept)


@router.get("/{dept_id}")
async def get_department(dept_id: str, current_user: dict = Depends(get_current_user)):
    async with get_db_session() as session:
        dept = await session.get(Department, uuid.UUID(dept_id))
        if not dept:
            raise HTTPException(status_code=404, detail="Department not found")
        return _dept_to_dict(dept)


@router.put("/{dept_id}")
async def update_department(
    dept_id: str,
    body: DeptUpdateRequest,
    current_user: dict = Depends(get_current_user),
):
    async with get_db_session() as session:
        dept = await session.get(Department, uuid.UUID(dept_id))
        if not dept:
            raise HTTPException(status_code=404, detail="Department not found")
        if body.name is not None:
            dept.name = body.name
        if body.description is not None:
            dept.description = body.description
        if body.manager_id is not None:
            dept.manager_id = uuid.UUID(body.manager_id) if body.manager_id else None
        if body.parent_id is not None:
            dept.parent_id = uuid.UUID(body.parent_id) if body.parent_id else None
        return _dept_to_dict(dept)


@router.delete("/{dept_id}")
async def delete_department(dept_id: str, current_user: dict = Depends(get_current_user)):
    async with get_db_session() as session:
        dept = await session.get(Department, uuid.UUID(dept_id))
        if not dept:
            raise HTTPException(status_code=404, detail="Department not found")
        children = await session.scalar(
            select(Department).where(Department.parent_id == uuid.UUID(dept_id))
        )
        if children:
            raise HTTPException(
                status_code=409, detail="Cannot delete department with sub-departments"
            )
        await session.delete(dept)
    return {"detail": "Department deleted"}


@router.get("/{dept_id}/members")
async def get_members(dept_id: str, current_user: dict = Depends(get_current_user)):
    async with get_db_session() as session:
        users = (
            await session.scalars(
                select(User).where(User.department_id == uuid.UUID(dept_id))
            )
        ).all()
        return [
            {
                "id": str(u.id),
                "username": u.username,
                "display_name": u.display_name,
                "email": u.email,
                "status": u.status,
            }
            for u in users
        ]
