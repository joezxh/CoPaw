# -*- coding: utf-8 -*-
"""
ReMe PostgreSQL Backend — 基于 PostgreSQL + pgvector 的记忆后端

企业版专用，提供：
- 向量相似度搜索（余弦距离）
- 记忆 CRUD 操作
- 记忆归档和清理
"""
from __future__ import annotations

import logging
from datetime import datetime
from typing import Any, Optional

from sqlalchemy import select, update, delete, desc, text
from sqlalchemy.ext.asyncio import AsyncSession

from ...db.models.memory import AIMemory

logger = logging.getLogger(__name__)


class ReMePostgresBackend:
    """PostgreSQL + pgvector 记忆后端"""

    def __init__(
        self,
        session_factory,
        workspace_id: str,
        tenant_id: str,
        agent_id: str,
    ):
        """初始化

        Args:
            session_factory: SQLAlchemy async session factory
            workspace_id: 工作空间 ID
            tenant_id: 租户 ID
            agent_id: Agent ID
        """
        self._session_factory = session_factory
        self._workspace_id = workspace_id
        self._tenant_id = tenant_id
        self._agent_id = agent_id

    async def add_memory(
        self,
        content: str,
        embedding: list[float],
        metadata: Optional[dict] = None,
        category: Optional[str] = None,
        importance: float = 0.5,
        tags: Optional[list[str]] = None,
    ) -> str:
        """添加记忆

        Args:
            content: 记忆内容
            embedding: 向量嵌入（list of float）
            metadata: 元数据
            category: 分类
            importance: 重要性评分 [0, 1]
            tags: 标签列表

        Returns:
            记忆 ID (UUID string)
        """
        import hashlib
        import json

        content_hash = hashlib.sha256(content.encode()).hexdigest()

        async with self._session_factory() as session:
            memory = AIMemory(
                tenant_id=self._tenant_id,
                workspace_id=self._workspace_id,
                agent_id=self._agent_id,
                content=content,
                content_hash=content_hash,
                embedding=json.dumps(embedding),  # 存储为 JSON 字符串
                embedding_model="text-embedding-ada-002",  # 可配置
                category=category,
                importance=importance,
                metadata=metadata or {},
                tags=tags or [],
            )
            session.add(memory)
            await session.commit()
            await session.refresh(memory)

            logger.info("Added memory: id=%s", memory.id)
            return str(memory.id)

    async def search_memories(
        self,
        query_embedding: list[float],
        top_k: int = 10,
        filters: Optional[dict[str, Any]] = None,
    ) -> list[dict]:
        """向量相似度搜索

        Args:
            query_embedding: 查询向量
            top_k: 返回数量
            filters: 过滤条件（category, tags, importance 等）

        Returns:
            记忆列表（按相似度降序）
        """
        import json

        async with self._session_factory() as session:
            # 使用 PostgreSQL 向量余弦相似度搜索
            # 注意：生产环境应使用 pgvector 的余弦距离操作符
            # 这里使用简化版本，实际部署时需要启用 pgvector 扩展
            query = text("""
                SELECT id, content, embedding, importance, category, tags, metadata
                FROM ai_memories
                WHERE tenant_id = :tenant_id
                  AND workspace_id = :workspace_id
                  AND archived_at IS NULL
                ORDER BY embedding <=> :query_embedding::text
                LIMIT :top_k
            """)

            result = await session.execute(
                query,
                {
                    "tenant_id": self._tenant_id,
                    "workspace_id": self._workspace_id,
                    "query_embedding": json.dumps(query_embedding),
                    "top_k": top_k,
                }
            )

            memories = []
            for row in result:
                memories.append({
                    "id": str(row[0]),
                    "content": row[1],
                    "importance": row[3],
                    "category": row[4],
                    "tags": row[5],
                    "metadata": row[6],
                })

            return memories

    async def get_memory(self, memory_id: str) -> Optional[dict]:
        """获取单个记忆

        Args:
            memory_id: 记忆 ID

        Returns:
            记忆数据或 None
        """
        import uuid

        async with self._session_factory() as session:
            result = await session.execute(
                select(AIMemory).where(
                    AIMemory.id == uuid.UUID(memory_id),
                    AIMemory.tenant_id == self._tenant_id,
                )
            )
            memory = result.scalar_one_or_none()

            if not memory:
                return None

            # 更新访问计数
            memory.access_count += 1
            memory.last_accessed_at = datetime.now(memory.last_accessed_at.tzinfo if memory.last_accessed_at.tzinfo else None)
            await session.commit()

            return {
                "id": str(memory.id),
                "content": memory.content,
                "category": memory.category,
                "importance": memory.importance,
                "tags": memory.tags,
                "metadata": memory.metadata,
                "created_at": memory.created_at.isoformat(),
            }

    async def delete_memory(self, memory_id: str) -> bool:
        """删除记忆（软删除）

        Args:
            memory_id: 记忆 ID

        Returns:
            是否成功删除
        """
        import uuid

        async with self._session_factory() as session:
            result = await session.execute(
                update(AIMemory)
                .where(
                    AIMemory.id == uuid.UUID(memory_id),
                    AIMemory.tenant_id == self._tenant_id,
                )
                .values(archived_at=datetime.utcnow())
            )
            await session.commit()
            return result.rowcount > 0

    async def update_memory(
        self,
        memory_id: str,
        **kwargs,
    ) -> bool:
        """更新记忆

        Args:
            memory_id: 记忆 ID
            **kwargs: 更新字段

        Returns:
            是否成功更新
        """
        import uuid

        async with self._session_factory() as session:
            result = await session.execute(
                update(AIMemory)
                .where(
                    AIMemory.id == uuid.UUID(memory_id),
                    AIMemory.tenant_id == self._tenant_id,
                )
                .values(**kwargs)
            )
            await session.commit()
            return result.rowcount > 0

    async def archive_old_memories(
        self,
        before_date: datetime,
        keep_importance: float = 0.3,
    ) -> int:
        """归档旧记忆

        Args:
            before_date: 归档此日期之前的记忆
            keep_importance: 保留高于此重要性的记忆

        Returns:
            归档的记忆数量
        """
        async with self._session_factory() as session:
            result = await session.execute(
                update(AIMemory)
                .where(
                    AIMemory.tenant_id == self._tenant_id,
                    AIMemory.workspace_id == self._workspace_id,
                    AIMemory.created_at < before_date,
                    AIMemory.importance < keep_importance,
                    AIMemory.archived_at.is_(None),
                )
                .values(archived_at=datetime.utcnow())
            )
            await session.commit()
            return result.rowcount

    async def close(self) -> None:
        """关闭后端（无需操作，连接池由全局管理）"""
        pass
