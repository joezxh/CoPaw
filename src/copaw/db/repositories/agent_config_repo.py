# -*- coding: utf-8 -*-
"""
Agent Config Repository — Agent配置元数据访问层
"""
from __future__ import annotations

import uuid
from typing import Optional

from sqlalchemy import select, update, delete
from sqlalchemy.ext.asyncio import AsyncSession

from ..models.storage_meta import AgentConfig


class AgentConfigRepository:
    """Agent配置元数据仓库"""

    def __init__(self, session: AsyncSession):
        self._session = session

    async def get_by_id(self, config_id: uuid.UUID, tenant_id: str) -> Optional[AgentConfig]:
        """根据ID获取配置"""
        result = await self._session.execute(
            select(AgentConfig).where(
                AgentConfig.id == config_id,
                AgentConfig.tenant_id == tenant_id,
            )
        )
        return result.scalar_one_or_none()

    async def get_by_agent_id(self, agent_id: str, tenant_id: str) -> Optional[AgentConfig]:
        """根据agent_id获取配置"""
        result = await self._session.execute(
            select(AgentConfig).where(
                AgentConfig.agent_id == agent_id,
                AgentConfig.tenant_id == tenant_id,
            )
        )
        return result.scalar_one_or_none()

    async def list_by_workspace(
        self,
        workspace_id: uuid.UUID,
        tenant_id: str,
        status: Optional[str] = None,
    ) -> list[AgentConfig]:
        """列出工作空间的所有Agent配置"""
        query = select(AgentConfig).where(
            AgentConfig.workspace_id == workspace_id,
            AgentConfig.tenant_id == tenant_id,
        )
        if status:
            query = query.where(AgentConfig.status == status)

        result = await self._session.execute(query)
        return list(result.scalars().all())

    async def create(self, config: AgentConfig) -> AgentConfig:
        """创建配置"""
        self._session.add(config)
        await self._session.flush()
        await self._session.refresh(config)
        return config

    async def update(self, config_id: uuid.UUID, tenant_id: str, **kwargs) -> bool:
        """更新配置"""
        result = await self._session.execute(
            update(AgentConfig)
            .where(
                AgentConfig.id == config_id,
                AgentConfig.tenant_id == tenant_id,
            )
            .values(**kwargs)
        )
        await self._session.commit()
        return result.rowcount > 0

    async def delete(self, config_id: uuid.UUID, tenant_id: str) -> bool:
        """删除配置"""
        result = await self._session.execute(
            delete(AgentConfig).where(
                AgentConfig.id == config_id,
                AgentConfig.tenant_id == tenant_id,
            )
        )
        await self._session.commit()
        return result.rowcount > 0

    async def search_by_model(
        self,
        model_provider: str,
        tenant_id: str,
        limit: int = 20,
    ) -> list[AgentConfig]:
        """按模型提供商搜索"""
        result = await self._session.execute(
            select(AgentConfig)
            .where(
                AgentConfig.model_provider == model_provider,
                AgentConfig.tenant_id == tenant_id,
            )
            .limit(limit)
        )
        return list(result.scalars().all())
