# -*- coding: utf-8 -*-
"""
UserSession and RefreshToken ORM models (Redis-backed sessions with PG audit).
"""
from __future__ import annotations

import uuid
from datetime import datetime
from typing import TYPE_CHECKING, Optional

from sqlalchemy import Boolean, DateTime, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base, TenantAwareMixin, UUIDPrimaryKeyMixin

if TYPE_CHECKING:
    from .user import User


class UserSession(Base, UUIDPrimaryKeyMixin, TenantAwareMixin):
    """Active user session record (mirrored in Redis for fast lookup).
    
    用户会话表 - 记录活跃的用户会话,Redis中也有镜像用于快速查找
    """

    __tablename__ = "sys_user_sessions"
    __table_args__ = {"comment": "用户会话表"}

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("sys_users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="用户ID"
    )
    access_token_jti: Mapped[str] = mapped_column(
        String(64), unique=True, nullable=False, index=True,
        comment="访问令牌的JWT ID(用于撤销)"
    )
    ip_address: Mapped[Optional[str]] = mapped_column(
        String(45), nullable=True,
        comment="客户端IP地址"
    )
    user_agent: Mapped[Optional[str]] = mapped_column(
        String(500), nullable=True,
        comment="客户端User-Agent信息"
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False,
        comment="会话创建时间"
    )
    expires_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, index=True,
        comment="会话过期时间"
    )
    revoked: Mapped[bool] = mapped_column(
        Boolean, default=False,
        comment="是否已撤销"
    )
    revoked_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True,
        comment="撤销时间"
    )

    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="sessions")
    refresh_tokens: Mapped[list["RefreshToken"]] = relationship(
        "RefreshToken", back_populates="session", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:  # pragma: no cover
        return f"<UserSession user_id={self.user_id} jti={self.access_token_jti!r}>"


class RefreshToken(Base, UUIDPrimaryKeyMixin, TenantAwareMixin):
    """Refresh token record — one-time-use, stored hashed.
    
    刷新令牌表 - 存储刷新令牌(一次性使用,哈希存储)
    """

    __tablename__ = "sys_refresh_tokens"
    __table_args__ = {"comment": "刷新令牌表"}

    session_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("sys_user_sessions.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="会话ID"
    )
    token_hash: Mapped[str] = mapped_column(
        String(128), nullable=False, unique=True,
        comment="令牌哈希值"
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False,
        comment="创建时间"
    )
    expires_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False,
        comment="过期时间"
    )
    used: Mapped[bool] = mapped_column(
        Boolean, default=False,
        comment="是否已使用"
    )
    used_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True,
        comment="使用时间"
    )

    session: Mapped["UserSession"] = relationship(
        "UserSession", back_populates="refresh_tokens"
    )
