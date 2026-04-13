# -*- coding: utf-8 -*-
"""
Registry Repository Tests — 注册表 Repository 测试
"""
import pytest
from uuid import uuid4
from unittest.mock import AsyncMock, MagicMock

from copaw.db.repositories.registry_repo import (
    SkillRegistryRepo,
    ModelRegistryRepo,
    InferenceTaskRepo,
)


class TestSkillRegistryRepo:
    """技能注册表 Repository 测试"""

    @pytest.mark.asyncio
    async def test_create_skill(self):
        """测试创建技能"""
        session = AsyncMock()
        session.flush = AsyncMock()

        skill = await SkillRegistryRepo.create(
            session=session,
            tenant_id="test-tenant",
            skill_name="test-skill",
            version="1.0.0",
            description="Test skill",
        )

        assert skill.tenant_id == "test-tenant"
        assert skill.skill_name == "test-skill"
        assert skill.version == "1.0.0"
        # server_default 在测试中不会自动应用
        assert skill.description == "Test skill"
        session.add.assert_called_once()

    @pytest.mark.asyncio
    async def test_list_active_skills(self):
        """测试列出激活的技能"""
        session = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = []
        session.execute = AsyncMock(return_value=mock_result)

        skills = await SkillRegistryRepo.list_active(
            session=session,
            tenant_id="test-tenant",
        )

        assert isinstance(skills, list)
        session.execute.assert_called_once()


class TestModelRegistryRepo:
    """模型注册表 Repository 测试"""

    @pytest.mark.asyncio
    async def test_create_model(self):
        """测试创建模型"""
        session = AsyncMock()
        session.flush = AsyncMock()

        model = await ModelRegistryRepo.create(
            session=session,
            tenant_id="test-tenant",
            model_name="test-model",
            model_type="llm",
            architecture="transformer",
        )

        assert model.tenant_id == "test-tenant"
        assert model.model_name == "test-model"
        assert model.model_type == "llm"
        assert model.architecture == "transformer"
        # server_default 在测试中不会自动应用
        session.add.assert_called_once()

    @pytest.mark.asyncio
    async def test_update_health(self):
        """测试更新模型健康状态"""
        session = AsyncMock()
        mock_model = MagicMock()
        mock_model.health_status = "unknown"

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_model
        session.execute = AsyncMock(return_value=mock_result)

        success = await ModelRegistryRepo.update_health(
            session=session,
            model_id=uuid4(),
            tenant_id="test-tenant",
            health_status="healthy",
        )

        assert success == True
        assert mock_model.health_status == "healthy"


class TestInferenceTaskRepo:
    """推理任务 Repository 测试"""

    @pytest.mark.asyncio
    async def test_create_task(self):
        """测试创建推理任务"""
        session = AsyncMock()
        session.flush = AsyncMock()

        task = await InferenceTaskRepo.create(
            session=session,
            tenant_id="test-tenant",
            task_type="completion",
            input_data={"prompt": "Hello"},
        )

        assert task.tenant_id == "test-tenant"
        assert task.task_type == "completion"
        assert task.input_data == {"prompt": "Hello"}
        # server_default 在测试中不会自动应用
        session.add.assert_called_once()

    @pytest.mark.asyncio
    async def test_update_task_status(self):
        """测试更新任务状态"""
        from datetime import datetime, timezone

        session = AsyncMock()
        mock_task = MagicMock()
        mock_task.status = "pending"
        mock_task.started_at = None
        mock_task.completed_at = None

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_task
        session.execute = AsyncMock(return_value=mock_result)

        success = await InferenceTaskRepo.update_status(
            session=session,
            task_id=uuid4(),
            tenant_id="test-tenant",
            status="running",
        )

        assert success == True
        assert mock_task.status == "running"
        assert mock_task.started_at is not None
