# -*- coding: utf-8 -*-
"""
Role, RolePermission, UserRole ORM models.
Supports hierarchical role inheritance (up to 5 levels).
"""
from __future__ import annotations

import uuid
from datetime import datetime
from typing import TYPE_CHECKING, List, Optional

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base, TenantAwareMixin, TimestampMixin, UUIDPrimaryKeyMixin

if TYPE_CHECKING:
    from .permission import Permission
    from .user import User
    from .organization import Department


class Role(Base, UUIDPrimaryKeyMixin, TimestampMixin, TenantAwareMixin):
    """Enterprise role (supports 5-level hierarchy via parent_role_id).
    
    角色表 - 企业角色管理,支持5级层次结构(通过parent_role_id实现)
    """

    __tablename__ = "sys_roles"
    __table_args__ = {"comment": "角色表"}

    name: Mapped[str] = mapped_column(
        String(100), unique=True, nullable=False, index=True,
        comment="角色名称"
    )
    description: Mapped[Optional[str]] = mapped_column(
        String(500), nullable=True,
        comment="角色描述"
    )
    parent_role_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("sys_roles.id", ondelete="SET NULL"),
        nullable=True,
        comment="父角色ID(用于实现角色层次结构)"
    )
    level: Mapped[int] = mapped_column(
        Integer, default=0,
        comment="角色层级(0-5级)"
    )
    department_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("sys_departments.id", ondelete="SET NULL"),
        nullable=True,
        comment="所属部门ID"
    )
    is_system_role: Mapped[bool] = mapped_column(
        Boolean, default=False,
        comment="是否为系统角色(系统角色不可删除)"
    )

    # Relationships
    parent: Mapped[Optional["Role"]] = relationship(
        "Role", remote_side="Role.id", back_populates="children"
    )
    children: Mapped[List["Role"]] = relationship(
        "Role", back_populates="parent"
    )
    permissions: Mapped[List["RolePermission"]] = relationship(
        "RolePermission", back_populates="role", cascade="all, delete-orphan"
    )
    user_roles: Mapped[List["UserRole"]] = relationship(
        "UserRole", back_populates="role", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:  # pragma: no cover
        return f"<Role id={self.id} name={self.name!r} level={self.level}>"


class RolePermission(Base, TenantAwareMixin):
    """Association table: Role ↔ Permission.
    
    角色权限关联表 - 实现角色与权限的多对多关系
    """

    __tablename__ = "sys_role_permissions"
    __table_args__ = {"comment": "角色权限关联表"}

    role_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("sys_roles.id", ondelete="CASCADE"),
        primary_key=True,
        comment="角色ID"
    )
    permission_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("sys_permissions.id", ondelete="CASCADE"),
        primary_key=True,
        comment="权限ID"
    )
    granted_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(),
        comment="授权时间"
    )

    # Relationships
    role: Mapped["Role"] = relationship("Role", back_populates="permissions")
    permission: Mapped["Permission"] = relationship(
        "Permission", back_populates="roles"
    )


class UserRole(Base, TenantAwareMixin):
    """Association table: User ↔ Role (with assignment audit trail).
    
    用户角色关联表 - 实现用户与角色的多对多关系,包含分配审计跟踪
    """

    __tablename__ = "sys_user_roles"
    __table_args__ = {"comment": "用户角色关联表"}

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("sys_users.id", ondelete="CASCADE"),
        primary_key=True,
        comment="用户ID"
    )
    role_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("sys_roles.id", ondelete="CASCADE"),
        primary_key=True,
        comment="角色ID"
    )
    assigned_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(),
        comment="分配时间"
    )
    assigned_by: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("sys_users.id", ondelete="SET NULL"),
        nullable=True,
        comment="分配者ID(执行角色分配的管理员)"
    )

    # Relationships
    user: Mapped["User"] = relationship(
        "User", back_populates="roles", foreign_keys=[user_id]
    )
    role: Mapped["Role"] = relationship("Role", back_populates="user_roles")
