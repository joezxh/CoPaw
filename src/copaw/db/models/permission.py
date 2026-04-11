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
    """A discrete permission entry (resource + action)."""

    __tablename__ = "permissions"

    resource: Mapped[str] = mapped_column(
        String(200), nullable=False, index=True
    )
    # e.g. 'agent:*', 'task:read', 'user:manage'
    action: Mapped[str] = mapped_column(
        String(50), nullable=False
    )
    # e.g. 'read' | 'write' | 'execute' | 'manage' | '*'
    description: Mapped[Optional[str]] = mapped_column(
        String(500), nullable=True
    )

    # Relationships
    roles: Mapped[List["RolePermission"]] = relationship(
        "RolePermission", back_populates="permission", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:  # pragma: no cover
        return f"<Permission {self.resource}:{self.action}>"
