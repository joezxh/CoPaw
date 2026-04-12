# -*- coding: utf-8 -*-
"""
Enterprise Scheduler — 企业版定时任务调度器

基于 ai_tasks 表的调度字段 + croniter 实现：
- 分布式锁（Redis SET NX）防止多节点重复执行
- 执行历史追踪（last_run_at, run_count, status）
- 超时控制 + 重试机制
"""
from __future__ import annotations

import asyncio
import logging
import uuid
from datetime import datetime
from typing import Any, Callable, Optional

from croniter import croniter

logger = logging.getLogger(__name__)


class EnterpriseScheduler:
    """企业版定时任务调度器"""

    def __init__(
        self,
        session_factory,
        redis_client=None,
        node_id: Optional[str] = None,
    ):
        """初始化

        Args:
            session_factory: SQLAlchemy async session factory
            redis_client: Redis 客户端（用于分布式锁）
            node_id: 节点 ID（用于分布式锁）
        """
        self._session_factory = session_factory
        self._redis = redis_client
        self._node_id = node_id or str(uuid.uuid4())[:8]
        self._running = False
        self._handlers: dict[str, Callable] = {}
        self._task: Optional[asyncio.Task] = None

    def register_task(self, task_id: str, handler: Callable) -> None:
        """注册任务处理器

        Args:
            task_id: 任务 ID
            handler: 异步处理函数
        """
        self._handlers[task_id] = handler
        logger.info("Registered task handler: %s", task_id)

    async def start(self) -> None:
        """启动调度循环"""
        if self._running:
            return

        self._running = True
        self._task = asyncio.create_task(self._tick_loop())
        logger.info("Scheduler started (node=%s)", self._node_id)

    async def stop(self) -> None:
        """停止调度循环"""
        self._running = False
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
        logger.info("Scheduler stopped")

    async def _tick_loop(self) -> None:
        """调度循环（每秒检查一次）"""
        while self._running:
            try:
                await self._tick()
            except Exception as e:
                logger.error("Scheduler tick error: %s", e, exc_info=True)

            await asyncio.sleep(1)

    async def _tick(self) -> None:
        """检查到期任务并执行"""
        from sqlalchemy import select, update
        from ...db.models.task import Task

        now = datetime.utcnow()

        async with self._session_factory() as session:
            # 查询到期的任务
            result = await session.execute(
                select(Task).where(
                    Task.schedule_expr.isnot(None),
                    Task.status == "active",
                    Task.next_run_at <= now,
                )
            )
            tasks = result.scalars().all()

            for task in tasks:
                # 尝试获取分布式锁
                lock_key = f"scheduler:lock:{task.id}"
                if self._redis:
                    acquired = await self._redis.set(
                        lock_key, self._node_id, nx=True, ex=300
                    )
                    if not acquired:
                        logger.debug("Task %s already locked, skipping", task.id)
                        continue

                try:
                    # 执行任务
                    await self._execute_task(task)

                    # 计算下次执行时间
                    if task.schedule_expr:
                        cron = croniter(task.schedule_expr, datetime.utcnow())
                        next_run = cron.get_next(datetime)

                        await session.execute(
                            update(Task)
                            .where(Task.id == task.id)
                            .values(
                                last_run_at=datetime.utcnow(),
                                next_run_at=next_run,
                                run_count=Task.run_count + 1,
                            )
                        )
                        await session.commit()

                except Exception as e:
                    logger.error("Task execution failed: %s", e, exc_info=True)
                    # 重试逻辑
                    if task.metadata and task.metadata.get("retry_count", 0) < task.metadata.get("max_retries", 3):
                        task.metadata["retry_count"] = task.metadata.get("retry_count", 0) + 1
                        task.status = "retrying"
                    else:
                        task.status = "failed"
                    await session.commit()

    async def _execute_task(self, task) -> None:
        """执行单个任务

        Args:
            task: Task ORM 对象
        """
        task_id = str(task.id)
        handler = self._handlers.get(task_id)

        if not handler:
            logger.warning("No handler registered for task: %s", task_id)
            return

        task.status = "running"
        logger.info("Executing task: %s", task_id)

        try:
            # 超时控制
            timeout = task.metadata.get("timeout_seconds", 300) if task.metadata else 300
            await asyncio.wait_for(handler(task), timeout=timeout)
            task.status = "active"
        except asyncio.TimeoutError:
            logger.error("Task %s timed out after %ds", task_id, timeout)
            task.status = "timeout"
            raise
        except Exception as e:
            logger.error("Task %s failed: %s", task_id, e, exc_info=True)
            task.status = "failed"
            raise
