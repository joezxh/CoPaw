# -*- coding: utf-8 -*-
"""
Channel Message Repository — 通道消息访问层（占位实现）
"""
from __future__ import annotations

import uuid
from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..models.storage_meta import ChannelMessage


class ChannelMessageRepository:
    """通道消息仓库（占位实现）"""

    def __init__(self, session: AsyncSession):
        self._session = session

    async def get_by_message_id(
        self,
        message_id: str,
        channel_type: str,
        tenant_id: str,
    ) -> Optional[ChannelMessage]:
        """根据消息ID获取消息"""
        result = await self._session.execute(
            select(ChannelMessage).where(
                ChannelMessage.message_id == message_id,
                ChannelMessage.channel_type == channel_type,
                ChannelMessage.tenant_id == tenant_id,
            )
        )
        return result.scalar_one_or_none()

    async def list_by_workspace(
        self,
        workspace_id: uuid.UUID,
        tenant_id: str,
        limit: int = 100,
    ) -> list[ChannelMessage]:
        """列出工作空间的消息"""
        result = await self._session.execute(
            select(ChannelMessage)
            .where(
                ChannelMessage.workspace_id == workspace_id,
                ChannelMessage.tenant_id == tenant_id,
            )
            .order_by(ChannelMessage.timestamp.desc())
            .limit(limit)
        )
        return list(result.scalars().all())
