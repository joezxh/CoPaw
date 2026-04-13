#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
权限系统初始化脚本

功能：
1. 初始化默认权限数据（permission_code 规范）
2. 创建默认角色
3. 为角色分配权限

用法:
    python scripts/init_permissions.py --tenant-id acme-corp
"""
import asyncio
import logging
from typing import List, Dict

from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)


# ============================================================================
# 默认权限数据
# ============================================================================

DEFAULT_PERMISSIONS: List[Dict] = [
    # ========== Agent 相关权限 ==========
    {
        "permission_code": "agent:config:read",
        "resource": "agent",
        "action": "read",
        "resource_path": "/agent-config",
        "permission_type": "menu",
        "description": "查看 Agent 配置",
        "icon": "SparkModifyLine",
        "sort_order": 1,
    },
    {
        "permission_code": "agent:config:write",
        "resource": "agent",
        "action": "write",
        "resource_path": "/agent-config",
        "permission_type": "api",
        "description": "修改 Agent 配置",
        "sort_order": 2,
    },
    {
        "permission_code": "agent:skill:read",
        "resource": "skill",
        "action": "read",
        "resource_path": "/skills",
        "permission_type": "menu",
        "description": "查看 Agent 技能",
        "icon": "SparkMagicWandLine",
        "sort_order": 3,
    },
    {
        "permission_code": "agent:skill:write",
        "resource": "skill",
        "action": "write",
        "permission_type": "api",
        "description": "管理 Agent 技能",
        "sort_order": 4,
    },
    {
        "permission_code": "agent:skill:execute",
        "resource": "skill",
        "action": "execute",
        "permission_type": "button",
        "description": "执行 Agent 技能",
        "sort_order": 5,
    },
    
    # ========== 通道相关权限 ==========
    {
        "permission_code": "channel:read",
        "resource": "channel",
        "action": "read",
        "resource_path": "/channels",
        "permission_type": "menu",
        "description": "查看通道列表",
        "icon": "SparkWifiLine",
        "sort_order": 10,
    },
    {
        "permission_code": "channel:write",
        "resource": "channel",
        "action": "write",
        "permission_type": "api",
        "description": "创建/修改通道",
        "sort_order": 11,
    },
    {
        "permission_code": "channel:manage",
        "resource": "channel",
        "action": "manage",
        "permission_type": "api",
        "description": "管理通道（启用/禁用/删除）",
        "sort_order": 12,
    },
    
    # ========== 会话相关权限 ==========
    {
        "permission_code": "session:read",
        "resource": "session",
        "action": "read",
        "resource_path": "/sessions",
        "permission_type": "menu",
        "description": "查看会话列表",
        "icon": "SparkUserGroupLine",
        "sort_order": 20,
    },
    {
        "permission_code": "session:write",
        "resource": "session",
        "action": "write",
        "permission_type": "api",
        "description": "创建/修改会话",
        "sort_order": 21,
    },
    {
        "permission_code": "session:delete",
        "resource": "session",
        "action": "delete",
        "permission_type": "api",
        "description": "删除会话",
        "sort_order": 22,
    },
    
    # ========== 定时任务相关权限 ==========
    {
        "permission_code": "cronjob:read",
        "resource": "cronjob",
        "action": "read",
        "resource_path": "/cron-jobs",
        "permission_type": "menu",
        "description": "查看定时任务",
        "icon": "SparkDateLine",
        "sort_order": 30,
    },
    {
        "permission_code": "cronjob:write",
        "resource": "cronjob",
        "action": "write",
        "permission_type": "api",
        "description": "创建/修改定时任务",
        "sort_order": 31,
    },
    
    # ========== 心跳检测相关权限 ==========
    {
        "permission_code": "heartbeat:read",
        "resource": "heartbeat",
        "action": "read",
        "resource_path": "/heartbeat",
        "permission_type": "menu",
        "description": "查看心跳状态",
        "icon": "SparkVoiceChat01Line",
        "sort_order": 40,
    },
    
    # ========== 工作空间相关权限 ==========
    {
        "permission_code": "workspace:read",
        "resource": "workspace",
        "action": "read",
        "resource_path": "/workspace",
        "permission_type": "menu",
        "description": "查看工作空间",
        "icon": "SparkLocalFileLine",
        "sort_order": 50,
    },
    {
        "permission_code": "workspace:write",
        "resource": "workspace",
        "action": "write",
        "permission_type": "api",
        "description": "管理工作空间",
        "sort_order": 51,
    },
    
    # ========== 技能池相关权限 ==========
    {
        "permission_code": "skill:pool:read",
        "resource": "skill",
        "action": "read",
        "resource_path": "/skill-pool",
        "permission_type": "menu",
        "description": "查看技能池",
        "icon": "SparkOtherLine",
        "sort_order": 60,
    },
    {
        "permission_code": "skill:pool:write",
        "resource": "skill",
        "action": "write",
        "permission_type": "api",
        "description": "管理技能池",
        "sort_order": 61,
    },
    
    # ========== 工具相关权限 ==========
    {
        "permission_code": "tool:read",
        "resource": "tool",
        "action": "read",
        "resource_path": "/tools",
        "permission_type": "menu",
        "description": "查看工具列表",
        "icon": "SparkToolLine",
        "sort_order": 70,
    },
    {
        "permission_code": "tool:write",
        "resource": "tool",
        "action": "write",
        "permission_type": "api",
        "description": "管理工具",
        "sort_order": 71,
    },
    
    # ========== MCP 相关权限 ==========
    {
        "permission_code": "mcp:read",
        "resource": "mcp",
        "action": "read",
        "resource_path": "/mcp",
        "permission_type": "menu",
        "description": "查看 MCP 服务",
        "icon": "SparkMcpMcpLine",
        "sort_order": 80,
    },
    {
        "permission_code": "mcp:write",
        "resource": "mcp",
        "action": "write",
        "permission_type": "api",
        "description": "管理 MCP 服务",
        "sort_order": 81,
    },
    
    # ========== 模型相关权限 ==========
    {
        "permission_code": "model:read",
        "resource": "model",
        "action": "read",
        "resource_path": "/models",
        "permission_type": "menu",
        "description": "查看模型列表",
        "icon": "SparkModePlazaLine",
        "sort_order": 90,
    },
    {
        "permission_code": "model:write",
        "resource": "model",
        "action": "write",
        "permission_type": "api",
        "description": "管理模型",
        "sort_order": 91,
    },
    {
        "permission_code": "model:deploy",
        "resource": "model",
        "action": "deploy",
        "permission_type": "api",
        "description": "部署模型",
        "sort_order": 92,
    },
    
    # ========== 环境相关权限 ==========
    {
        "permission_code": "environment:read",
        "resource": "environment",
        "action": "read",
        "resource_path": "/environments",
        "permission_type": "menu",
        "description": "查看环境配置",
        "icon": "SparkInternetLine",
        "sort_order": 100,
    },
    {
        "permission_code": "environment:write",
        "resource": "environment",
        "action": "write",
        "permission_type": "api",
        "description": "管理环境配置",
        "sort_order": 101,
    },
    
    # ========== 安全相关权限 ==========
    {
        "permission_code": "security:read",
        "resource": "security",
        "action": "read",
        "resource_path": "/security",
        "permission_type": "menu",
        "description": "查看安全设置",
        "icon": "SparkBrowseLine",
        "sort_order": 110,
    },
    {
        "permission_code": "security:write",
        "resource": "security",
        "action": "write",
        "permission_type": "api",
        "description": "管理安全设置",
        "sort_order": 111,
    },
    
    # ========== Token 使用相关权限 ==========
    {
        "permission_code": "token:usage:read",
        "resource": "token",
        "action": "read",
        "resource_path": "/token-usage",
        "permission_type": "menu",
        "description": "查看 Token 使用情况",
        "icon": "SparkDataLine",
        "sort_order": 120,
    },
    
    # ========== 语音转写相关权限 ==========
    {
        "permission_code": "voice:transcription:read",
        "resource": "voice",
        "action": "read",
        "resource_path": "/voice-transcription",
        "permission_type": "menu",
        "description": "查看语音转写",
        "icon": "SparkMicLine",
        "sort_order": 130,
    },
    
    # ========== 用户管理权限 ==========
    {
        "permission_code": "user:read",
        "resource": "user",
        "action": "read",
        "resource_path": "/enterprise/users",
        "permission_type": "menu",
        "description": "查看用户列表",
        "icon": "SparkSearchUserLine",
        "sort_order": 200,
    },
    {
        "permission_code": "user:write",
        "resource": "user",
        "action": "write",
        "permission_type": "api",
        "description": "创建/修改用户",
        "sort_order": 201,
    },
    {
        "permission_code": "user:manage",
        "resource": "user",
        "action": "manage",
        "permission_type": "api",
        "description": "管理用户（启用/禁用/删除）",
        "sort_order": 202,
    },
    
    # ========== 角色权限管理 ==========
    {
        "permission_code": "role:read",
        "resource": "role",
        "action": "read",
        "resource_path": "/enterprise/permissions",
        "permission_type": "menu",
        "description": "查看角色列表",
        "icon": "SparkModifyLine",
        "sort_order": 210,
    },
    {
        "permission_code": "role:write",
        "resource": "role",
        "action": "write",
        "permission_type": "api",
        "description": "创建/修改角色",
        "sort_order": 211,
    },
    {
        "permission_code": "role:manage",
        "resource": "role",
        "action": "manage",
        "permission_type": "api",
        "description": "管理角色（删除/分配权限）",
        "sort_order": 212,
    },
    
    # ========== 用户组管理 ==========
    {
        "permission_code": "group:read",
        "resource": "group",
        "action": "read",
        "resource_path": "/enterprise/groups",
        "permission_type": "menu",
        "description": "查看用户组",
        "icon": "SparkUserGroupLine",
        "sort_order": 220,
    },
    {
        "permission_code": "group:write",
        "resource": "group",
        "action": "write",
        "permission_type": "api",
        "description": "管理用户组",
        "sort_order": 221,
    },
    
    # ========== 审计日志权限 ==========
    {
        "permission_code": "audit:log:read",
        "resource": "audit",
        "action": "read",
        "resource_path": "/enterprise/audit",
        "permission_type": "menu",
        "description": "查看审计日志",
        "icon": "SparkBrowseLine",
        "sort_order": 300,
    },
    {
        "permission_code": "audit:log:export",
        "resource": "audit",
        "action": "export",
        "permission_type": "button",
        "description": "导出审计日志",
        "sort_order": 301,
    },
    
    # ========== DLP 规则权限 ==========
    {
        "permission_code": "dlp:rule:read",
        "resource": "dlp",
        "action": "read",
        "resource_path": "/enterprise/dlp-rules",
        "permission_type": "menu",
        "description": "查看 DLP 规则",
        "icon": "SparkBrowseLine",
        "sort_order": 310,
    },
    {
        "permission_code": "dlp:rule:write",
        "resource": "dlp",
        "action": "write",
        "permission_type": "api",
        "description": "管理 DLP 规则",
        "sort_order": 311,
    },
    {
        "permission_code": "dlp:rule:execute",
        "resource": "dlp",
        "action": "execute",
        "permission_type": "api",
        "description": "执行 DLP 检查",
        "sort_order": 312,
    },
    
    # ========== 告警规则权限 ==========
    {
        "permission_code": "alert:rule:read",
        "resource": "alert",
        "action": "read",
        "resource_path": "/enterprise/alert-rules",
        "permission_type": "menu",
        "description": "查看告警规则",
        "icon": "SparkWifiLine",
        "sort_order": 320,
    },
    {
        "permission_code": "alert:rule:write",
        "resource": "alert",
        "action": "write",
        "permission_type": "api",
        "description": "管理告警规则",
        "sort_order": 321,
    },
    
    # ========== Dify 连接器权限 ==========
    {
        "permission_code": "dify:connector:read",
        "resource": "dify",
        "action": "read",
        "resource_path": "/enterprise/dify-connectors",
        "permission_type": "menu",
        "description": "查看 Dify 连接器",
        "icon": "SparkDataLine",
        "sort_order": 330,
    },
    {
        "permission_code": "dify:connector:write",
        "resource": "dify",
        "action": "write",
        "permission_type": "api",
        "description": "管理 Dify 连接器",
        "sort_order": 331,
    },
]


# ============================================================================
# 默认角色数据
# ============================================================================

DEFAULT_ROLES: List[Dict] = [
    {
        "name": "系统管理员",
        "code": "sys_admin",
        "level": 0,
        "description": "拥有所有权限的系统管理员",
        "is_system_role": True,
        "permissions": ["*"],  # 所有权限
    },
    {
        "name": "普通用户",
        "code": "user",
        "level": 1,
        "description": "基础用户权限",
        "is_system_role": True,
        "permissions": [
            "agent:config:read",
            "agent:skill:read",
            "agent:skill:execute",
            "channel:read",
            "session:read",
            "session:write",
            "cronjob:read",
            "heartbeat:read",
            "workspace:read",
            "skill:pool:read",
            "tool:read",
            "mcp:read",
            "model:read",
            "environment:read",
            "token:usage:read",
            "voice:transcription:read",
        ],
    },
    {
        "name": "Agent 管理员",
        "code": "agent_admin",
        "level": 1,
        "description": "管理 Agent 配置和技能",
        "is_system_role": True,
        "permissions": [
            "agent:config:read",
            "agent:config:write",
            "agent:skill:read",
            "agent:skill:write",
            "agent:skill:execute",
            "workspace:read",
            "workspace:write",
            "skill:pool:read",
            "skill:pool:write",
            "tool:read",
            "tool:write",
            "mcp:read",
            "mcp:write",
            "model:read",
        ],
    },
    {
        "name": "安全管理员",
        "code": "security_admin",
        "level": 1,
        "description": "管理安全和审计",
        "is_system_role": True,
        "permissions": [
            "security:read",
            "security:write",
            "audit:log:read",
            "audit:log:export",
            "dlp:rule:read",
            "dlp:rule:write",
            "dlp:rule:execute",
            "alert:rule:read",
            "alert:rule:write",
        ],
    },
    {
        "name": "用户管理员",
        "code": "user_admin",
        "level": 1,
        "description": "管理用户和角色",
        "is_system_role": True,
        "permissions": [
            "user:read",
            "user:write",
            "user:manage",
            "role:read",
            "role:write",
            "role:manage",
            "group:read",
            "group:write",
        ],
    },
]


# ============================================================================
# 初始化函数
# ============================================================================

async def init_permissions(tenant_id: str = "default-tenant"):
    """初始化权限和角色数据"""
    from copaw.db.postgresql import get_database_manager
    from copaw.db.models.permission import Permission
    from copaw.db.models.role import Role, RolePermission
    from sqlalchemy import select
    
    db_manager = get_database_manager()
    
    async with db_manager.session() as session:
        # 1. 初始化权限
        logger.info(f"开始初始化 {len(DEFAULT_PERMISSIONS)} 个权限...")
        
        for perm_data in DEFAULT_PERMISSIONS:
            # 检查是否已存在
            existing = await session.execute(
                select(Permission).where(
                    Permission.permission_code == perm_data["permission_code"],
                    Permission.tenant_id == tenant_id,
                )
            )
            
            if existing.scalar_one_or_none():
                logger.debug(f"权限已存在: {perm_data['permission_code']}")
                continue
            
            # 创建权限
            permission = Permission(
                tenant_id=tenant_id,
                permission_code=perm_data["permission_code"],
                resource=perm_data["resource"],
                action=perm_data["action"],
                resource_path=perm_data.get("resource_path"),
                permission_type=perm_data.get("permission_type", "menu"),
                description=perm_data.get("description"),
                icon=perm_data.get("icon"),
                sort_order=perm_data.get("sort_order", 0),
                is_visible=True,
            )
            session.add(permission)
        
        await session.flush()
        logger.info(f"✅ 权限初始化完成")
        
        # 2. 初始化角色
        logger.info(f"开始初始化 {len(DEFAULT_ROLES)} 个角色...")
        
        for role_data in DEFAULT_ROLES:
            # 检查是否已存在
            existing = await session.execute(
                select(Role).where(
                    Role.name == role_data["name"],
                    Role.tenant_id == tenant_id,
                )
            )
            
            if existing.scalar_one_or_none():
                logger.debug(f"角色已存在: {role_data['name']}")
                continue
            
            # 创建角色
            role = Role(
                tenant_id=tenant_id,
                name=role_data["name"],
                description=role_data.get("description"),
                level=role_data.get("level", 0),
                is_system_role=role_data.get("is_system_role", False),
            )
            session.add(role)
            await session.flush()
            
            # 3. 为角色分配权限
            permission_codes = role_data.get("permissions", [])
            
            if "*" in permission_codes:
                # 分配所有权限
                all_perms = await session.execute(
                    select(Permission).where(
                        Permission.tenant_id == tenant_id,
                    )
                )
                permissions = all_perms.scalars().all()
            else:
                # 分配指定权限
                perms_result = await session.execute(
                    select(Permission).where(
                        Permission.permission_code.in_(permission_codes),
                        Permission.tenant_id == tenant_id,
                    )
                )
                permissions = perms_result.scalars().all()
            
            # 创建角色权限关联
            for perm in permissions:
                role_perm = RolePermission(
                    tenant_id=tenant_id,
                    role_id=role.id,
                    permission_id=perm.id,
                )
                session.add(role_perm)
            
            logger.info(f"✅ 角色 '{role.name}' 已创建，分配 {len(permissions)} 个权限")
        
        # 提交事务
        await session.commit()
        logger.info("✅ 权限系统初始化完成！")


async def main():
    """主函数"""
    import argparse
    
    parser = argparse.ArgumentParser(description="初始化权限系统")
    parser.add_argument(
        "--tenant-id",
        default="default-tenant",
        help="租户ID（默认: default-tenant）",
    )
    
    args = parser.parse_args()
    
    # 初始化数据库连接
    print("=" * 60)
    print("🚀 开始初始化权限系统")
    print("=" * 60)
    print(f"📋 租户ID: {args.tenant_id}")
    print()
    
    from copaw.db.postgresql import get_database_manager
    
    db_manager = get_database_manager()
    await db_manager.initialize()
    print("✅ 数据库连接成功")
    print()
    
    try:
        await init_permissions(tenant_id=args.tenant_id)
        print()
        print("=" * 60)
        print("✅ 权限系统初始化完成！")
        print("=" * 60)
    except Exception as e:
        print()
        print("=" * 60)
        print(f"❌ 权限初始化失败: {e}")
        print("=" * 60)
        raise
    finally:
        await db_manager.close()
        print("\n🔌 数据库连接已关闭")


if __name__ == "__main__":
    import logging
    logging.basicConfig(level=logging.INFO)
    
    asyncio.run(main())
