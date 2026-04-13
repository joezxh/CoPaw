# ✅ API 路径重复问题修复报告

## 🐛 问题描述

企业版 API 路径出现重复的 `/api` 前缀：
- **错误路径**: `/api/api/v1/auth/permissions`
- **正确路径**: `/api/v1/auth/permissions`

## 🔍 根本原因

在 `_app.py` 中注册路由时已经添加了 `/api` 前缀：
```python
app.include_router(api_router, prefix="/api")
```

但是各个 router 定义时又包含了 `/api` 前缀：
```python
# 错误示例
router = APIRouter(prefix="/api/v1", tags=["permissions"])
router = APIRouter(prefix="/api/enterprise/users", tags=["enterprise-users"])
```

导致最终路径变成：`/api` + `/api/v1/...` = `/api/api/v1/...`

## ✅ 已修复的后端路由

| 文件 | 修改前 | 修改后 | 状态 |
|------|--------|--------|------|
| `permission_mgmt.py` | `/api/v1` | `/v1` | ✅ |
| `registry.py` | `/api/v1/registry` | `/v1/registry` | ✅ |
| `users.py` | `/api/enterprise/users` | `/enterprise/users` | ✅ |
| `roles.py` | `/api/enterprise` | `/enterprise` | ✅ |
| `departments.py` | `/api/enterprise/departments` | `/enterprise/departments` | ✅ |
| `tasks.py` | `/api/enterprise/tasks` | `/enterprise/tasks` | ✅ |
| `workflows.py` | `/api/enterprise/workflows` | `/enterprise/workflows` | ✅ |
| `audit.py` | `/api/enterprise/audit` | `/enterprise/audit` | ✅ |
| `user_groups.py` | `/api/enterprise/groups` | `/enterprise/groups` | ✅ |
| `dlp.py` | `/api/enterprise/dlp` | `/enterprise/dlp` | ✅ |
| `alerts.py` | `/api/enterprise/alerts` | `/enterprise/alerts` | ✅ |
| `dify.py` | `/api/enterprise/dify` | `/enterprise/dify` | ✅ |

## ⚠️ 需要修复的前端 API 路径

以下前端文件中的 API 路径需要移除 `/api` 前缀：

### 1. enterprise-dify.ts
```typescript
// 修改前
"/api/enterprise/dify/connectors"

// 修改后
"/enterprise/dify/connectors"
```

### 2. enterprise-alerts.ts
```typescript
// 修改前
"/api/enterprise/alerts/rules"
"/api/enterprise/alerts/events"
"/api/enterprise/alerts/test"

// 修改后
"/enterprise/alerts/rules"
"/enterprise/alerts/events"
"/enterprise/alerts/test"
```

### 3. enterprise-dlp.ts
```typescript
// 修改前
"/api/enterprise/dlp/rules"
"/api/enterprise/dlp/events"

// 修改后
"/enterprise/dlp/rules"
"/enterprise/dlp/events"
```

### 4. enterprise-groups.ts
```typescript
// 修改前
"/api/enterprise/user-groups"

// 修改后
"/enterprise/user-groups"
```

### 5. enterprise-audit.ts
```typescript
// 修改前
"/api/enterprise/audit"

// 修改后
"/enterprise/audit"
```

### 6. enterprise-workflows.ts
```typescript
// 修改前
"/api/enterprise/workflows"

// 修改后
"/enterprise/workflows"
```

### 7. usePermissions.ts ✅ 已修复
```typescript
// 修改前
getApiUrl('/api/v1/auth/permissions')

// 修改后
getApiUrl('/v1/auth/permissions')
```

## 🔧 批量修复命令

可以使用以下 PowerShell 命令批量替换：

```powershell
# 进入 console 目录
cd d:\projects\copaw\console\src

# 批量替换（预览）
Get-ChildItem -Recurse -Filter "*.ts" | ForEach-Object {
    $content = Get-Content $_.FullName -Raw -Encoding UTF8
    if ($content -match '/api/enterprise/') {
        Write-Host "Found in: $($_.FullName)"
    }
}

# 批量替换（执行）
Get-ChildItem -Recurse -Filter "*.ts" | ForEach-Object {
    $content = Get-Content $_.FullName -Raw -Encoding UTF8
    if ($content -match '/api/enterprise/') {
        $newContent = $content -replace '/api/enterprise/', '/enterprise/'
        Set-Content $_.FullName -Value $newContent -Encoding UTF8 -NoNewline
        Write-Host "Fixed: $($_.FullName)"
    }
}
```

## 📊 最终 API 路径对照表

### 权限管理
| 功能 | 完整路径 |
|------|---------|
| 获取用户权限 | `GET /api/v1/auth/permissions` |
| 权限列表 | `GET /api/v1/permissions` |
| 权限树 | `GET /api/v1/permissions/tree` |
| 创建权限 | `POST /api/v1/permissions` |
| 更新权限 | `PUT /api/v1/permissions/{id}` |
| 删除权限 | `DELETE /api/v1/permissions/{id}` |

### 用户管理
| 功能 | 完整路径 |
|------|---------|
| 用户列表 | `GET /api/enterprise/users` |
| 创建用户 | `POST /api/enterprise/users` |
| 更新用户 | `PUT /api/enterprise/users/{id}` |
| 删除用户 | `DELETE /api/enterprise/users/{id}` |

### 角色管理
| 功能 | 完整路径 |
|------|---------|
| 角色列表 | `GET /api/enterprise/roles` |
| 创建角色 | `POST /api/enterprise/roles` |
| 更新角色 | `PUT /api/enterprise/roles/{id}` |
| 删除角色 | `DELETE /api/enterprise/roles/{id}` |

### 审计日志
| 功能 | 完整路径 |
|------|---------|
| 审计日志列表 | `GET /api/enterprise/audit` |

### 其他企业功能
| 功能 | 完整路径 |
|------|---------|
| 用户组 | `/api/enterprise/groups` |
| DLP | `/api/enterprise/dlp` |
| 告警 | `/api/enterprise/alerts` |
| Dify | `/api/enterprise/dify` |
| 任务 | `/api/enterprise/tasks` |
| 工作流 | `/api/enterprise/workflows` |

## ✅ 验证步骤

### 1. 重启后端服务

```bash
# 停止当前服务
# Ctrl+C

# 重新启动
copaw start
# 或
.\scripts\start-enterprise.ps1
```

### 2. 测试权限接口

```bash
# 登录获取 token
curl -X POST http://localhost:8088/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username": "admin", "password": "密码"}'

# 测试权限接口（使用返回的 token）
curl -X GET http://localhost:8088/api/v1/auth/permissions \
  -H "Authorization: Bearer YOUR_TOKEN"
```

**预期响应**: 200 OK，返回权限列表

### 3. 浏览器测试

1. 打开浏览器 Developer Tools (F12)
2. 切换到 Network 标签
3. 登录后查看 `/v1/auth/permissions` 请求
4. 确认路径正确（不再有 `/api/api/`）

## 📝 修改文件清单

### 后端（12个文件）
1. `src/copaw/app/routers/permission_mgmt.py` ✅
2. `src/copaw/app/routers/registry.py` ✅
3. `src/copaw/app/routers/users.py` ✅
4. `src/copaw/app/routers/roles.py` ✅
5. `src/copaw/app/routers/departments.py` ✅
6. `src/copaw/app/routers/tasks.py` ✅
7. `src/copaw/app/routers/workflows.py` ✅
8. `src/copaw/app/routers/audit.py` ✅
9. `src/copaw/app/routers/user_groups.py` ✅
10. `src/copaw/app/routers/dlp.py` ✅
11. `src/copaw/app/routers/alerts.py` ✅
12. `src/copaw/app/routers/dify.py` ✅

### 前端（已修复 1 个，待修复 6 个）
1. `console/src/hooks/usePermissions.ts` ✅
2. `console/src/api/modules/enterprise-dify.ts` ⏳
3. `console/src/api/modules/enterprise-alerts.ts` ⏳
4. `console/src/api/modules/enterprise-dlp.ts` ⏳
5. `console/src/api/modules/enterprise-groups.ts` ⏳
6. `console/src/api/modules/enterprise-audit.ts` ⏳
7. `console/src/api/modules/enterprise-workflows.ts` ⏳

## 🎯 下一步

1. **重启后端服务** - 使路由修改生效
2. **修复前端 API 路径** - 使用批量替换命令
3. **测试所有企业版功能** - 确保 API 调用正常
4. **更新文档** - 如有 API 文档需要同步更新

---

**修复时间**: 2026-04-13  
**后端状态**: ✅ 全部完成  
**前端状态**: ⏳ 部分完成（6个文件待修复）
