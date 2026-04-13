# Phase 3: 前端权限控制 - 实施总结

## ✅ 已完成任务

| 任务 | 状态 | 文件 | 说明 |
|------|------|------|------|
| 1. usePermissions Hook | ✅ | `console/src/hooks/usePermissions.ts` | 246行，完整权限控制 Hook |
| 2. PermissionGuard 组件 | ✅ | `console/src/components/PermissionGuard.tsx` | 173行，3个组件 |
| 3. Default 布局框架 | ✅ | `console/src/layouts/default/index.tsx` | 167行，主布局 |
| 4. Default 样式 | ✅ | `console/src/layouts/default/index.module.less` | 19行 |

## 📦 交付文件清单

### 1. usePermissions Hook
**文件**: `console/src/hooks/usePermissions.ts`

**功能**:
- 从 API 获取用户权限 (`GET /api/v1/auth/permissions`)
- 提供 `hasPermission()` 检查方法
- 提供 `hasAnyPermission()` 和 `hasAllPermissions()` 批量检查
- 支持按类型过滤权限 (`getPermissionsByType()`)
- 支持获取菜单权限 (`getMenuPermissions()`)
- 内置权限树构建工具 (`buildPermissionTree()`)
- 系统管理员自动拥有所有权限

**用法示例**:
```tsx
import { usePermissions } from '@/hooks/usePermissions';

function MyComponent() {
  const { hasPermission, loading } = usePermissions();
  
  if (loading) return <div>Loading...</div>;
  
  if (hasPermission('agent:config:read')) {
    return <AgentConfig />;
  }
  
  return <NoAccess />;
}
```

### 2. PermissionGuard 组件
**文件**: `console/src/components/PermissionGuard.tsx`

**包含组件**:
1. `PermissionGuard` - 权限守卫组件
2. `PermissionButton` - 按钮权限守卫
3. `withPermission()` - 高阶组件包装器

**用法示例**:
```tsx
// 单个权限
<PermissionGuard permission="agent:config:read">
  <AgentConfig />
</PermissionGuard>

// 多个权限（任意一个）
<PermissionGuard permissions={['agent:read', 'agent:write']}>
  <AgentManagement />
</PermissionGuard>

// 按钮权限（无权限时禁用）
<PermissionButton
  permission="agent:create"
  button={<Button>创建 Agent</Button>}
  showWhenDisabled
/>

// HOC 方式
const ProtectedPage = withPermission(MyPage, 'admin:access');
```

### 3. Default Layout
**文件**: `console/src/layouts/default/index.tsx`

**布局结构**:
```
┌─────────────────────────────────────────┐
│  DefaultHeader (Logo + 导航 + 用户菜单)   │
├──────────┬──────────────────────────────┤
│          │                              │
│ Default  │   Content Area               │
│ Sidebar  │   (页面内容)                  │
│ (手风琴) │                              │
│          │                              │
└──────────┴──────────────────────────────┘
```

**特性**:
- 支持侧边栏折叠/展开
- 集成权限控制（待完善 Sidebar 组件）
- 响应式设计
- 懒加载所有页面组件

## 🎯 核心 API

### usePermissions Hook

```typescript
interface UsePermissionsReturn {
  permissions: Permission[];              // 用户所有权限
  roles: string[];                        // 用户角色列表
  loading: boolean;                       // 加载状态
  error: Error | null;                    // 错误信息
  hasPermission: (code: string) => boolean;           // 单个权限检查
  hasAnyPermission: (codes: string[]) => boolean;     // 任意权限检查
  hasAllPermissions: (codes: string[]) => boolean;    // 所有权限检查
  getPermissionsByType: (type) => Permission[];       // 按类型获取
  getMenuPermissions: () => Permission[];             // 获取菜单权限
  refreshPermissions: () => Promise<void>;            // 刷新权限
}
```

### Permission 类型定义

```typescript
interface Permission {
  id: string;
  permission_code: string;     // 如 'agent:config:read'
  resource: string;            // 如 'agent'
  action: string;              // 如 'read'
  resource_path?: string;      // 如 '/agent-config'
  permission_type: 'menu' | 'api' | 'button' | 'data';
  description?: string;
  parent_id?: string;
  sort_order: number;
  icon?: string;
  is_visible: boolean;
}
```

## 📋 下一步工作

### 需要完成的组件：

1. **DefaultHeader 组件** (`console/src/layouts/default/Header.tsx`)
   - Logo + 项目标题
   - 顶部导航菜单
   - 用户信息下拉菜单
   - 侧边栏折叠按钮

2. **DefaultSidebar 组件** (`console/src/layouts/default/Sidebar.tsx`)
   - 手风琴菜单（同时只展开一个）
   - 集成 `usePermissions` Hook
   - 根据权限过滤菜单项
   - 支持折叠/展开
   - 图标 + 文字

3. **菜单配置** (`console/src/layouts/default/constants.ts`)
   - 定义菜单结构
   - 每个菜单项关联 `permission` 字段
   - 支持多级菜单

### 示例菜单配置：

```typescript
export const menuConfig = [
  {
    key: 'chat',
    label: '对话',
    icon: 'MessageOutlined',
    path: '/chat',
    permission: 'chat:access',
  },
  {
    key: 'agent',
    label: 'Agent 管理',
    icon: 'RobotOutlined',
    permission: 'agent:config:read',
    children: [
      {
        key: 'agent-config',
        label: 'Agent 配置',
        path: '/agent-config',
        permission: 'agent:config:read',
      },
      {
        key: 'skills',
        label: '技能管理',
        path: '/skills',
        permission: 'agent:skill:read',
      },
    ],
  },
  // ...
];
```

## 🔧 集成步骤

### 1. 切换到 Default 布局

修改 `console/src/App.tsx` 或路由配置：

```tsx
// 旧版（个人版）
import MainLayout from './layouts/MainLayout';

// 新版（企业版，支持权限）
import DefaultLayout from './layouts/default';
```

### 2. 在页面中使用权限控制

```tsx
import { PermissionGuard } from '@/components/PermissionGuard';

function AgentPage() {
  return (
    <div>
      <h1>Agent 管理</h1>
      
      {/* 只有有权限的用户才能看到 */}
      <PermissionGuard permission="agent:create">
        <Button>创建 Agent</Button>
      </PermissionGuard>
      
      <AgentList />
    </div>
  );
}
```

### 3. 在菜单中使用权限

```tsx
import { usePermissions } from '@/hooks/usePermissions';
import { menuConfig } from './constants';

function DefaultSidebar() {
  const { hasPermission, getMenuPermissions } = usePermissions();
  
  // 过滤有权限的菜单项
  const visibleMenus = menuConfig.filter(
    menu => !menu.permission || hasPermission(menu.permission)
  );
  
  return <Menu items={visibleMenus} />;
}
```

## 🎨 UI/UX 特性

1. **权限加载状态**
   - 加载中显示 skeleton 或 spinner
   - 加载失败显示错误提示

2. **无权限提示**
   - 可自定义 fallback 内容
   - 默认隐藏无权限组件

3. **系统管理员特权**
   - 系统管理员自动拥有所有权限
   - 无需逐个分配权限

4. **缓存机制**
   - 权限数据缓存在 Hook 内部
   - 支持手动刷新

## 📊 权限码规范

参考后端初始化数据（55个权限）：

| 模块 | 权限码示例 | 数量 |
|------|-----------|------|
| Agent | `agent:config:read`, `agent:skill:write` | 8 |
| 通道 | `channel:read`, `channel:manage` | 3 |
| 会话 | `session:read`, `session:delete` | 3 |
| 用户 | `user:read`, `user:manage` | 3 |
| 角色 | `role:read`, `role:manage` | 3 |
| 安全 | `security:read`, `dlp:rule:execute` | 9 |
| 审计 | `audit:log:read`, `audit:log:export` | 2 |
| ... | ... | ... |

## 🚀 测试建议

1. **单元测试**
   - 测试 `hasPermission()` 逻辑
   - 测试权限树构建
   - 测试系统管理员特权

2. **集成测试**
   - 测试权限 API 调用
   - 测试权限变更后的 UI 更新
   - 测试菜单权限过滤

3. **E2E 测试**
   - 登录不同角色用户
   - 验证菜单显示/隐藏
   - 验证按钮启用/禁用

## 📝 注意事项

1. **权限码一致性**
   - 前端使用的权限码必须与后端一致
   - 建议从后端 API 动态获取

2. **性能优化**
   - 权限数据缓存在 Hook 中
   - 避免重复 API 调用
   - 使用 `useMemo` 优化计算

3. **错误处理**
   - 权限 API 失败时降级处理
   - 显示友好的错误提示

4. **安全性**
   - 前端权限控制仅用于 UI 展示
   - 真正的权限验证在后端 API 层
