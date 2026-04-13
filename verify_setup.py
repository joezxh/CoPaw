#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
验证权限系统配置
"""
import sys
from pathlib import Path

def check_file_exists(filepath: str, description: str) -> bool:
    """检查文件是否存在"""
    path = Path(filepath)
    if path.exists():
        print(f"✅ {description}: {filepath}")
        return True
    else:
        print(f"❌ {description}: {filepath} (不存在)")
        return False

def check_file_content(filepath: str, keyword: str, description: str) -> bool:
    """检查文件内容是否包含关键字"""
    try:
        path = Path(filepath)
        content = path.read_text(encoding='utf-8')
        if keyword in content:
            print(f"✅ {description}")
            return True
        else:
            print(f"❌ {description} (未找到 '{keyword}')")
            return False
    except Exception as e:
        print(f"❌ {description} (错误: {e})")
        return False

def main():
    print("=" * 70)
    print("🔍 CoPaw 权限系统配置验证")
    print("=" * 70)
    print()
    
    all_ok = True
    
    # 1. 检查后端文件
    print("📦 后端文件检查:")
    print("-" * 70)
    all_ok &= check_file_exists(
        "src/copaw/db/models/permission.py",
        "Permission 模型"
    )
    all_ok &= check_file_exists(
        "alembic/versions/009_permission_enhancement.py",
        "Alembic 迁移 009"
    )
    all_ok &= check_file_exists(
        "scripts/init_permissions.py",
        "权限初始化脚本"
    )
    all_ok &= check_file_exists(
        "src/copaw/app/routers/permission_mgmt.py",
        "权限管理 API"
    )
    print()
    
    # 2. 检查前端文件
    print("🎨 前端文件检查:")
    print("-" * 70)
    all_ok &= check_file_exists(
        "console/src/hooks/usePermissions.ts",
        "usePermissions Hook"
    )
    all_ok &= check_file_exists(
        "console/src/components/PermissionGuard.tsx",
        "PermissionGuard 组件"
    )
    all_ok &= check_file_exists(
        "console/src/layouts/default/index.tsx",
        "Default Layout"
    )
    all_ok &= check_file_exists(
        "console/src/layouts/default/Sidebar.tsx",
        "Default Sidebar"
    )
    all_ok &= check_file_exists(
        "console/src/layouts/default/Header.tsx",
        "Default Header"
    )
    all_ok &= check_file_exists(
        "console/src/layouts/default/constants.tsx",
        "菜单配置"
    )
    print()
    
    # 3. 检查布局切换
    print("🔄 布局配置检查:")
    print("-" * 70)
    all_ok &= check_file_content(
        "console/src/App.tsx",
        "import DefaultLayout from",
        "App.tsx 导入 DefaultLayout"
    )
    all_ok &= check_file_content(
        "console/src/App.tsx",
        "<DefaultLayout />",
        "App.tsx 使用 DefaultLayout"
    )
    print()
    
    # 4. 检查数据库
    print("📊 数据库检查:")
    print("-" * 70)
    print("⚠️  请手动执行以下命令验证:")
    print("   python run_migration.py              # 数据库迁移")
    print("   python scripts/init_permissions.py   # 初始化权限")
    print("   python verify_permissions.py         # 验证权限数据")
    print()
    
    # 总结
    print("=" * 70)
    if all_ok:
        print("✅ 所有文件检查通过！")
        print()
        print("📋 下一步操作:")
        print("  1. 修复编译错误 (详见 docs/permission-integration-fixes.md)")
        print("  2. 执行数据库迁移: python run_migration.py")
        print("  3. 初始化权限数据: python scripts/init_permissions.py")
        print("  4. 启动前端: cd console && npm run dev")
        print("  5. 测试权限功能")
    else:
        print("❌ 部分文件缺失，请检查上述错误")
    print("=" * 70)
    
    return 0 if all_ok else 1

if __name__ == "__main__":
    sys.exit(main())
