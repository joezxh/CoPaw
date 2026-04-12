#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
个人版到企业版数据迁移工具
Personal-to-Enterprise Data Migration Tool

将CoPaw个人版的SQLite数据库和JSON配置文件迁移到企业版PostgreSQL数据库。

功能:
1. 迁移用户认证数据 (auth.json → sys_users)
2. 迁移租户信息 (创建默认租户)
3. 迁移工作空间 (JSON → sys_workspaces)
4. 迁移Agent配置 (YAML/JSON → ai_agents)
5. 保留记忆数据 (SQLite保持独立存储)

使用方法:
    python migrate_personal_to_enterprise.py [--dry-run] [--skip-auth] [--skip-agents]
"""
from __future__ import annotations

import argparse
import json
import logging
import os
import sys
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

# 添加项目根目录到Python路径
PROJECT_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from sqlalchemy import create_engine, text, inspect
from sqlalchemy.orm import sessionmaker
from passlib.hash import bcrypt

# 导入个人版模块
from copaw.constant import SECRET_DIR, WORKING_DIR
from copaw.app.auth import _load_auth_data, AUTH_FILE
from copaw.security.secret_store import decrypt_dict_fields, AUTH_SECRET_FIELDS

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-8s | %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger("migrate_personal_to_enterprise")


class PersonalToEnterpriseMigrator:
    """个人版到企业版数据迁移器"""

    def __init__(
        self,
        postgres_url: str,
        dry_run: bool = False,
        skip_auth: bool = False,
        skip_agents: bool = False,
    ):
        """
        初始化迁移器

        Args:
            postgres_url: PostgreSQL连接字符串
            dry_run: 仅预览不执行
            skip_auth: 跳过认证数据迁移
            skip_agents: 跳过Agent数据迁移
        """
        self.postgres_url = postgres_url
        self.dry_run = dry_run
        self.skip_auth = skip_auth
        self.skip_agents = skip_agents

        # 企业版数据库连接
        self.engine = create_engine(postgres_url, echo=dry_run)
        self.Session = sessionmaker(bind=self.engine)

        # 统计数据
        self.stats = {
            "users_created": 0,
            "tenants_created": 0,
            "workspaces_created": 0,
            "agents_migrated": 0,
            "errors": 0,
        }

    def run(self) -> bool:
        """执行迁移"""
        logger.info("=" * 80)
        logger.info("CoPaw 个人版 → 企业版 数据迁移工具")
        logger.info("=" * 80)
        logger.info(f"模式: {'预览 (Dry Run)' if self.dry_run else '执行'}")
        logger.info(f"跳过认证: {'是' if self.skip_auth else '否'}")
        logger.info(f"跳过Agent: {'是' if self.skip_agents else '否'}")
        logger.info("=" * 80)

        try:
            # 1. 验证数据库连接
            self._verify_connection()

            # 2. 迁移用户认证数据
            if not self.skip_auth:
                self._migrate_authentication()

            # 3. 迁移租户和工作空间
            self._migrate_workspaces()

            # 4. 迁移Agent配置
            if not self.skip_agents:
                self._migrate_agents()

            # 5. 输出统计信息
            self._print_summary()

            return True

        except Exception as e:
            logger.error(f"迁移失败: {e}", exc_info=True)
            return False

    def _verify_connection(self):
        """验证PostgreSQL连接"""
        logger.info("\n📋 步骤 1/4: 验证数据库连接...")
        try:
            with self.engine.connect() as conn:
                result = conn.execute(text("SELECT version()"))
                version = result.scalar()
                logger.info(f"✅ PostgreSQL连接成功: {version[:50]}...")
        except Exception as e:
            logger.error(f"❌ 数据库连接失败: {e}")
            raise

    def _migrate_authentication(self):
        """迁移用户认证数据 (auth.json → sys_users)"""
        logger.info("\n📋 步骤 2/4: 迁移用户认证数据...")

        # 加载个人版认证数据
        if not AUTH_FILE.exists():
            logger.warning(f"⚠️  未找到认证文件: {AUTH_FILE}")
            logger.info("跳过认证数据迁移")
            return

        auth_data = _load_auth_data()
        if not auth_data.get("user"):
            logger.info("ℹ️  个人版未注册用户,跳过认证迁移")
            return

        user_data = auth_data["user"]
        username = user_data["username"]
        password_hash = user_data["password_hash"]
        password_salt = user_data["password_salt"]

        logger.info(f"发现用户: {username}")

        session = self.Session()
        try:
            # 1. 创建默认租户 (如果不存在)
            tenant_id = self._ensure_default_tenant(session)

            # 2. 创建用户记录
            user_id = self._create_user(
                session,
                username=username,
                password_hash=password_hash,
                password_salt=password_salt,
                tenant_id=tenant_id,
            )

            # 3. 分配管理员角色
            self._assign_admin_role(session, user_id, tenant_id)

            session.commit()
            logger.info(f"✅ 用户迁移成功: {username} (ID: {user_id})")

        except Exception as e:
            session.rollback()
            logger.error(f"❌ 用户迁移失败: {e}")
            self.stats["errors"] += 1
            raise
        finally:
            session.close()

    def _ensure_default_tenant(self, session) -> uuid.UUID:
        """确保默认租户存在"""
        # 检查租户是否已存在
        result = session.execute(
            text("SELECT id FROM sys_tenants WHERE domain = 'default'")
        )
        row = result.fetchone()

        if row:
            tenant_id = row[0]
            logger.info(f"默认租户已存在: {tenant_id}")
            return tenant_id

        # 创建新租户
        tenant_id = uuid.uuid4()
        if not self.dry_run:
            session.execute(
                text("""
                    INSERT INTO sys_tenants (id, domain, name, is_active, created_at, updated_at)
                    VALUES (:id, :domain, :name, :is_active, :created_at, :updated_at)
                """),
                {
                    "id": tenant_id,
                    "domain": "default",
                    "name": "Default Tenant",
                    "is_active": True,
                    "created_at": datetime.now(timezone.utc),
                    "updated_at": datetime.now(timezone.utc),
                },
            )
            logger.info(f"✅ 创建默认租户: {tenant_id}")
            self.stats["tenants_created"] += 1
        else:
            logger.info(f"[预览] 将创建默认租户: {tenant_id}")

        return tenant_id

    def _create_user(
        self,
        session,
        username: str,
        password_hash: str,
        password_salt: str,
        tenant_id: uuid.UUID,
    ) -> uuid.UUID:
        """创建用户记录"""
        # 检查用户是否已存在
        result = session.execute(
            text("SELECT id FROM sys_users WHERE username = :username"),
            {"username": username},
        )
        row = result.fetchone()

        if row:
            user_id = row[0]
            logger.info(f"用户已存在,跳过创建: {username} (ID: {user_id})")
            return user_id

        # 创建新用户
        user_id = uuid.uuid4()
        if not self.dry_run:
            session.execute(
                text("""
                    INSERT INTO sys_users (
                        id, tenant_id, username, email, password_hash, password_salt,
                        display_name, status, mfa_enabled, created_at, updated_at
                    ) VALUES (
                        :id, :tenant_id, :username, :email, :password_hash, :password_salt,
                        :display_name, :status, :mfa_enabled, :created_at, :updated_at
                    )
                """),
                {
                    "id": user_id,
                    "tenant_id": tenant_id,
                    "username": username,
                    "email": None,
                    "password_hash": password_hash,
                    "password_salt": password_salt,
                    "display_name": username,
                    "status": "active",
                    "mfa_enabled": False,
                    "created_at": datetime.now(timezone.utc),
                    "updated_at": datetime.now(timezone.utc),
                },
            )
            self.stats["users_created"] += 1
        else:
            logger.info(f"[预览] 将创建用户: {username}")

        return user_id

    def _assign_admin_role(
        self,
        session,
        user_id: uuid.UUID,
        tenant_id: uuid.UUID,
    ):
        """为用户分配管理员角色"""
        # 查找或创建admin角色
        result = session.execute(
            text("SELECT id FROM sys_roles WHERE name = 'admin' AND tenant_id = :tenant_id"),
            {"tenant_id": tenant_id},
        )
        row = result.fetchone()

        if row:
            role_id = row[0]
            logger.info(f"找到admin角色: {role_id}")
        else:
            # 创建admin角色
            role_id = uuid.uuid4()
            if not self.dry_run:
                session.execute(
                    text("""
                        INSERT INTO sys_roles (id, tenant_id, name, display_name, is_system_role, created_at, updated_at)
                        VALUES (:id, :tenant_id, :name, :display_name, :is_system_role, :created_at, :updated_at)
                    """),
                    {
                        "id": role_id,
                        "tenant_id": tenant_id,
                        "name": "admin",
                        "display_name": "System Administrator",
                        "is_system_role": True,
                        "created_at": datetime.now(timezone.utc),
                        "updated_at": datetime.now(timezone.utc),
                    },
                )
                logger.info(f"✅ 创建admin角色: {role_id}")
            else:
                logger.info(f"[预览] 将创建admin角色: {role_id}")

        # 分配角色
        if not self.dry_run:
            # 检查是否已分配
            result = session.execute(
                text("""
                    SELECT 1 FROM sys_user_roles 
                    WHERE user_id = :user_id AND role_id = :role_id
                """),
                {"user_id": user_id, "role_id": role_id},
            )
            if not result.fetchone():
                session.execute(
                    text("""
                        INSERT INTO sys_user_roles (user_id, role_id, assigned_at)
                        VALUES (:user_id, :role_id, :assigned_at)
                    """),
                    {
                        "user_id": user_id,
                        "role_id": role_id,
                        "assigned_at": datetime.now(timezone.utc),
                    },
                )
                logger.info(f"✅ 分配admin角色给用户: {user_id}")
        else:
            logger.info(f"[预览] 将分配admin角色给用户: {user_id}")

    def _migrate_workspaces(self):
        """迁移工作空间数据"""
        logger.info("\n📋 步骤 3/4: 迁移工作空间数据...")

        # 这里可以扩展为从JSON配置读取工作空间信息
        # 目前创建默认工作空间
        session = self.Session()
        try:
            # 获取租户ID
            result = session.execute(
                text("SELECT id FROM sys_tenants WHERE domain = 'default'")
            )
            row = result.fetchone()

            if not row:
                logger.warning("⚠️  未找到默认租户,跳过工作空间迁移")
                return

            tenant_id = row[0]

            # 获取用户ID
            result = session.execute(
                text("SELECT id FROM sys_users WHERE tenant_id = :tenant_id LIMIT 1"),
                {"tenant_id": tenant_id},
            )
            row = result.fetchone()

            if not row:
                logger.warning("⚠️  未找到用户,跳过工作空间迁移")
                return

            owner_id = row[0]

            # 创建默认工作空间
            result = session.execute(
                text("SELECT id FROM sys_workspaces WHERE tenant_id = :tenant_id AND is_default = true"),
                {"tenant_id": tenant_id},
            )
            if result.fetchone():
                logger.info("默认工作空间已存在,跳过创建")
                return

            workspace_id = uuid.uuid4()
            if not self.dry_run:
                session.execute(
                    text("""
                        INSERT INTO sys_workspaces (
                            id, tenant_id, name, description, is_default, owner_id,
                            created_at, updated_at
                        ) VALUES (
                            :id, :tenant_id, :name, :description, :is_default, :owner_id,
                            :created_at, :updated_at
                        )
                    """),
                    {
                        "id": workspace_id,
                        "tenant_id": tenant_id,
                        "name": "Default Workspace",
                        "description": "默认工作空间 (从个人版迁移)",
                        "is_default": True,
                        "owner_id": owner_id,
                        "created_at": datetime.now(timezone.utc),
                        "updated_at": datetime.now(timezone.utc),
                    },
                )
                logger.info(f"✅ 创建默认工作空间: {workspace_id}")
                self.stats["workspaces_created"] += 1
            else:
                logger.info(f"[预览] 将创建默认工作空间: {workspace_id}")

            session.commit()

        except Exception as e:
            session.rollback()
            logger.error(f"❌ 工作空间迁移失败: {e}")
            self.stats["errors"] += 1
            raise
        finally:
            session.close()

    def _migrate_agents(self):
        """迁移Agent配置数据"""
        logger.info("\n📝 步骤 4/4: 迁移Agent配置数据...")
        
        # 查找Agent配置文件
        agent_configs = self._find_agent_configs()

        if not agent_configs:
            logger.info("ℹ️  未找到Agent配置")
            return

        logger.info(f"发现 {len(agent_configs)} 个Agent配置")
        
        # 检查ai_agents表是否存在
        session = self.Session()
        try:
            inspector = inspect(self.engine)
            if "ai_agents" not in inspector.get_table_names():
                logger.warning("⚠️  ai_agents表不存在,Agent配置将保留在文件系统")
                logger.info("ℹ️  Agent配置位置:")
                for config_file in agent_configs:
                    logger.info(f"  - {config_file}")
                logger.info("💡 提示: 企业版启动后会自动读取这些配置文件")
                return
            
            # 表存在,执行迁移
            logger.info("✅ ai_agents表已存在,开始迁移...")
            
            # 获取工作空间ID映射
            result = session.execute(
                text("SELECT id, name FROM sys_workspaces")
            )
            workspaces = {row[1]: row[0] for row in result.fetchall()}
            
            for config_file in agent_configs:
                try:
                    workspace_name = config_file.parent.name
                    workspace_id = workspaces.get(workspace_name)
                    
                    if not workspace_id:
                        logger.warning(f"⚠️  未找到工作空间 '{workspace_name}',跳过")
                        continue
                    
                    self._migrate_single_agent(
                        session, 
                        config_file, 
                        uuid.UUID(str(workspace_id))
                    )
                except Exception as e:
                    logger.error(f"❌ Agent迁移失败 {config_file}: {e}")
                    self.stats["errors"] += 1
            
            session.commit()
            logger.info(f"✅ 成功迁移 {self.stats['agents_migrated']} 个Agent")
            
        except Exception as e:
            session.rollback()
            logger.error(f"❌ Agent迁移失败: {e}")
            self.stats["errors"] += 1
            raise
        finally:
            session.close()

    def _find_agent_configs(self) -> list[Path]:
        """查找Agent配置文件"""
        # Agent配置通常在 working/workspaces/ 目录下
        workspaces_dir = WORKING_DIR / "workspaces"
        if not workspaces_dir.exists():
            return []

        configs = []
        for workspace_dir in workspaces_dir.iterdir():
            if workspace_dir.is_dir():
                # 查找 agent.yaml 或 agent.json
                for config_name in ["agent.yaml", "agent.json", "config.yaml", "config.json"]:
                    config_file = workspace_dir / config_name
                    if config_file.exists():
                        configs.append(config_file)
                        break

        return configs

    def _migrate_single_agent(
        self,
        session,
        config_file: Path,
        workspace_id: uuid.UUID,
    ):
        """迁移单个Agent配置"""
        logger.info(f"处理Agent配置: {config_file}")

        # 读取配置文件
        if config_file.suffix == ".json":
            with open(config_file, "r", encoding="utf-8") as f:
                config = json.load(f)
        else:
            logger.warning(f"⚠️  跳过非JSON配置: {config_file}")
            return

        agent_id = uuid.uuid4()
        agent_name = config.get("name", config_file.parent.name)
        description = config.get("description", "")

        if not self.dry_run:
            # 插入Agent记录
            session.execute(
                text("""
                    INSERT INTO ai_agents (
                        id, workspace_id, name, description, config, status,
                        created_at, updated_at
                    ) VALUES (
                        :id, :workspace_id, :name, :description, :config, :status,
                        :created_at, :updated_at
                    )
                """),
                {
                    "id": agent_id,
                    "workspace_id": workspace_id,
                    "name": agent_name,
                    "description": description or f"从个人版迁移 (原路径: {config_file.parent.name})",
                    "config": json.dumps(config, ensure_ascii=False),
                    "status": "active",
                    "created_at": datetime.now(timezone.utc),
                    "updated_at": datetime.now(timezone.utc),
                },
            )
            logger.info(f"✅ 迁移Agent: {agent_name} (ID: {agent_id})")
            self.stats["agents_migrated"] += 1
        else:
            logger.info(f"[预览] 将迁移Agent: {agent_name}")

    def _print_summary(self):
        """打印迁移统计"""
        logger.info("\n" + "=" * 80)
        logger.info("📊 迁移统计")
        logger.info("=" * 80)
        logger.info(f"✅ 创建租户: {self.stats['tenants_created']}")
        logger.info(f"✅ 创建用户: {self.stats['users_created']}")
        logger.info(f"✅ 创建工作空间: {self.stats['workspaces_created']}")
        logger.info(f"✅ 迁移Agent: {self.stats['agents_migrated']}")
        logger.info(f"❌ 错误数: {self.stats['errors']}")
        logger.info("=" * 80)

        if self.dry_run:
            logger.info("⚠️  这是预览模式,未实际执行迁移")
            logger.info("💡 移除 --dry-run 参数以执行实际迁移")


def main():
    parser = argparse.ArgumentParser(
        description="CoPaw 个人版 → 企业版 数据迁移工具",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  # 预览迁移 (不执行)
  python migrate_personal_to_enterprise.py --dry-run

  # 执行完整迁移
  python migrate_personal_to_enterprise.py \\
    --postgres-url "postgresql://user:password@localhost:5432/copaw_enterprise"

  # 仅迁移认证数据
  python migrate_personal_to_enterprise.py --skip-agents

  # 跳过认证数据 (已手动创建用户)
  python migrate_personal_to_enterprise.py --skip-auth
        """,
    )

    parser.add_argument(
        "--postgres-url",
        required=True,
        help="PostgreSQL连接字符串 (例: postgresql://user:pass@localhost:5432/copaw)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="预览模式,不实际执行迁移",
    )
    parser.add_argument(
        "--skip-auth",
        action="store_true",
        help="跳过认证数据迁移",
    )
    parser.add_argument(
        "--skip-agents",
        action="store_true",
        help="跳过Agent配置迁移",
    )

    args = parser.parse_args()

    migrator = PersonalToEnterpriseMigrator(
        postgres_url=args.postgres_url,
        dry_run=args.dry_run,
        skip_auth=args.skip_auth,
        skip_agents=args.skip_agents,
    )

    success = migrator.run()
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
