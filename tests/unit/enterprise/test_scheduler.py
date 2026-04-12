# -*- coding: utf-8 -*-
"""
测试 Phase 4: 任务调度器 - EnterpriseScheduler
"""
import pytest
from copaw.enterprise.scheduler import EnterpriseScheduler


class TestEnterpriseScheduler:
    """测试企业版调度器"""

    def test_parse_cron_expression(self):
        """测试Cron表达式解析"""
        scheduler = EnterpriseScheduler()

        # 每分钟
        next_run = scheduler._get_next_run("* * * * *")
        assert next_run is not None

        # 每小时
        next_run = scheduler._get_next_run("0 * * * *")
        assert next_run is not None

    def test_schedule_task(self):
        """测试任务调度"""
        scheduler = EnterpriseScheduler()

        async def dummy_task():
            return "done"

        task_id = scheduler.add_task(
            name="test-task",
            schedule_expr="* * * * *",
            task_func=dummy_task,
            max_retries=3,
            timeout_seconds=60,
        )

        assert task_id is not None
        assert task_id in scheduler._tasks

    def test_remove_task(self):
        """测试移除任务"""
        scheduler = EnterpriseScheduler()

        async def dummy_task():
            pass

        task_id = scheduler.add_task(
            name="test-task",
            schedule_expr="* * * * *",
            task_func=dummy_task,
        )

        scheduler.remove_task(task_id)
        assert task_id not in scheduler._tasks

    def test_get_task(self):
        """测试获取任务"""
        scheduler = EnterpriseScheduler()

        async def dummy_task():
            pass

        task_id = scheduler.add_task(
            name="test-task",
            schedule_expr="* * * * *",
            task_func=dummy_task,
        )

        task = scheduler.get_task(task_id)
        assert task is not None
        assert task["name"] == "test-task"

    def test_list_tasks(self):
        """测试列出任务"""
        scheduler = EnterpriseScheduler()

        async def dummy_task():
            pass

        scheduler.add_task("task-1", "* * * * *", dummy_task)
        scheduler.add_task("task-2", "0 * * * *", dummy_task)

        tasks = scheduler.list_tasks()
        assert len(tasks) == 2

    def test_execute_task_with_timeout(self):
        """测试任务执行超时"""
        import asyncio

        scheduler = EnterpriseScheduler()

        async def slow_task():
            await asyncio.sleep(10)
            return "done"

        # 这里我们只测试超时逻辑，不真正执行
        assert scheduler._check_timeout(1, 0.1) is False

    def test_retry_logic(self):
        """测试重试逻辑"""
        scheduler = EnterpriseScheduler()

        async def failing_task():
            raise Exception("Test error")

        task_id = scheduler.add_task(
            name="failing-task",
            schedule_expr="* * * * *",
            task_func=failing_task,
            max_retries=3,
        )

        task = scheduler.get_task(task_id)
        assert task["retry_count"] == 0
        assert task["max_retries"] == 3

    @pytest.mark.asyncio
    async def test_task_execution_success(self):
        """测试任务成功执行"""
        scheduler = EnterpriseScheduler()
        execution_count = {"count": 0}

        async def successful_task():
            execution_count["count"] += 1
            return "success"

        task_id = scheduler.add_task(
            name="success-task",
            schedule_expr="* * * * *",
            task_func=successful_task,
        )

        result = await scheduler._execute_task(task_id)
        assert result is True
        assert execution_count["count"] == 1

    @pytest.mark.asyncio
    async def test_task_execution_failure(self):
        """测试任务执行失败"""
        scheduler = EnterpriseScheduler()

        async def failing_task():
            raise Exception("Intentional failure")

        task_id = scheduler.add_task(
            name="failing-task",
            schedule_expr="* * * * *",
            task_func=failing_task,
            max_retries=3,
        )

        result = await scheduler._execute_task(task_id)
        assert result is False

        task = scheduler.get_task(task_id)
        assert task["retry_count"] == 1
