# -*- coding: utf-8 -*-
"""
User, UserGroup, UserGroupMember ORM models.
"""
from __future__ import annotations

import uuid
from datetime import datetime
from typing import TYPE_CHECKING, List, Optional

from sqlalchemy import Boolean, DateTime, ForeignKey, String, Text, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ...enterprise.crypto import EncryptedString

from .base import Base, TimestampMixin, UUIDPrimaryKeyMixin, TenantAwareMixin

if TYPE_CHECKING:
    from .role import UserRole
    from .organization import Department
    from .session import UserSession


class User(Base, UUIDPrimaryKeyMixin, TimestampMixin, TenantAwareMixin):
    """Enterprise user account."""

    __tablename__ = "users"

    username: Mapped[str] = mapped_column(
        String(100), unique=True, nullable=False, index=True
    )
    email: Mapped[Optional[str]] = mapped_column(
        String(255), unique=True, nullable=True, index=True
    )
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    password_salt: Mapped[str] = mapped_column(String(64), nullable=False)
    display_name: Mapped[Optional[str]] = mapped_column(
        String(200), nullable=True
    )
    department_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("departments.id", ondelete="SET NULL"),
        nullable=True,
    )
    status: Mapped[str] = mapped_column(
        String(20), default="active", nullable=False
    )  # active | disabled | vacation
    mfa_enabled: Mapped[bool] = mapped_column(Boolean, default=False)
    mfa_secret: Mapped[Optional[str]] = mapped_column(
        EncryptedString(), nullable=True
    )  # AES-256-GCM encrypted at rest
    last_login_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    # Relationships
    department: Mapped[Optional["Department"]] = relationship(
        "Department", back_populates="members", foreign_keys=[department_id]
    )
    roles: Mapped[List["UserRole"]] = relationship(
        "UserRole", back_populates="user", cascade="all, delete-orphan"
    )
    sessions: Mapped[List["UserSession"]] = relationship(
        "UserSession", back_populates="user", cascade="all, delete-orphan"
    )
    group_memberships: Mapped[List["UserGroupMember"]] = relationship(
        "UserGroupMember", back_populates="user", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:  # pragma: no cover
        return f"<User id={self.id} username={self.username!r}>"


class UserGroup(Base, UUIDPrimaryKeyMixin, TimestampMixin, TenantAwareMixin):
    """A named group of users (team / squad / department group)."""

    __tablename__ = "user_groups"

    name: Mapped[str] = mapped_column(
        String(200), unique=True, nullable=False
    )
    description: Mapped[Optional[str]] = mapped_column(
        String(500), nullable=True
    )
    department_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("departments.id", ondelete="SET NULL"),
        nullable=True,
    )

    # Relationships
    members: Mapped[List["UserGroupMember"]] = relationship(
        "UserGroupMember", back_populates="group", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:  # pragma: no cover
        return f"<UserGroup id={self.id} name={self.name!r}>"


class UserGroupMember(Base):
    """Association table: Many-to-many User ↔ UserGroup."""

    __tablename__ = "user_group_members"

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        primary_key=True,
    )
    group_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("user_groups.id", ondelete="CASCADE"),
        primary_key=True,
    )
    joined_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="group_memberships")
    group: Mapped["UserGroup"] = relationship("UserGroup", back_populates="members")
