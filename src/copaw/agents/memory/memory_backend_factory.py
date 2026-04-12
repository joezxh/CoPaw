# -*- coding: utf-8 -*-
"""
Memory Backend Factory — 记忆后端工厂

根据运行版本（企业版/个人版）自动选择记忆后端：
- 企业版: PostgreSQL + pgvector
- 个人版: SQLite / Chroma / 本地文件
"""
from __future__ import annotations

import logging
import os
from typing import Optional

logger = logging.getLogger(__name__)


def create_memory_backend(
    workspace_dir: str,
    agent_id: str,
    tenant_id: Optional[str] = None,
    workspace_id: Optional[str] = None,
):
    """根据运行版本创建记忆后端

    Args:
        workspace_dir: 工作空间目录
        agent_id: Agent ID
        tenant_id: 租户 ID（企业版必需）
        workspace_id: 工作空间 ID（企业版必需）

    Returns:
        记忆后端实例

    Raises:
        ValueError: 当后端配置无效时
    """
    # 读取配置
    enterprise_enabled = os.getenv("COPAW_ENTERPRISE_ENABLED", "false").lower() == "true"
    memory_backend = os.getenv("COPAW_MEMORY_BACKEND", "auto").lower()

    # 自动选择后端
    if memory_backend == "auto":
        memory_backend = "postgres" if enterprise_enabled else "sqlite"

    logger.info(
        "Creating memory backend: enterprise=%s backend=%s",
        enterprise_enabled,
        memory_backend,
    )

    if memory_backend == "postgres":
        # 企业版: PostgreSQL + pgvector
        if not tenant_id or not workspace_id:
            raise ValueError(
                "PostgreSQL memory backend requires tenant_id and workspace_id"
            )
        return _create_postgres_backend(tenant_id, workspace_id, agent_id)

    elif memory_backend in ("sqlite", "chroma", "local"):
        # 个人版: 保持原有 ReMe 行为
        return _create_local_backend(workspace_dir, agent_id, memory_backend)

    else:
        valid_backends = ["auto", "postgres", "sqlite", "chroma", "local"]
        raise ValueError(
            f"Unsupported memory backend: {memory_backend}. "
            f"Valid options: {valid_backends}"
        )


def _create_postgres_backend(
    tenant_id: str,
    workspace_id: str,
    agent_id: str,
):
    """创建 PostgreSQL 记忆后端"""
    try:
        from .reme_postgres_backend import ReMePostgresBackend
        from ...db.postgresql import get_database_manager

        manager = get_database_manager()
        backend = ReMePostgresBackend(
            session_factory=manager.session,
            workspace_id=workspace_id,
            tenant_id=tenant_id,
            agent_id=agent_id,
        )
        logger.info("PostgreSQL memory backend created for tenant=%s workspace=%s", tenant_id, workspace_id)
        return backend

    except ImportError as e:
        raise ImportError(
            "PostgreSQL memory backend requires 'pgvector' package. "
            "Install with: pip install copaw[enterprise]"
        ) from e


def _create_local_backend(
    workspace_dir: str,
    agent_id: str,
    backend_type: str,
):
    """创建本地记忆后端（个人版）"""
    try:
        # 保持原有 ReMe 行为
        from .reme_light_memory_manager import ReMeLightMemoryManager

        backend = ReMeLightMemoryManager(
            working_dir=workspace_dir,
            agent_id=agent_id,
        )
        logger.info("Local memory backend created: type=%s", backend_type)
        return backend

    except ImportError as e:
        raise ImportError(
            f"Failed to create local memory backend ({backend_type}): {e}"
        ) from e
