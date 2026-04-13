# 权限系统调试指南

## 🔍 问题诊断

### 症状
- 登录后菜单不显示
- 权限接口返回 401 Unauthorized
- Request URL: `http://localhost:8088/api/v1/auth/permissions`

## 📋 检查清单

### 1. 检查 Token 是否正确保存

打开浏览器开发者工具（F12），在 Console 中执行：

```javascript
// 检查 localStorage 中的 token
console.log('Auth Token:', localStorage.getItem('copaw_auth_token'));
```

**预期结果**: 应该显示一个 JWT token 字符串

**如果为 null**:
- 登录可能失败了
- 检查登录接口的响应
- 查看 Network 标签中的 `/auth/login` 请求

### 2. 检查权限请求头

在 Network 标签中查看 `/api/v1/auth/permissions` 请求：

**Request Headers 应该包含**:
```
Authorization: Bearer <your-jwt-token>
Content-Type: application/json
```

**如果缺少 Authorization**:
- Token 没有正确获取
- 检查 `usePermissions` Hook 的 `getApiToken()` 调用

### 3. 检查后端日志

查看后端服务的日志输出：

```bash
# 如果通过脚本启动
tail -f working/copaw.log

# 如果直接运行
# 查看终端输出
```

**关键日志**:
```
[EnterpriseAuthMiddleware] Token validation failed
[EnterpriseAuthMiddleware] Not authenticated
```

### 4. 检查用户是否有角色和权限

连接 PostgreSQL 数据库执行：

```sql
-- 检查用户
SELECT id, username, is_active FROM sys_users WHERE username = '你的用户名';

-- 检查用户角色
SELECT ur.user_id, r.name, r.code
FROM sys_user_roles ur
JOIN sys_roles r ON ur.role_id = r.id
WHERE ur.user_id = '你的user_id';

-- 检查角色权限
SELECT rp.role_id, p.permission_code, p.resource, p.action
FROM sys_role_permissions rp
JOIN sys_permissions p ON rp.permission_id = p.id
WHERE rp.role_id IN (
    SELECT role_id FROM sys_user_roles WHERE user_id = '你的user_id'
);
```

**预期结果**:
- 用户应该有至少一个角色
- 角色应该有权限关联

### 5. 手动测试权限接口

使用 curl 或 Postman 测试：

```bash
# 1. 登录获取 token
curl -X POST http://localhost:8088/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username": "admin", "password": "你的密码"}'

# 响应示例:
# {"access_token": "eyJ...", "token_type": "bearer"}

# 2. 使用 token 请求权限
curl -X GET http://localhost:8088/api/v1/auth/permissions \
  -H "Authorization: Bearer eyJ..."

# 预期响应:
# {"user_id": "...", "permissions": [...], "roles": [...]}
```

## 🛠️ 常见问题修复

### 问题 1: Token 未保存

**原因**: 登录接口响应格式不匹配

**修复**: 检查登录页面代码
```tsx
// console/src/pages/Login/index.tsx
// 确保正确调用 setAuthToken
setAuthToken(loginRes.access_token || loginRes.token);
```

### 问题 2: 用户没有角色

**原因**: 初始化脚本未执行或执行失败

**修复**: 重新执行权限初始化
```bash
cd d:\projects\copaw
python scripts/init_permissions.py --tenant-id default-tenant
```

### 问题 3: Token 格式错误

**原因**: 前端传递的 token 不包含 "Bearer " 前缀

**修复**: 已在 `usePermissions.ts` 中修复
```typescript
headers['Authorization'] = `Bearer ${token}`;
```

### 问题 4: 后端中间件路径不匹配

**原因**: 权限接口路径不在保护范围内

**检查**: `middleware.py` 中的 `_PUBLIC_PATHS`
```python
_PUBLIC_PATHS: frozenset[str] = frozenset({
    "/api/enterprise/auth/login",
    # ... 不应该包含 /api/v1/auth/permissions
})
```

## 🔧 快速修复步骤

### Step 1: 清除缓存并重新登录

```javascript
// 浏览器 Console
localStorage.clear();
location.reload();
```

### Step 2: 重新登录

1. 访问 http://localhost:5173/login
2. 输入用户名和密码
3. 检查 Network 标签确认登录成功

### Step 3: 验证 Token

```javascript
// 浏览器 Console
const token = localStorage.getItem('copaw_auth_token');
console.log('Token exists:', !!token);
console.log('Token preview:', token?.substring(0, 50) + '...');
```

### Step 4: 手动请求权限

```javascript
// 浏览器 Console
const token = localStorage.getItem('copaw_auth_token');
fetch('http://localhost:8088/api/v1/auth/permissions', {
  headers: {
    'Authorization': `Bearer ${token}`,
    'Content-Type': 'application/json'
  }
})
.then(res => {
  console.log('Status:', res.status);
  return res.json();
})
.then(data => console.log('Permissions:', data))
.catch(err => console.error('Error:', err));
```

### Step 5: 检查数据库

```bash
# 运行验证脚本
python verify_permissions.py
```

## 📊 调试代码

### 在 usePermissions Hook 中添加日志

```typescript
// console/src/hooks/usePermissions.ts
const loadPermissions = useCallback(async () => {
  try {
    setLoading(true);
    setError(null);

    const token = getApiToken();
    console.log('[usePermissions] Token:', token ? 'exists' : 'missing');
    
    const headers: HeadersInit = {
      'Content-Type': 'application/json',
    };

    if (token) {
      headers['Authorization'] = `Bearer ${token}`;
      console.log('[usePermissions] Authorization header set');
    }

    const url = getApiUrl('/api/v1/auth/permissions');
    console.log('[usePermissions] Request URL:', url);

    const response = await fetch(url, {
      method: 'GET',
      headers,
      credentials: 'include',
    });

    console.log('[usePermissions] Response status:', response.status);

    if (!response.ok) {
      if (response.status === 401) {
        console.warn('[usePermissions] 401 Unauthorized');
        setPermissions([]);
        setRoles([]);
        setLoading(false);
        return;
      }
      throw new Error(`HTTP ${response.status}: ${response.statusText}`);
    }

    const data: UserPermissionsResponse = await response.json();
    console.log('[usePermissions] Permissions loaded:', data.permissions.length);
    console.log('[usePermissions] Roles:', data.roles);
    
    setPermissions(data.permissions);
    setRoles(data.roles);
  } catch (err) {
    console.error('[usePermissions] Error:', err);
    // ...
  }
}, []);
```

## ✅ 验证成功

当一切正常时，您应该看到：

1. **Network 标签**: `/api/v1/auth/permissions` 返回 200
2. **Console**: 权限数据正确加载
3. **菜单**: 根据权限显示对应菜单项
4. **数据库**: 用户有角色，角色有权限

## 📞 需要帮助？

如果以上步骤都无法解决问题，请提供：

1. 浏览器 Console 的完整输出
2. Network 标签中 `/auth/login` 和 `/api/v1/auth/permissions` 的请求/响应
3. 后端日志的相关部分
4. 数据库中用户的角色信息

---

**更新日期**: 2026-04-13  
**适用版本**: CoPaw Enterprise v2.0+
