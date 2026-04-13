# -*- coding: utf-8 -*-
"""
Collaboration Workspace ORM Model.
"""
from __future__ import annotations

import uuid
from typing import TYPE_CHECKING, List, Optional
from datetime import datetime

from sqlalchemy import String, ForeignKey, DateTime, func, Boolean
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base, UUIDPrimaryKeyMixin, TimestampMixin, TenantAwareMixin

if TYPE_CHECKING:
    from .user import User

class Workspace(Base, UUIDPrimaryKeyMixin, TimestampMixin, TenantAwareMixin):
    """
    A Team/Collaboration Workspace inside a Tenant.
    Agents belong to a Workspace. 
    
    工作空间表 - 租户内的团队协作空间,Agent属于工作空间
    """
    __tablename__ = "sys_workspaces"
    __table_args__ = {"comment": "团队协作工作空间表"}

    name: Mapped[str] = mapped_column(
        String(200), nullable=False,
        comment="工作空间名称"
    )
    description: Mapped[Optional[str]] = mapped_column(
        String(500), nullable=True,
        comment="工作空间描述"
    )
    is_default: Mapped[bool] = mapped_column(
        Boolean, default=False,
        comment="是否为默认工作空间"
    )
    
    # Who created it?
    owner_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("sys_users.id", ondelete="SET NULL"),
        nullable=True,
        comment="创建者/所有者ID"
    )

    # An Agent belongs to a given workspace (mapping to their agent_id JSON profile)
    # The actual config is in YAML, but the RBAC ownership is resolved here.
    
    def __repr__(self) -> str:
        return f"<Workspace id={self.id} name={self.name!r}>"

class WorkspaceMember(Base, TenantAwareMixin):
    """Many-to-many link resolving Which Users are explicitly added to Which Workspace.
    
    工作空间成员表 - 多对多关联,记录哪些用户被明确添加到哪些工作空间
    """
    
    __tablename__ = "sys_workspace_members"
    __table_args__ = {"comment": "工作空间成员关联表"}

    workspace_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("sys_workspaces.id", ondelete="CASCADE"),
        primary_key=True,
        comment="工作空间ID"
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("sys_users.id", ondelete="CASCADE"),
        primary_key=True,
        comment="用户ID"
    )
    # Role within workspace, e.g. "viewer", "editor", "admin"
    role: Mapped[str] = mapped_column(
        String(50), default="viewer",
        comment="工作空间内角色: viewer(查看者) | editor(编辑者) | admin(管理员)"
    )
    
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False,
        comment="加入时间"
    )

class WorkspaceAgent(Base, TenantAwareMixin):
    """Maps a physical agent folder JSON ID to a Workspace.
    
    工作空间Agent表 - 将物理Agent文件夹JSON ID映射到工作空间
    """
    __tablename__ = "sys_workspace_agents"
    __table_args__ = {"comment": "工作空间Agent关联表"}

    workspace_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("sys_workspaces.id", ondelete="CASCADE"),
        primary_key=True,
        comment="工作空间ID"
    )
    agent_id: Mapped[str] = mapped_column(
        String(100), primary_key=True,
        comment="Agent ID(对应文件夹JSON配置中的ID)"
    )
    # Role/Visibility required for this agent
    visibility: Mapped[str] = mapped_column(
        String(50), default="PRIVATE",
        comment="可见性: PRIVATE(私有) | WORKSPACE(工作空间) | ENTERPRISE(企业)"
    )
