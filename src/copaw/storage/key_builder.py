# -*- coding: utf-8 -*-
"""
Storage Key Builder — 对象键命名规范构建器

按照统一命名规范构建对象存储键：
    {tenant_id}/{department_id}/shared/{category}/{resource_path}
    {tenant_id}/users/{user_id}/{category}/{resource_path}
    _system/{category}/{resource_path}
"""
from __future__ import annotations

from typing import Optional


class StorageKeyBuilder:
    """构建和解析多租户对象存储键"""

    @staticmethod
    def build(
        tenant_id: str,
        user_id: Optional[str] = None,
        department_id: Optional[str] = None,
        category: Optional[str] = None,
        resource_path: Optional[str] = None,
    ) -> str:
        """构建对象存储键

        Args:
            tenant_id: 租户 ID（必须）
            user_id: 用户 ID（与 department_id 互斥）
            department_id: 部门 ID（与 user_id 互斥）
            category: 资源类别（workspace/skill/memory/media/model/config）
            resource_path: 资源路径（文件名或子路径）

        Returns:
            完整的对象存储键

        Examples:
            >>> StorageKeyBuilder.build("tenant-a", user_id="user-1", category="workspaces", resource_path="ws-123/agent.json")
            'tenant-a/users/user-1/workspaces/ws-123/agent.json'
            >>> StorageKeyBuilder.build("tenant-a", department_id="dept-1", category="skills", resource_path="python.json")
            'tenant-a/dept-1/shared/skills/python.json'
            >>> StorageKeyBuilder.build("_system", category="skill_pool", resource_path="browser_cdp")
            '_system/skill_pool/browser_cdp'
        """
        parts: list[str] = []

        # 系统资源
        if tenant_id == "_system":
            parts.append("_system")
        else:
            # 租户级前缀
            parts.append(tenant_id)

            if department_id:
                # 部门共享资源
                parts.append(department_id)
                parts.append("shared")
            elif user_id:
                # 用户级资源
                parts.append("users")
                parts.append(user_id)

        # 类别
        if category:
            parts.append(category)

        # 资源路径
        if resource_path:
            # 标准化路径分隔符
            parts.append(resource_path.replace("\\", "/"))

        return "/".join(parts)

    @staticmethod
    def build_workspace_key(
        tenant_id: str,
        user_id: str,
        workspace_id: str,
        resource: str,
    ) -> str:
        """构建工作空间资源键

        Args:
            tenant_id: 租户 ID
            user_id: 用户 ID
            workspace_id: 工作空间 ID
            resource: 资源名称（agent.json/chats.json/skills/...）

        Returns:
            对象存储键
        """
        return StorageKeyBuilder.build(
            tenant_id=tenant_id,
            user_id=user_id,
            category="workspaces",
            resource_path=f"{workspace_id}/{resource}",
        )

    @staticmethod
    def build_skill_key(
        tenant_id: str,
        user_id: str | None,
        skill_name: str,
        is_system: bool = False,
    ) -> str:
        """构建技能文件键

        Args:
            tenant_id: 租户 ID
            user_id: 用户 ID（系统技能可为 None）
            skill_name: 技能名称
            is_system: 是否为系统级技能

        Returns:
            对象存储键
        """
        if is_system:
            return StorageKeyBuilder.build(
                tenant_id="_system",
                category="skill_pool",
                resource_path=skill_name,
            )
        return StorageKeyBuilder.build(
            tenant_id=tenant_id,
            user_id=user_id,
            category="skills",
            resource_path=skill_name,
        )

    @staticmethod
    def build_memory_key(
        tenant_id: str,
        user_id: str,
        workspace_id: str,
        doc_name: str,
    ) -> str:
        """构建记忆文档键

        Args:
            tenant_id: 租户 ID
            user_id: 用户 ID
            workspace_id: 工作空间 ID
            doc_name: 文档名称（MEMORY.md/2026-04-11.md/...）

        Returns:
            对象存储键
        """
        return StorageKeyBuilder.build(
            tenant_id=tenant_id,
            user_id=user_id,
            category="workspaces",
            resource_path=f"{workspace_id}/memory/{doc_name}",
        )

    @staticmethod
    def parse(key: str) -> dict:
        """解析对象键，提取租户/部门/用户/类别信息

        Args:
            key: 对象存储键

        Returns:
            包含 tenant_id, department_id, user_id, category, resource_path 的字典
        """
        parts = key.split("/")
        result: dict = {
            "tenant_id": None,
            "department_id": None,
            "user_id": None,
            "category": None,
            "resource_path": None,
        }

        if not parts:
            return result

        idx = 0
        result["tenant_id"] = parts[idx]
        idx += 1

        if result["tenant_id"] == "_system":
            # _system/category/resource_path
            if idx < len(parts):
                result["category"] = parts[idx]
                idx += 1
            if idx < len(parts):
                result["resource_path"] = "/".join(parts[idx:])
            return result

        # tenant_id/...
        if idx < len(parts):
            if parts[idx] == "users" and idx + 1 < len(parts):
                # tenant_id/users/{user_id}/category/resource_path
                idx += 1  # skip "users"
                result["user_id"] = parts[idx]
                idx += 1
            else:
                # tenant_id/{dept_id}/shared/category/resource_path
                result["department_id"] = parts[idx]
                idx += 1
                if idx < len(parts) and parts[idx] == "shared":
                    idx += 1  # skip "shared"

        if idx < len(parts):
            result["category"] = parts[idx]
            idx += 1

        if idx < len(parts):
            result["resource_path"] = "/".join(parts[idx:])

        return result

    @staticmethod
    def validate(key: str, tenant_id: str, user_id: Optional[str] = None) -> bool:
        """验证用户是否有权访问指定的对象键

        Args:
            key: 对象存储键
            tenant_id: 用户所属租户 ID
            user_id: 用户 ID（可选）

        Returns:
            True 表示有权访问
        """
        parsed = StorageKeyBuilder.parse(key)

        # 系统资源：任何人都不能直接访问（需通过 API 代理）
        if parsed["tenant_id"] == "_system":
            return False

        # 租户隔离：键中的租户必须与用户租户匹配
        if parsed["tenant_id"] != tenant_id:
            return False

        # 用户资源隔离：如果键包含 user_id，必须与请求用户匹配
        if parsed["user_id"] and user_id:
            if parsed["user_id"] != user_id:
                return False

        return True
