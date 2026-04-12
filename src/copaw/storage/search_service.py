# -*- coding: utf-8 -*-
"""
Storage Search Service — 存储搜索服务

提供基于 PostgreSQL 全文搜索和过滤的存储对象搜索能力。
"""
from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Optional

from sqlalchemy import select, func, desc, asc, and_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.sql import text

from ..db.models.storage_meta import StorageObject

logger = logging.getLogger(__name__)


@dataclass
class StorageSearchRequest:
    """存储搜索请求"""
    query: str = ""                                # 搜索关键词
    tenant_id: str = ""                            # 租户ID (必须)
    category: Optional[str] = None                 # 文件类别过滤
    owner_id: Optional[str] = None                 # 所有者过滤
    workspace_id: Optional[str] = None             # 工作空间过滤
    tags: Optional[list[str]] = None               # 标签过滤
    content_type: Optional[str] = None             # MIME 类型过滤
    min_size: Optional[int] = None                 # 最小文件大小
    max_size: Optional[int] = None                 # 最大文件大小
    date_from: Optional[str] = None                # 起始日期
    date_to: Optional[str] = None                  # 截止日期
    page: int = 1                                  # 页码
    page_size: int = 20                            # 每页数量
    sort_by: str = "updated_at"                    # 排序字段
    sort_order: str = "desc"                       # 排序方向


@dataclass
class StorageSearchResult:
    """存储搜索结果"""
    total: int
    page: int
    page_size: int
    items: list[dict] = field(default_factory=list)


class StorageSearchService:
    """存储搜索服务"""

    async def search(
        self,
        request: StorageSearchRequest,
        db_session: AsyncSession,
    ) -> StorageSearchResult:
        """全文搜索 + 过滤

        Args:
            request: 搜索请求
            db_session: 数据库会话

        Returns:
            搜索结果（包含总数和分页）
        """
        # 基础查询：强制租户隔离
        conditions = [
            StorageObject.tenant_id == request.tenant_id,
            StorageObject.deleted_at.is_(None),
        ]

        # 全文搜索
        if request.query:
            # PostgreSQL 全文搜索
            conditions.append(
                text(
                    "to_tsvector('simple', COALESCE(storage_objects.search_text, '')) "
                    "@@ plainto_tsquery('simple', :query)"
                ).params(query=request.query)
            )

        # 类别过滤
        if request.category:
            conditions.append(StorageObject.category == request.category)

        # 所有者过滤
        if request.owner_id:
            conditions.append(StorageObject.user_id == request.owner_id)

        # 工作空间过滤
        if request.workspace_id:
            conditions.append(StorageObject.workspace_id == request.workspace_id)

        # 标签过滤
        if request.tags:
            conditions.append(StorageObject.tags.op("@>")(request.tags))

        # MIME 类型过滤
        if request.content_type:
            conditions.append(StorageObject.content_type == request.content_type)

        # 文件大小范围
        if request.min_size is not None:
            conditions.append(StorageObject.file_size >= request.min_size)
        if request.max_size is not None:
            conditions.append(StorageObject.file_size <= request.max_size)

        # 时间范围
        if request.date_from:
            conditions.append(StorageObject.created_at >= request.date_from)
        if request.date_to:
            conditions.append(StorageObject.created_at <= request.date_to)

        # 构建查询
        where_clause = and_(*conditions)

        # 获取总数
        count_query = select(func.count()).select_from(StorageObject).where(where_clause)
        total_result = await db_session.execute(count_query)
        total = total_result.scalar() or 0

        # 分页查询
        offset = (request.page - 1) * request.page_size
        order_col = getattr(StorageObject, request.sort_by, StorageObject.updated_at)
        order_func = desc if request.sort_order == "desc" else asc

        query = (
            select(StorageObject)
            .where(where_clause)
            .order_by(order_func(order_col))
            .limit(request.page_size)
            .offset(offset)
        )

        result = await db_session.execute(query)
        objects = result.scalars().all()

        # 转换为字典
        items = []
        for obj in objects:
            items.append({
                "id": str(obj.id),
                "object_key": obj.object_key,
                "file_name": obj.file_name,
                "file_ext": obj.file_ext,
                "content_type": obj.content_type,
                "file_size": obj.file_size,
                "category": obj.category,
                "tags": obj.tags,
                "content_hash": obj.content_hash,
                "storage_class": obj.storage_class,
                "workspace_id": str(obj.workspace_id) if obj.workspace_id else None,
                "user_id": str(obj.user_id) if obj.user_id else None,
                "created_at": obj.created_at.isoformat() if obj.created_at else None,
                "updated_at": obj.updated_at.isoformat() if obj.updated_at else None,
            })

        return StorageSearchResult(
            total=total,
            page=request.page,
            page_size=request.page_size,
            items=items,
        )

    async def search_by_content(
        self,
        tenant_id: str,
        text_query: str,
        limit: int = 10,
        db_session: Optional[AsyncSession] = None,
    ) -> list[dict]:
        """基于内容的模糊搜索（使用 GIN 索引）

        Args:
            tenant_id: 租户 ID
            text_query: 搜索文本
            limit: 返回数量限制
            db_session: 数据库会话

        Returns:
            搜索结果列表
        """
        if not db_session:
            return []

        # 使用 PostgreSQL 的 SIMILARITY 或 ILIKE 进行模糊搜索
        query = (
            select(StorageObject)
            .where(
                StorageObject.tenant_id == tenant_id,
                StorageObject.deleted_at.is_(None),
                StorageObject.search_text.ilike(f"%{text_query}%"),
            )
            .limit(limit)
        )

        result = await db_session.execute(query)
        objects = result.scalars().all()

        return [
            {
                "object_key": obj.object_key,
                "file_name": obj.file_name,
                "category": obj.category,
                "file_size": obj.file_size,
            }
            for obj in objects
        ]
