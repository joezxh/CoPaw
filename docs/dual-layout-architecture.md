# CoPaw 双布局架构说明

## 📐 架构概述

CoPaw 现在支持两种布局模式，分别面向不同的使用场景：

| 布局 | 版本 | 权限控制 | 目标用户 |
|------|------|---------|---------|
| **Default Layout** | 企业版 | ✅ 完整权限控制 | 企业用户、团队 |
| **Copaw Layout** | 个人版 | ❌ 无权限控制 | 个人开发者 |

## 📁 目录结构

```
console/src/layouts/
├── default/              # 企业版布局（新增）
│   ├── index.tsx         # 主布局文件
│   ├── Sidebar.tsx       # 侧边栏（手风琴菜单 + 权限过滤）
│   ├── Header.tsx        # 顶部导航栏
│   ├── constants.tsx     # 菜单配置（含权限码）
│   └── index.module.less # 样式文件
│
├── copaw/                # 个人版布局（从旧布局迁移）
│   ├── index.tsx         # 主布局文件
│   ├── Sidebar.tsx       # 侧边栏（传统菜单）
│   ├── Header.tsx        # 顶部导航栏
│   ├── constants.ts      # 菜单配置
│   └── index.module.less # 样式文件
│
└── MainLayout/           # 旧入口（已废弃，保留兼容）
    └── index.tsx
```

## 🚀 使用方法

### 方式 1: 环境变量控制

#### 企业版（默认）
```bash
# 使用默认配置
cd console
npm run dev

# 或显式指定
VITE_APP_EDITION=enterprise npm run dev
```

#### 个人版
```bash
# 方式 1: 修改 .env 文件
# 编辑 console/.env，添加：
VITE_APP_EDITION=personal

# 方式 2: 使用专用环境文件
cp .env.personal .env
npm run dev

# 方式 3: 命令行指定
VITE_APP_EDITION=personal npm run dev
```

### 方式 2: 代码中直接切换

编辑 `console/src/App.tsx`：

```tsx
// 企业版
const LayoutComponent = DefaultLayout;

// 个人版
const LayoutComponent = CopawLayout;
```

## 🎯 功能对比

### Default Layout（企业版）

#### ✅ 核心特性
- **权限控制**: 集成 `usePermissions` Hook
- **权限过滤**: 自动隐藏无权限菜单项
- **手风琴菜单**: 同时只展开一个子菜单
- **角色管理**: 支持 6 种默认角色
- **审计日志**: 记录所有权限操作

#### 📋 权限码示例
```typescript
// 菜单配置
{
  key: 'agent-config',
  label: 'Agent 配置',
  path: '/agent-config',
  permission: 'agent:config:read',  // ← 权限码
}
```

#### 🔐 权限检查
```tsx
// Hook 方式
const { hasPermission } = usePermissions();
if (hasPermission('agent:config:read')) {
  // 显示内容
}

// 组件方式
<PermissionGuard permission="agent:config:read">
  <YourComponent />
</PermissionGuard>

// 按钮方式
<PermissionButton 
  permission="agent:create" 
  button={<Button>创建 Agent</Button>} 
/>
```

### Copaw Layout（个人版）

#### ✅ 核心特性
- **简洁快速**: 无权限检查，直接渲染
- **完整功能**: 所有菜单项始终可见
- **向后兼容**: 与旧版布局完全一致
- **个人使用**: 适合单人开发环境

#### 📋 菜单配置
```typescript
// 无需权限码
{
  key: 'agent-config',
  label: 'Agent 配置',
  path: '/agent-config',
  // 无 permission 字段
}
```

## 🔧 技术实现

### 布局选择逻辑

```tsx
// App.tsx
const appEdition = import.meta.env.VITE_APP_EDITION || "enterprise";
const LayoutComponent = appEdition === "personal" ? CopawLayout : DefaultLayout;

// 路由中使用
<Route
  path="/*"
  element={
    <AuthGuard>
      <LayoutComponent />
    </AuthGuard>
  }
/>
```

### 权限加载流程（仅企业版）

```
1. 用户登录
   ↓
2. AuthGuard 验证 Token
   ↓
3. DefaultLayout 加载
   ↓
4. usePermissions Hook 调用 /api/v1/auth/permissions
   ↓
5. 获取用户权限列表和角色
   ↓
6. filterMenuByPermission() 过滤菜单
   ↓
7. 渲染过滤后的菜单
```

## 📊 数据库要求

### 企业版（Default Layout）

需要以下数据库表和初始化数据：

```bash
# 1. 执行数据库迁移
python run_migration.py

# 2. 初始化权限数据
python scripts/init_permissions.py --tenant-id default-tenant

# 3. 验证权限
python verify_permissions.py
```

**必需表**:
- `sys_permissions` - 权限表（48个默认权限）
- `sys_roles` - 角色表（6个默认角色）
- `sys_user_roles` - 用户角色关联表
- `sys_role_permissions` - 角色权限关联表
- `sys_audit_logs` - 审计日志表

### 个人版（Copaw Layout）

**无需额外数据库表**，使用原有数据库结构即可。

## 🎨 自定义布局

### 创建新布局

1. 在 `console/src/layouts/` 下创建新目录
```bash
mkdir console/src/layouts/custom
```

2. 创建布局文件
```tsx
// console/src/layouts/custom/index.tsx
import Sidebar from "./Sidebar";
import Header from "./Header";
// ...

export default function CustomLayout() {
  return (
    <Layout>
      <Header />
      <Sidebar />
      <Content>...</Content>
    </Layout>
  );
}
```

3. 在 App.tsx 中注册
```tsx
import CustomLayout from "./layouts/custom";

// 添加选择逻辑
const LayoutComponent = {
  enterprise: DefaultLayout,
  personal: CopawLayout,
  custom: CustomLayout,
}[appEdition] || DefaultLayout;
```

## 🔍 调试技巧

### 查看当前使用的布局

在浏览器控制台执行：
```javascript
console.log('Current Edition:', import.meta.env.VITE_APP_EDITION);
```

### 强制切换布局

临时修改 `App.tsx`：
```tsx
// 强制使用企业版
const LayoutComponent = DefaultLayout;

// 强制使用个人版
const LayoutComponent = CopawLayout;
```

### 权限调试

```tsx
// 在组件中打印权限信息
const { permissions, roles, loading } = usePermissions();

useEffect(() => {
  console.log('User Permissions:', permissions);
  console.log('User Roles:', roles);
  console.log('Loading:', loading);
}, [permissions, roles, loading]);
```

## 📝 迁移指南

### 从旧布局迁移到 Copaw Layout

旧布局文件已从 `layouts/` 根目录移动到 `layouts/copaw/`，导入路径需要更新：

```tsx
// 旧代码
import Sidebar from "../layouts/Sidebar";
import Header from "../layouts/Header";

// 新代码
import Sidebar from "../layouts/copaw/Sidebar";
import Header from "../layouts/copaw/Header";
```

**但是**，如果使用 `CopawLayout` 入口文件，则无需修改：
```tsx
import CopawLayout from "../layouts/copaw";
// 内部已正确处理所有导入
```

### 企业版新功能接入

1. **添加新菜单项**
```tsx
// console/src/layouts/default/constants.tsx
{
  key: 'new-feature',
  label: '新功能',
  icon: <SparkMagicWandLine size={18} />,
  path: '/new-feature',
  permission: 'feature:access',  // ← 添加权限码
}
```

2. **创建对应权限**
```python
# scripts/init_permissions.py 或数据库
Permission(
    permission_code="feature:access",
    resource="feature",
    action="access",
    resource_path="/new-feature",
    permission_type="menu",
    description="访问新功能",
)
```

3. **分配给角色**
```python
# 将权限添加到角色
role.permissions.append(permission)
```

## ⚠️ 注意事项

### 1. 环境变量优先级

```
命令行 > .env 文件 > 代码默认值
```

示例：
```bash
# .env 中 VITE_APP_EDITION=personal
# 但命令行指定 enterprise，最终使用 enterprise
VITE_APP_EDITION=enterprise npm run dev
```

### 2. 权限 API 依赖

企业版布局依赖后端权限 API：
- `GET /api/v1/auth/permissions` - 获取用户权限
- `GET /api/v1/permissions/tree` - 获取权限树

如果 API 不可用，菜单将显示为空。

### 3. 系统管理员特权

系统管理员角色（`sys_admin`）自动拥有所有权限，无需单独分配。

### 4. 缓存策略

权限数据在组件生命周期内缓存，如需刷新：
```tsx
const { refreshPermissions } = usePermissions();
refreshPermissions(); // 重新从 API 加载
```

## 📚 相关文档

- [权限系统完整实施总结](./permission-system-complete-summary.md)
- [权限系统改造设计](./permission-system-redesign.md)
- [前端权限控制总结](./phase3-frontend-permission-summary.md)
- [编译修复报告](./permission-fix-complete.md)
- [企业存储迁移报告](./PHASE-2-4-FINAL-REPORT.md)

## 🎯 最佳实践

### 开发环境

```bash
# 个人开发：使用个人版（快速）
VITE_APP_EDITION=personal npm run dev

# 企业功能开发：使用企业版
VITE_APP_EDITION=enterprise npm run dev
```

### 生产环境

```bash
# 企业部署
VITE_APP_EDITION=enterprise npm run build

# 个人部署
VITE_APP_EDITION=personal npm run build
```

### 测试环境

```bash
# 测试权限功能
VITE_APP_EDITION=enterprise npm run dev

# 测试基础功能
VITE_APP_EDITION=personal npm run dev
```

---

**更新日期**: 2026-04-13  
**维护人员**: CoPaw Team  
**版本**: v2.0.0
