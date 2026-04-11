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
    from .user import User, UserGroup

class Workspace(Base, UUIDPrimaryKeyMixin, TimestampMixin, TenantAwareMixin):
    """
    A Team/Collaboration Workspace inside a Tenant.
    Agents belong to a Workspace. 
    """
    __tablename__ = "workspaces"

    name: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    is_default: Mapped[bool] = mapped_column(Boolean, default=False)
    
    # Who created it?
    owner_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )

    # An Agent belongs to a given workspace (mapping to their agent_id JSON profile)
    # The actual config is in YAML, but the RBAC ownership is resolved here.
    
    def __repr__(self) -> str:
        return f"<Workspace id={self.id} name={self.name!r}>"

class WorkspaceMember(Base, TenantAwareMixin):
    """Many-to-many link resolving Which Users are explicitly added to Which Workspace."""
    
    __tablename__ = "workspace_members"

    workspace_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("workspaces.id", ondelete="CASCADE"),
        primary_key=True
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        primary_key=True
    )
    # Role within workspace, e.g. "viewer", "editor", "admin"
    role: Mapped[str] = mapped_column(String(50), default="viewer")
    
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

class WorkspaceAgent(Base, TenantAwareMixin):
    """Maps a physical agent folder JSON ID to a Workspace."""
    __tablename__ = "workspace_agents"

    workspace_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("workspaces.id", ondelete="CASCADE"),
        primary_key=True
    )
    agent_id: Mapped[str] = mapped_column(String(100), primary_key=True)
    # Role/Visibility required for this agent
    visibility: Mapped[str] = mapped_column(String(50), default="PRIVATE")  # PRIVATE, WORKSPACE, ENTERPRISE
