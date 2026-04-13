# -*- coding: utf-8 -*-
"""
Permission ORM model.
"""
from __future__ import annotations

import uuid
from typing import TYPE_CHECKING, List, Optional

from sqlalchemy import Boolean, ForeignKey, Integer, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base, TenantAwareMixin, UUIDPrimaryKeyMixin

if TYPE_CHECKING:
    from .role import RolePermission


class Permission(Base, UUIDPrimaryKeyMixin, TenantAwareMixin):
    """A discrete permission entry (resource + action).
    
    权限表 - 定义系统中的权限项,支持细粒度权限控制
    权限码格式: 模块:资源:操作 (如 'agent:config:read')
    """

    __tablename__ = "sys_permissions"
    __table_args__ = (
        {"comment": "权限表 - 支持细粒度权限控制"},
    )

    # ========== 原有字段 ==========
    resource: Mapped[str] = mapped_column(
        String(200), nullable=False, index=True,
        comment="资源标识(如: 'agent', 'skill', 'model')"
    )
    action: Mapped[str] = mapped_column(
        String(50), nullable=False,
        comment="操作类型: 'read' | 'write' | 'execute' | 'manage' | '*'"
    )
    description: Mapped[Optional[str]] = mapped_column(
        String(500), nullable=True,
        comment="权限描述"
    )

    # ========== 新增字段（参考 risk_control 设计）==========
    permission_code: Mapped[str] = mapped_column(
        String(100), unique=True, nullable=False, index=True,
        comment="权限码(格式: 模块:资源:操作, 如 'agent:config:read')"
    )
    resource_path: Mapped[Optional[str]] = mapped_column(
        String(200), nullable=True,
        comment="前端路由路径(如: '/agent-config')"
    )
    permission_type: Mapped[str] = mapped_column(
        String(20), default="menu", nullable=False,
        comment="权限类型: menu(菜单) | api(接口) | button(按钮) | data(数据)"
    )
    parent_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("sys_permissions.id", ondelete="SET NULL"),
        nullable=True,
        comment="父权限ID(支持权限层次结构)"
    )
    sort_order: Mapped[int] = mapped_column(
        Integer, default=0,
        comment="排序顺序"
    )
    icon: Mapped[Optional[str]] = mapped_column(
        String(100), nullable=True,
        comment="图标标识(前端使用)"
    )
    is_visible: Mapped[bool] = mapped_column(
        Boolean, default=True, nullable=False,
        comment="是否在菜单中可见"
    )
    
    # 审计字段
    created_by: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("sys_users.id", ondelete="SET NULL"),
        nullable=True,
        comment="创建者ID"
    )

    # ========== 关系 ==========
    roles: Mapped[List["RolePermission"]] = relationship(
        "RolePermission", back_populates="permission", cascade="all, delete-orphan"
    )
    parent: Mapped[Optional["Permission"]] = relationship(
        "Permission", remote_side="Permission.id", back_populates="children"
    )
    children: Mapped[List["Permission"]] = relationship(
        "Permission", back_populates="parent"
    )

    def __repr__(self) -> str:  # pragma: no cover
        return f"<Permission {self.permission_code}>"
