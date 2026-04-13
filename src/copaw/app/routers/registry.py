# -*- coding: utf-8 -*-
"""
Registry API Routes — 注册表 API 路由

提供 SkillRegistry 和 ModelRegistry 的 RESTful API
"""
from __future__ import annotations

from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from copaw.db.postgresql import get_db_session
from copaw.db.repositories.registry_repo import (
    SkillRegistryRepo,
    ModelRegistryRepo,
    InferenceTaskRepo,
)

router = APIRouter(prefix="/v1/registry", tags=["registry"])


# ============================================================================
# Pydantic Schemas
# ============================================================================

class SkillRegistryCreate(BaseModel):
    """创建技能请求"""
    skill_name: str = Field(..., description="技能名称")
    version: str = Field(..., description="技能版本")
    description: Optional[str] = Field(None, description="技能描述")
    storage_key: Optional[str] = Field(None, description="对象存储键")


class SkillRegistryResponse(BaseModel):
    """技能响应"""
    id: UUID
    tenant_id: str
    skill_name: str
    version: str
    description: Optional[str]
    storage_key: Optional[str]
    is_active: bool

    class Config:
        from_attributes = True


class ModelRegistryCreate(BaseModel):
    """创建模型请求"""
    model_name: str = Field(..., description="模型名称")
    model_type: str = Field(..., description="模型类型")
    architecture: Optional[str] = Field(None, description="模型架构")
    storage_key: Optional[str] = Field(None, description="对象存储键")
    file_size: Optional[int] = Field(None, description="文件大小")
    quantization: Optional[str] = Field(None, description="量化格式")
    default_params: Optional[dict] = Field(None, description="默认参数")
    min_gpu_memory: Optional[int] = Field(None, description="最小GPU内存(MB)")
    min_ram: Optional[int] = Field(None, description="最小系统内存(MB)")


class ModelRegistryResponse(BaseModel):
    """模型响应"""
    id: UUID
    tenant_id: str
    model_name: str
    model_type: str
    architecture: Optional[str]
    storage_key: Optional[str]
    file_size: Optional[int]
    quantization: Optional[str]
    default_params: Optional[dict]
    min_gpu_memory: Optional[int]
    min_ram: Optional[int]
    is_available: bool
    health_status: str

    class Config:
        from_attributes = True


class InferenceTaskCreate(BaseModel):
    """创建推理任务请求"""
    task_type: str = Field(..., description="任务类型")
    input_data: dict = Field(..., description="输入数据")
    model_id: Optional[UUID] = Field(None, description="模型ID")


class InferenceTaskResponse(BaseModel):
    """推理任务响应"""
    id: UUID
    tenant_id: str
    model_id: Optional[UUID]
    user_id: Optional[UUID]
    workspace_id: Optional[UUID]
    task_type: str
    input_data: dict
    output_data: Optional[dict]
    status: str
    worker_id: Optional[str]
    prompt_tokens: int
    completion_tokens: int
    error_message: Optional[str]

    class Config:
        from_attributes = True


# ============================================================================
# Skill Registry Endpoints
# ============================================================================

@router.post("/skills", response_model=SkillRegistryResponse)
async def create_skill(
    data: SkillRegistryCreate,
    tenant_id: str = Query("default-tenant", description="租户ID"),
    session: AsyncSession = Depends(get_db_session),
):
    """创建技能注册记录"""
    skill = await SkillRegistryRepo.create(
        session=session,
        tenant_id=tenant_id,
        skill_name=data.skill_name,
        version=data.version,
        description=data.description,
        storage_key=data.storage_key,
    )
    return skill


@router.get("/skills", response_model=List[SkillRegistryResponse])
async def list_skills(
    tenant_id: str = Query("default-tenant", description="租户ID"),
    active_only: bool = Query(True, description="仅显示激活的技能"),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    session: AsyncSession = Depends(get_db_session),
):
    """列出技能"""
    if active_only:
        skills = await SkillRegistryRepo.list_active(
            session=session,
            tenant_id=tenant_id,
            skip=skip,
            limit=limit,
        )
    else:
        from sqlalchemy import select
        from copaw.db.models.storage_meta import SkillRegistry
        result = await session.execute(
            select(SkillRegistry)
            .where(SkillRegistry.tenant_id == tenant_id)
            .order_by(SkillRegistry.skill_name)
            .offset(skip)
            .limit(limit)
        )
        skills = list(result.scalars().all())
    return skills


@router.get("/skills/search", response_model=List[SkillRegistryResponse])
async def search_skills(
    keyword: str = Query(..., description="搜索关键词"),
    tenant_id: str = Query("default-tenant", description="租户ID"),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    session: AsyncSession = Depends(get_db_session),
):
    """搜索技能"""
    skills = await SkillRegistryRepo.search(
        session=session,
        tenant_id=tenant_id,
        keyword=keyword,
        skip=skip,
        limit=limit,
    )
    return skills


@router.get("/skills/{skill_id}", response_model=SkillRegistryResponse)
async def get_skill(
    skill_id: UUID,
    tenant_id: str = Query("default-tenant", description="租户ID"),
    session: AsyncSession = Depends(get_db_session),
):
    """获取技能详情"""
    skill = await SkillRegistryRepo.get_by_id(
        session=session,
        skill_id=skill_id,
        tenant_id=tenant_id,
    )
    if not skill:
        raise HTTPException(status_code=404, detail="Skill not found")
    return skill


@router.delete("/skills/{skill_id}")
async def deactivate_skill(
    skill_id: UUID,
    tenant_id: str = Query("default-tenant", description="租户ID"),
    session: AsyncSession = Depends(get_db_session),
):
    """停用技能"""
    success = await SkillRegistryRepo.deactivate(
        session=session,
        skill_id=skill_id,
        tenant_id=tenant_id,
    )
    if not success:
        raise HTTPException(status_code=404, detail="Skill not found")
    return {"message": "Skill deactivated"}


# ============================================================================
# Model Registry Endpoints
# ============================================================================

@router.post("/models", response_model=ModelRegistryResponse)
async def create_model(
    data: ModelRegistryCreate,
    tenant_id: str = Query("default-tenant", description="租户ID"),
    session: AsyncSession = Depends(get_db_session),
):
    """创建模型注册记录"""
    model = await ModelRegistryRepo.create(
        session=session,
        tenant_id=tenant_id,
        model_name=data.model_name,
        model_type=data.model_type,
        architecture=data.architecture,
        storage_key=data.storage_key,
        file_size=data.file_size,
        quantization=data.quantization,
        default_params=data.default_params,
        min_gpu_memory=data.min_gpu_memory,
        min_ram=data.min_ram,
    )
    return model


@router.get("/models", response_model=List[ModelRegistryResponse])
async def list_models(
    tenant_id: str = Query("default-tenant", description="租户ID"),
    model_type: Optional[str] = Query(None, description="模型类型过滤"),
    available_only: bool = Query(True, description="仅显示可用模型"),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    session: AsyncSession = Depends(get_db_session),
):
    """列出模型"""
    models = await ModelRegistryRepo.list_available(
        session=session,
        tenant_id=tenant_id,
        model_type=model_type,
        skip=skip,
        limit=limit,
    )
    return models


@router.get("/models/{model_id}", response_model=ModelRegistryResponse)
async def get_model(
    model_id: UUID,
    tenant_id: str = Query("default-tenant", description="租户ID"),
    session: AsyncSession = Depends(get_db_session),
):
    """获取模型详情"""
    model = await ModelRegistryRepo.get_by_id(
        session=session,
        model_id=model_id,
        tenant_id=tenant_id,
    )
    if not model:
        raise HTTPException(status_code=404, detail="Model not found")
    return model


@router.patch("/models/{model_id}/health")
async def update_model_health(
    model_id: UUID,
    health_status: str = Query(..., description="健康状态"),
    tenant_id: str = Query("default-tenant", description="租户ID"),
    session: AsyncSession = Depends(get_db_session),
):
    """更新模型健康状态"""
    success = await ModelRegistryRepo.update_health(
        session=session,
        model_id=model_id,
        tenant_id=tenant_id,
        health_status=health_status,
    )
    if not success:
        raise HTTPException(status_code=404, detail="Model not found")
    return {"message": f"Model health updated to {health_status}"}


# ============================================================================
# Inference Task Endpoints
# ============================================================================

@router.post("/tasks", response_model=InferenceTaskResponse)
async def create_inference_task(
    data: InferenceTaskCreate,
    tenant_id: str = Query("default-tenant", description="租户ID"),
    session: AsyncSession = Depends(get_db_session),
):
    """创建推理任务"""
    task = await InferenceTaskRepo.create(
        session=session,
        tenant_id=tenant_id,
        task_type=data.task_type,
        input_data=data.input_data,
        model_id=data.model_id,
    )
    return task


@router.get("/tasks/{task_id}", response_model=InferenceTaskResponse)
async def get_inference_task(
    task_id: UUID,
    tenant_id: str = Query("default-tenant", description="租户ID"),
    session: AsyncSession = Depends(get_db_session),
):
    """获取推理任务详情"""
    task = await InferenceTaskRepo.get_by_id(
        session=session,
        task_id=task_id,
        tenant_id=tenant_id,
    )
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    return task


@router.get("/tasks", response_model=List[InferenceTaskResponse])
async def list_inference_tasks(
    status: str = Query("pending", description="任务状态"),
    tenant_id: str = Query("default-tenant", description="租户ID"),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    session: AsyncSession = Depends(get_db_session),
):
    """列出推理任务"""
    tasks = await InferenceTaskRepo.list_by_status(
        session=session,
        tenant_id=tenant_id,
        status=status,
        skip=skip,
        limit=limit,
    )
    return tasks
