#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
SQLite to PostgreSQL Migration Tool — SQLite到PostgreSQL迁移工具

将个人版SQLite数据迁移到企业版PostgreSQL。
"""
import asyncio
import json
import logging
import os
import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)


class SQLiteToPostgresMigrator:
    """SQLite到PostgreSQL数据迁移器"""

    def __init__(
        self,
        sqlite_db_path: str,
        pg_dsn: str,
        tenant_id: str = "default-tenant",
    ):
        self.sqlite_db_path = sqlite_db_path
        self.pg_dsn = pg_dsn
        self.tenant_id = tenant_id

    async def migrate(self) -> dict:
        """执行完整迁移"""
        stats = {
            "agents": 0,
            "skills": 0,
            "conversations": 0,
            "messages": 0,
            "errors": [],
        }

        # 1. 连接SQLite
        sqlite_conn = sqlite3.connect(self.sqlite_db_path)
        sqlite_conn.row_factory = sqlite3.Row

        try:
            # 2. 迁移Agent配置
            stats["agents"] = await self._migrate_agents(sqlite_conn)

            # 3. 迁移Skill配置
            stats["skills"] = await self._migrate_skills(sqlite_conn)

            # 4. 迁移对话
            stats["conversations"], stats["messages"] = await self._migrate_conversations(
                sqlite_conn
            )

            logger.info(f"✅ 迁移完成: {stats}")
            return stats

        except Exception as e:
            stats["errors"].append(str(e))
            logger.error(f"❌ 迁移失败: {e}")
            return stats
        finally:
            sqlite_conn.close()

    async def _migrate_agents(self, sqlite_conn) -> int:
        """迁移Agent配置"""
        from copaw.db.models.storage_meta import AgentConfig
        from copaw.db.session import async_session_maker

        cursor = sqlite_conn.cursor()
        cursor.execute("SELECT * FROM agents")
        agents = cursor.fetchall()

        count = 0
        async with async_session_maker() as session:
            for agent in agents:
                config = AgentConfig(
                    tenant_id=self.tenant_id,
                    agent_id=agent.get("id", ""),
                    name=agent.get("name", "Unknown"),
                    model_provider=agent.get("model_provider"),
                    model_name=agent.get("model_name"),
                    status="active",
                )
                session.add(config)
                count += 1

            await session.commit()

        logger.info(f"迁移了 {count} 个Agent配置")
        return count

    async def _migrate_skills(self, sqlite_conn) -> int:
        """迁移Skill配置"""
        # 简化实现：从 skill_pool 目录扫描
        skill_pool = Path("working/skill_pool")
        if not skill_pool.exists():
            return 0

        from copaw.db.models.storage_meta import SkillConfig
        from copaw.db.session import async_session_maker

        count = 0
        async with async_session_maker() as session:
            for skill_dir in skill_pool.iterdir():
                if not skill_dir.is_dir():
                    continue

                skill_json = skill_dir / "skill.json"
                if not skill_json.exists():
                    continue

                with open(skill_json, "r", encoding="utf-8") as f:
                    data = json.load(f)

                skill = SkillConfig(
                    tenant_id=self.tenant_id,
                    skill_name=data.get("name", skill_dir.name),
                    display_name=data.get("display_name"),
                    description=data.get("description"),
                    version=data.get("version", "1.0.0"),
                    source="local",
                )
                session.add(skill)
                count += 1

            await session.commit()

        logger.info(f"迁移了 {count} 个Skill配置")
        return count

    async def _migrate_conversations(self, sqlite_conn) -> tuple[int, int]:
        """迁移对话和消息"""
        from copaw.db.models.storage_meta import Conversation, ConversationMessage
        from copaw.db.session import async_session_maker

        cursor = sqlite_conn.cursor()
        cursor.execute("SELECT * FROM conversations")
        conversations = cursor.fetchall()

        conv_count = 0
        msg_count = 0

        async with async_session_maker() as session:
            for conv in conversations:
                conversation = Conversation(
                    tenant_id=self.tenant_id,
                    chat_id=conv.get("id", ""),
                    title=conv.get("title"),
                    message_count=conv.get("message_count", 0),
                )
                session.add(conversation)
                conv_count += 1

                # 迁移消息
                cursor.execute(
                    "SELECT * FROM messages WHERE conversation_id = ?",
                    (conv.get("id"),),
                )
                messages = cursor.fetchall()

                for msg in messages:
                    message = ConversationMessage(
                        tenant_id=self.tenant_id,
                        role=msg.get("role", "user"),
                        content=msg.get("content", ""),
                    )
                    session.add(message)
                    msg_count += 1

            await session.commit()

        logger.info(f"迁移了 {conv_count} 个对话, {msg_count} 条消息")
        return conv_count, msg_count


async def main():
    """主函数"""
    import argparse

    parser = argparse.ArgumentParser(description="SQLite到PostgreSQL迁移工具")
    parser.add_argument("--sqlite-db", required=True, help="SQLite数据库路径")
    parser.add_argument("--pg-dsn", required=True, help="PostgreSQL DSN")
    parser.add_argument("--tenant-id", default="default-tenant", help="租户ID")

    args = parser.parse_args()

    migrator = SQLiteToPostgresMigrator(
        sqlite_db_path=args.sqlite_db,
        pg_dsn=args.pg_dsn,
        tenant_id=args.tenant_id,
    )

    stats = await migrator.migrate()

    print("\n=== 迁移统计 ===")
    print(f"Agent配置: {stats['agents']}")
    print(f"Skill配置: {stats['skills']}")
    print(f"对话: {stats['conversations']}")
    print(f"消息: {stats['messages']}")

    if stats["errors"]:
        print(f"\n错误: {len(stats['errors'])}")
        for error in stats["errors"]:
            print(f"  - {error}")


if __name__ == "__main__":
    asyncio.run(main())
