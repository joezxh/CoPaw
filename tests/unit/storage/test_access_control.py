# -*- coding: utf-8 -*-
"""
测试 Phase 2: 多租户存储 - StorageAccessControl
"""
import pytest
from copaw.storage import StorageAccessLevel, StorageACLEntry


class TestStorageACL:
    """测试存储访问控制"""

    def test_super_admin_cross_tenant(self):
        """测试超级管理员跨租户访问"""
        assert StorageACLEntry.validate_access(
            user_roles=["super_admin"],
            user_tenant_id="tenant-001",
            user_id="admin-001",
            requested_key="tenant-002/users/user-123/workspace/agent.json",
        ) is True

    def test_tenant_admin_same_tenant(self):
        """测试租户管理员同租户访问"""
        assert StorageACLEntry.validate_access(
            user_roles=["tenant_admin"],
            user_tenant_id="tenant-001",
            user_id="admin-001",
            requested_key="tenant-001/users/user-123/workspace/agent.json",
        ) is True

    def test_tenant_admin_cross_tenant_denied(self):
        """测试租户管理员跨租户拒绝"""
        assert StorageACLEntry.validate_access(
            user_roles=["tenant_admin"],
            user_tenant_id="tenant-001",
            user_id="admin-001",
            requested_key="tenant-002/users/user-456/workspace/agent.json",
        ) is False

    def test_user_own_resource(self):
        """测试用户访问自己的资源"""
        assert StorageACLEntry.validate_access(
            user_roles=["user"],
            user_tenant_id="tenant-001",
            user_id="user-123",
            requested_key="tenant-001/users/user-123/workspace/agent.json",
        ) is True

    def test_user_other_user_resource_denied(self):
        """测试用户访问其他用户资源拒绝"""
        assert StorageACLEntry.validate_access(
            user_roles=["user"],
            user_tenant_id="tenant-001",
            user_id="user-123",
            requested_key="tenant-001/users/user-456/workspace/agent.json",
        ) is False

    def test_dept_admin_department_resource(self):
        """测试部门管理员访问部门资源"""
        assert StorageACLEntry.validate_access(
            user_roles=["dept_admin"],
            user_tenant_id="tenant-001",
            user_id="admin-dept",
            requested_key="tenant-001/dept-456/shared/skills/web_search",
        ) is True

    def test_invalid_key_format(self):
        """测试无效键格式"""
        assert StorageACLEntry.validate_access(
            user_roles=["user"],
            user_tenant_id="tenant-001",
            user_id="user-123",
            requested_key="invalid-key",
        ) is False

    def test_empty_roles(self):
        """测试空角色列表"""
        assert StorageACLEntry.validate_access(
            user_roles=[],
            user_tenant_id="tenant-001",
            user_id="user-123",
            requested_key="tenant-001/users/user-123/workspace/agent.json",
        ) is False

    def test_access_level_mapping(self):
        """测试访问级别映射"""
        assert StorageACLEntry.ROLE_LEVEL_MAP["super_admin"] == StorageAccessLevel.SYSTEM
        assert StorageACLEntry.ROLE_LEVEL_MAP["tenant_admin"] == StorageAccessLevel.TENANT
        assert StorageACLEntry.ROLE_LEVEL_MAP["dept_admin"] == StorageAccessLevel.DEPARTMENT
        assert StorageACLEntry.ROLE_LEVEL_MAP["user"] == StorageAccessLevel.USER
