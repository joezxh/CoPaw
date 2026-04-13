# CoPaw 权限系统改造设计方案

## 📋 概述

本方案参考 risk_control 项目的权限管理设计，对 CoPaw 项目的角色权限系统进行全面改造，实现细粒度的权限控制、前端动态菜单渲染和统一的布局架构。

---

## 1️⃣ 数据模型改造分析

### 1.1 risk_control 权限模型特点

```python
# risk_control/backend/app/models/user.py

Permission 表:
- permission_code: String(100)  # 唯一权限码，如 'admin:dashboard:stats:read'
- permission_type: String(20)   # 权限类型
- resource_path: String(200)    # 资源路径
- parent_id: BigInteger         # 支持权限层次结构

Role 表:
- role_code: String(50)         # 角色编码
- region_code: String(20)       # 区域隔离
- region_level: String(20)      # 区域层级

SysAuditLog 表:
- operation_type: String(50)    # 操作类型
- operation_module: String(50)  # 操作模块
- request_params: JSONB         # 请求参数
- old_data / new_data: JSONB    # 数据变更审计
```

**核心设计理念**：
1. **权限码规范化**：`模块:资源:操作` 格式（如 `admin:users:read`）
2. **资源路径映射**：`resource_path` 字段直接映射到前端路由
3. **审计日志完善**：记录操作类型、模块、参数和数据变更
4. **区域隔离**：支持多级区域权限控制

### 1.2 CoPaw 现有权限模型

```python
# copaw/src/copaw/db/models/permission.py

Permission 表:
- resource: String(200)         # 资源标识（如 'agent:*'）
- action: String(50)            # 操作类型（read/write/execute/manage/*）
- description: String(500)      # 权限描述

Role 表:
- name: String(100)             # 角色名称
- parent_role_id: UUID          # 支持5级层次结构
- level: Integer                # 角色层级（0-5）
- department_id: UUID           # 部门关联
- is_system_role: Boolean       # 系统角色保护

# 缺少字段:
# - permission_code (权限码)
# - resource_path (前端路由映射)
# - operation_type (审计用)
```

### 1.3 改造方案

#### 新增字段（Permission 表）

```python
class Permission(Base, UUIDPrimaryKeyMixin, TenantAwareMixin):
    """权限表 - 支持细粒度权限控制"""
    
    __tablename__ = "sys_permissions"
    
    # 保留现有字段
    resource: Mapped[str] = mapped_column(
        String(200), nullable=False, index=True,
        comment="资源标识(如: 'agent', 'skill', 'model')"
    )
    action: Mapped[str] = mapped_column(
        String(50), nullable=False,
        comment="操作类型: read|write|execute|manage|*"
    )
    description: Mapped[Optional[str]] = mapped_column(
        String(500), nullable=True,
        comment="权限描述"
    )
    
    # ✅ 新增字段 - 参考 risk_control 设计
    permission_code: Mapped[str] = mapped_column(
        String(100), unique=True, nullable=False, index=True,
        comment="权限码(格式: 模块:资源:操作, 如 'agent:config:read')"
    )
    resource_path: Mapped[Optional[str]] = mapped_column(
        String(200), nullable=True,
        comment="前端路由路径(如: '/agent-config')"
    )
    permission_type: Mapped[str] = mapped_column(
        String(20), default="menu", nullable=False,
        comment="权限类型: menu|api|button|data"
    )
    parent_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("sys_permissions.id", ondelete="SET NULL"),
        nullable=True,
        comment="父权限ID(支持权限层次结构)"
    )
    sort_order: Mapped[int] = mapped_column(
        Integer, default=0,
        comment="排序顺序"
    )
    icon: Mapped[Optional[str]] = mapped_column(
        String(100), nullable=True,
        comment="图标标识(前端使用)"
    )
    is_visible: Mapped[bool] = mapped_column(
        Boolean, default=True, nullable=False,
        comment="是否在菜单中可见"
    )
    
    # 审计字段
    created_by: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("sys_users.id", ondelete="SET NULL"),
        nullable=True,
        comment="创建者ID"
    )
```

#### 新增 AuditLog 表

```python
class AuditLog(Base, UUIDPrimaryKeyMixin, TenantAwareMixin):
    """审计日志表 - 记录所有权限相关操作"""
    
    __tablename__ = "sys_audit_logs"
    __table_args__ = (
        Index("idx_audit_operation", "operation_type", "operation_module"),
        Index("idx_audit_user", "user_id", "created_at"),
        {"comment": "审计日志表"},
    )
    
    user_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), nullable=True, index=True,
        comment="操作用户ID"
    )
    username: Mapped[Optional[str]] = mapped_column(
        String(100), nullable=True,
        comment="操作用户名"
    )
    operation_type: Mapped[str] = mapped_column(
        String(50), nullable=False,
        comment="操作类型: create|update|delete|read|login|logout"
    )
    operation_module: Mapped[Optional[str]] = mapped_column(
        String(50), nullable=True,
        comment="操作模块: user|role|permission|agent|skill"
    )
    operation_desc: Mapped[Optional[str]] = mapped_column(
        Text, nullable=True,
        comment="操作描述"
    )
    request_method: Mapped[Optional[str]] = mapped_column(
        String(10), nullable=True,
        comment="HTTP方法: GET|POST|PUT|DELETE"
    )
    request_url: Mapped[Optional[str]] = mapped_column(
        String(500), nullable=True,
        comment="请求URL"
    )
    request_params: Mapped[Optional[dict]] = mapped_column(
        JSONB, nullable=True,
        comment="请求参数"
    )
    request_ip: Mapped[Optional[str]] = mapped_column(
        String(50), nullable=True, index=True,
        comment="请求IP地址"
    )
    user_agent: Mapped[Optional[str]] = mapped_column(
        String(500), nullable=True,
        comment="用户代理"
    )
    response_status: Mapped[Optional[int]] = mapped_column(
        Integer, nullable=True,
        comment="响应状态码"
    )
    response_time_ms: Mapped[Optional[int]] = mapped_column(
        Integer, nullable=True,
        comment="响应时间(毫秒)"
    )
    old_data: Mapped[Optional[dict]] = mapped_column(
        JSONB, nullable=True,
        comment="变更前数据"
    )
    new_data: Mapped[Optional[dict]] = mapped_column(
        JSONB, nullable=True,
        comment="变更后数据"
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), 
        nullable=False, index=True,
        comment="创建时间"
    )
```

---

## 2️⃣ 前端权限控制改造

### 2.1 risk_control 前端权限控制分析

```vue
<!-- risk_control/frontend/src/views/admin/index.vue -->

<!-- 子菜单权限控制 -->
<a-sub-menu v-permission="['admin:dashboard:stats:read', 'admin:users:read']" key="console-group">
  <template #icon><DashboardOutlined /></template>
  <template #title>控制台</template>
  
  <!-- 子项权限控制 -->
  <a-menu-item v-permission="'admin:dashboard:stats:read'" key="dashboard">
    <DashboardOutlined />
    <span>控制台门户</span>
  </a-menu-item>
</a-sub-menu>
```

**核心特点**：
1. `v-permission` 指令控制菜单项显示/隐藏
2. 权限码格式：`模块:资源:操作`
3. 支持单个或多个权限（OR 逻辑）
4. 无权限时整个菜单项不渲染

### 2.2 CoPaw 前端权限控制方案

#### 步骤 1: 创建权限 Hook

```typescript
// console/src/hooks/usePermission.ts

import { useState, useEffect, useCallback } from "react";
import { api } from "../api";

export interface UserPermission {
  permission_code: string;
  resource: string;
  action: string;
  resource_path: string | null;
  permission_type: "menu" | "api" | "button" | "data";
}

export function usePermissions() {
  const [permissions, setPermissions] = useState<UserPermission[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    api.auth
      .getPermissions()
      .then((perms) => setPermissions(perms))
      .catch(() => setPermissions([]))
      .finally(() => setLoading(false));
  }, []);

  const hasPermission = useCallback(
    (permissionCode: string | string[]): boolean => {
      const codes = Array.isArray(permissionCode) ? permissionCode : [permissionCode];
      return codes.some((code) =>
        permissions.some((p) => p.permission_code === code)
      );
    },
    [permissions]
  );

  const hasAnyPermission = useCallback(
    (permissionCodes: string[]): boolean => {
      return permissionCodes.some((code) => hasPermission(code));
    },
    [hasPermission]
  );

  return { permissions, loading, hasPermission, hasAnyPermission };
}
```

#### 步骤 2: 创建权限组件

```typescript
// console/src/components/PermissionGuard/index.tsx

import React from "react";
import { usePermissions } from "../../hooks/usePermission";

interface PermissionGuardProps {
  permission: string | string[];
  fallback?: React.ReactNode;
  children: React.ReactNode;
}

export const PermissionGuard: React.FC<PermissionGuardProps> = ({
  permission,
  fallback = null,
  children,
}) => {
  const { hasPermission, loading } = usePermissions();

  if (loading) return null;
  
  if (!hasPermission(permission)) {
    return <>{fallback}</>;
  }

  return <>{children}</>;
};
```

#### 步骤 3: 改造 Sidebar 菜单

```typescript
// console/src/layouts/Sidebar.tsx (改造后)

import { PermissionGuard } from "../components/PermissionGuard";

const menuItems: MenuProps["items"] = [
  {
    key: "chat",
    label: collapsed ? null : t("nav.chat"),
    icon: <SparkChatTabFill size={16} />,
    // 无需权限控制（默认所有人可见）
  },
  {
    key: "control-group",
    label: collapsed ? null : t("nav.control"),
    // ✅ 子菜单权限控制：拥有任一子项权限则显示
    permission: [
      "channel:read",
      "session:read",
      "cronjob:read",
      "heartbeat:read",
    ],
    children: [
      {
        key: "channels",
        label: collapsed ? null : t("nav.channels"),
        icon: <SparkWifiLine size={16} />,
        permission: "channel:read", // ✅ 子项权限
      },
      {
        key: "sessions",
        label: collapsed ? null : t("nav.sessions"),
        icon: <SparkUserGroupLine size={16} />,
        permission: "session:read",
      },
      // ...
    ],
  },
  {
    key: "enterprise-group",
    label: collapsed ? null : t("nav.enterprise", "Enterprise"),
    permission: [
      "user:manage",
      "role:manage",
      "audit:read",
      "dlp:manage",
    ],
    children: [
      {
        key: "enterprise-users",
        label: collapsed ? null : t("nav.enterpriseUsers", "User Management"),
        icon: <SparkSearchUserLine size={16} />,
        permission: "user:manage",
      },
      {
        key: "enterprise-permissions",
        label: collapsed ? null : t("nav.enterprisePermissions", "Permission Management"),
        icon: <SparkModifyLine size={16} />,
        permission: "role:manage",
      },
      // ...
    ],
  },
];

// 过滤菜单项的函数
function filterMenuItemsByPermission(
  items: MenuProps["items"],
  hasPermission: (code: string | string[]) => boolean
): MenuProps["items"] {
  return items
    .filter((item) => {
      if (!item) return false;
      if ("permission" in item && item.permission) {
        return hasPermission(item.permission as string | string[]);
      }
      return true;
    })
    .map((item) => {
      if (!item) return item;
      if ("children" in item && item.children) {
        return {
          ...item,
          children: filterMenuItemsByPermission(item.children, hasPermission),
        };
      }
      return item;
    })
    .filter((item) => {
      // 过滤掉子项为空的父菜单
      if (item && "children" in item && item.children) {
        return (item.children as any[]).length > 0;
      }
      return true;
    });
}
```

---

## 3️⃣ 布局重构方案

### 3.1 目录结构调整

```
console/src/layouts/
├── copaw/                    # 现有布局（保留）
│   ├── Header.tsx
│   ├── Sidebar.tsx
│   ├── constants.ts
│   └── index.module.less
├── default/                  # 新布局（支持权限控制）
│   ├── index.tsx             # 主布局组件
│   ├── Header.tsx            # 顶部导航
│   ├── Sidebar.tsx           # 左侧菜单（手风琴模式）
│   ├── constants.ts          # 菜单配置
│   ├── PermissionGuard.tsx   # 权限守卫组件
│   └── index.module.less     # 样式文件
└── index.ts                  # 布局导出
```

### 3.2 新布局设计

#### DefaultLayout 主组件

```typescript
// console/src/layouts/default/index.tsx

import React, { useState } from "react";
import { Layout } from "antd";
import { Outlet, useLocation } from "react-router-dom";
import { useTheme } from "../../contexts/ThemeContext";
import { DefaultHeader } from "./Header";
import { DefaultSidebar } from "./Sidebar";
import styles from "./index.module.less";

const { Content } = Layout;

export const DefaultLayout: React.FC = () => {
  const { isDark } = useTheme();
  const location = useLocation();
  const [sidebarCollapsed, setSidebarCollapsed] = useState(false);

  // 从路径中提取 selectedKey
  const selectedKey = location.pathname.split("/").filter(Boolean)[0] || "chat";

  return (
    <Layout className={`${styles.layout} ${isDark ? styles.dark : ""}`}>
      {/* 顶部区域 */}
      <DefaultHeader 
        collapsed={sidebarCollapsed}
        onToggleSidebar={() => setSidebarCollapsed(!sidebarCollapsed)}
      />
      
      <Layout>
        {/* 左侧菜单 */}
        <DefaultSidebar 
          selectedKey={selectedKey}
          collapsed={sidebarCollapsed}
        />
        
        {/* 右侧内容区 */}
        <Content className={styles.content}>
          <Outlet />
        </Content>
      </Layout>
    </Layout>
  );
};
```

#### DefaultSidebar 组件（手风琴模式）

```typescript
// console/src/layouts/default/Sidebar.tsx

import React, { useState } from "react";
import { Layout, Menu, type MenuProps } from "antd";
import { useNavigate } from "react-router-dom";
import { useTranslation } from "react-i18next";
import { usePermissions } from "../../hooks/usePermission";
import { menuConfig } from "./constants";
import styles from "./index.module.less";

const { Sider } = Layout;

interface SidebarProps {
  selectedKey: string;
  collapsed: boolean;
}

export const DefaultSidebar: React.FC<SidebarProps> = ({ 
  selectedKey, 
  collapsed 
}) => {
  const navigate = useNavigate();
  const { t } = useTranslation();
  const { hasPermission, loading } = usePermissions();
  const [openKeys, setOpenKeys] = useState<string[]>([]);

  // 处理手风琴模式
  const handleOpenChange = (keys: string[]) => {
    setOpenKeys((prev) => {
      const latestOpenKey = keys.find((key) => !prev.includes(key));
      return latestOpenKey ? [latestOpenKey] : keys;
    });
  };

  // 过滤菜单（权限控制）
  const filteredMenuItems = React.useMemo(() => {
    if (loading) return [];
    
    return menuConfig
      .filter((item) => {
        if (item.permission) {
          return hasPermission(item.permission);
        }
        return true;
      })
      .map((item) => {
        if (item.children) {
          const filteredChildren = item.children.filter((child) => {
            if (child.permission) {
              return hasPermission(child.permission);
            }
            return true;
          });
          
          // 如果子项过滤后为空，则隐藏父菜单
          if (filteredChildren.length === 0) return null;
          
          return { ...item, children: filteredChildren };
        }
        return item;
      })
      .filter(Boolean) as MenuProps["items"];
  }, [loading, hasPermission]);

  return (
    <Sider
      width={collapsed ? 72 : 240}
      className={`${styles.sider} ${collapsed ? styles.collapsed : ""}`}
      theme={isDark ? "dark" : "light"}
    >
      <Menu
        mode="inline"
        selectedKeys={[selectedKey]}
        openKeys={collapsed ? [] : openKeys}
        onOpenChange={handleOpenChange}
        onClick={({ key }) => {
          const path = menuConfig.find((item) => item.key === key)?.path;
          if (path) navigate(path);
        }}
        items={filteredMenuItems}
        className={styles.menu}
      />
    </Sider>
  );
};
```

### 3.3 菜单配置（带权限码）

```typescript
// console/src/layouts/default/constants.ts

import {
  SparkChatTabFill,
  SparkWifiLine,
  SparkUserGroupLine,
  // ... 其他图标
} from "@agentscope-ai/icons";

export interface MenuItem {
  key: string;
  path?: string;
  label: string;
  icon: React.ReactNode;
  permission?: string | string[]; // ✅ 权限码
  children?: MenuItem[];
}

export const menuConfig: MenuItem[] = [
  {
    key: "chat",
    path: "/chat",
    label: "nav.chat",
    icon: <SparkChatTabFill size={18} />,
    // 无权限要求（默认可见）
  },
  {
    key: "control-group",
    label: "nav.control",
    icon: null,
    permission: ["channel:read", "session:read", "cronjob:read"], // 任一权限即可
    children: [
      {
        key: "channels",
        path: "/channels",
        label: "nav.channels",
        icon: <SparkWifiLine size={18} />,
        permission: "channel:read",
      },
      {
        key: "sessions",
        path: "/sessions",
        label: "nav.sessions",
        icon: <SparkUserGroupLine size={18} />,
        permission: "session:read",
      },
      // ...
    ],
  },
  {
    key: "enterprise-group",
    label: "nav.enterprise",
    icon: null,
    permission: ["user:manage", "role:manage", "audit:read"],
    children: [
      {
        key: "enterprise-users",
        path: "/enterprise/users",
        label: "nav.enterpriseUsers",
        icon: <SparkSearchUserLine size={18} />,
        permission: "user:manage",
      },
      {
        key: "enterprise-permissions",
        path: "/enterprise/permissions",
        label: "nav.enterprisePermissions",
        icon: <SparkModifyLine size={18} />,
        permission: "role:manage",
      },
      // ...
    ],
  },
];
```

### 3.4 路由配置

```typescript
// console/src/App.tsx

import { DefaultLayout } from "./layouts/default";
import { CopawLayout } from "./layouts/copaw";

function App() {
  const isEnterprise = useIsEnterprise(); // 判断是否企业版

  return (
    <Routes>
      {/* 企业版使用新布局 */}
      {isEnterprise ? (
        <Route path="/" element={<DefaultLayout />}>
          <Route path="chat" element={<ChatPage />} />
          <Route path="channels" element={<ChannelsPage />} />
          {/* ... 其他路由 */}
        </Route>
      ) : (
        /* 个人版使用原布局 */
        <Route path="/" element={<CopawLayout />}>
          {/* ... */}
        </Route>
      )}
    </Routes>
  );
}
```

---

## 4️⃣ 权限码规范

### 4.1 命名规则

格式：`模块:资源:操作`

| 模块 | 资源 | 操作 | 示例 |
|------|------|------|------|
| agent | config | read/write/manage | `agent:config:read` |
| agent | skill | read/write/execute | `agent:skill:execute` |
| channel | * | read/write/manage | `channel:read` |
| session | * | read/write/delete | `session:read` |
| user | * | read/write/manage | `user:manage` |
| role | * | read/write/manage | `role:manage` |
| audit | log | read/export | `audit:log:read` |
| skill | pool | read/write | `skill:pool:read` |
| model | * | read/write/deploy | `model:deploy` |
| dlp | rule | read/write/execute | `dlp:rule:execute` |

### 4.2 初始化权限数据

```python
# alembic/versions/009_init_permissions.py

DEFAULT_PERMISSIONS = [
    # Agent 相关
    {"code": "agent:config:read", "resource": "agent", "action": "read", "path": "/agent-config"},
    {"code": "agent:config:write", "resource": "agent", "action": "write", "path": "/agent-config"},
    {"code": "agent:skill:read", "resource": "skill", "action": "read", "path": "/skills"},
    {"code": "agent:skill:execute", "resource": "skill", "action": "execute"},
    
    # 通道相关
    {"code": "channel:read", "resource": "channel", "action": "read", "path": "/channels"},
    {"code": "channel:write", "resource": "channel", "action": "write"},
    {"code": "channel:manage", "resource": "channel", "action": "manage"},
    
    # 会话相关
    {"code": "session:read", "resource": "session", "action": "read", "path": "/sessions"},
    {"code": "session:write", "resource": "session", "action": "write"},
    {"code": "session:delete", "resource": "session", "action": "delete"},
    
    # 用户管理
    {"code": "user:read", "resource": "user", "action": "read", "path": "/enterprise/users"},
    {"code": "user:write", "resource": "user", "action": "write"},
    {"code": "user:manage", "resource": "user", "action": "manage"},
    
    # 角色权限
    {"code": "role:read", "resource": "role", "action": "read", "path": "/enterprise/permissions"},
    {"code": "role:write", "resource": "role", "action": "write"},
    {"code": "role:manage", "resource": "role", "action": "manage"},
    
    # 审计日志
    {"code": "audit:log:read", "resource": "audit", "action": "read", "path": "/enterprise/audit"},
    {"code": "audit:log:export", "resource": "audit", "action": "export"},
    
    # 技能池
    {"code": "skill:pool:read", "resource": "skill", "action": "read", "path": "/skill-pool"},
    {"code": "skill:pool:write", "resource": "skill", "action": "write"},
    
    # 模型管理
    {"code": "model:read", "resource": "model", "action": "read", "path": "/models"},
    {"code": "model:write", "resource": "model", "action": "write"},
    {"code": "model:deploy", "resource": "model", "action": "deploy"},
    
    # DLP
    {"code": "dlp:rule:read", "resource": "dlp", "action": "read", "path": "/enterprise/dlp-rules"},
    {"code": "dlp:rule:write", "resource": "dlp", "action": "write"},
    {"code": "dlp:rule:execute", "resource": "dlp", "action": "execute"},
]

DEFAULT_ROLES = [
    {
        "name": "系统管理员",
        "code": "sys_admin",
        "level": 0,
        "permissions": ["*"],  # 所有权限
    },
    {
        "name": "普通用户",
        "code": "user",
        "level": 1,
        "permissions": [
            "agent:config:read",
            "channel:read",
            "session:read",
            "skill:pool:read",
            "model:read",
        ],
    },
    {
        "name": "Agent管理员",
        "code": "agent_admin",
        "level": 1,
        "permissions": [
            "agent:config:read",
            "agent:config:write",
            "agent:skill:read",
            "agent:skill:execute",
        ],
    },
]
```

---

## 5️⃣ 实施步骤

### Phase 1: 数据模型改造（1-2天）

1. ✅ 新增 Permission 表字段
   - `permission_code`
   - `resource_path`
   - `permission_type`
   - `parent_id`
   - `sort_order`
   - `icon`
   - `is_visible`

2. ✅ 创建 AuditLog 表
   - 参考 risk_control 的 SysAuditLog

3. ✅ 创建数据库迁移文件
   - `009_permission_enhancement.py`

4. ✅ 初始化权限数据
   - 插入默认权限码
   - 创建默认角色

### Phase 2: 后端 API 开发（2-3天）

1. ✅ 创建权限查询 API
   - `GET /api/v1/auth/permissions` - 获取当前用户权限

2. ✅ 创建权限管理 API
   - `GET /api/v1/permissions` - 列出所有权限
   - `POST /api/v1/permissions` - 创建权限
   - `PUT /api/v1/permissions/{id}` - 更新权限
   - `DELETE /api/v1/permissions/{id}` - 删除权限

3. ✅ 创建审计日志 API
   - `GET /api/v1/audit/logs` - 查询审计日志
   - `POST /api/v1/audit/logs/export` - 导出审计日志

4. ✅ 实现权限中间件
   - 自动记录操作审计日志
   - 权限验证装饰器

### Phase 3: 前端权限控制（3-4天）

1. ✅ 创建权限 Hook
   - `usePermissions()`
   - `hasPermission()`
   - `hasAnyPermission()`

2. ✅ 创建权限组件
   - `PermissionGuard`
   - `RequirePermission`

3. ✅ 改造 Sidebar 菜单
   - 添加权限过滤逻辑
   - 支持动态菜单渲染

4. ✅ 创建新布局
   - `layouts/default/`
   - 集成权限控制

### Phase 4: 测试与优化（2-3天）

1. ✅ 单元测试
   - 权限验证逻辑
   - 菜单过滤逻辑

2. ✅ 集成测试
   - 权限控制端到端测试
   - 布局切换测试

3. ✅ 性能优化
   - 权限缓存
   - 菜单懒加载

---

## 6️⃣ 兼容性与迁移

### 6.1 向后兼容

- 保留现有 `resource` + `action` 字段
- 新增 `permission_code` 字段（自动生成）
- 提供迁移脚本自动生成权限码

### 6.2 数据迁移脚本

```python
# 自动生成 permission_code
def migrate_permissions():
    permissions = session.query(Permission).all()
    for perm in permissions:
        if not perm.permission_code:
            perm.permission_code = f"{perm.resource}:{perm.action}"
    session.commit()
```

### 6.3 渐进式启用

1. 第一阶段：仅记录权限，不强制验证
2. 第二阶段：关键接口强制权限验证
3. 第三阶段：所有接口启用权限控制

---

## 7️⃣ 关键差异对比

| 特性 | risk_control | CoPaw 改造后 |
|------|--------------|--------------|
| 权限码格式 | `模块:资源:操作` | `模块:资源:操作` ✅ |
| 前端指令 | `v-permission` (Vue) | `PermissionGuard` (React) |
| 多租户 | ❌ 区域隔离 | ✅ tenant_id |
| 角色层次 | ❌ 扁平 | ✅ 5级层次 |
| 审计日志 | ✅ 完善 | ✅ 完善 |
| 权限类型 | 菜单/API | 菜单/API/按钮/数据 ✅ |
| 资源路径映射 | ✅ resource_path | ✅ resource_path |
| 布局架构 | 单一布局 | 多布局支持 ✅ |

---

## 8️⃣ 总结

本方案完整吸收了 risk_control 项目的权限管理最佳实践，并结合 CoPaw 的企业级多租户架构进行了优化：

✅ **细粒度权限控制**：`模块:资源:操作` 权限码规范  
✅ **前端动态菜单**：基于权限的菜单过滤和渲染  
✅ **完善审计日志**：记录所有操作和数据变更  
✅ **多租户兼容**：保持现有 tenant_id 隔离机制  
✅ **渐进式迁移**：向后兼容，平滑过渡  
✅ **现代化布局**：支持多布局切换和权限控制

**预期收益**：
- 权限管理标准化，降低维护成本
- 前端菜单动态化，提升用户体验
- 审计日志完善化，满足合规要求
- 多租户隔离强化，保障数据安全
