#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
批量索引注册表 — 扫描文件系统并同步到注册表

用法:
    python scripts/batch_index_registry.py --tenant-id acme-corp
"""
import asyncio
import json
import logging
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)


class RegistryIndexer:
    """注册表批量索引器"""

    def __init__(self, tenant_id: str):
        self.tenant_id = tenant_id

    async def index_all(self) -> dict:
        """索引所有技能和模型"""
        stats = {
            "skills_global": 0,
            "skills_agent": 0,
            "models": 0,
            "errors": [],
        }

        # 1. 索引全局 Skill 池
        stats["skills_global"] = await self._index_global_skills()

        # 2. 索引工作空间中的 Agent Skills
        stats["skills_agent"] = await self._index_agent_skills()

        # 3. 索引模型配置（如果有）
        stats["models"] = await self._index_models()

        logger.info(f"✅ 注册表索引完成: {stats}")
        return stats

    async def _index_global_skills(self) -> int:
        """索引全局 Skill 池"""
        from copaw.db.postgresql import get_database_manager
        from copaw.storage.registry_hook import on_skill_uploaded

        skill_pool = Path("working/skill_pool")
        if not skill_pool.exists():
            return 0

        count = 0
        db_manager = get_database_manager()

        for skill_dir in skill_pool.iterdir():
            if not skill_dir.is_dir():
                continue

            skill_json = skill_dir / "skill.json"
            if not skill_json.exists():
                continue

            try:
                storage_key = f"{self.tenant_id}/skills/global/{skill_dir.name}/skill.json"
                async with db_manager.session() as session:
                    await on_skill_uploaded(
                        skill_json_path=skill_json,
                        storage_key=storage_key,
                        tenant_id=self.tenant_id,
                        session=session,
                    )
                count += 1
            except Exception as e:
                logger.error(f"Failed to index skill {skill_dir.name}: {e}")

        return count

    async def _index_agent_skills(self) -> int:
        """索引工作空间中分配给 Agent 的 Skills"""
        from copaw.db.postgresql import get_database_manager
        from copaw.storage.registry_hook import on_skill_uploaded

        workspaces_dir = Path("working/workspaces")
        if not workspaces_dir.exists():
            return 0

        count = 0
        db_manager = get_database_manager()

        for workspace_dir in workspaces_dir.iterdir():
            if not workspace_dir.is_dir():
                continue

            # 读取 agent.json 获取 agent_id
            agent_json = workspace_dir / "agent.json"
            if not agent_json.exists():
                continue

            try:
                with open(agent_json, "r", encoding="utf-8") as f:
                    agent_data = json.load(f)
                agent_id = agent_data.get("id", workspace_dir.name)

                # 扫描 {agent_id}/skills 目录
                agent_skills_dir = workspace_dir / agent_id / "skills"
                if not agent_skills_dir.exists():
                    continue

                for skill_dir in agent_skills_dir.iterdir():
                    if not skill_dir.is_dir():
                        continue

                    skill_json = skill_dir / "skill.json"
                    if not skill_json.exists():
                        continue

                    storage_key = f"{self.tenant_id}/workspaces/{workspace_dir.name}/{agent_id}/skills/{skill_dir.name}/skill.json"
                    async with db_manager.session() as session:
                        await on_skill_uploaded(
                            skill_json_path=skill_json,
                            storage_key=storage_key,
                            tenant_id=self.tenant_id,
                            session=session,
                        )
                    count += 1
            except Exception as e:
                logger.error(f"Failed to index agent skills in {workspace_dir.name}: {e}")

        return count

    async def _index_models(self) -> int:
        """索引模型配置"""
        from copaw.db.postgresql import get_database_manager
        from copaw.storage.registry_hook import on_model_config_uploaded

        # 模型配置通常在全局目录
        models_dir = Path("working/models")
        if not models_dir.exists():
            return 0

        count = 0
        db_manager = get_database_manager()

        for model_dir in models_dir.iterdir():
            if not model_dir.is_dir():
                continue

            model_config = model_dir / "config.json"
            if not model_config.exists():
                continue

            try:
                storage_key = f"{self.tenant_id}/models/{model_dir.name}/config.json"
                async with db_manager.session() as session:
                    await on_model_config_uploaded(
                        model_config_path=model_config,
                        storage_key=storage_key,
                        tenant_id=self.tenant_id,
                        session=session,
                    )
                count += 1
            except Exception as e:
                logger.error(f"Failed to index model {model_dir.name}: {e}")

        return count


async def main():
    """主函数"""
    import argparse
    from copaw.db.postgresql import get_database_manager

    parser = argparse.ArgumentParser(description="批量索引注册表")
    parser.add_argument("--tenant-id", default="default-tenant", help="租户ID")

    args = parser.parse_args()

    # 初始化数据库连接
    print("正在连接数据库...")
    db_manager = get_database_manager()
    await db_manager.initialize()
    print("✅ 数据库连接成功")

    try:
        indexer = RegistryIndexer(tenant_id=args.tenant_id)
        stats = await indexer.index_all()

        print("\n=== 注册表索引统计 ===")
        print(f"全局技能: {stats['skills_global']}")
        print(f"Agent技能: {stats['skills_agent']}")
        print(f"模型: {stats['models']}")

        if stats["errors"]:
            print(f"\n错误: {len(stats['errors'])}")
            for error in stats["errors"]:
                print(f"  - {error}")
    finally:
        await db_manager.close()
        print("\n✅ 数据库连接已关闭")


if __name__ == "__main__":
    asyncio.run(main())
