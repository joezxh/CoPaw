# -*- coding: utf-8 -*-
"""
Storage Access Control — 存储访问控制

实现多租户存储的 RBAC 访问控制策略。
"""
from __future__ import annotations

from enum import Enum
from typing import Optional

from .base import StoragePermissionError


class StorageAccessLevel(str, Enum):
    """存储访问级别"""

    SYSTEM = "system"           # 系统管理员
    TENANT = "tenant"           # 租户管理员
    DEPARTMENT = "department"   # 部门管理员
    USER = "user"               # 普通用户
    PUBLIC = "public"           # 公开访问


class StorageACLEntry:
    """存储访问控制条目"""

    # 角色到访问级别的映射
    ROLE_LEVEL_MAP = {
        "super_admin": StorageAccessLevel.SYSTEM,
        "tenant_admin": StorageAccessLevel.TENANT,
        "dept_admin": StorageAccessLevel.DEPARTMENT,
        "user": StorageAccessLevel.USER,
    }

    @staticmethod
    def get_access_level(roles: list[str]) -> StorageAccessLevel:
        """从角色列表获取最高访问级别

        Args:
            roles: 用户角色列表

        Returns:
            最高访问级别
        """
        for role in ["super_admin", "tenant_admin", "dept_admin", "user"]:
            if role in roles:
                return StorageACLEntry.ROLE_LEVEL_MAP[role]
        return StorageAccessLevel.USER  # 默认普通用户

    @staticmethod
    def build_key_prefix(
        tenant_id: str,
        department_id: Optional[str] = None,
        user_id: Optional[str] = None,
        category: Optional[str] = None,
    ) -> str:
        """构建存储键前缀

        Args:
            tenant_id: 租户 ID
            department_id: 部门 ID（与 user_id 互斥）
            user_id: 用户 ID（与 department_id 互斥）
            category: 资源类别

        Returns:
            存储键前缀
        """
        parts = [tenant_id]
        if department_id:
            parts.append(department_id)
            parts.append("shared")
        elif user_id:
            parts.extend(["users", user_id])
        if category:
            parts.append(category)
        return "/".join(parts)

    @staticmethod
    def validate_access(
        user_roles: list[str],
        user_tenant_id: str,
        user_id: Optional[str],
        requested_key: str,
    ) -> bool:
        """验证用户对指定存储键的访问权限

        Args:
            user_roles: 用户角色列表
            user_tenant_id: 用户所属租户 ID
            user_id: 用户 ID
            requested_key: 请求访问的存储键

        Returns:
            True 表示允许访问
        """
        # 1. 解析目标键中的租户 ID
        parts = requested_key.split("/")
        if not parts:
            return False

        key_tenant = parts[0]

        # 2. Super Admin 可跨租户
        if "super_admin" in user_roles:
            return True

        # 3. 租户级隔离
        if key_tenant != user_tenant_id:
            return False

        # 4. 系统资源：仅 tenant_admin 及以上可读
        if requested_key.startswith("_system/"):
            access_level = StorageACLEntry.get_access_level(user_roles)
            return access_level in (StorageAccessLevel.SYSTEM, StorageAccessLevel.TENANT)

        # 5. 解析用户级资源
        if len(parts) >= 3 and parts[1] == "users":
            key_user_id = parts[2]
            access_level = StorageACLEntry.get_access_level(user_roles)

            # 租户管理员可访问租户内所有资源
            if access_level == StorageAccessLevel.TENANT:
                return True

            # 部门管理员可访问部门共享资源
            if access_level == StorageAccessLevel.DEPARTMENT:
                # 检查是否为当前用户的资源或部门共享资源
                return key_user_id == user_id or "shared" in parts

            # 普通用户只能访问自己的资源
            return key_user_id == user_id

        # 6. 部门共享资源
        if len(parts) >= 3 and "shared" in parts:
            access_level = StorageACLEntry.get_access_level(user_roles)
            return access_level in (
                StorageAccessLevel.TENANT,
                StorageAccessLevel.DEPARTMENT,
                StorageAccessLevel.USER,
            )

        # 7. 租户级资源（_tenant/）
        if len(parts) >= 2 and parts[1] == "_tenant":
            access_level = StorageACLEntry.get_access_level(user_roles)
            return access_level in (StorageAccessLevel.SYSTEM, StorageAccessLevel.TENANT)

        return True

    @staticmethod
    def enforce_access(
        user_roles: list[str],
        user_tenant_id: str,
        user_id: Optional[str],
        requested_key: str,
    ) -> None:
        """强制执行访问控制，失败时抛出异常

        Args:
            user_roles: 用户角色列表
            user_tenant_id: 用户所属租户 ID
            user_id: 用户 ID
            requested_key: 请求访问的存储键

        Raises:
            StoragePermissionError: 当访问被拒绝时
        """
        if not StorageACLEntry.validate_access(
            user_roles, user_tenant_id, user_id, requested_key
        ):
            raise StoragePermissionError(
                key=requested_key,
                reason="access denied by storage ACL policy",
            )
