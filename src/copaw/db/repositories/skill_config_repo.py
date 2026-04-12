# -*- coding: utf-8 -*-
"""
Skill Config Repository — Skill配置元数据访问层
"""
from __future__ import annotations

import uuid
from typing import Optional

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from ..models.storage_meta import SkillConfig


class SkillConfigRepository:
    """Skill配置元数据仓库"""

    def __init__(self, session: AsyncSession):
        self._session = session

    async def get_by_id(self, skill_id: uuid.UUID, tenant_id: str) -> Optional[SkillConfig]:
        result = await self._session.execute(
            select(SkillConfig).where(
                SkillConfig.id == skill_id,
                SkillConfig.tenant_id == tenant_id,
            )
        )
        return result.scalar_one_or_none()

    async def list_by_workspace(
        self,
        workspace_id: uuid.UUID,
        tenant_id: str,
        enabled: Optional[bool] = None,
    ) -> list[SkillConfig]:
        query = select(SkillConfig).where(
            SkillConfig.workspace_id == workspace_id,
            SkillConfig.tenant_id == tenant_id,
        )
        if enabled is not None:
            query = query.where(SkillConfig.enabled == enabled)

        result = await self._session.execute(query)
        return list(result.scalars().all())

    async def create(self, skill: SkillConfig) -> SkillConfig:
        self._session.add(skill)
        await self._session.flush()
        await self._session.refresh(skill)
        return skill

    async def update(self, skill_id: uuid.UUID, tenant_id: str, **kwargs) -> bool:
        result = await self._session.execute(
            update(SkillConfig)
            .where(
                SkillConfig.id == skill_id,
                SkillConfig.tenant_id == tenant_id,
            )
            .values(**kwargs)
        )
        await self._session.commit()
        return result.rowcount > 0

    async def list_by_source(self, source: str, tenant_id: str) -> list[SkillConfig]:
        result = await self._session.execute(
            select(SkillConfig).where(
                SkillConfig.source == source,
                SkillConfig.tenant_id == tenant_id,
            )
        )
        return list(result.scalars().all())
