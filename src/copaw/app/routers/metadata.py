# -*- coding: utf-8 -*-
"""
Metadata API Router — 元数据管理 API

提供元数据查询、搜索和管理接口。
"""
from __future__ import annotations

import uuid
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from copaw.db.session import get_db_session
from copaw.storage.search_service import (
    StorageSearchService,
    StorageSearchRequest,
    StorageSearchResult,
)
from copaw.db.repositories.agent_config_repo import AgentConfigRepository
from copaw.db.repositories.skill_config_repo import SkillConfigRepository

router = APIRouter(prefix="/metadata", tags=["metadata"])


@router.get("/search", response_model=StorageSearchResult)
async def search_storage_objects(
    q: str = Query("", description="搜索关键词"),
    category: Optional[str] = Query(None, description="文件类别"),
    tags: Optional[str] = Query(None, description="标签（逗号分隔）"),
    min_size: Optional[int] = Query(None, description="最小文件大小"),
    max_size: Optional[int] = Query(None, description="最大文件大小"),
    tenant_id: str = Query("default-tenant", description="租户ID"),
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页数量"),
    db: AsyncSession = Depends(get_db_session),
):
    """搜索存储对象（全文搜索）"""
    tag_list = [t.strip() for t in tags.split(",") if t.strip()] if tags else []

    request = StorageSearchRequest(
        tenant_id=tenant_id,
        query=q,
        category=category,
        tags=tag_list,
        min_file_size=min_size,
        max_file_size=max_size,
        page=page,
        page_size=page_size,
    )

    service = StorageSearchService()
    return await service.search(request, db)


@router.get("/agents")
async def list_agent_configs(
    workspace_id: str = Query(..., description="工作空间ID"),
    tenant_id: str = Query("default-tenant", description="租户ID"),
    status: Optional[str] = Query(None, description="状态过滤"),
    db: AsyncSession = Depends(get_db_session),
):
    """列出Agent配置"""
    repo = AgentConfigRepository(db)
    workspace_uuid = uuid.UUID(workspace_id)
    
    configs = await repo.list_by_workspace(workspace_uuid, tenant_id, status)
    return {
        "total": len(configs),
        "items": [
            {
                "id": str(c.id),
                "agent_id": c.agent_id,
                "name": c.name,
                "model_provider": c.model_provider,
                "model_name": c.model_name,
                "status": c.status,
                "created_at": c.created_at.isoformat() if c.created_at else None,
            }
            for c in configs
        ],
    }


@router.get("/agents/{agent_id}")
async def get_agent_config(
    agent_id: str,
    tenant_id: str = Query("default-tenant", description="租户ID"),
    db: AsyncSession = Depends(get_db_session),
):
    """获取Agent配置详情"""
    repo = AgentConfigRepository(db)
    config = await repo.get_by_agent_id(agent_id, tenant_id)
    
    if not config:
        raise HTTPException(status_code=404, detail="Agent config not found")
    
    return {
        "id": str(config.id),
        "agent_id": config.agent_id,
        "name": config.name,
        "description": config.description,
        "model_provider": config.model_provider,
        "model_name": config.model_name,
        "model_base_url": config.model_base_url,
        "temperature": config.temperature,
        "max_tokens": config.max_tokens,
        "enabled_channels": config.enabled_channels,
        "memory_backend": config.memory_backend,
        "skills": config.skills,
        "status": config.status,
        "created_at": config.created_at.isoformat() if config.created_at else None,
        "updated_at": config.updated_at.isoformat() if config.updated_at else None,
    }


@router.get("/skills")
async def list_skill_configs(
    workspace_id: str = Query(..., description="工作空间ID"),
    tenant_id: str = Query("default-tenant", description="租户ID"),
    enabled: Optional[bool] = Query(None, description="启用状态过滤"),
    db: AsyncSession = Depends(get_db_session),
):
    """列出Skill配置"""
    repo = SkillConfigRepository(db)
    workspace_uuid = uuid.UUID(workspace_id)
    
    skills = await repo.list_by_workspace(workspace_uuid, tenant_id, enabled)
    return {
        "total": len(skills),
        "items": [
            {
                "id": str(s.id),
                "skill_name": s.skill_name,
                "display_name": s.display_name,
                "version": s.version,
                "source": s.source,
                "enabled": s.enabled,
                "created_at": s.created_at.isoformat() if s.created_at else None,
            }
            for s in skills
        ],
    }


@router.get("/stats/by-category")
async def get_storage_stats_by_category(
    tenant_id: str = Query("default-tenant", description="租户ID"),
    workspace_id: Optional[str] = Query(None, description="工作空间ID"),
    db: AsyncSession = Depends(get_db_session),
):
    """按类别统计存储使用情况"""
    from copaw.db.models.storage_meta import StorageObject
    from sqlalchemy import func, select

    query = (
        select(
            StorageObject.category,
            func.count(StorageObject.id).label("file_count"),
            func.sum(StorageObject.file_size).label("total_size"),
        )
        .where(StorageObject.tenant_id == tenant_id)
        .group_by(StorageObject.category)
    )

    if workspace_id:
        query = query.where(StorageObject.workspace_id == uuid.UUID(workspace_id))

    result = await db.execute(query)
    rows = result.all()

    return {
        "tenant_id": tenant_id,
        "categories": [
            {
                "category": row.category,
                "file_count": row.file_count,
                "total_size": row.total_size or 0,
            }
            for row in rows
        ],
    }
