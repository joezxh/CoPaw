#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
运行 Alembic 数据库迁移的便捷脚本

用法:
    python run_migration.py              # 升级到最新版本
    python run_migration.py --downgrade  # 降级一个版本
    python run_migration.py --version    # 查看当前版本
"""
import argparse
import sys
from pathlib import Path

from dotenv import load_dotenv

# 加载 .env 文件
env_path = Path(__file__).parent / ".env"
load_dotenv(env_path, override=True)
print(f"✅ 已加载环境变量: {env_path}")

from alembic.config import Config
from alembic import command


def get_alembic_config():
    """获取 Alembic 配置"""
    alembic_ini = Path(__file__).parent / "alembic.ini"
    return Config(str(alembic_ini))


def upgrade():
    """升级到最新版本"""
    print("\n🚀 开始升级到最新版本...")
    config = get_alembic_config()
    command.upgrade(config, "head")
    print("✅ 升级完成！")


def downgrade():
    """降级一个版本"""
    print("\n⬇️  开始降级...")
    config = get_alembic_config()
    command.downgrade(config, "-1")
    print("✅ 降级完成！")


def current():
    """查看当前版本"""
    print("\n📋 当前数据库版本:")
    config = get_alembic_config()
    command.current(config)


def main():
    parser = argparse.ArgumentParser(description="运行数据库迁移")
    parser.add_argument(
        "--downgrade",
        action="store_true",
        help="降级一个版本",
    )
    parser.add_argument(
        "--version",
        action="store_true",
        help="查看当前版本",
    )
    
    args = parser.parse_args()
    
    try:
        if args.version:
            current()
        elif args.downgrade:
            downgrade()
        else:
            upgrade()
    except Exception as e:
        print(f"\n❌ 迁移失败: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
