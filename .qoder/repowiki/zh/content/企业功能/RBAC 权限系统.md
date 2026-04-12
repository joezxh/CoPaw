# RBAC 权限系统

<cite>
**本文引用的文件**
- [rbac_service.py](file://src/copaw/enterprise/rbac_service.py)
- [permission.py](file://src/copaw/db/models/permission.py)
- [role.py](file://src/copaw/db/models/role.py)
- [user.py](file://src/copaw/db/models/user.py)
- [organization.py](file://src/copaw/db/models/organization.py)
- [middleware.py](file://src/copaw/enterprise/middleware.py)
- [roles.py](file://src/copaw/app/routers/roles.py)
- [user_groups.py](file://src/copaw/app/routers/user_groups.py)
- [auth_service.py](file://src/copaw/enterprise/auth_service.py)
- [audit_service.py](file://src/copaw/enterprise/audit_service.py)
- [base.py](file://src/copaw/db/models/base.py)
</cite>

## 目录
1. [简介](#简介)
2. [项目结构](#项目结构)
3. [核心组件](#核心组件)
4. [架构总览](#架构总览)
5. [详细组件分析](#详细组件分析)
6. [依赖分析](#依赖分析)
7. [性能考量](#性能考量)
8. [故障排查指南](#故障排查指南)
9. [结论](#结论)
10. [附录](#附录)

## 简介
本文件面向 CoPaw 企业版 RBAC（基于角色的访问控制）权限控制系统，系统性阐述权限模型设计、角色层级管理、权限继承机制、组织架构映射、权限检查流程、角色与用户组管理、审计与安全中间件集成，以及性能优化与调试实践。目标是帮助产品、研发与运维团队建立清晰、可维护、可扩展且合规的权限管理体系。

## 项目结构
围绕企业版 RBAC 的关键代码分布在以下模块：
- 数据模型层：角色、权限、用户、用户组、部门等 ORM 模型
- 权限服务层：RBACService 提供权限检查、角色 CRUD、权限分配、用户角色分配/撤销等能力
- 路由层：企业版角色与权限、用户组管理 API
- 认证与中间件：JWT 解码、会话校验、DLP 内容扫描与拦截
- 审计服务：ISO 27001 合规的审计日志记录与查询
- 基础设施：多租户隔离、UUID 主键、时间戳等通用混入

```mermaid
graph TB
subgraph "路由层"
R1["角色与权限路由<br/>roles.py"]
R2["用户组路由<br/>user_groups.py"]
end
subgraph "权限服务层"
S1["RBACService<br/>rbac_service.py"]
end
subgraph "认证与中间件"
M1["企业认证中间件<br/>middleware.py"]
A1["AuthService<br/>auth_service.py"]
end
subgraph "数据模型层"
D1["权限模型<br/>permission.py"]
D2["角色模型<br/>role.py"]
D3["用户模型<br/>user.py"]
D4["部门模型<br/>organization.py"]
B1["基础混入<br/>base.py"]
end
subgraph "审计服务"
AU["AuditService<br/>audit_service.py"]
end
R1 --> S1
R2 --> S1
R1 --> AU
R2 --> AU
S1 --> D1
S1 --> D2
S1 --> D3
S1 --> D4
M1 --> A1
M1 --> S1
```

图表来源
- [roles.py:1-259](file://src/copaw/app/routers/roles.py#L1-L259)
- [user_groups.py:1-278](file://src/copaw/app/routers/user_groups.py#L1-L278)
- [rbac_service.py:1-262](file://src/copaw/enterprise/rbac_service.py#L1-L262)
- [middleware.py:1-191](file://src/copaw/enterprise/middleware.py#L1-L191)
- [auth_service.py:1-367](file://src/copaw/enterprise/auth_service.py#L1-L367)
- [permission.py:1-49](file://src/copaw/db/models/permission.py#L1-L49)
- [role.py:1-150](file://src/copaw/db/models/role.py#L1-L150)
- [user.py:1-158](file://src/copaw/db/models/user.py#L1-L158)
- [organization.py:1-88](file://src/copaw/db/models/organization.py#L1-L88)
- [audit_service.py:1-135](file://src/copaw/enterprise/audit_service.py#L1-L135)
- [base.py:1-76](file://src/copaw/db/models/base.py#L1-L76)

章节来源
- [roles.py:1-259](file://src/copaw/app/routers/roles.py#L1-L259)
- [user_groups.py:1-278](file://src/copaw/app/routers/user_groups.py#L1-L278)
- [rbac_service.py:1-262](file://src/copaw/enterprise/rbac_service.py#L1-L262)
- [middleware.py:1-191](file://src/copaw/enterprise/middleware.py#L1-L191)
- [auth_service.py:1-367](file://src/copaw/enterprise/auth_service.py#L1-L367)
- [permission.py:1-49](file://src/copaw/db/models/permission.py#L1-L49)
- [role.py:1-150](file://src/copaw/db/models/role.py#L1-L150)
- [user.py:1-158](file://src/copaw/db/models/user.py#L1-L158)
- [organization.py:1-88](file://src/copaw/db/models/organization.py#L1-L88)
- [audit_service.py:1-135](file://src/copaw/enterprise/audit_service.py#L1-L135)
- [base.py:1-76](file://src/copaw/db/models/base.py#L1-L76)

## 核心组件
- 权限模型 Permission：资源与操作的最小权限单元，支持通配符匹配
- 角色模型 Role：支持最多 5 级父子层级，可绑定部门与系统角色标记
- 关联模型 RolePermission、UserRole：角色-权限多对多、用户-角色多对多
- 用户模型 User：用户基本信息、部门归属、状态与 MFA 加密存储
- 用户组 UserGroup 及成员 UserGroupMember：按团队/部门维度进行用户分组
- 部门 Department：组织架构树，邻接表+递归 CTE 支持祖先/后代链遍历
- RBACService：权限检查、角色 CRUD、权限分配、用户角色分配/撤销、缓存失效
- 企业认证中间件 EnterpriseAuthMiddleware：JWT 校验、注入用户上下文、DLP 扫描
- AuthService：注册/登录/登出、JWT 签发、会话生命周期、MFA
- AuditService：审计日志记录与查询，覆盖角色与权限变更

章节来源
- [permission.py:18-49](file://src/copaw/db/models/permission.py#L18-L49)
- [role.py:24-150](file://src/copaw/db/models/role.py#L24-L150)
- [user.py:25-158](file://src/copaw/db/models/user.py#L25-L158)
- [organization.py:21-88](file://src/copaw/db/models/organization.py#L21-L88)
- [rbac_service.py:30-262](file://src/copaw/enterprise/rbac_service.py#L30-L262)
- [middleware.py:57-191](file://src/copaw/enterprise/middleware.py#L57-L191)
- [auth_service.py:107-367](file://src/copaw/enterprise/auth_service.py#L107-L367)
- [audit_service.py:51-135](file://src/copaw/enterprise/audit_service.py#L51-L135)

## 架构总览
下图展示从请求到权限判定、再到审计与 DLP 的完整链路，体现企业版 RBAC 的关键交互点。

```mermaid
sequenceDiagram
participant Client as "客户端"
participant Router as "FastAPI 路由<br/>roles.py / user_groups.py"
participant MW as "企业认证中间件<br/>middleware.py"
participant SVC as "RBACService<br/>rbac_service.py"
participant DB as "数据库<br/>SQLAlchemy"
participant AUD as "审计服务<br/>audit_service.py"
Client->>MW : 发起受保护请求
MW->>MW : 校验 JWT 与公开路径
MW->>Router : 注入用户上下文并放行
Router->>SVC : has_permission()/角色/权限操作
SVC->>DB : 查询用户角色/角色层级/权限
DB-->>SVC : 返回权限集合
SVC-->>Router : 返回权限判定结果
Router->>AUD : 记录审计日志
AUD-->>Router : 完成写入
Router-->>Client : 返回响应
```

图表来源
- [middleware.py:69-144](file://src/copaw/enterprise/middleware.py#L69-L144)
- [roles.py:78-259](file://src/copaw/app/routers/roles.py#L78-L259)
- [user_groups.py:56-278](file://src/copaw/app/routers/user_groups.py#L56-L278)
- [rbac_service.py:35-124](file://src/copaw/enterprise/rbac_service.py#L35-L124)
- [audit_service.py:54-87](file://src/copaw/enterprise/audit_service.py#L54-L87)

## 详细组件分析

### 权限模型与匹配规则
- 权限由“资源:操作”构成，支持通配符匹配，包括“资源:*”、“*:操作”、“*:*
- 匹配优先级：精确匹配 > 资源通配 > 全局通配；在权限检查时一次性加载用户所有权限并进行 O(n) 判断
- 权限持久化于 sys_permissions 表，与角色通过 sys_role_permissions 关联

```mermaid
flowchart TD
Start(["开始"]) --> Load["加载用户权限列表"]
Load --> CheckExact{"是否存在精确匹配?"}
CheckExact --> |是| Allow["允许访问"]
CheckExact --> |否| CheckResWildcard{"是否存在资源通配?"}
CheckResWildcard --> |是| Allow
CheckResWildcard --> |否| CheckGlobal{"是否存在全局通配?"}
CheckGlobal --> |是| Allow
CheckGlobal --> |否| Deny["拒绝访问"]
Allow --> End(["结束"])
Deny --> End
```

图表来源
- [rbac_service.py:253-262](file://src/copaw/enterprise/rbac_service.py#L253-L262)
- [permission.py:27-40](file://src/copaw/db/models/permission.py#L27-L40)

章节来源
- [rbac_service.py:253-262](file://src/copaw/enterprise/rbac_service.py#L253-L262)
- [permission.py:18-49](file://src/copaw/db/models/permission.py#L18-L49)

### 角色层级与继承
- 角色支持最多 5 级父子层级，通过 parent_role_id 维护树形结构
- 权限继承：用户的所有直接角色与其祖先角色（最多 5 层）共同决定最终权限集
- 层级展开采用广度优先搜索，逐层收集父角色 ID 并去重，避免循环与重复查询

```mermaid
classDiagram
class Role {
+uuid id
+string name
+uuid parent_role_id
+int level
+uuid department_id
+bool is_system_role
+children : Role[]
+permissions : RolePermission[]
+user_roles : UserRole[]
}
class RolePermission {
+uuid role_id
+uuid permission_id
+datetime granted_at
+role : Role
+permission : Permission
}
class Permission {
+uuid id
+string resource
+string action
+string description
+roles : RolePermission[]
}
Role <|-- Role : "父子关系"
Role "1" --> "*" RolePermission : "拥有"
Permission "1" --> "*" RolePermission : "被授予"
```

图表来源
- [role.py:24-150](file://src/copaw/db/models/role.py#L24-L150)
- [permission.py:18-49](file://src/copaw/db/models/permission.py#L18-L49)

章节来源
- [rbac_service.py:80-124](file://src/copaw/enterprise/rbac_service.py#L80-L124)
- [role.py:24-150](file://src/copaw/db/models/role.py#L24-L150)

### 用户、用户组与组织架构
- 用户与部门通过外键关联，支持部门负责人与成员关系
- 用户组用于按团队/小队/部门维度进行用户分组，便于批量权限与任务协作
- 组成员关系为多对多，支持批量添加/移除

```mermaid
classDiagram
class User {
+uuid id
+string username
+uuid department_id
+string status
+bool mfa_enabled
+roles : UserRole[]
+group_memberships : UserGroupMember[]
}
class UserGroup {
+uuid id
+string name
+uuid department_id
+members : UserGroupMember[]
}
class UserGroupMember {
+uuid user_id
+uuid group_id
+datetime joined_at
+user : User
+group : UserGroup
}
class Department {
+uuid id
+string name
+uuid parent_id
+uuid manager_id
+int level
+members : User[]
+manager : User
}
User --> Department : "属于"
UserGroup --> Department : "属于"
User "many" --> "many" UserGroupMember
UserGroupMember --> UserGroup : "成员"
```

图表来源
- [user.py:25-158](file://src/copaw/db/models/user.py#L25-L158)
- [user_groups.py:96-158](file://src/copaw/db/models/user.py#L96-L158)
- [organization.py:21-88](file://src/copaw/db/models/organization.py#L21-L88)

章节来源
- [user.py:25-158](file://src/copaw/db/models/user.py#L25-L158)
- [user_groups.py:56-278](file://src/copaw/app/routers/user_groups.py#L56-L278)
- [organization.py:21-88](file://src/copaw/db/models/organization.py#L21-L88)

### 权限检查与缓存
- 缓存键格式：rbac:user:{user_id}:perms，值为 JSON 序列的“资源:操作”集合
- 缓存 TTL：默认 300 秒；当角色权限或用户角色发生变更时，主动失效相关用户的权限缓存
- 权限检查流程：先查缓存命中则直接返回，未命中则从数据库加载并写入缓存

```mermaid
sequenceDiagram
participant C as "调用方"
participant S as "RBACService"
participant R as "Redis"
participant DB as "数据库"
C->>S : has_permission(user_id, resource, action)
S->>R : GET rbac : user : {user_id} : perms
alt 命中
R-->>S : JSON 权限列表
S-->>C : 匹配结果
else 未命中
S->>DB : 查询用户角色与权限
DB-->>S : 权限集合
S->>R : SET rbac : user : {user_id} : perms(JSON)
S-->>C : 匹配结果
end
```

图表来源
- [rbac_service.py:35-64](file://src/copaw/enterprise/rbac_service.py#L35-L64)

章节来源
- [rbac_service.py:27-64](file://src/copaw/enterprise/rbac_service.py#L27-L64)

### 角色与权限管理 API
- 角色：创建、更新、删除、查询、列出；支持设置父角色、部门、系统角色标记
- 权限：创建、查询、列出；权限与角色通过批量替换式接口进行分配
- 审计：所有角色与权限相关操作均记录审计日志

```mermaid
sequenceDiagram
participant Admin as "管理员"
participant API as "角色路由<br/>roles.py"
participant SVC as "RBACService"
participant DB as "数据库"
participant AUD as "AuditService"
Admin->>API : POST /roles
API->>SVC : create_role(...)
SVC->>DB : 写入角色
DB-->>SVC : 角色ID
SVC-->>API : 角色对象
API->>AUD : 记录审计
API-->>Admin : 返回角色
Admin->>API : PUT /roles/{id}/permissions
API->>SVC : assign_permissions(role_id, ids)
SVC->>DB : 清空旧权限并写入新权限
SVC->>Redis : 删除用户权限缓存
API-->>Admin : 更新完成
```

图表来源
- [roles.py:91-235](file://src/copaw/app/routers/roles.py#L91-L235)
- [rbac_service.py:127-184](file://src/copaw/enterprise/rbac_service.py#L127-L184)
- [audit_service.py:54-87](file://src/copaw/enterprise/audit_service.py#L54-L87)

章节来源
- [roles.py:78-259](file://src/copaw/app/routers/roles.py#L78-L259)
- [rbac_service.py:127-234](file://src/copaw/enterprise/rbac_service.py#L127-L234)
- [audit_service.py:51-135](file://src/copaw/enterprise/audit_service.py#L51-L135)

### 用户组管理 API
- 用户组：创建、更新、删除、查询、分页列表、按部门过滤
- 成员管理：批量添加、移除成员；添加为幂等操作
- 审计：记录组创建/更新/删除、成员增删事件

```mermaid
sequenceDiagram
participant Admin as "管理员"
participant API as "用户组路由<br/>user_groups.py"
participant DB as "数据库"
participant AUD as "AuditService"
Admin->>API : POST /groups
API->>DB : 创建用户组
API->>AUD : 记录审计
API-->>Admin : 返回组信息
Admin->>API : POST /groups/{id}/members
API->>DB : 批量添加成员(幂等)
API->>AUD : 记录审计
API-->>Admin : 返回添加统计
```

图表来源
- [user_groups.py:87-278](file://src/copaw/app/routers/user_groups.py#L87-L278)
- [audit_service.py:54-87](file://src/copaw/enterprise/audit_service.py#L54-L87)

章节来源
- [user_groups.py:56-278](file://src/copaw/app/routers/user_groups.py#L56-L278)
- [audit_service.py:51-135](file://src/copaw/enterprise/audit_service.py#L51-L135)

### 认证中间件与会话管理
- 企业认证中间件负责：跳过公开路径与 OPTIONS、提取并验证 JWT、注入用户上下文、DLP 内容扫描与拦截
- AuthService 负责：注册/登录/登出、签发/校验/吊销令牌、会话生命周期、MFA
- 中间件不直接访问数据库进行权限校验，权限校验由 RBACService 在路由层完成

```mermaid
sequenceDiagram
participant Client as "客户端"
participant MW as "企业认证中间件"
participant Auth as "AuthService"
participant Router as "业务路由"
participant SVC as "RBACService"
Client->>MW : 请求受保护资源
MW->>MW : 跳过公开路径/OPTIONS
MW->>Auth : decode_access_token()
Auth-->>MW : payload 或 None
alt 有效
MW->>Router : 注入用户上下文
Router->>SVC : has_permission(...)
SVC-->>Router : true/false
Router-->>Client : 响应
else 无效
MW-->>Client : 401/403
end
```

图表来源
- [middleware.py:69-144](file://src/copaw/enterprise/middleware.py#L69-L144)
- [auth_service.py:93-103](file://src/copaw/enterprise/auth_service.py#L93-L103)
- [rbac_service.py:35-64](file://src/copaw/enterprise/rbac_service.py#L35-L64)

章节来源
- [middleware.py:57-191](file://src/copaw/enterprise/middleware.py#L57-L191)
- [auth_service.py:107-367](file://src/copaw/enterprise/auth_service.py#L107-L367)
- [rbac_service.py:30-64](file://src/copaw/enterprise/rbac_service.py#L30-L64)

## 依赖分析
- 权限服务依赖数据库模型：Permission、Role、UserRole、RolePermission、User、Department
- 路由层依赖 RBACService 与审计服务；用户组路由依赖用户与组模型
- 中间件依赖 AuthService 进行 JWT 解码，并在响应阶段进行 DLP 扫描
- 多租户隔离通过 TenantAwareMixin 统一约束，确保数据隔离

```mermaid
graph LR
SVC["RBACService"] --> PM["Permission"]
SVC --> RM["Role"]
SVC --> UR["UserRole"]
SVC --> RP["RolePermission"]
SVC --> UM["User"]
SVC --> DM["Department"]
ROLES["角色路由"] --> SVC
ROLES --> AUD["AuditService"]
GROUPS["用户组路由"] --> UM
GROUPS --> DM
GROUPS --> AUD
MW["企业认证中间件"] --> AUTH["AuthService"]
MW --> SVC
```

图表来源
- [rbac_service.py:21-25](file://src/copaw/enterprise/rbac_service.py#L21-L25)
- [roles.py:19-24](file://src/copaw/app/routers/roles.py#L19-L24)
- [user_groups.py:18-22](file://src/copaw/app/routers/user_groups.py#L18-L22)
- [middleware.py:22-25](file://src/copaw/enterprise/middleware.py#L22-L25)

章节来源
- [rbac_service.py:21-25](file://src/copaw/enterprise/rbac_service.py#L21-L25)
- [roles.py:19-24](file://src/copaw/app/routers/roles.py#L19-L24)
- [user_groups.py:18-22](file://src/copaw/app/routers/user_groups.py#L18-L22)
- [middleware.py:22-25](file://src/copaw/enterprise/middleware.py#L22-L25)

## 性能考量
- 缓存策略：权限检查使用 Redis 缓存，TTL 默认 300 秒；权限或角色变更时主动失效相关用户缓存，避免陈旧权限
- 查询优化：角色层级展开限制为 5 层，减少深层遍历成本；权限集合一次性加载后进行内存匹配
- 会话与令牌：中间件仅做签名与过期校验，实际吊销检查在路由层按需执行，降低中间件开销
- 批量操作：用户组成员批量添加为幂等，减少重复写入；角色权限分配采用“清空-重建”以简化逻辑与保证一致性

[本节为通用性能指导，无需列出具体文件来源]

## 故障排查指南
- 权限不生效
  - 检查用户是否已分配角色，且角色层级不超过 5 层
  - 确认权限字符串格式为“资源:操作”，并考虑通配符匹配规则
  - 若刚变更权限，请等待缓存过期或触发缓存失效
- 角色/权限变更后仍提示旧权限
  - 确认 RBACService 在权限或角色变更时已清理相关用户缓存键
  - 检查 Redis 是否可用，以及缓存键命名是否一致
- 登录失败或被拒绝
  - 中间件返回 401/403 时，确认 JWT 是否有效、是否被吊销、是否命中 DLP 拦截
  - 使用 AuthService 的令牌校验接口确认会话状态
- 审计与合规
  - 使用 AuditService 查询接口定位问题操作人、时间、结果与上下文
  - 对敏感操作开启 is_sensitive 标记，便于审计追踪

章节来源
- [rbac_service.py:175-184](file://src/copaw/enterprise/rbac_service.py#L175-L184)
- [middleware.py:86-144](file://src/copaw/enterprise/middleware.py#L86-L144)
- [audit_service.py:90-135](file://src/copaw/enterprise/audit_service.py#L90-L135)

## 结论
CoPaw 企业版 RBAC 通过清晰的数据模型、严格的层级继承与高效的缓存策略，构建了可扩展、可观测、可审计的权限体系。结合企业认证中间件与审计服务，实现了从登录到权限判定、再到合规审计的全链路闭环。建议在生产环境中配合缓存监控、权限变更审计与 DLP 策略，持续优化权限治理与安全运营。

[本节为总结性内容，无需列出具体文件来源]

## 附录
- 多租户隔离：所有实体均继承 TenantAwareMixin，默认租户 ID 为 default-tenant，可通过请求头或 JWT 注入
- 时间戳与软删除：统一使用 TimestampMixin 与 SoftDeleteMixin，便于审计与数据恢复
- 组织架构：Department 支持邻接表与递归 CTE 遍历，满足复杂组织关系查询需求

章节来源
- [base.py:65-76](file://src/copaw/db/models/base.py#L65-L76)
- [organization.py:26-36](file://src/copaw/db/models/organization.py#L26-L36)