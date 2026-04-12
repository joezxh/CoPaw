#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
迁移工具测试脚本
Test suite for migration tool
"""
import json
import os
import sys
import tempfile
import uuid
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime, timezone

# 添加项目根目录
PROJECT_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

import pytest
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

# 导入迁移工具
from scripts.migrate_personal_to_enterprise import PersonalToEnterpriseMigrator


class TestMigrator:
    """迁移工具测试类"""

    @pytest.fixture
    def mock_engine(self):
        """创建模拟数据库引擎"""
        engine = MagicMock()
        engine.connect.return_value.__enter__ = Mock(
            return_value=Mock(
                execute=Mock(
                    return_value=Mock(scalar=Mock(return_value="PostgreSQL 15.0"))
                )
            )
        )
        engine.connect.return_value.__exit__ = Mock(return_value=False)
        return engine

    @pytest.fixture
    def migrator(self, mock_engine):
        """创建迁移器实例"""
        with patch('scripts.migrate_personal_to_enterprise.create_engine', return_value=mock_engine):
            m = PersonalToEnterpriseMigrator(
                postgres_url="postgresql://test:test@localhost/test",
                dry_run=True,
            )
            m.engine = mock_engine
            m.Session = sessionmaker(bind=mock_engine)
            return m

    def test_initialization(self, migrator):
        """测试初始化"""
        assert migrator.dry_run is True
        assert migrator.skip_auth is False
        assert migrator.skip_agents is False
        assert migrator.stats["users_created"] == 0

    def test_verify_connection_success(self, migrator):
        """测试数据库连接验证 - 成功"""
        # 应该不抛出异常
        migrator._verify_connection()

    @patch('scripts.migrate_personal_to_enterprise.AUTH_FILE')
    def test_migrate_auth_no_file(self, mock_auth_file, migrator):
        """测试认证迁移 - 无auth.json文件"""
        mock_auth_file.exists.return_value = False
        migrator._migrate_authentication()
        # 应该跳过,不抛出异常

    @patch('scripts.migrate_personal_to_enterprise._load_auth_data')
    @patch('scripts.migrate_personal_to_enterprise.AUTH_FILE')
    def test_migrate_auth_no_user(self, mock_auth_file, mock_load_data, migrator):
        """测试认证迁移 - 未注册用户"""
        mock_auth_file.exists.return_value = True
        mock_load_data.return_value = {}
        migrator._migrate_authentication()
        # 应该跳过

    @patch('scripts.migrate_personal_to_enterprise._load_auth_data')
    @patch('scripts.migrate_personal_to_enterprise.AUTH_FILE')
    def test_migrate_auth_with_user(self, mock_auth_file, mock_load_data, migrator):
        """测试认证迁移 - 有注册用户"""
        mock_auth_file.exists.return_value = True
        mock_load_data.return_value = {
            "user": {
                "username": "testuser",
                "password_hash": "abc123",
                "password_salt": "salt456",
            }
        }
        
        # Mock session
        mock_session = MagicMock()
        mock_session.execute.return_value.fetchone.return_value = None
        migrator.Session = Mock(return_value=mock_session)
        
        # 执行迁移
        migrator._migrate_authentication()
        
        # 验证统计
        assert migrator.stats["users_created"] == 1
        mock_session.commit.assert_called_once()

    def test_find_agent_configs_empty(self, migrator):
        """测试查找Agent配置 - 无配置"""
        with patch('scripts.migrate_personal_to_enterprise.WORKSPACE_DIR') as mock_dir:
            mock_workspace = Mock()
            mock_workspace.exists.return_value = False
            mock_dir.__truediv__.return_value = mock_workspace
            
            configs = migrator._find_agent_configs()
            assert configs == []

    def test_print_summary(self, migrator, capsys):
        """测试打印统计信息"""
        migrator.stats = {
            "users_created": 1,
            "tenants_created": 1,
            "workspaces_created": 1,
            "agents_migrated": 2,
            "errors": 0,
        }
        migrator._print_summary()
        
        captured = capsys.readouterr()
        assert "创建租户: 1" in captured.out
        assert "创建用户: 1" in captured.out
        assert "迁移Agent: 2" in captured.out


class TestMigrationIntegration:
    """集成测试 (使用SQLite模拟PostgreSQL)"""

    @pytest.fixture
    def temp_db(self):
        """创建临时SQLite数据库用于测试"""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = Path(tmpdir) / "test.db"
            engine = create_engine(f"sqlite:///{db_path}")
            
            # 创建简化的表结构
            with engine.connect() as conn:
                conn.execute(text("""
                    CREATE TABLE sys_tenants (
                        id TEXT PRIMARY KEY,
                        domain TEXT,
                        name TEXT,
                        is_active INTEGER,
                        created_at TEXT,
                        updated_at TEXT
                    )
                """))
                conn.execute(text("""
                    CREATE TABLE sys_users (
                        id TEXT PRIMARY KEY,
                        tenant_id TEXT,
                        username TEXT,
                        email TEXT,
                        password_hash TEXT,
                        password_salt TEXT,
                        display_name TEXT,
                        status TEXT,
                        mfa_enabled INTEGER,
                        created_at TEXT,
                        updated_at TEXT
                    )
                """))
                conn.execute(text("""
                    CREATE TABLE sys_roles (
                        id TEXT PRIMARY KEY,
                        tenant_id TEXT,
                        name TEXT,
                        display_name TEXT,
                        is_system_role INTEGER,
                        created_at TEXT,
                        updated_at TEXT
                    )
                """))
                conn.execute(text("""
                    CREATE TABLE sys_user_roles (
                        user_id TEXT,
                        role_id TEXT,
                        assigned_at TEXT
                    )
                """))
                conn.execute(text("""
                    CREATE TABLE sys_workspaces (
                        id TEXT PRIMARY KEY,
                        tenant_id TEXT,
                        name TEXT,
                        description TEXT,
                        is_default INTEGER,
                        owner_id TEXT,
                        created_at TEXT,
                        updated_at TEXT
                    )
                """))
                conn.commit()
            
            yield str(db_path)

    def test_full_migration_dry_run(self, temp_db):
        """测试完整迁移流程 - 预览模式"""
        # 创建临时auth.json
        with tempfile.TemporaryDirectory() as tmpdir:
            auth_file = Path(tmpdir) / "auth.json"
            auth_data = {
                "user": {
                    "username": "testadmin",
                    "password_hash": "test_hash_123",
                    "password_salt": "test_salt_456",
                },
                "jwt_secret": "test_jwt_secret",
            }
            with open(auth_file, "w") as f:
                json.dump(auth_data, f)
            
            # Mock常量
            with patch('scripts.migrate_personal_to_enterprise.AUTH_FILE', auth_file):
                migrator = PersonalToEnterpriseMigrator(
                    postgres_url=f"sqlite:///{temp_db}",
                    dry_run=True,
                )
                
                # 执行迁移 (预览模式)
                success = migrator.run()
                
                assert success is True
                # 预览模式不创建数据
                assert migrator.stats["users_created"] == 0

    def test_full_migration_execute(self, temp_db):
        """测试完整迁移流程 - 执行模式"""
        # 创建临时auth.json
        with tempfile.TemporaryDirectory() as tmpdir:
            auth_file = Path(tmpdir) / "auth.json"
            auth_data = {
                "user": {
                    "username": "testadmin",
                    "password_hash": "test_hash_123",
                    "password_salt": "test_salt_456",
                },
                "jwt_secret": "test_jwt_secret",
            }
            with open(auth_file, "w") as f:
                json.dump(auth_data, f)
            
            # Mock常量
            with patch('scripts.migrate_personal_to_enterprise.AUTH_FILE', auth_file):
                migrator = PersonalToEnterpriseMigrator(
                    postgres_url=f"sqlite:///{temp_db}",
                    dry_run=False,
                )
                
                # 执行迁移
                success = migrator.run()
                
                assert success is True
                
                # 验证数据库中的数据
                engine = create_engine(f"sqlite:///{temp_db}")
                with engine.connect() as conn:
                    # 检查租户
                    result = conn.execute(text("SELECT COUNT(*) FROM sys_tenants"))
                    assert result.scalar() == 1
                    
                    # 检查用户
                    result = conn.execute(text("SELECT username FROM sys_users"))
                    users = [row[0] for row in result.fetchall()]
                    assert "testadmin" in users
                    
                    # 检查角色
                    result = conn.execute(text("SELECT name FROM sys_roles"))
                    roles = [row[0] for row in result.fetchall()]
                    assert "admin" in roles
                    
                    # 检查工作空间
                    result = conn.execute(text("SELECT COUNT(*) FROM sys_workspaces"))
                    assert result.scalar() == 1


def test_main_function():
    """测试main函数参数解析"""
    test_args = [
        "migrate_personal_to_enterprise.py",
        "--postgres-url", "postgresql://test:test@localhost/test",
        "--dry-run",
        "--skip-agents",
    ]
    
    with patch.object(sys, 'argv', test_args):
        with patch('scripts.migrate_personal_to_enterprise.PersonalToEnterpriseMigrator') as mock_migrator:
            mock_instance = Mock()
            mock_instance.run.return_value = True
            mock_migrator.return_value = mock_instance
            
            # 不应该抛出SystemExit
            with patch.object(sys, 'exit') as mock_exit:
                from scripts.migrate_personal_to_enterprise import main
                main()
                
                # 验证调用
                mock_migrator.assert_called_once()
                mock_exit.assert_called_once_with(0)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
