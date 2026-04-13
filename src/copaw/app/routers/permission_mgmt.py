# -*- coding: utf-8 -*-
"""
权限管理 API Router

功能：
1. 用户权限查询 - GET /api/v1/auth/permissions
2. 权限 CRUD 管理 - /api/v1/permissions
3. 权限树查询 - GET /api/v1/permissions/tree

权限码规范：模块:资源:操作 (如 'agent:config:read')
"""
from __future__ import annotations

import uuid
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy import select, func

from ...db.postgresql import get_db_session
from ...db.models.permission import Permission
from ...db.models.role import Role, RolePermission, UserRole
from ...enterprise.middleware import get_current_user
from ...enterprise.rbac_service import RBACService
from ...enterprise.audit_service import AuditService, AuditAction

router = APIRouter(prefix="/v1", tags=["permissions"])


# ============================================================================
# Pydantic Schemas
# ============================================================================

class PermissionResponse(BaseModel):
    """权限响应"""
    id: str
    tenant_id: str
    permission_code: str
    resource: str
    action: str
    resource_path: Optional[str] = None
    permission_type: str
    description: Optional[str] = None
    parent_id: Optional[str] = None
    sort_order: int
    icon: Optional[str] = None
    is_visible: bool
    created_by: Optional[str] = None

    class Config:
        from_attributes = True


class PermissionCreateRequest(BaseModel):
    """创建权限请求"""
    permission_code: str = Field(..., max_length=100, description="权限码(如: agent:config:read)")
    resource: str = Field(..., max_length=200, description="资源标识")
    action: str = Field(..., max_length=50, description="操作类型")
    resource_path: Optional[str] = Field(None, max_length=200, description="前端路由路径")
    permission_type: str = Field(default="menu", description="权限类型: menu|api|button|data")
    description: Optional[str] = Field(None, max_length=500)
    parent_id: Optional[str] = Field(None, description="父权限ID")
    sort_order: int = Field(default=0, ge=0)
    icon: Optional[str] = Field(None, max_length=100)
    is_visible: bool = Field(default=True)


class PermissionUpdateRequest(BaseModel):
    """更新权限请求"""
    resource_path: Optional[str] = Field(None, max_length=200)
    permission_type: Optional[str] = Field(None, max_length=20)
    description: Optional[str] = Field(None, max_length=500)
    parent_id: Optional[str] = None
    sort_order: Optional[int] = Field(None, ge=0)
    icon: Optional[str] = Field(None, max_length=100)
    is_visible: Optional[bool] = None


class UserPermissionsResponse(BaseModel):
    """用户权限响应"""
    user_id: str
    permissions: List[PermissionResponse]
    roles: List[str]


class PermissionTreeNode(BaseModel):
    """权限树节点"""
    id: str
    permission_code: str
    resource: str
    action: str
    resource_path: Optional[str] = None
    permission_type: str
    description: Optional[str] = None
    icon: Optional[str] = None
    is_visible: bool
    sort_order: int
    children: List["PermissionTreeNode"] = []


# ============================================================================
# Helper Functions
# ============================================================================

def _permission_to_dict(perm: Permission) -> dict:
    """将 Permission ORM 对象转换为字典"""
    return {
        "id": str(perm.id),
        "tenant_id": str(perm.tenant_id),
        "permission_code": perm.permission_code,
        "resource": perm.resource,
        "action": perm.action,
        "resource_path": perm.resource_path,
        "permission_type": perm.permission_type,
        "description": perm.description,
        "parent_id": str(perm.parent_id) if perm.parent_id else None,
        "sort_order": perm.sort_order,
        "icon": perm.icon,
        "is_visible": perm.is_visible,
        "created_by": str(perm.created_by) if perm.created_by else None,
    }


# ============================================================================
# User Permission Query API
# ============================================================================

@router.get("/auth/permissions", response_model=UserPermissionsResponse)
async def get_user_permissions(
    current_user: dict = Depends(get_current_user),
):
    """
    获取当前用户的权限列表
    
    返回用户通过角色获得的所有权限，前端用于初始化权限控制。
    """
    user_id = uuid.UUID(current_user["user_id"])
    tenant_id = current_user.get("tenant_id", "default-tenant")
    
    async with get_db_session() as session:
        # 获取用户权限
        permissions = await RBACService.get_user_permissions(session, user_id)
        
        # 获取用户角色
        user_roles_result = await session.execute(
            select(Role)
            .join(UserRole, UserRole.role_id == Role.id)
            .where(UserRole.user_id == user_id)
        )
        roles = user_roles_result.scalars().all()
        role_names = [role.name for role in roles]
        
        return UserPermissionsResponse(
            user_id=str(user_id),
            permissions=[PermissionResponse(**_permission_to_dict(p)) for p in permissions],
            roles=role_names,
        )


# ============================================================================
# Permission CRUD APIs
# ============================================================================

@router.get("/permissions", response_model=List[PermissionResponse])
async def list_permissions(
    permission_type: Optional[str] = Query(None, description="权限类型过滤"),
    is_visible: Optional[bool] = Query(None, description="是否可见过滤"),
    search: Optional[str] = Query(None, description="搜索权限码或描述"),
    current_user: dict = Depends(get_current_user),
):
    """
    查询权限列表
    
    支持按权限类型、可见性、搜索关键字过滤
    """
    async with get_db_session() as session:
        stmt = select(Permission)
        
        # 过滤条件
        if permission_type:
            stmt = stmt.where(Permission.permission_type == permission_type)
        if is_visible is not None:
            stmt = stmt.where(Permission.is_visible == is_visible)
        if search:
            stmt = stmt.where(
                (Permission.permission_code.ilike(f"%{search}%")) |
                (Permission.description.ilike(f"%{search}%"))
            )
        
        # 排序
        stmt = stmt.order_by(Permission.permission_type, Permission.sort_order)
        
        perms = (await session.scalars(stmt)).all()
        return [PermissionResponse(**_permission_to_dict(p)) for p in perms]


@router.get("/permissions/tree", response_model=List[PermissionTreeNode])
async def get_permissions_tree(
    permission_type: Optional[str] = Query("menu", description="权限类型"),
    current_user: dict = Depends(get_current_user),
):
    """
    获取权限树结构
    
    返回层次化的权限树，用于前端菜单渲染
    """
    async with get_db_session() as session:
        # 查询指定类型的所有权限
        stmt = (
            select(Permission)
            .where(Permission.permission_type == permission_type)
            .order_by(Permission.sort_order)
        )
        perms = (await session.scalars(stmt)).all()
        
        # 构建树结构
        perm_map = {}
        root_nodes = []
        
        for perm in perms:
            node = PermissionTreeNode(
                id=str(perm.id),
                permission_code=perm.permission_code,
                resource=perm.resource,
                action=perm.action,
                resource_path=perm.resource_path,
                permission_type=perm.permission_type,
                description=perm.description,
                icon=perm.icon,
                is_visible=perm.is_visible,
                sort_order=perm.sort_order,
                children=[],
            )
            perm_map[str(perm.id)] = node
            
            if perm.parent_id:
                parent_id_str = str(perm.parent_id)
                if parent_id_str in perm_map:
                    perm_map[parent_id_str].children.append(node)
            else:
                root_nodes.append(node)
        
        return root_nodes


@router.get("/permissions/{perm_id}", response_model=PermissionResponse)
async def get_permission(
    perm_id: str,
    current_user: dict = Depends(get_current_user),
):
    """获取权限详情"""
    async with get_db_session() as session:
        perm = await session.get(Permission, uuid.UUID(perm_id))
        if not perm:
            raise HTTPException(status_code=404, detail="权限不存在")
        return PermissionResponse(**_permission_to_dict(perm))


@router.post("/permissions", status_code=201, response_model=PermissionResponse)
async def create_permission(
    body: PermissionCreateRequest,
    current_user: dict = Depends(get_current_user),
):
    """
    创建权限
    
    需要管理员权限
    """
    async with get_db_session() as session:
        # 检查权限码是否已存在
        existing = await session.execute(
            select(Permission).where(
                Permission.permission_code == body.permission_code
            )
        )
        if existing.scalar_one_or_none():
            raise HTTPException(
                status_code=409,
                detail=f"权限码 '{body.permission_code}' 已存在"
            )
        
        # 创建权限
        perm = Permission(
            tenant_id=current_user.get("tenant_id", "default-tenant"),
            permission_code=body.permission_code,
            resource=body.resource,
            action=body.action,
            resource_path=body.resource_path,
            permission_type=body.permission_type,
            description=body.description,
            parent_id=uuid.UUID(body.parent_id) if body.parent_id else None,
            sort_order=body.sort_order,
            icon=body.icon,
            is_visible=body.is_visible,
            created_by=uuid.UUID(current_user["user_id"]),
        )
        session.add(perm)
        await session.flush()
        
        # 审计日志
        await AuditService.log(
            session,
            action_type=AuditAction.PERMISSION_CREATE,
            resource_type="permission",
            resource_id=str(perm.id),
            result="success",
            user_id=uuid.UUID(current_user["user_id"]),
            data_after=_permission_to_dict(perm),
        )
        
        return PermissionResponse(**_permission_to_dict(perm))


@router.put("/permissions/{perm_id}", response_model=PermissionResponse)
async def update_permission(
    perm_id: str,
    body: PermissionUpdateRequest,
    current_user: dict = Depends(get_current_user),
):
    """
    更新权限
    
    需要管理员权限
    """
    async with get_db_session() as session:
        perm = await session.get(Permission, uuid.UUID(perm_id))
        if not perm:
            raise HTTPException(status_code=404, detail="权限不存在")
        
        # 保存旧数据
        old_data = _permission_to_dict(perm)
        
        # 更新字段
        if body.resource_path is not None:
            perm.resource_path = body.resource_path
        if body.permission_type is not None:
            perm.permission_type = body.permission_type
        if body.description is not None:
            perm.description = body.description
        if body.parent_id is not None:
            perm.parent_id = uuid.UUID(body.parent_id) if body.parent_id else None
        if body.sort_order is not None:
            perm.sort_order = body.sort_order
        if body.icon is not None:
            perm.icon = body.icon
        if body.is_visible is not None:
            perm.is_visible = body.is_visible
        
        await session.flush()
        
        # 审计日志
        await AuditService.log(
            session,
            action_type=AuditAction.PERMISSION_UPDATE,
            resource_type="permission",
            resource_id=perm_id,
            result="success",
            user_id=uuid.UUID(current_user["user_id"]),
            data_before=old_data,
            data_after=_permission_to_dict(perm),
        )
        
        return PermissionResponse(**_permission_to_dict(perm))


@router.delete("/permissions/{perm_id}")
async def delete_permission(
    perm_id: str,
    current_user: dict = Depends(get_current_user),
):
    """
    删除权限
    
    需要管理员权限
    """
    async with get_db_session() as session:
        perm = await session.get(Permission, uuid.UUID(perm_id))
        if not perm:
            raise HTTPException(status_code=404, detail="权限不存在")
        
        # 检查是否有角色使用此权限
        role_count_result = await session.execute(
            select(func.count(RolePermission.id)).where(
                RolePermission.permission_id == perm.id
            )
        )
        role_count = role_count_result.scalar()
        
        if role_count > 0:
            raise HTTPException(
                status_code=409,
                detail=f"该权限正在被 {role_count} 个角色使用，无法删除"
            )
        
        await session.delete(perm)
        
        # 审计日志
        await AuditService.log(
            session,
            action_type=AuditAction.PERMISSION_DELETE,
            resource_type="permission",
            resource_id=perm_id,
            result="success",
            user_id=uuid.UUID(current_user["user_id"]),
            data_before=_permission_to_dict(perm),
        )
        
        return {"detail": "权限已删除"}
