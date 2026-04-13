#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Batch Index Tool — 批量索引工具

扫描工作空间目录，将文件元数据批量索引到PostgreSQL。
"""
import asyncio
import hashlib
import json
import logging
import uuid
from pathlib import Path
from dotenv import load_dotenv

# 加载 .env 文件
load_dotenv()

logger = logging.getLogger(__name__)


class BatchIndexer:
    """批量索引器"""

    def __init__(
        self,
        workspace_root: str = "working/workspaces",
        tenant_id: str = "default-tenant",
    ):
        self.workspace_root = Path(workspace_root)
        self.tenant_id = tenant_id

    async def index_all(self) -> dict:
        """索引所有工作空间"""
        stats = {
            "workspaces": 0,
            "agent_configs": 0,
            "skill_configs": 0,
            "conversations": 0,
            "memory_docs": 0,
            "errors": [],
        }

        if not self.workspace_root.exists():
            logger.warning(f"工作空间根目录不存在: {self.workspace_root}")
            return stats

        # 遍历所有工作空间
        for workspace_dir in self.workspace_root.iterdir():
            if not workspace_dir.is_dir():
                continue

            logger.info(f"索引工作空间: {workspace_dir.name}")
            stats["workspaces"] += 1

            try:
                # 索引Agent配置
                stats["agent_configs"] += await self._index_agent_configs(workspace_dir)

                # 索引Skill配置
                stats["skill_configs"] += await self._index_skills(workspace_dir)

                # 索引对话
                stats["conversations"] += await self._index_conversations(workspace_dir)

                # 索引记忆文档
                stats["memory_docs"] += await self._index_memory_docs(workspace_dir)

            except Exception as e:
                error_msg = f"索引工作空间 {workspace_dir.name} 失败: {e}"
                stats["errors"].append(error_msg)
                logger.error(error_msg)

        logger.info(f"✅ 批量索引完成: {stats}")
        return stats

    async def _index_agent_configs(self, workspace_dir: Path) -> int:
        """索引Agent配置"""
        from copaw.db.models.storage_meta import AgentConfig
        from copaw.db.postgresql import get_database_manager
        from copaw.storage.key_builder import StorageKeyBuilder

        agent_json = workspace_dir / "agent.json"
        if not agent_json.exists():
            return 0

        with open(agent_json, "r", encoding="utf-8") as f:
            data = json.load(f)

        content_hash = self._compute_hash(agent_json)
        workspace_dir_name = workspace_dir.name

        key = StorageKeyBuilder.build(
            tenant_id=self.tenant_id,
            department_id=workspace_dir_name,
            category="workspace",
            resource_path="agent.json",
        )

        # 确保工作空间记录存在
        workspace_uuid = await self._ensure_workspace_exists(workspace_dir_name)
        
        db_manager = get_database_manager()
        async with db_manager.session() as session:
            config = AgentConfig(
                tenant_id=self.tenant_id,
                workspace_id=workspace_uuid,
                agent_id=data.get("id", workspace_dir_name),
                name=data.get("name", "Unknown"),
                description=data.get("description"),
                model_provider=data.get("model_provider"),
                model_name=data.get("model_name"),
                storage_key=key,
                content_hash=content_hash,
            )
            session.add(config)

        return 1

    async def _index_skills(self, workspace_dir: Path) -> int:
        """索引Skill配置（全局池 + 工作空间已分配）"""
        from copaw.db.models.storage_meta import SkillConfig
        from copaw.db.postgresql import get_database_manager

        workspace_uuid = await self._ensure_workspace_exists(workspace_dir.name)
        count = 0
        
        # 1. 索引全局 Skill 池（未分配）
        global_skill_pool = Path("working/skill_pool")
        if global_skill_pool.exists():
            for skill_dir in global_skill_pool.iterdir():
                if not skill_dir.is_dir():
                    continue
                    
                skill_json = skill_dir / "skill.json"
                if not skill_json.exists():
                    continue
                    
                with open(skill_json, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    
                db_manager = get_database_manager()
                async with db_manager.session() as session:
                    skill = SkillConfig(
                        tenant_id=self.tenant_id,
                        skill_name=data.get("name", skill_dir.name),
                        display_name=data.get("display_name"),
                        description=data.get("description"),
                        version=data.get("version", "1.0.0"),
                        source="global_pool",
                    )
                    session.add(skill)
                count += 1
        
        # 2. 索引工作空间下已分配到 Agent 的 Skill
        # 扫描所有 agent 目录
        agent_json = workspace_dir / "agent.json"
        if agent_json.exists():
            with open(agent_json, "r", encoding="utf-8") as f:
                agent_data = json.load(f)
            agent_id = agent_data.get("id", workspace_dir.name)
            
            # 检查 {agent_id}/skills 目录
            agent_skills_dir = workspace_dir / agent_id / "skills"
            if agent_skills_dir.exists():
                for skill_dir in agent_skills_dir.iterdir():
                    if not skill_dir.is_dir():
                        continue
                        
                    skill_json = skill_dir / "skill.json"
                    if not skill_json.exists():
                        continue
                        
                    with open(skill_json, "r", encoding="utf-8") as f:
                        data = json.load(f)
                    
                    # 验证数据格式
                    if not isinstance(data, dict):
                        continue
                        
                    db_manager = get_database_manager()
                    async with db_manager.session() as session:
                        skill = SkillConfig(
                            tenant_id=self.tenant_id,
                            workspace_id=workspace_uuid,
                            skill_name=data.get("name", skill_dir.name),
                            display_name=data.get("display_name"),
                            description=data.get("description"),
                            version=data.get("version", "1.0.0"),
                            source="agent_assigned",
                        )
                        session.add(skill)
                    count += 1

        return count

    async def _index_conversations(self, workspace_dir: Path) -> int:
        """索引对话"""
        from copaw.db.models.storage_meta import Conversation
        from copaw.db.postgresql import get_database_manager

        chats_json = workspace_dir / "chats.json"
        if not chats_json.exists():
            return 0

        with open(chats_json, "r", encoding="utf-8") as f:
            data = json.load(f)

        # 确保工作空间记录存在
        workspace_uuid = await self._ensure_workspace_exists(workspace_dir.name)

        # chats.json 格式: {chat_id: {title, messages, ...}}
        count = 0
        db_manager = get_database_manager()
        async with db_manager.session() as session:
            for chat_id, chat_data in data.items():
                conversation = Conversation(
                    tenant_id=self.tenant_id,
                    workspace_id=workspace_uuid,
                    chat_id=chat_id,
                    title=chat_data.get("title"),
                    message_count=len(chat_data.get("messages", [])),
                )
                session.add(conversation)
                count += 1


        return count

    async def _ensure_workspace_exists(self, workspace_name: str) -> uuid.UUID:
        """确保租户和工作空间记录存在，如果不存在则创建
        
        Args:
            workspace_name: 工作空间名称
            
        Returns:
            工作空间 UUID
        """
        from copaw.db.models.workspace import Workspace
        from copaw.db.models.tenant import Tenant
        from copaw.db.postgresql import get_database_manager
        from sqlalchemy import select
        
        db_manager = get_database_manager()
        async with db_manager.session() as session:
            # 1. 确保租户存在
            tenant_result = await session.execute(
                select(Tenant).where(Tenant.id == self.tenant_id)
            )
            tenant = tenant_result.scalar_one_or_none()
            
            if not tenant:
                # 创建默认租户
                tenant = Tenant(
                    id=self.tenant_id,
                    name=self.tenant_id,
                    is_active=True,
                )
                session.add(tenant)
                await session.flush()  # 立即获取 ID
            
            # 2. 查询工作空间是否存在
            ws_result = await session.execute(
                select(Workspace).where(
                    Workspace.name == workspace_name,
                    Workspace.tenant_id == self.tenant_id,
                )
            )
            workspace = ws_result.scalar_one_or_none()
            
            if workspace:
                return workspace.id
            
            # 3. 创建工作空间
            workspace = Workspace(
                tenant_id=self.tenant_id,
                name=workspace_name,
                description=f"Auto-created workspace: {workspace_name}",
            )
            session.add(workspace)
            await session.flush()  # 确保 ID 已生成
            # session 会自动 commit
            return workspace.id

    async def _index_memory_docs(self, workspace_dir: Path) -> int:
        """索引记忆文档"""
        from copaw.db.models.storage_meta import MemoryDocument
        from copaw.db.postgresql import get_database_manager

        memory_dir = workspace_dir / "memory"
        if not memory_dir.exists():
            return 0

        # 确保工作空间记录存在
        workspace_uuid = await self._ensure_workspace_exists(workspace_dir.name)

        count = 0
        for md_file in memory_dir.glob("*.md"):
            content_hash = self._compute_hash(md_file)

            db_manager = get_database_manager()
            async with db_manager.session() as session:
                doc = MemoryDocument(
                    tenant_id=self.tenant_id,
                    workspace_id=workspace_uuid,
                    doc_type="memory",
                    title=md_file.stem,
                    storage_key=f"{workspace_dir.name}/memory/{md_file.name}",
                    content_hash=content_hash,
                    file_size=md_file.stat().st_size,
                )
                session.add(doc)
    
            count += 1

        return count

    @staticmethod
    def _compute_hash(file_path: Path) -> str:
        """计算文件SHA-256哈希"""
        sha256 = hashlib.sha256()
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(8192), b""):
                sha256.update(chunk)
        return sha256.hexdigest()


async def main():
    """主函数"""
    import argparse
    from copaw.db.postgresql import get_database_manager

    parser = argparse.ArgumentParser(description="批量索引工具")
    parser.add_argument(
        "--workspace-root",
        default="working/workspaces",
        help="工作空间根目录",
    )
    parser.add_argument("--tenant-id", default="default-tenant", help="租户ID")

    args = parser.parse_args()

    # 初始化数据库连接
    print("正在连接数据库...")
    db_manager = get_database_manager()
    await db_manager.initialize()
    print("✅ 数据库连接成功")

    try:
        indexer = BatchIndexer(
            workspace_root=args.workspace_root,
            tenant_id=args.tenant_id,
        )

        stats = await indexer.index_all()

        print("\n=== 索引统计 ===")
        print(f"工作空间: {stats['workspaces']}")
        print(f"Agent配置: {stats['agent_configs']}")
        print(f"Skill配置: {stats['skill_configs']}")
        print(f"对话: {stats['conversations']}")
        print(f"记忆文档: {stats['memory_docs']}")

        if stats["errors"]:
            print(f"\n错误: {len(stats['errors'])}")
            for error in stats["errors"]:
                print(f"  - {error}")
    finally:
        await db_manager.close()
        print("\n✅ 数据库连接已关闭")


if __name__ == "__main__":
    asyncio.run(main())
