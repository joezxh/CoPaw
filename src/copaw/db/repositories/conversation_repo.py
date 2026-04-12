# -*- coding: utf-8 -*-
"""
Conversation Repository — 对话元数据访问层（占位实现）
"""
from __future__ import annotations

import uuid
from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..models.storage_meta import Conversation


class ConversationRepository:
    """对话元数据仓库（占位实现）"""

    def __init__(self, session: AsyncSession):
        self._session = session

    async def get_by_chat_id(self, chat_id: str, tenant_id: str) -> Optional[Conversation]:
        """根据chat_id获取对话"""
        result = await self._session.execute(
            select(Conversation).where(
                Conversation.chat_id == chat_id,
                Conversation.tenant_id == tenant_id,
            )
        )
        return result.scalar_one_or_none()

    async def list_by_workspace(
        self,
        workspace_id: uuid.UUID,
        tenant_id: str,
        limit: int = 50,
    ) -> list[Conversation]:
        """列出工作空间的对话"""
        result = await self._session.execute(
            select(Conversation)
            .where(
                Conversation.workspace_id == workspace_id,
                Conversation.tenant_id == tenant_id,
            )
            .order_by(Conversation.started_at.desc())
            .limit(limit)
        )
        return list(result.scalars().all())
