# -*- coding: utf-8 -*-
"""
Registry WriteHook — 注册表写入钩子

在文件上传/更新时自动同步技能注册表和模型注册表
"""
from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Optional

from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)


async def on_skill_uploaded(
    skill_json_path: Path,
    storage_key: str,
    tenant_id: str,
    session: AsyncSession,
) -> bool:
    """
    Skill 文件上传后的同步钩子
    
    Args:
        skill_json_path: skill.json 文件路径
        storage_key: 对象存储键
        tenant_id: 租户ID
        session: 数据库会话
        
    Returns:
        是否成功同步
    """
    try:
        from copaw.db.models.storage_meta import SkillRegistry
        from copaw.db.repositories.registry_repo import SkillRegistryRepo
        
        # 读取 skill.json
        with open(skill_json_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        
        if not isinstance(data, dict):
            logger.warning(f"Invalid skill.json format: {skill_json_path}")
            return False
        
        skill_name = data.get("name", skill_json_path.parent.name)
        version = data.get("version", "1.0.0")
        description = data.get("description")
        
        # 检查是否已存在
        existing = await SkillRegistryRepo.get_by_name(
            session=session,
            tenant_id=tenant_id,
            skill_name=skill_name,
            version=version,
        )
        
        if existing:
            # 更新现有记录
            existing.description = description
            existing.storage_key = storage_key
            logger.info(f"Updated skill registry: {skill_name} v{version}")
        else:
            # 创建新记录
            await SkillRegistryRepo.create(
                session=session,
                tenant_id=tenant_id,
                skill_name=skill_name,
                version=version,
                description=description,
                storage_key=storage_key,
            )
            logger.info(f"Created skill registry: {skill_name} v{version}")
        
        return True
        
    except Exception as e:
        logger.error(f"Failed to sync skill registry: {e}", exc_info=True)
        return False


async def on_model_config_uploaded(
    model_config_path: Path,
    storage_key: str,
    tenant_id: str,
    session: AsyncSession,
) -> bool:
    """
    模型配置文件上传后的同步钩子
    
    Args:
        model_config_path: 模型配置文件路径
        storage_key: 对象存储键
        tenant_id: 租户ID
        session: 数据库会话
        
    Returns:
        是否成功同步
    """
    try:
        from copaw.db.models.storage_meta import ModelRegistry
        from copaw.db.repositories.registry_repo import ModelRegistryRepo
        
        # 读取模型配置
        with open(model_config_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        
        if not isinstance(data, dict):
            logger.warning(f"Invalid model config format: {model_config_path}")
            return False
        
        model_name = data.get("model_name") or data.get("name")
        if not model_name:
            logger.warning(f"Missing model_name in config: {model_config_path}")
            return False
        
        model_type = data.get("model_type", "llm")
        architecture = data.get("architecture")
        file_size = data.get("file_size")
        quantization = data.get("quantization")
        default_params = data.get("default_params", {})
        min_gpu_memory = data.get("min_gpu_memory")
        min_ram = data.get("min_ram")
        
        # 检查是否已存在
        existing = await ModelRegistryRepo.get_by_name(
            session=session,
            tenant_id=tenant_id,
            model_name=model_name,
        )
        
        if existing:
            # 更新现有记录
            existing.model_type = model_type
            existing.architecture = architecture
            existing.storage_key = storage_key
            existing.file_size = file_size
            existing.quantization = quantization
            existing.default_params = default_params
            existing.min_gpu_memory = min_gpu_memory
            existing.min_ram = min_ram
            logger.info(f"Updated model registry: {model_name}")
        else:
            # 创建新记录
            await ModelRegistryRepo.create(
                session=session,
                tenant_id=tenant_id,
                model_name=model_name,
                model_type=model_type,
                architecture=architecture,
                storage_key=storage_key,
                file_size=file_size,
                quantization=quantization,
                default_params=default_params,
                min_gpu_memory=min_gpu_memory,
                min_ram=min_ram,
            )
            logger.info(f"Created model registry: {model_name}")
        
        return True
        
    except Exception as e:
        logger.error(f"Failed to sync model registry: {e}", exc_info=True)
        return False


async def sync_skill_from_storage(
    skill_json: Path,
    tenant_id: str,
    session: AsyncSession,
    workspace_id: Optional[str] = None,
) -> bool:
    """
    从对象存储同步 Skill 到注册表
    
    Args:
        skill_json: skill.json 文件路径（本地临时文件）
        tenant_id: 租户ID
        session: 数据库会话
        workspace_id: 工作空间ID（可选）
        
    Returns:
        是否成功同步
    """
    if not skill_json.exists():
        return False
    
    # 构建 storage_key
    skill_dir = skill_json.parent
    storage_key = f"{tenant_id}/skills/{skill_dir.name}/skill.json"
    
    return await on_skill_uploaded(
        skill_json_path=skill_json,
        storage_key=storage_key,
        tenant_id=tenant_id,
        session=session,
    )


async def sync_model_from_storage(
    model_config: Path,
    tenant_id: str,
    session: AsyncSession,
) -> bool:
    """
    从对象存储同步模型配置到注册表
    
    Args:
        model_config: 模型配置文件路径
        tenant_id: 租户ID
        session: 数据库会话
        
    Returns:
        是否成功同步
    """
    if not model_config.exists():
        return False
    
    # 构建 storage_key
    storage_key = f"{tenant_id}/models/{model_config.parent.name}/config.json"
    
    return await on_model_config_uploaded(
        model_config_path=model_config,
        storage_key=storage_key,
        tenant_id=tenant_id,
        session=session,
    )
