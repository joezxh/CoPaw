# -*- coding: utf-8 -*-
"""
Registry Repositories — 注册表数据访问层

提供 SkillRegistry、ModelRegistry、InferenceTask 的 CRUD 操作
"""
from __future__ import annotations

from typing import List, Optional
from uuid import UUID

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from copaw.db.models.storage_meta import (
    SkillRegistry,
    ModelRegistry,
    InferenceTask,
)


class SkillRegistryRepo:
    """技能注册表 Repository"""

    @staticmethod
    async def create(
        session: AsyncSession,
        tenant_id: str,
        skill_name: str,
        version: str,
        description: Optional[str] = None,
        storage_key: Optional[str] = None,
    ) -> SkillRegistry:
        """创建技能注册记录"""
        skill = SkillRegistry(
            tenant_id=tenant_id,
            skill_name=skill_name,
            version=version,
            description=description,
            storage_key=storage_key,
        )
        session.add(skill)
        await session.flush()
        return skill

    @staticmethod
    async def get_by_id(
        session: AsyncSession,
        skill_id: UUID,
        tenant_id: str,
    ) -> Optional[SkillRegistry]:
        """根据ID获取技能"""
        result = await session.execute(
            select(SkillRegistry).where(
                SkillRegistry.id == skill_id,
                SkillRegistry.tenant_id == tenant_id,
            )
        )
        return result.scalar_one_or_none()

    @staticmethod
    async def get_by_name(
        session: AsyncSession,
        tenant_id: str,
        skill_name: str,
        version: Optional[str] = None,
    ) -> Optional[SkillRegistry]:
        """根据名称获取技能"""
        query = select(SkillRegistry).where(
            SkillRegistry.tenant_id == tenant_id,
            SkillRegistry.skill_name == skill_name,
        )
        if version:
            query = query.where(SkillRegistry.version == version)
        result = await session.execute(query)
        return result.scalar_one_or_none()

    @staticmethod
    async def list_active(
        session: AsyncSession,
        tenant_id: str,
        skip: int = 0,
        limit: int = 50,
    ) -> List[SkillRegistry]:
        """列出所有激活的技能"""
        result = await session.execute(
            select(SkillRegistry)
            .where(
                SkillRegistry.tenant_id == tenant_id,
                SkillRegistry.is_active == True,
            )
            .order_by(SkillRegistry.skill_name)
            .offset(skip)
            .limit(limit)
        )
        return list(result.scalars().all())

    @staticmethod
    async def search(
        session: AsyncSession,
        tenant_id: str,
        keyword: str,
        skip: int = 0,
        limit: int = 50,
    ) -> List[SkillRegistry]:
        """搜索技能"""
        result = await session.execute(
            select(SkillRegistry)
            .where(
                SkillRegistry.tenant_id == tenant_id,
                SkillRegistry.skill_name.ilike(f"%{keyword}%"),
            )
            .order_by(SkillRegistry.skill_name)
            .offset(skip)
            .limit(limit)
        )
        return list(result.scalars().all())

    @staticmethod
    async def deactivate(
        session: AsyncSession,
        skill_id: UUID,
        tenant_id: str,
    ) -> bool:
        """停用技能"""
        result = await session.execute(
            select(SkillRegistry).where(
                SkillRegistry.id == skill_id,
                SkillRegistry.tenant_id == tenant_id,
            )
        )
        skill = result.scalar_one_or_none()
        if not skill:
            return False
        skill.is_active = False
        return True


class ModelRegistryRepo:
    """模型注册表 Repository"""

    @staticmethod
    async def create(
        session: AsyncSession,
        tenant_id: str,
        model_name: str,
        model_type: str,
        architecture: Optional[str] = None,
        storage_key: Optional[str] = None,
        file_size: Optional[int] = None,
        quantization: Optional[str] = None,
        default_params: Optional[dict] = None,
        min_gpu_memory: Optional[int] = None,
        min_ram: Optional[int] = None,
    ) -> ModelRegistry:
        """创建模型注册记录"""
        model = ModelRegistry(
            tenant_id=tenant_id,
            model_name=model_name,
            model_type=model_type,
            architecture=architecture,
            storage_key=storage_key,
            file_size=file_size,
            quantization=quantization,
            default_params=default_params or {},
            min_gpu_memory=min_gpu_memory,
            min_ram=min_ram,
        )
        session.add(model)
        await session.flush()
        return model

    @staticmethod
    async def get_by_id(
        session: AsyncSession,
        model_id: UUID,
        tenant_id: str,
    ) -> Optional[ModelRegistry]:
        """根据ID获取模型"""
        result = await session.execute(
            select(ModelRegistry).where(
                ModelRegistry.id == model_id,
                ModelRegistry.tenant_id == tenant_id,
            )
        )
        return result.scalar_one_or_none()

    @staticmethod
    async def get_by_name(
        session: AsyncSession,
        tenant_id: str,
        model_name: str,
    ) -> Optional[ModelRegistry]:
        """根据名称获取模型"""
        result = await session.execute(
            select(ModelRegistry).where(
                ModelRegistry.tenant_id == tenant_id,
                ModelRegistry.model_name == model_name,
            )
        )
        return result.scalar_one_or_none()

    @staticmethod
    async def list_available(
        session: AsyncSession,
        tenant_id: str,
        model_type: Optional[str] = None,
        skip: int = 0,
        limit: int = 50,
    ) -> List[ModelRegistry]:
        """列出所有可用模型"""
        query = select(ModelRegistry).where(
            ModelRegistry.tenant_id == tenant_id,
            ModelRegistry.is_available == True,
        )
        if model_type:
            query = query.where(ModelRegistry.model_type == model_type)
        query = query.order_by(ModelRegistry.model_name).offset(skip).limit(limit)
        result = await session.execute(query)
        return list(result.scalars().all())

    @staticmethod
    async def update_health(
        session: AsyncSession,
        model_id: UUID,
        tenant_id: str,
        health_status: str,
    ) -> bool:
        """更新模型健康状态"""
        result = await session.execute(
            select(ModelRegistry).where(
                ModelRegistry.id == model_id,
                ModelRegistry.tenant_id == tenant_id,
            )
        )
        model = result.scalar_one_or_none()
        if not model:
            return False
        model.health_status = health_status
        return True


class InferenceTaskRepo:
    """推理任务 Repository"""

    @staticmethod
    async def create(
        session: AsyncSession,
        tenant_id: str,
        task_type: str,
        input_data: dict,
        model_id: Optional[UUID] = None,
        user_id: Optional[UUID] = None,
        workspace_id: Optional[UUID] = None,
    ) -> InferenceTask:
        """创建推理任务"""
        task = InferenceTask(
            tenant_id=tenant_id,
            model_id=model_id,
            user_id=user_id,
            workspace_id=workspace_id,
            task_type=task_type,
            input_data=input_data,
        )
        session.add(task)
        await session.flush()
        return task

    @staticmethod
    async def get_by_id(
        session: AsyncSession,
        task_id: UUID,
        tenant_id: str,
    ) -> Optional[InferenceTask]:
        """根据ID获取任务"""
        result = await session.execute(
            select(InferenceTask).where(
                InferenceTask.id == task_id,
                InferenceTask.tenant_id == tenant_id,
            )
        )
        return result.scalar_one_or_none()

    @staticmethod
    async def list_by_status(
        session: AsyncSession,
        tenant_id: str,
        status: str,
        skip: int = 0,
        limit: int = 50,
    ) -> List[InferenceTask]:
        """按状态列出任务"""
        result = await session.execute(
            select(InferenceTask)
            .where(
                InferenceTask.tenant_id == tenant_id,
                InferenceTask.status == status,
            )
            .order_by(InferenceTask.created_at.desc())
            .offset(skip)
            .limit(limit)
        )
        return list(result.scalars().all())

    @staticmethod
    async def update_status(
        session: AsyncSession,
        task_id: UUID,
        tenant_id: str,
        status: str,
        output_data: Optional[dict] = None,
        error_message: Optional[str] = None,
        prompt_tokens: int = 0,
        completion_tokens: int = 0,
    ) -> bool:
        """更新任务状态"""
        from datetime import datetime, timezone
        
        result = await session.execute(
            select(InferenceTask).where(
                InferenceTask.id == task_id,
                InferenceTask.tenant_id == tenant_id,
            )
        )
        task = result.scalar_one_or_none()
        if not task:
            return False
        
        task.status = status
        if output_data is not None:
            task.output_data = output_data
        if error_message is not None:
            task.error_message = error_message
        task.prompt_tokens = prompt_tokens
        task.completion_tokens = completion_tokens
        
        if status == "running" and not task.started_at:
            task.started_at = datetime.now(timezone.utc)
        elif status in ("completed", "failed"):
            task.completed_at = datetime.now(timezone.utc)
        
        return True
