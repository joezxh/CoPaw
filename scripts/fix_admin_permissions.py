#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
快速修复 admin 角色权限关联

用途：
当 admin 用户没有权限时，运行此脚本为 admin/sys_admin 角色添加所有权限
"""
import sys
import asyncio
from pathlib import Path

# 添加项目根目录到路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from dotenv import load_dotenv
load_dotenv(Path(__file__).parent.parent / ".env", override=True)

from sqlalchemy import select
from copaw.db.postgresql import async_engine
from copaw.db.models.permission import Permission
from copaw.db.models.role import Role, RolePermission


async def fix_admin_permissions():
    """修复 admin 角色的权限关联"""
    print("=" * 70)
    print("🔧 修复 Admin 角色权限关联")
    print("=" * 70)
    print()
    
    async with async_engine.begin() as conn:
        # 获取所有权限
        result = await conn.execute(select(Permission))
        all_permissions = result.scalars().all()
        print(f"✅ 找到 {len(all_permissions)} 个权限")
        
        # 查找 admin 或系统管理员角色
        result = await conn.execute(
            select(Role).where(
                (Role.code == 'admin') | 
                (Role.code == 'sys_admin') |
                (Role.name == '系统管理员') |
                (Role.name == 'Admin')
            )
        )
        admin_roles = result.scalars().all()
        
        if not admin_roles:
            print("❌ 未找到 admin 角色！")
            print("请先执行: python scripts/init_permissions.py")
            return False
        
        print(f"✅ 找到 {len(admin_roles)} 个 admin 相关角色:")
        for role in admin_roles:
            print(f"   - {role.name} (code: {role.code}, id: {role.id})")
        print()
        
        # 为每个 admin 角色添加权限
        for role in admin_roles:
            print(f"📝 处理角色: {role.name}")
            
            # 获取该角色已有的权限
            result = await conn.execute(
                select(RolePermission).where(RolePermission.role_id == role.id)
            )
            existing_perms = result.scalars().all()
            existing_perm_ids = {rp.permission_id for rp in existing_perms}
            
            print(f"   已有权限: {len(existing_perm_ids)}")
            
            # 添加缺失的权限
            added_count = 0
            for perm in all_permissions:
                if perm.id not in existing_perm_ids:
                    role_perm = RolePermission(
                        role_id=role.id,
                        permission_id=perm.id
                    )
                    conn.add(role_perm)
                    added_count += 1
            
            print(f"   新增权限: {added_count}")
            print(f"   总权限数: {len(existing_perm_ids) + added_count}")
            print()
        
        # 提交事务
        print("💾 保存更改...")
        # conn.commit() 会自动处理
        
        print()
        print("=" * 70)
        print("✅ 修复完成！")
        print("=" * 70)
        print()
        print("📋 验证步骤:")
        print("  1. 刷新浏览器页面")
        print("  2. 检查权限接口: /api/v1/auth/permissions")
        print("  3. 应该能看到所有权限")
        print()
        
        return True


if __name__ == "__main__":
    try:
        success = asyncio.run(fix_admin_permissions())
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"❌ 错误: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
