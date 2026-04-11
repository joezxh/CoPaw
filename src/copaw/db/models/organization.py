# -*- coding: utf-8 -*-
"""
Department ORM model (PostgreSQL-based org hierarchy using parent_id).
No Neo4j dependency — hierarchy is traversed via recursive CTEs.
"""
from __future__ import annotations

import uuid
from typing import TYPE_CHECKING, List, Optional

from sqlalchemy import ForeignKey, Integer, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base, TenantAwareMixin, TimestampMixin, UUIDPrimaryKeyMixin

if TYPE_CHECKING:
    from .user import User


class Department(Base, UUIDPrimaryKeyMixin, TimestampMixin, TenantAwareMixin):
    """Hierarchical department/organisation unit (adjacency list pattern).

    Use a recursive CTE to traverse full ancestor/descendant chains::

        WITH RECURSIVE tree AS (
            SELECT id, parent_id, name, 0 AS depth
            FROM departments WHERE id = :root_id
          UNION ALL
            SELECT d.id, d.parent_id, d.name, t.depth + 1
            FROM departments d JOIN tree t ON d.parent_id = t.id
        )
        SELECT * FROM tree;
    """

    __tablename__ = "departments"

    name: Mapped[str] = mapped_column(
        String(200), nullable=False, index=True
    )
    parent_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("departments.id", ondelete="SET NULL"),
        nullable=True,
    )
    manager_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )
    level: Mapped[int] = mapped_column(Integer, default=0)
    description: Mapped[Optional[str]] = mapped_column(
        String(500), nullable=True
    )

    # Self-referential relationship
    parent: Mapped[Optional["Department"]] = relationship(
        "Department", remote_side="Department.id", back_populates="children"
    )
    children: Mapped[List["Department"]] = relationship(
        "Department", back_populates="parent"
    )

    # Members of this department
    members: Mapped[List["User"]] = relationship(
        "User",
        back_populates="department",
        foreign_keys="User.department_id",
    )
    manager: Mapped[Optional["User"]] = relationship(
        "User", foreign_keys=[manager_id]
    )

    def __repr__(self) -> str:  # pragma: no cover
        return (
            f"<Department id={self.id} name={self.name!r} level={self.level}>"
        )
