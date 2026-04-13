# -*- coding: utf-8 -*-
"""
Enterprise RBACService — role-based access control with Redis caching.

Provides:
- Role/permission CRUD
- User-role assignment
- Permission check (with Redis-cached role→permissions map)
- Hierarchical role traversal (parent_role_id chain, up to 5 levels)
"""
from __future__ import annotations

import json
import logging
import uuid
from typing import Optional

from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import AsyncSession

from ..db.models.role import Role, RolePermission, UserRole
from ..db.models.permission import Permission
from ..db.models.user import User

logger = logging.getLogger(__name__)

_PERMISSION_CACHE_TTL = 300  # 5 minutes


class RBACService:
    """Inject AsyncSession + optional RedisManager per call."""

    # ── Permission check ─────────────────────────────────────────────────────

    @staticmethod
    async def has_permission(
        session: AsyncSession,
        user_id: uuid.UUID,
        resource: str,
        action: str,
        redis=None,  # RedisManager instance (optional, for caching)
    ) -> bool:
        """Return True if the user has the given permission (direct or via role hierarchy).

        Cache key: ``rbac:user:{user_id}:perms`` → JSON list of "resource:action".
        """
        cache_key = f"rbac:user:{user_id}:perms"

        # Try Redis cache first
        if redis:
            cached = await redis.get(cache_key)
            if cached:
                perms: list[str] = json.loads(cached)
                return _matches_any(perms, resource, action)

        # Load from DB
        perms = await RBACService._load_user_permissions(session, user_id)

        # Store in Redis
        if redis:
            await redis.set(cache_key, json.dumps(perms), ttl=_PERMISSION_CACHE_TTL)

        return _matches_any(perms, resource, action)

    @staticmethod
    async def _load_user_permissions(
        session: AsyncSession,
        user_id: uuid.UUID,
    ) -> list[str]:
        """Collect all permissions for a user via their roles (with hierarchy)."""
        # Get direct roles
        user_roles = (
            await session.scalars(
                select(UserRole).where(UserRole.user_id == user_id)
            )
        ).all()

        role_ids: set[uuid.UUID] = {ur.role_id for ur in user_roles}

        # Expand role hierarchy (up to 5 levels)
        expanded: set[uuid.UUID] = set(role_ids)
        queue = list(role_ids)
        for _ in range(5):
            if not queue:
                break
            roles = (
                await session.scalars(
                    select(Role).where(
                        Role.id.in_(queue), Role.parent_role_id.is_not(None)
                    )
                )
            ).all()
            new_parents = {
                r.parent_role_id
                for r in roles
                if r.parent_role_id and r.parent_role_id not in expanded
            }
            expanded |= new_parents
            queue = list(new_parents)

        if not expanded:
            return []

        # Get permissions for all expanded roles
        role_perms = (
            await session.scalars(
                select(RolePermission).where(
                    RolePermission.role_id.in_(expanded)
                )
            )
        ).all()

        perm_ids = {rp.permission_id for rp in role_perms}
        if not perm_ids:
            return []

        permissions = (
            await session.scalars(
                select(Permission).where(Permission.id.in_(perm_ids))
            )
        ).all()

        return [f"{p.resource}:{p.action}" for p in permissions]

    # ── Role CRUD ────────────────────────────────────────────────────────────

    @staticmethod
    async def create_role(
        session: AsyncSession,
        name: str,
        description: str = "",
        parent_role_id: Optional[uuid.UUID] = None,
        department_id: Optional[uuid.UUID] = None,
        is_system_role: bool = False,
    ) -> Role:
        existing = await session.scalar(select(Role).where(Role.name == name))
        if existing:
            raise ValueError(f"Role '{name}' already exists")

        level = 0
        if parent_role_id:
            parent = await session.get(Role, parent_role_id)
            if parent:
                level = parent.level + 1
                if level > 5:
                    raise ValueError("Maximum role hierarchy depth (5) exceeded")

        role = Role(
            name=name,
            description=description,
            parent_role_id=parent_role_id,
            department_id=department_id,
            level=level,
            is_system_role=is_system_role,
        )
        session.add(role)
        await session.flush()
        logger.info("Created role: %s (id=%s)", name, role.id)
        return role

    @staticmethod
    async def assign_permissions(
        session: AsyncSession,
        role_id: uuid.UUID,
        permission_ids: list[uuid.UUID],
        redis=None,
    ) -> None:
        """Replace all permissions for a role."""
        await session.execute(
            delete(RolePermission).where(RolePermission.role_id == role_id)
        )
        for perm_id in permission_ids:
            session.add(RolePermission(role_id=role_id, permission_id=perm_id))

        # Invalidate permission caches for all users with this role
        if redis:
            user_roles = (
                await session.scalars(
                    select(UserRole).where(UserRole.role_id == role_id)
                )
            ).all()
            for ur in user_roles:
                await redis.delete(f"rbac:user:{ur.user_id}:perms")

    @staticmethod
    async def assign_role_to_user(
        session: AsyncSession,
        user_id: uuid.UUID,
        role_id: uuid.UUID,
        assigned_by: Optional[uuid.UUID] = None,
        redis=None,
    ) -> None:
        exists = await session.scalar(
            select(UserRole).where(
                UserRole.user_id == user_id, UserRole.role_id == role_id
            )
        )
        if exists:
            return  # Already assigned
        ur = UserRole(user_id=user_id, role_id=role_id, assigned_by=assigned_by)
        session.add(ur)
        if redis:
            await redis.delete(f"rbac:user:{user_id}:perms")

    @staticmethod
    async def revoke_role_from_user(
        session: AsyncSession,
        user_id: uuid.UUID,
        role_id: uuid.UUID,
        redis=None,
    ) -> None:
        await session.execute(
            delete(UserRole).where(
                UserRole.user_id == user_id, UserRole.role_id == role_id
            )
        )
        if redis:
            await redis.delete(f"rbac:user:{user_id}:perms")

    # ── Permission CRUD ──────────────────────────────────────────────────────

    @staticmethod
    async def create_permission(
        session: AsyncSession,
        resource: str,
        action: str,
        description: str = "",
    ) -> Permission:
        perm = Permission(resource=resource, action=action, description=description)
        session.add(perm)
        await session.flush()
        return perm

    @staticmethod
    async def get_user_roles(
        session: AsyncSession, user_id: uuid.UUID
    ) -> list[Role]:
        user_roles = (
            await session.scalars(
                select(UserRole).where(UserRole.user_id == user_id)
            )
        ).all()
        role_ids = [ur.role_id for ur in user_roles]
        if not role_ids:
            return []
        return list(
            (await session.scalars(select(Role).where(Role.id.in_(role_ids)))).all()
        )

    @staticmethod
    async def get_user_permissions(
        session: AsyncSession, user_id: uuid.UUID
    ) -> list[Permission]:
        """获取用户的完整权限对象列表（用于前端权限控制）"""
        # 获取用户角色
        user_roles = (
            await session.scalars(
                select(UserRole).where(UserRole.user_id == user_id)
            )
        ).all()

        role_ids: set[uuid.UUID] = {ur.role_id for ur in user_roles}

        # 展开角色层次结构（最多5级）
        expanded: set[uuid.UUID] = set(role_ids)
        queue = list(role_ids)
        for _ in range(5):
            if not queue:
                break
            roles = (
                await session.scalars(
                    select(Role).where(
                        Role.id.in_(queue), Role.parent_role_id.is_not(None)
                    )
                )
            ).all()
            new_parents = {
                r.parent_role_id
                for r in roles
                if r.parent_role_id and r.parent_role_id not in expanded
            }
            expanded |= new_parents
            queue = list(new_parents)

        if not expanded:
            return []

        # 获取所有角色关联的权限
        role_perms = (
            await session.scalars(
                select(RolePermission).where(
                    RolePermission.role_id.in_(expanded)
                )
            )
        ).all()

        perm_ids = {rp.permission_id for rp in role_perms}
        if not perm_ids:
            return []

        # 返回完整的 Permission 对象
        permissions = (
            await session.scalars(
                select(Permission).where(Permission.id.in_(perm_ids))
            )
        ).all()

        return list(permissions)


# ── Helpers ──────────────────────────────────────────────────────────────────

def _matches_any(perms: list[str], resource: str, action: str) -> bool:
    """Check if any permission in the list grants resource:action."""
    target = f"{resource}:{action}"
    wildcard_resource = f"{resource}:*"
    global_wildcard = "*:*"
    return any(
        p in (target, wildcard_resource, global_wildcard, f"*:{action}")
        for p in perms
    )
