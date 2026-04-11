# -*- coding: utf-8 -*-
"""
Declarative base and reusable column mixins for all CoPaw ORM models.
"""
from __future__ import annotations

import uuid
from datetime import datetime, timezone

from sqlalchemy import DateTime, String, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


class Base(DeclarativeBase):
    """Shared declarative base — all models inherit from this."""


class UUIDPrimaryKeyMixin:
    """UUID v4 primary key, server-default via gen_random_uuid()."""

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        server_default=func.gen_random_uuid(),
        default=uuid.uuid4,
    )


class TimestampMixin:
    """``created_at`` and ``updated_at`` auto-managed columns."""

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        default=_utcnow,
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        default=_utcnow,
        nullable=False,
    )


class SoftDeleteMixin:
    """Logical delete via ``deleted_at`` — NULL means active."""

    deleted_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        default=None,
    )

    @property
    def is_deleted(self) -> bool:
        return self.deleted_at is not None

class TenantAwareMixin:
    """Multi-tenant isolation constraint. Every table should inherit this to ensure records belong to a specific Tenant, avoiding cross-organization leakage."""
    
    tenant_id: Mapped[str | None] = mapped_column(
        String(36), 
        index=True, 
        nullable=True, 
        default="default-tenant",
        server_default="default-tenant"
    )

