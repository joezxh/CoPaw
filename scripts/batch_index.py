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
from pathlib import Path
from typing import Optional

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
        from copaw.db.session import async_session_maker
        from copaw.storage.key_builder import StorageKeyBuilder

        agent_json = workspace_dir / "agent.json"
        if not agent_json.exists():
            return 0

        with open(agent_json, "r", encoding="utf-8") as f:
            data = json.load(f)

        content_hash = self._compute_hash(agent_json)
        workspace_id = workspace_dir.name

        key = StorageKeyBuilder.build(
            tenant_id=self.tenant_id,
            workspace_id=workspace_id,
            category="workspace",
            resource_path="agent.json",
        )

        async with async_session_maker() as session:
            config = AgentConfig(
                tenant_id=self.tenant_id,
                workspace_id=workspace_id,
                agent_id=data.get("id", workspace_id),
                name=data.get("name", "Unknown"),
                description=data.get("description"),
                model_provider=data.get("model_provider"),
                model_name=data.get("model_name"),
                storage_key=key,
                content_hash=content_hash,
            )
            session.add(config)
            await session.commit()

        return 1

    async def _index_skills(self, workspace_dir: Path) -> int:
        """索引Skill配置"""
        from copaw.db.models.storage_meta import SkillConfig
        from copaw.db.session import async_session_maker

        skill_pool = workspace_dir / "skill_pool"
        if not skill_pool.exists():
            return 0

        count = 0
        for skill_dir in skill_pool.iterdir():
            if not skill_dir.is_dir():
                continue

            skill_json = skill_dir / "skill.json"
            if not skill_json.exists():
                continue

            with open(skill_json, "r", encoding="utf-8") as f:
                data = json.load(f)

            from copaw.db.session import async_session_maker

            async with async_session_maker() as session:
                skill = SkillConfig(
                    tenant_id=self.tenant_id,
                    workspace_id=workspace_dir.name,
                    skill_name=data.get("name", skill_dir.name),
                    display_name=data.get("display_name"),
                    description=data.get("description"),
                    version=data.get("version", "1.0.0"),
                    source="local",
                )
                session.add(skill)
                await session.commit()

            count += 1

        return count

    async def _index_conversations(self, workspace_dir: Path) -> int:
        """索引对话"""
        from copaw.db.models.storage_meta import Conversation
        from copaw.db.session import async_session_maker

        chats_json = workspace_dir / "chats.json"
        if not chats_json.exists():
            return 0

        with open(chats_json, "r", encoding="utf-8") as f:
            data = json.load(f)

        # chats.json 格式: {chat_id: {title, messages, ...}}
        count = 0
        async with async_session_maker() as session:
            for chat_id, chat_data in data.items():
                conversation = Conversation(
                    tenant_id=self.tenant_id,
                    workspace_id=workspace_dir.name,
                    chat_id=chat_id,
                    title=chat_data.get("title"),
                    message_count=len(chat_data.get("messages", [])),
                )
                session.add(conversation)
                count += 1

            await session.commit()

        return count

    async def _index_memory_docs(self, workspace_dir: Path) -> int:
        """索引记忆文档"""
        from copaw.db.models.storage_meta import MemoryDocument
        from copaw.db.session import async_session_maker

        memory_dir = workspace_dir / "memory"
        if not memory_dir.exists():
            return 0

        count = 0
        for md_file in memory_dir.glob("*.md"):
            content_hash = self._compute_hash(md_file)

            async with async_session_maker() as session:
                doc = MemoryDocument(
                    tenant_id=self.tenant_id,
                    workspace_id=workspace_dir.name,
                    doc_type="memory",
                    title=md_file.stem,
                    storage_key=f"{workspace_dir.name}/memory/{md_file.name}",
                    content_hash=content_hash,
                    file_size=md_file.stat().st_size,
                )
                session.add(doc)
                await session.commit()

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

    parser = argparse.ArgumentParser(description="批量索引工具")
    parser.add_argument(
        "--workspace-root",
        default="working/workspaces",
        help="工作空间根目录",
    )
    parser.add_argument("--tenant-id", default="default-tenant", help="租户ID")

    args = parser.parse_args()

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


if __name__ == "__main__":
    asyncio.run(main())
