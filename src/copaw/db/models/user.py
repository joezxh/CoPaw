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
    """Enterprise user account.
    
    企业用户账户表 - 存储系统中的所有用户基本信息、认证凭据和状态
    """

    __tablename__ = "sys_users"
    __table_args__ = {"comment": "企业用户账户表"}

    username: Mapped[str] = mapped_column(
        String(100), unique=True, nullable=False, index=True,
        comment="用户名(登录账号)"
    )
    email: Mapped[Optional[str]] = mapped_column(
        String(255), unique=True, nullable=True, index=True,
        comment="电子邮箱地址"
    )
    password_hash: Mapped[str] = mapped_column(
        String(255), nullable=False,
        comment="密码哈希值(加密存储)"
    )
    password_salt: Mapped[str] = mapped_column(
        String(64), nullable=False,
        comment="密码盐值(用于增强密码安全性)"
    )
    display_name: Mapped[Optional[str]] = mapped_column(
        String(200), nullable=True,
        comment="显示名称(昵称)"
    )
    department_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("sys_departments.id", ondelete="SET NULL"),
        nullable=True,
        comment="所属部门ID"
    )
    status: Mapped[str] = mapped_column(
        String(20), default="active", nullable=False,
        comment="账户状态: active(活跃) | disabled(禁用) | vacation(休假)"
    )
    mfa_enabled: Mapped[bool] = mapped_column(
        Boolean, default=False,
        comment="是否启用多因素认证(MFA)"
    )
    mfa_secret: Mapped[Optional[str]] = mapped_column(
        EncryptedString(), nullable=True,
        comment="MFA密钥(AES-256-GCM加密存储)"
    )
    last_login_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True,
        comment="最后登录时间"
    )

    # Relationships
    department: Mapped[Optional["Department"]] = relationship(
        "Department", back_populates="members", foreign_keys=[department_id]
    )
    roles: Mapped[List["UserRole"]] = relationship(
        "UserRole", back_populates="user", cascade="all, delete-orphan",
        foreign_keys="UserRole.user_id"
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
    """A named group of users (team / squad / department group).
    
    用户组表 - 用于管理用户分组,支持团队、小队或部门级别的分组
    """

    __tablename__ = "sys_user_groups"
    __table_args__ = {"comment": "用户组表"}

    name: Mapped[str] = mapped_column(
        String(200), unique=True, nullable=False,
        comment="用户组名称"
    )
    description: Mapped[Optional[str]] = mapped_column(
        String(500), nullable=True,
        comment="用户组描述"
    )
    department_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("sys_departments.id", ondelete="SET NULL"),
        nullable=True,
        comment="所属部门ID"
    )

    # Relationships
    members: Mapped[List["UserGroupMember"]] = relationship(
        "UserGroupMember", back_populates="group", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:  # pragma: no cover
        return f"<UserGroup id={self.id} name={self.name!r}>"


class UserGroupMember(Base):
    """Association table: Many-to-many User ↔ UserGroup.
    
    用户组成员关联表 - 实现用户与用户组的多对多关系
    """

    __tablename__ = "sys_user_group_members"
    __table_args__ = {"comment": "用户组成员关联表"}

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("sys_users.id", ondelete="CASCADE"),
        primary_key=True,
        comment="用户ID"
    )
    group_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("sys_user_groups.id", ondelete="CASCADE"),
        primary_key=True,
        comment="用户组ID"
    )
    joined_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(),
        comment="加入时间"
    )

    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="group_memberships")
    group: Mapped["UserGroup"] = relationship("UserGroup", back_populates="members")
