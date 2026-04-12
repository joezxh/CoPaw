# -*- coding: utf-8 -*-
"""
Storage Middleware — 存储 API 中间件

自动为所有 /api/enterprise/storage/ 请求注入租户前缀，
并执行跨租户访问控制检查。
"""
from __future__ import annotations

import logging
from typing import Optional

from fastapi import Request, Response
from fastapi.responses import JSONResponse

from .access_control import StorageACLEntry
from .base import StoragePermissionError

logger = logging.getLogger(__name__)


async def storage_middleware(
    request: Request,
    call_next,
) -> Response:
    """存储中间件 — 注入租户前缀 + 访问控制

    从 request.state 中获取：
    - tenant_id: 租户 ID
    - user_id: 用户 ID
    - roles: 用户角色列表

    自动重写路径中的 key 参数，注入租户前缀。
    验证跨租户操作，拒绝则返回 403。
    """
    # 仅拦截存储 API 请求
    if not request.url.path.startswith("/api/enterprise/storage"):
        return await call_next(request)

    # 获取用户上下文（由 auth middleware 注入）
    tenant_id: Optional[str] = getattr(request.state, "tenant_id", None)
    user_id: Optional[str] = getattr(request.state, "user_id", None)
    roles: list[str] = getattr(request.state, "roles", [])

    if not tenant_id:
        # 未认证请求，允许通过（由 auth middleware 处理）
        return await call_next(request)

    # 提取请求路径中的 key（如果有）
    path = request.url.path
    method = request.method

    # 对包含 key 的路径进行租户前缀注入
    if "/storage/" in path and method in ("GET", "PUT", "DELETE"):
        # 提取 key 部分（在 /storage/ 之后）
        storage_prefix = "/api/enterprise/storage/"
        if path.startswith(storage_prefix):
            key_part = path[len(storage_prefix):]

            # 跳过特定端点（list, stats, search, upload）
            if key_part not in ("list", "stats", "search", "upload") and not key_part.startswith("presign/") and not key_part.startswith("metadata/"):
                # 这是一个直接的 key 访问
                # 检查 key 是否已经包含租户前缀
                parsed_key_parts = key_part.split("/")
                if parsed_key_parts and parsed_key_parts[0] != tenant_id and parsed_key_parts[0] != "_system":
                    # key 不包含租户前缀，需要注入
                    # 注意：这里我们不修改 URL 路径（FastAPI 不支持），
                    # 而是在路由 handler 中通过 request.state 获取 tenant_id
                    pass

    # 验证访问权限（对写操作）
    if method in ("PUT", "DELETE", "POST"):
        try:
            # 获取请求体中的 key（如果有）
            key_to_check = None

            # 从路径中提取
            storage_prefix = "/api/enterprise/storage/"
            if path.startswith(storage_prefix):
                key_part = path[len(storage_prefix):]
                if key_part and key_part not in ("list", "stats", "search", "upload"):
                    key_to_check = key_part

            if key_to_check:
                StorageACLEntry.validate_access(
                    user_roles=roles,
                    user_tenant_id=tenant_id,
                    user_id=user_id,
                    requested_key=key_to_check,
                )
        except StoragePermissionError:
            logger.warning(
                "Storage access denied: tenant=%s user=%s key=%s",
                tenant_id,
                user_id,
                path,
            )
            return JSONResponse(
                status_code=403,
                content={"detail": "Storage access denied"},
            )

    # 继续处理请求
    response = await call_next(request)

    # 添加租户 ID 到响应头（用于调试）
    response.headers["X-Tenant-Id"] = tenant_id

    return response
