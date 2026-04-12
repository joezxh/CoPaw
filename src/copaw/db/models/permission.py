# -*- coding: utf-8 -*-
"""
Permission ORM model.
"""
from __future__ import annotations

from typing import TYPE_CHECKING, List, Optional

from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import String

from .base import Base, TenantAwareMixin, UUIDPrimaryKeyMixin

if TYPE_CHECKING:
    from .role import RolePermission


class Permission(Base, UUIDPrimaryKeyMixin, TenantAwareMixin):
    """A discrete permission entry (resource + action).
    
    权限表 - 定义系统中的权限项,由资源(resource)和操作(action)组成
    """

    __tablename__ = "sys_permissions"
    __table_args__ = {"comment": "权限表"}

    resource: Mapped[str] = mapped_column(
        String(200), nullable=False, index=True,
        comment="资源标识(如: 'agent:*', 'task:read', 'user:manage')"
    )
    # e.g. 'agent:*', 'task:read', 'user:manage'
    action: Mapped[str] = mapped_column(
        String(50), nullable=False,
        comment="操作类型: 'read' | 'write' | 'execute' | 'manage' | '*'"
    )
    # e.g. 'read' | 'write' | 'execute' | 'manage' | '*'
    description: Mapped[Optional[str]] = mapped_column(
        String(500), nullable=True,
        comment="权限描述"
    )

    # Relationships
    roles: Mapped[List["RolePermission"]] = relationship(
        "RolePermission", back_populates="permission", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:  # pragma: no cover
        return f"<Permission {self.resource}:{self.action}>"
