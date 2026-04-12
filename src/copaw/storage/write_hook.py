# -*- coding: utf-8 -*-
"""
Storage Write Hook — 存储写入钩子

在文件上传到对象存储后自动触发元数据双写：
1. 创建 StorageObject 记录（通用索引）
2. 根据 category 调用 MetadataExtractor 对应方法
3. 插入/更新业务元数据表（upsert by storage_key）
4. 通过 content_hash 检测变更，仅更新变化的记录
"""
from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Optional

from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession

from ..db.models.storage_meta import (
    AgentConfig,
    ChannelMessage,
    Conversation,
    ConversationMessage,
    MemoryDocument,
    SkillConfig,
    StorageObject,
    TokenUsageStat,
)
from .metadata_extractor import MetadataExtractor

if TYPE_CHECKING:
    from .base import ObjectStorageProvider

logger = logging.getLogger(__name__)


async def on_file_uploaded(
    key: str,
    data: bytes,
    metadata: dict,
    provider: ObjectStorageProvider,
    db_session: AsyncSession,
    tenant_id: str,
    workspace_id: Optional[str] = None,
    user_id: Optional[str] = None,
) -> None:
    """文件上传后的元数据双写钩子

    Args:
        key: 对象存储键
        data: 文件内容（字节）
        metadata: 文件元数据
        provider: 存储提供者
        db_session: 数据库会话
        tenant_id: 租户 ID
        workspace_id: 工作空间 ID
        user_id: 用户 ID
    """
    try:
        # 1. 计算内容哈希
        content_hash = MetadataExtractor.compute_content_hash(data)

        # 2. 提取文件类别
        category = MetadataExtractor.extract_category(key)

        # 3. 提取搜索文本
        search_text = MetadataExtractor.extract_search_text(key, data)

        # 4. 创建或更新 StorageObject（通用索引）
        existing = await db_session.execute(
            select(StorageObject).where(
                StorageObject.object_key == key,
                StorageObject.deleted_at.is_(None),
            )
        )
        storage_obj = existing.scalar_one_or_none()

        if storage_obj:
            # 检查内容是否变更
            if storage_obj.content_hash == content_hash:
                logger.debug("File unchanged, skipping metadata update: %s", key)
                return

            # 更新现有记录
            storage_obj.content_hash = content_hash
            storage_obj.search_text = search_text[:10000] if search_text else None
            storage_obj.file_size = len(data)
            storage_obj.is_latest = True
        else:
            # 创建新记录
            from pathlib import PurePosixPath
            path = PurePosixPath(key)

            storage_obj = StorageObject(
                tenant_id=tenant_id,
                object_key=key,
                file_name=path.name,
                file_ext=path.suffix.lower(),
                content_type=metadata.get("content_type", "application/octet-stream"),
                file_size=len(data),
                category=category,
                search_text=search_text[:10000] if search_text else None,
                content_hash=content_hash,
                workspace_id=workspace_id,
                user_id=user_id,
            )
            db_session.add(storage_obj)

        await db_session.flush()

        # 5. 根据类别抽取业务元数据
        await _extract_business_metadata(
            key=key,
            data=data,
            category=category,
            content_hash=content_hash,
            db_session=db_session,
            tenant_id=tenant_id,
            workspace_id=workspace_id,
            user_id=user_id,
            storage_key=key,
        )

        await db_session.commit()
        logger.info("Metadata extracted and saved for: %s", key)

    except Exception as e:
        logger.error("Failed to extract metadata for %s: %s", key, e, exc_info=True)
        # 不抛出异常，避免影响文件上传
        await db_session.rollback()


async def _extract_business_metadata(
    key: str,
    data: bytes,
    category: str,
    content_hash: str,
    db_session: AsyncSession,
    tenant_id: str,
    workspace_id: Optional[str],
    user_id: Optional[str],
    storage_key: str,
) -> None:
    """根据文件类别抽取业务元数据"""
    import json

    # 仅处理 JSON 和 Markdown 文件
    if not (key.endswith(".json") or key.endswith(".md")):
        return

    try:
        if key.endswith(".json"):
            file_data = json.loads(data)
        else:
            file_data = None
    except Exception as e:
        logger.warning("Failed to parse file %s: %s", key, e)
        return

    # 根据文件名和类别路由到不同的抽取逻辑
    filename = key.split("/")[-1]

    if filename == "agent.json" and file_data:
        await _extract_agent_config(
            file_data, content_hash, db_session, tenant_id, workspace_id, user_id, storage_key
        )
    elif filename == "skill.json" and file_data:
        await _extract_skill_config(
            file_data, content_hash, db_session, tenant_id, workspace_id, user_id, storage_key
        )
    elif filename == "chats.json" and file_data:
        await _extract_conversations(
            file_data, content_hash, db_session, tenant_id, workspace_id, user_id, storage_key
        )
    elif filename == "token_usage.json" and file_data:
        await _extract_token_usage(
            file_data, content_hash, db_session, tenant_id, workspace_id, user_id, storage_key
        )
    elif filename.endswith(".md") and data:
        await _extract_memory_document(
            data.decode("utf-8", errors="replace"),
            filename,
            content_hash,
            db_session,
            tenant_id,
            workspace_id,
            user_id,
            storage_key,
        )


async def _extract_agent_config(
    data: dict,
    content_hash: str,
    db_session: AsyncSession,
    tenant_id: str,
    workspace_id: Optional[str],
    user_id: Optional[str],
    storage_key: str,
) -> None:
    """抽取 Agent 配置元数据"""
    extracted = MetadataExtractor.extract_agent_config(data)
    agent_id = data.get("id", "")

    # Upsert by agent_id
    existing = await db_session.execute(
        select(AgentConfig).where(
            AgentConfig.tenant_id == tenant_id,
            AgentConfig.agent_id == agent_id,
        )
    )
    config = existing.scalar_one_or_none()

    if config:
        if config.content_hash == content_hash:
            return
        for k, v in extracted.items():
            setattr(config, k, v)
        config.content_hash = content_hash
        config.storage_key = storage_key
    else:
        config = AgentConfig(
            tenant_id=tenant_id,
            workspace_id=workspace_id,
            user_id=user_id,
            agent_id=agent_id,
            storage_key=storage_key,
            content_hash=content_hash,
            **extracted,
        )
        db_session.add(config)


async def _extract_skill_config(
    data: dict,
    content_hash: str,
    db_session: AsyncSession,
    tenant_id: str,
    workspace_id: Optional[str],
    user_id: Optional[str],
    storage_key: str,
) -> None:
    """抽取 Skill 配置元数据"""
    extracted = MetadataExtractor.extract_skill_config(data)
    skill_name = extracted.get("skill_name", "")

    existing = await db_session.execute(
        select(SkillConfig).where(
            SkillConfig.tenant_id == tenant_id,
            SkillConfig.skill_name == skill_name,
        )
    )
    config = existing.scalar_one_or_none()

    if config:
        if config.content_hash == content_hash:
            return
        for k, v in extracted.items():
            setattr(config, k, v)
        config.content_hash = content_hash
        config.storage_key = storage_key
    else:
        config = SkillConfig(
            tenant_id=tenant_id,
            workspace_id=workspace_id,
            user_id=user_id,
            storage_key=storage_key,
            content_hash=content_hash,
            **extracted,
        )
        db_session.add(config)


async def _extract_conversations(
    data: dict,
    content_hash: str,
    db_session: AsyncSession,
    tenant_id: str,
    workspace_id: Optional[str],
    user_id: Optional[str],
    storage_key: str,
) -> None:
    """抽取对话元数据"""
    conversations = MetadataExtractor.extract_conversations(data)

    for conv_data in conversations:
        chat_id = conv_data.pop("chat_id")
        messages = conv_data.pop("messages", [])

        # Upsert conversation
        existing = await db_session.execute(
            select(Conversation).where(
                Conversation.tenant_id == tenant_id,
                Conversation.chat_id == chat_id,
            )
        )
        conv = existing.scalar_one_or_none()

        if conv:
            if conv.content_hash == content_hash:
                continue
            conv.message_count = conv_data["message_count"]
            conv.content_hash = content_hash
            conv.storage_key = storage_key
        else:
            conv = Conversation(
                tenant_id=tenant_id,
                workspace_id=workspace_id,
                user_id=user_id,
                chat_id=chat_id,
                storage_key=storage_key,
                content_hash=content_hash,
                **conv_data,
            )
            db_session.add(conv)
            await db_session.flush()

        # Upsert messages
        for msg_data in messages:
            msg = ConversationMessage(
                tenant_id=tenant_id,
                conversation_id=conv.id,
                **msg_data,
            )
            db_session.add(msg)


async def _extract_token_usage(
    data: dict,
    content_hash: str,
    db_session: AsyncSession,
    tenant_id: str,
    workspace_id: Optional[str],
    user_id: Optional[str],
    storage_key: str,
) -> None:
    """抽取 Token 使用统计"""
    stats = MetadataExtractor.extract_token_usage(data)

    for stat_data in stats:
        stat_date = stat_data.pop("stat_date")
        model_provider = stat_data.get("model_provider")
        model_name = stat_data.get("model_name")

        # Upsert by unique constraint
        existing = await db_session.execute(
            select(TokenUsageStat).where(
                TokenUsageStat.tenant_id == tenant_id,
                TokenUsageStat.workspace_id == workspace_id,
                TokenUsageStat.stat_date == stat_date,
                TokenUsageStat.model_provider == model_provider,
                TokenUsageStat.model_name == model_name,
            )
        )
        stat = existing.scalar_one_or_none()

        if stat:
            for k, v in stat_data.items():
                setattr(stat, k, v)
        else:
            stat = TokenUsageStat(
                tenant_id=tenant_id,
                workspace_id=workspace_id,
                user_id=user_id,
                stat_date=stat_date,
                **stat_data,
            )
            db_session.add(stat)


async def _extract_memory_document(
    content: str,
    filename: str,
    content_hash: str,
    db_session: AsyncSession,
    tenant_id: str,
    workspace_id: Optional[str],
    user_id: Optional[str],
    storage_key: str,
) -> None:
    """抽取记忆文档元数据"""
    # 确定文档类型
    if filename.startswith("20") and filename.endswith(".md"):
        doc_type = "memory_daily"
    elif filename == "MEMORY.md":
        doc_type = "long_term"
    elif filename == "AGENTS.md":
        doc_type = "personality"
    elif filename == "SOUL.md":
        doc_type = "soul"
    elif filename == "PROFILE.md":
        doc_type = "profile"
    else:
        doc_type = "other"

    extracted = MetadataExtractor.extract_memory_document(content, doc_type)

    existing = await db_session.execute(
        select(MemoryDocument).where(
            MemoryDocument.tenant_id == tenant_id,
            MemoryDocument.storage_key == storage_key,
        )
    )
    doc = existing.scalar_one_or_none()

    if doc:
        if doc.content_hash == content_hash:
            return
        for k, v in extracted.items():
            setattr(doc, k, v)
        doc.content_hash = content_hash
        doc.file_size = len(content.encode("utf-8"))
    else:
        doc = MemoryDocument(
            tenant_id=tenant_id,
            workspace_id=workspace_id,
            user_id=user_id,
            storage_key=storage_key,
            content_hash=content_hash,
            file_size=len(content.encode("utf-8")),
            **extracted,
        )
        db_session.add(doc)
