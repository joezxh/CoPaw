# -*- coding: utf-8 -*-
"""
User ORM model.
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

    def __repr__(self) -> str:  # pragma: no cover
        return f"<User id={self.id} username={self.username!r}>"

