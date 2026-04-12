# -*- coding: utf-8 -*-
"""
Channel Message Middleware — 通道消息中间件

拦截通道消息，自动写入PostgreSQL实现审计和追溯。
"""
from __future__ import annotations

import logging
from datetime import datetime
from typing import Optional

from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)


class ChannelMessageMiddleware:
    """通道消息中间件"""

    def __init__(self, db_session: AsyncSession, tenant_id: str):
        self._db_session = db_session
        self._tenant_id = tenant_id

    async def on_message_received(
        self,
        channel_type: str,
        message_id: str,
        content: str,
        sender_id: Optional[str] = None,
        sender_name: Optional[str] = None,
        workspace_id: Optional[str] = None,
        agent_id: Optional[str] = None,
    ) -> None:
        """消息接收时触发"""
        try:
            from copaw.db.models.storage_meta import ChannelMessage

            message = ChannelMessage(
                tenant_id=self._tenant_id,
                channel_type=channel_type,
                message_id=message_id,
                direction="inbound",
                content=content,
                sender_id=sender_id,
                sender_name=sender_name,
                is_bot=False,
                processing_status="received",
                timestamp=datetime.utcnow(),
            )

            if workspace_id:
                from uuid import UUID
                message.workspace_id = UUID(workspace_id)

            self._db_session.add(message)
            await self._db_session.commit()

            logger.debug(
                f"记录通道消息: {channel_type}/{message_id} "
                f"from {sender_name or sender_id}"
            )

        except Exception as e:
            logger.error(f"记录通道消息失败: {e}")
            # 不抛出异常，避免影响消息处理流程

    async def on_message_sent(
        self,
        channel_type: str,
        message_id: str,
        content: str,
        sender_id: Optional[str] = None,
        workspace_id: Optional[str] = None,
        agent_id: Optional[str] = None,
        reply_to_id: Optional[str] = None,
    ) -> None:
        """消息发送时触发"""
        try:
            from copaw.db.models.storage_meta import ChannelMessage

            message = ChannelMessage(
                tenant_id=self._tenant_id,
                channel_type=channel_type,
                message_id=message_id,
                direction="outbound",
                content=content,
                sender_id=sender_id,
                is_bot=True,
                processing_status="sent",
                timestamp=datetime.utcnow(),
            )

            if workspace_id:
                from uuid import UUID
                message.workspace_id = UUID(workspace_id)

            if reply_to_id:
                message.reply_to_id = reply_to_id

            self._db_session.add(message)
            await self._db_session.commit()

            logger.debug(f"记录发送消息: {channel_type}/{message_id}")

        except Exception as e:
            logger.error(f"记录发送消息失败: {e}")

    async def mark_processed(
        self,
        message_id: str,
        channel_type: str,
        status: str = "processed",
    ) -> None:
        """标记消息已处理"""
        try:
            from sqlalchemy import update
            from copaw.db.models.storage_meta import ChannelMessage

            result = await self._db_session.execute(
                update(ChannelMessage)
                .where(
                    ChannelMessage.message_id == message_id,
                    ChannelMessage.channel_type == channel_type,
                    ChannelMessage.tenant_id == self._tenant_id,
                )
                .values(
                    processing_status=status,
                    processed_at=datetime.utcnow(),
                )
            )

            await self._db_session.commit()

            if result.rowcount == 0:
                logger.warning(f"未找到消息: {channel_type}/{message_id}")

        except Exception as e:
            logger.error(f"标记消息处理状态失败: {e}")


async def create_channel_middleware(
    db_session: AsyncSession,
    tenant_id: str = "default-tenant",
) -> ChannelMessageMiddleware:
    """创建通道消息中间件工厂函数"""
    return ChannelMessageMiddleware(db_session, tenant_id)
