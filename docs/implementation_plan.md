# CoPaw 企业级协同AI产品升级实施计划

将 CoPaw 从个人AI助手扩展为企业级多用户协作办公自动化平台，整合 PostgreSQL/Redis/Neo4j 关系数据库基础设施，实现多用户权限管理、团队任务协作、数据安全增强和自动化工作流编排。

## User Review Required

> [!IMPORTANT]
> **数据库选型确认**：本计划使用以下基础设施组合，请确认是否符合预期：
> - **PostgreSQL** — 核心业务数据（用户/角色/权限/任务/审计日志/工作流）
> - **Redis** — 会话缓存/权限缓存/消息队列/实时状态
> - **Neo4j** — 组织架构关系图谱/权限继承图/任务依赖图/知识图谱

> [!WARNING]
> **Breaking Changes**：
> 1. 现有单用户 `auth.json` 文件认证将迁移到 PostgreSQL 多用户模型
> 2. `config.json` 中的 agent 配置需扩展多租户隔离字段
> 3. 现有 `docker-compose.yml` 将大幅扩展以部署 PG/Redis/Neo4j
> 4. 前端 Console 需从单用户模式升级为多用户+权限控制模式

> [!CAUTION]
> **现有数据兼容性**：升级需提供数据迁移脚本，将现有文件系统数据迁移至 PostgreSQL。请确认是否需要保持向后兼容（单用户模式可降级运行）。

---

## 当前架构分析

### 后端 (`src/copaw/`)
| 模块 | 当前状态 | 企业升级影响 |
|------|---------|------------|
| `app/auth.py` | 单用户 + 文件存储 `auth.json` | → PostgreSQL 多用户 + RBAC |
| `app/_app.py` | FastAPI + AgentScope | → 添加多租户中间件/DB初始化 |
| `app/routers/` | 21个路由模块 | → 添加权限验证装饰器 |
| `config/config.py` | Pydantic + JSON文件 | → 扩展数据库配置/企业配置 |
| `agents/react_agent.py` | 单Agent + ToolGuardMixin | → 多用户Agent隔离 |
| `agents/memory/` | ReMe本地文件存储 | → PostgreSQL/Redis持久化 |
| `security/` | secret_store + tool_guard | → ABAC策略引擎 |
| `plugins/` | 插件系统 | → 企业级插件权限控制 |

### 前端 (`console/`)
| 模块 | 当前状态 | 企业升级影响 |
|------|---------|------------|
| `pages/Login` | 简单用户名密码 | → 企业级登录 + MFA |
| `pages/Chat` | 单用户对话 | → 多用户对话隔离 |
| `pages/Settings` | 个人设置 | → 用户管理/权限管理 |
| `pages/Control` | 基础控制面板 | → 企业管理控制台 |
| `stores/` | 单agentStore | → 多Store（用户/权限/任务/工作流） |

---

## Proposed Changes

### 阶段一：基础设施与数据层（第1-4周）

---

#### 1.1 数据库基础设施

##### [NEW] `src/copaw/db/__init__.py`
数据库包初始化，导出核心连接管理组件。

##### [NEW] `src/copaw/db/postgresql.py`
PostgreSQL 连接管理组件：
- SQLAlchemy 2.0 async engine + session factory
- Alembic 迁移管理集成
- 连接池配置（pool_size=20, max_overflow=10）
- 健康检查与自动重连
- 多租户 schema 隔离支持

```python
# 核心设计
class DatabaseManager:
    engine: AsyncEngine
    session_factory: async_sessionmaker
    
    async def initialize(config: DatabaseConfig)
    async def get_session() -> AsyncSession
    async def health_check() -> bool
    async def run_migrations()
```

##### [NEW] `src/copaw/db/redis_client.py`
Redis 连接管理组件：
- aioredis 异步客户端
- 连接池管理
- 键命名空间隔离（按租户/功能）
- 缓存操作封装（get/set/delete/expire）
- Pub/Sub 消息通道

```python
class RedisManager:
    pool: aioredis.ConnectionPool
    
    async def initialize(config: RedisConfig)
    async def cache_get(key: str) -> Optional[str]
    async def cache_set(key: str, value: str, ttl: int)
    async def publish(channel: str, message: str)
    async def subscribe(channel: str) -> AsyncIterator
```

##### [NEW] `src/copaw/db/neo4j_client.py`
Neo4j 图数据库客户端：
- neo4j Python driver 异步支持
- 组织架构图谱 CRUD
- 权限继承关系查询
- 任务依赖图构建

```python
class Neo4jManager:
    driver: neo4j.AsyncDriver
    
    async def initialize(config: Neo4jConfig)
    async def create_org_node(org: Organization)
    async def query_permission_chain(user_id: str) -> List[Permission]
    async def build_task_dependency_graph(workflow_id: str) -> DAG
```

##### [NEW] `src/copaw/db/models/`
SQLAlchemy ORM 模型定义：

```
db/models/
├── __init__.py
├── base.py              # DeclarativeBase + 通用Mixin（ID/时间戳/软删除）
├── user.py              # User, UserGroup, UserGroupMember
├── role.py              # Role, RolePermission, RoleHierarchy
├── permission.py        # Permission, ABACPolicy
├── organization.py      # Department, Organization
├── task.py              # Task, TaskAssignment, TaskDependency, TaskComment
├── audit_log.py         # AuditLog
├── workflow.py          # Workflow, WorkflowNode, WorkflowExecution
├── agent_config.py      # AgentConfig（多租户隔离）
└── session.py           # UserSession, RefreshToken
```

**核心表设计**：

```sql
-- 用户表
CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    username VARCHAR(100) UNIQUE NOT NULL,
    email VARCHAR(255) UNIQUE,
    password_hash VARCHAR(255) NOT NULL,
    password_salt VARCHAR(64) NOT NULL,
    display_name VARCHAR(200),
    department_id UUID REFERENCES departments(id),
    status VARCHAR(20) DEFAULT 'active',  -- active/disabled/vacation
    mfa_enabled BOOLEAN DEFAULT FALSE,
    mfa_secret VARCHAR(200),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    last_login_at TIMESTAMPTZ
);

-- 角色表（支持层级继承）
CREATE TABLE roles (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(100) UNIQUE NOT NULL,
    description TEXT,
    parent_role_id UUID REFERENCES roles(id),  -- 层级继承
    level INT DEFAULT 0,  -- 角色层级（最多5级）
    department_id UUID REFERENCES departments(id),  -- 可绑定部门
    is_system_role BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- 权限表
CREATE TABLE permissions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    resource VARCHAR(200) NOT NULL,  -- e.g., 'agent:*', 'task:read'
    action VARCHAR(50) NOT NULL,     -- read/write/execute/manage
    description TEXT
);

-- 用户-角色关联
CREATE TABLE user_roles (
    user_id UUID REFERENCES users(id),
    role_id UUID REFERENCES roles(id),
    assigned_at TIMESTAMPTZ DEFAULT NOW(),
    assigned_by UUID REFERENCES users(id),
    PRIMARY KEY (user_id, role_id)
);

-- ABAC策略表
CREATE TABLE abac_policies (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(200) NOT NULL,
    description TEXT,
    policy_json JSONB NOT NULL,       -- 策略定义（用户属性/资源属性/环境属性）
    priority INT DEFAULT 0,
    effect VARCHAR(10) DEFAULT 'deny',-- allow/deny
    is_active BOOLEAN DEFAULT TRUE,
    valid_from TIMESTAMPTZ,
    valid_until TIMESTAMPTZ,
    version INT DEFAULT 1,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- 任务表
CREATE TABLE tasks (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    title VARCHAR(500) NOT NULL,
    description TEXT,
    status VARCHAR(20) DEFAULT 'pending',  -- pending/in_progress/completed/blocked
    priority VARCHAR(10) DEFAULT 'medium', -- high/medium/low
    creator_id UUID REFERENCES users(id),
    assignee_id UUID REFERENCES users(id),
    assignee_group_id UUID REFERENCES user_groups(id),
    department_id UUID REFERENCES departments(id),
    due_date TIMESTAMPTZ,
    completed_at TIMESTAMPTZ,
    parent_task_id UUID REFERENCES tasks(id),
    workflow_id UUID REFERENCES workflows(id),
    metadata JSONB,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- 审计日志表（ISO 27001 标准）
CREATE TABLE audit_logs (
    id BIGSERIAL PRIMARY KEY,
    timestamp TIMESTAMPTZ DEFAULT NOW(),
    user_id UUID REFERENCES users(id),
    user_role VARCHAR(100),
    action_type VARCHAR(100) NOT NULL,
    resource_type VARCHAR(100) NOT NULL,
    resource_id VARCHAR(200),
    action_result VARCHAR(20),         -- success/failure/denied
    client_ip INET,
    client_device JSONB,
    context JSONB,                     -- task_id, session_id, etc.
    data_before JSONB,
    data_after JSONB,
    is_sensitive BOOLEAN DEFAULT FALSE
);
-- 审计日志按月分区
CREATE INDEX idx_audit_logs_timestamp ON audit_logs (timestamp);
CREATE INDEX idx_audit_logs_user_id ON audit_logs (user_id);

-- DAG 工作流表
CREATE TABLE workflows (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(200) NOT NULL,
    description TEXT,
    category VARCHAR(100),          -- 类别（例如：区分 dify 工作流类别等）
    definition JSONB NOT NULL,      -- DAG 结构定义
    version INT DEFAULT 1,
    status VARCHAR(20) DEFAULT 'draft',
    creator_id UUID REFERENCES users(id),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- 部门/组织表
CREATE TABLE departments (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(200) NOT NULL,
    parent_id UUID REFERENCES departments(id),
    manager_id UUID REFERENCES users(id),
    level INT DEFAULT 0,
    created_at TIMESTAMPTZ DEFAULT NOW()
);
```

##### [NEW] `alembic/` - 数据库迁移目录
```
alembic/
├── alembic.ini
├── env.py
├── versions/
│   ├── 001_initial_schema.py
│   ├── 002_rbac_tables.py
│   ├── 003_task_management.py
│   ├── 004_audit_log.py
│   └── 005_workflow_engine.py
```

---

#### 1.2 配置系统扩展

##### [MODIFY] [config.py](file:///d:/projects/copaw/src/copaw/config/config.py)
扩展配置系统，新增数据库配置模型：

```python
class DatabaseConfig(BaseModel):
    """PostgreSQL 数据库配置"""
    host: str = "localhost"
    port: int = 5432
    database: str = "copaw_enterprise"
    username: str = "copaw"
    password: str = ""   # 从环境变量/secret_store读取
    pool_size: int = 20
    max_overflow: int = 10
    ssl_mode: str = "prefer"

class RedisConfig(BaseModel):
    """Redis 配置"""
    host: str = "localhost"
    port: int = 6379
    db: int = 0
    password: str = ""
    max_connections: int = 50
    key_prefix: str = "copaw:"

class Neo4jConfig(BaseModel):
    """Neo4j 图数据库配置"""
    uri: str = "bolt://localhost:7687"
    username: str = "neo4j"
    password: str = ""
    database: str = "copaw"

class EnterpriseConfig(BaseModel):
    """企业级功能总开关"""
    enabled: bool = False
    database: DatabaseConfig = DatabaseConfig()
    redis: RedisConfig = RedisConfig()
    neo4j: Neo4jConfig = Neo4jConfig()
    auth_mode: Literal["single", "enterprise"] = "single"
    audit_log_enabled: bool = True
    abac_enabled: bool = False
    task_management_enabled: bool = True
    workflow_engine_enabled: bool = False
```

##### [MODIFY] [docker-compose.yml](file:///d:/projects/copaw/docker-compose.yml)
扩展容器编排，添加 PostgreSQL、Redis、Neo4j 服务：

```yaml
services:
  postgres:
    image: postgres:16-alpine
    container_name: copaw-postgres
    restart: always
    environment:
      POSTGRES_DB: copaw_enterprise
      POSTGRES_USER: copaw
      POSTGRES_PASSWORD: ${POSTGRES_PASSWORD:-copaw_secret}
    ports:
      - "127.0.0.1:5432:5432"
    volumes:
      - copaw-pg-data:/var/lib/postgresql/data
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U copaw"]
      interval: 10s
      timeout: 5s
      retries: 5

  redis:
    image: redis:7-alpine
    container_name: copaw-redis
    restart: always
    command: redis-server --requirepass ${REDIS_PASSWORD:-copaw_redis}
    ports:
      - "127.0.0.1:6379:6379"
    volumes:
      - copaw-redis-data:/data
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 10s
      timeout: 5s
      retries: 5

  neo4j:
    image: neo4j:5-community
    container_name: copaw-neo4j
    restart: always
    environment:
      NEO4J_AUTH: neo4j/${NEO4J_PASSWORD:-copaw_neo4j}
    ports:
      - "127.0.0.1:7474:7474"
      - "127.0.0.1:7687:7687"
    volumes:
      - copaw-neo4j-data:/data
```

---

### 阶段二：多用户权限管理系统（第2-5周）

---

#### 2.1 企业级认证服务

##### [NEW] `src/copaw/enterprise/__init__.py`
企业级功能包入口。

##### [NEW] `src/copaw/enterprise/auth_service.py`
企业级认证服务，替代 `app/auth.py` 的单用户模型：
- 多用户注册/登录
- JWT token 签发/刷新/吊销
- MFA 支持（TOTP）
- LDAP/AD 集成接口
- 密码策略（强度/过期/历史）
- 会话管理（Redis存储）

##### [NEW] `src/copaw/enterprise/rbac_service.py`
RBAC 角色权限管理服务：
- 角色 CRUD（支持5级层级继承）
- 权限分配/撤销
- 用户组管理
- 权限缓存（Redis）
- 权限变更审计

##### [NEW] `src/copaw/enterprise/abac_engine.py`
ABAC 策略引擎：
- 策略定义（YAML/JSON）
- 策略评估（用户属性 + 资源属性 + 环境属性）
- 策略优先级/冲突解决
- 策略缓存与热更新
- 评估结果审计

##### [NEW] `src/copaw/enterprise/audit_service.py`
审计日志服务（ISO 27001）：
- 结构化日志写入 PostgreSQL
- 异步批量写入（减少性能开销）
- 日志查询/过滤/导出
- WORM 策略（不可变存储）
- 敏感操作标记

#### 2.2 认证中间件升级

##### [MODIFY] [auth.py](file:///d:/projects/copaw/src/copaw/app/auth.py)
重构认证中间件，支持双模式运行：
- `single` 模式：保持现有单用户行为（向后兼容）
- `enterprise` 模式：切换到多用户 PostgreSQL 认证
- 请求上下文注入用户角色/权限信息
- 权限验证装饰器 `@require_permission("resource:action")`

##### [NEW] `src/copaw/enterprise/middleware.py`
企业级中间件组件：
- `EnterpriseAuthMiddleware` — 替代现有 AuthMiddleware
- `AuditLogMiddleware` — 自动记录API调用审计日志
- `RateLimitMiddleware` — API限流（Redis 令牌桶）
- `TenantIsolationMiddleware` — 多租户数据隔离

#### 2.3 权限控制路由

##### [NEW] `src/copaw/app/routers/enterprise_auth.py`
企业级认证 API 路由：
```
POST   /api/enterprise/auth/login        # 企业登录
POST   /api/enterprise/auth/register     # 用户注册（管理员）
POST   /api/enterprise/auth/refresh      # Token 刷新
POST   /api/enterprise/auth/logout       # 登出
GET    /api/enterprise/auth/me           # 当前用户信息
PUT    /api/enterprise/auth/password     # 修改密码
POST   /api/enterprise/auth/mfa/setup    # MFA 设置
POST   /api/enterprise/auth/mfa/verify   # MFA 验证
```

##### [NEW] `src/copaw/app/routers/users.py`
用户管理 API 路由：
```
GET    /api/enterprise/users             # 用户列表（分页/搜索）
POST   /api/enterprise/users             # 创建用户
GET    /api/enterprise/users/{id}        # 用户详情
PUT    /api/enterprise/users/{id}        # 更新用户
DELETE /api/enterprise/users/{id}        # 禁用用户
POST   /api/enterprise/users/import      # 批量导入（CSV）
GET    /api/enterprise/users/{id}/roles  # 用户角色列表
PUT    /api/enterprise/users/{id}/roles  # 分配角色
```

##### [NEW] `src/copaw/app/routers/roles.py`
角色权限管理 API 路由：
```
GET    /api/enterprise/roles             # 角色列表
POST   /api/enterprise/roles             # 创建角色
GET    /api/enterprise/roles/{id}        # 角色详情
PUT    /api/enterprise/roles/{id}        # 更新角色
DELETE /api/enterprise/roles/{id}        # 删除角色
GET    /api/enterprise/roles/{id}/permissions  # 角色权限
PUT    /api/enterprise/roles/{id}/permissions  # 设置权限
GET    /api/enterprise/roles/hierarchy   # 权限继承树
```

##### [NEW] `src/copaw/app/routers/departments.py`
组织架构管理 API 路由（关联 Neo4j）：
```
GET    /api/enterprise/departments          # 部门树
POST   /api/enterprise/departments          # 创建部门
PUT    /api/enterprise/departments/{id}     # 更新部门
DELETE /api/enterprise/departments/{id}     # 删除部门
GET    /api/enterprise/departments/{id}/members  # 部门成员
GET    /api/enterprise/org/graph            # 组织架构图谱（Neo4j）
```

---

### 阶段三：团队协作与工作流（第3-7周）

---

#### 3.1 任务管理系统

##### [NEW] `src/copaw/enterprise/task_service.py`
任务管理核心业务服务：
- 任务 CRUD
- 任务分配（个人/组/部门）
- 任务状态流转（状态机）
- 任务依赖管理（DAG，Neo4j存储）
- 任务进度追踪
- 通知推送（钉钉/飞书/邮件）

##### [NEW] `src/copaw/app/routers/tasks.py`
任务管理 API 路由：
```
GET    /api/enterprise/tasks              # 任务列表（支持看板/列表/甘特图视图）
POST   /api/enterprise/tasks              # 创建任务
GET    /api/enterprise/tasks/{id}         # 任务详情
PUT    /api/enterprise/tasks/{id}         # 更新任务
DELETE /api/enterprise/tasks/{id}         # 删除任务
PUT    /api/enterprise/tasks/{id}/status  # 变更状态
PUT    /api/enterprise/tasks/{id}/assign  # 分配任务
GET    /api/enterprise/tasks/{id}/comments # 评论列表
POST   /api/enterprise/tasks/{id}/comments # 添加评论
GET    /api/enterprise/tasks/board        # 看板数据
GET    /api/enterprise/tasks/gantt        # 甘特图数据
GET    /api/enterprise/tasks/stats        # 任务统计
```

#### 3.2 审计日志管理

##### [NEW] `src/copaw/app/routers/audit.py`
审计日志 API 路由：
```
GET    /api/enterprise/audit/logs         # 日志列表（时间范围/用户/操作类型）
GET    /api/enterprise/audit/logs/{id}    # 日志详情
POST   /api/enterprise/audit/logs/export  # 导出日志（CSV/PDF）
GET    /api/enterprise/audit/dashboard    # 审计仪表盘
GET    /api/enterprise/audit/compliance   # 合规检查报告
```

#### 3.3 DAG 工作流引擎

##### [NEW] `src/copaw/enterprise/workflow_engine.py`
DAG 工作流引擎：
- 工作流定义（YAML/JSON → DAG）
- 节点类型：技能执行/Dify调用/条件判断/子工作流/人工审批
- 工作流执行引擎（拓扑排序 + 并行/串行）
- 状态管理（Redis + PostgreSQL）
- 断点续传/失败重试
- 工作流版本控制

##### [NEW] `src/copaw/enterprise/dify_integration.py`
Dify 深度集成服务：
- MCP 客户端封装
- REST API 调用（带限流和重试）
- Webhook 事件处理
- 消息格式转换（CoPaw Msg ⇄ Dify MCP）
- 任务状态同步

##### [NEW] `src/copaw/app/routers/workflows.py`
工作流管理 API 路由：
```
GET    /api/enterprise/workflows           # 工作流列表
POST   /api/enterprise/workflows           # 创建工作流
GET    /api/enterprise/workflows/{id}      # 工作流详情
PUT    /api/enterprise/workflows/{id}      # 更新工作流
DELETE /api/enterprise/workflows/{id}      # 删除工作流
POST   /api/enterprise/workflows/{id}/run  # 执行工作流
GET    /api/enterprise/workflows/{id}/status  # 执行状态
POST   /api/enterprise/workflows/{id}/pause   # 暂停
POST   /api/enterprise/workflows/{id}/resume  # 恢复
GET    /api/enterprise/workflows/{id}/history # 执行历史
```

---

### 阶段四：前端控制台升级

---

#### 4.1 新增前端页面

##### [NEW] `console/src/pages/Enterprise/`
```
Enterprise/
├── Users/              # 用户管理页面
│   ├── UserList.tsx     # 用户列表（表格 + 搜索 + 批量操作）
│   ├── UserDetail.tsx   # 用户详情（角色/权限/操作日志）
│   └── UserImport.tsx   # 批量导入
├── Roles/              # 角色权限管理
│   ├── RoleList.tsx     # 角色列表
│   ├── RoleEditor.tsx   # 角色编辑（权限矩阵）
│   └── RoleTree.tsx     # 层级继承可视化
├── Tasks/              # 任务管理
│   ├── TaskBoard.tsx    # 看板视图（Kanban）
│   ├── TaskList.tsx     # 列表视图
│   ├── TaskGantt.tsx    # 甘特图视图
│   ├── TaskDetail.tsx   # 任务详情（评论/附件/状态历史）
│   └── TaskCreate.tsx   # 创建任务
├── Departments/        # 组织架构
│   ├── DeptTree.tsx     # 部门树
│   └── OrgGraph.tsx     # 组织架构图（Neo4j 可视化）
├── Audit/              # 审计日志
│   ├── AuditLog.tsx     # 日志列表
│   └── AuditDashboard.tsx  # 审计仪表盘
├── Workflows/          # 工作流管理
│   ├── WorkflowList.tsx    # 工作流列表
│   ├── WorkflowEditor.tsx  # 可视化工作流编辑器（DAG）
│   └── WorkflowMonitor.tsx # 执行监控
└── Dashboard/          # 企业级仪表盘
    └── EnterpriseDashboard.tsx  # 综合仪表盘
```

#### 4.2 前端状态管理扩展

##### [NEW] `console/src/stores/`
```
stores/
├── agentStore.ts        # [EXISTS] Agent状态
├── authStore.ts         # [NEW] 企业级认证状态
├── userStore.ts         # [NEW] 用户管理状态
├── roleStore.ts         # [NEW] 角色权限状态
├── taskStore.ts         # [NEW] 任务管理状态
├── auditStore.ts        # [NEW] 审计日志状态
├── workflowStore.ts     # [NEW] 工作流状态
└── departmentStore.ts   # [NEW] 组织架构状态
```

#### 4.3 前端 API 模块

##### [NEW] `console/src/api/modules/`
新增 API 通信模块：
```
modules/
├── enterprise-auth.ts   # 企业认证 API
├── enterprise-users.ts  # 用户管理 API
├── enterprise-roles.ts  # 角色权限 API
├── enterprise-tasks.ts  # 任务管理 API
├── enterprise-audit.ts  # 审计日志 API
├── enterprise-workflows.ts  # 工作流 API
└── enterprise-departments.ts  # 组织架构 API
```

---

## 依赖变更

### Python 后端新增依赖

```toml
# pyproject.toml [project.optional-dependencies]
enterprise = [
    "sqlalchemy[asyncio]>=2.0",
    "asyncpg>=0.29.0",           # PostgreSQL async driver
    "alembic>=1.13.0",           # 数据库迁移
    "redis[hiredis]>=5.0.0",     # Redis
    "neo4j>=5.0.0",              # Neo4j
    "pyotp>=2.9.0",              # TOTP MFA
    "python-jose[cryptography]>=3.3.0",  # JWT (标准库方式)
    "passlib[bcrypt]>=1.7.4",    # 密码哈希（升级自SHA256）
    "ldap3>=2.9.0",              # LDAP 集成
]
```

### 前端新增依赖

```json
{
  "@ant-design/pro-components": "^2.x",  // 企业级表格/表单
  "@antv/g6": "^5.x",                    // 图可视化（组织架构/DAG）
  "dhtmlx-gantt": "^8.x",                // 甘特图
  "react-beautiful-dnd": "^13.x"         // 看板拖拽
}
```

---

## 文件变更汇总

| 类型 | 路径 | 说明 |
|------|------|------|
| **[NEW]** | `src/copaw/db/` | 数据库连接管理包 (4 files) |
| **[NEW]** | `src/copaw/db/models/` | ORM 模型 (10 files) |
| **[NEW]** | `alembic/` | 数据库迁移 (5 versions) |
| **[NEW]** | `src/copaw/enterprise/` | 企业级服务包 (7 files) |
| **[NEW]** | `src/copaw/app/routers/` | 企业级 API 路由 (7 files) |
| **[NEW]** | `console/src/pages/Enterprise/` | 企业管理页面 (~15 files) |
| **[NEW]** | `console/src/stores/` | 状态管理 (7 stores) |
| **[NEW]** | `console/src/api/modules/` | API 模块 (7 modules) |
| **[MODIFY]** | `src/copaw/config/config.py` | 扩展数据库/企业配置 |
| **[MODIFY]** | `src/copaw/app/_app.py` | 添加DB初始化/企业中间件 |
| **[MODIFY]** | `src/copaw/app/auth.py` | 双模式认证支持 |
| **[MODIFY]** | `docker-compose.yml` | 添加 PG/Redis/Neo4j 服务 |
| **[MODIFY]** | `pyproject.toml` | 添加企业级依赖 |
| **[MODIFY]** | `console/package.json` | 添加前端企业级依赖 |
| **[MODIFY]** | `console/src/App.tsx` | 添加企业级路由 |

> **预计新增文件 ~60 个，修改文件 ~8 个**

---

## 实施优先级

由于改动量大，建议按以下优先级分批实施：

### 🔴 P0 — 立即实施（本迭代）
1. `docker-compose.yml` 扩展（PG/Redis/Neo4j 容器）
2. `src/copaw/db/` 数据库连接管理
3. `src/copaw/db/models/` 核心 ORM 模型（user/role/permission/department）
4. `alembic/` 数据库迁移框架
5. `pyproject.toml` 依赖扩展
6. `src/copaw/config/config.py` 企业配置模型

### 🟡 P1 — 第二迭代
7. `src/copaw/enterprise/auth_service.py` 企业认证
8. `src/copaw/enterprise/rbac_service.py` 角色权限
9. `src/copaw/app/routers/enterprise_auth.py` 认证路由
10. `src/copaw/app/routers/users.py` 用户管理路由
11. `src/copaw/app/routers/roles.py` 角色管理路由
12. `src/copaw/app/auth.py` 中间件重构

### 🟢 P2 — 第三迭代
13. 任务管理系统（service + router + models）
14. 审计日志系统（service + router）
15. ABAC 策略引擎
16. 组织架构（departments + Neo4j）
17. 前端企业管理页面

### 🔵 P3 — 第四迭代
18. DAG 工作流引擎
19. Dify 深度集成
20. 前端工作流可视化编辑器
21. 性能优化/压力测试

---

## Open Questions

> [!IMPORTANT]
> 1. **实施范围确认**：是否一次性实施全部四个阶段，还是先聚焦 P0（基础设施+数据库）开始？我建议先实施 P0 基础设施层并验证可用性，再逐步推进后续阶段。
>
> 2. **向后兼容策略**：是否保留 `single` 单用户模式作为降级选项？还是企业版完全替代现有模式？
>
> 3. **部署环境**：目标生产环境是 Docker Compose 还是 Kubernetes？这会影响部署配置和服务发现方案。

> [!WARNING]
> 4. **Neo4j 必要性**：对于初期 MVP，组织架构和权限继承可以仅用 PostgreSQL 的 `parent_id` 递归查询实现。Neo4j 可以作为后续优化引入。是否可以 P0 阶段先跳过 Neo4j？

---

## Verification Plan

### Automated Tests
```bash
# 单元测试 - 数据库模型与服务
pytest tests/enterprise/ -v

# 集成测试 - API 路由（需要 docker-compose 启动 PG/Redis）
pytest tests/integration/enterprise/ -v --docker

# 压力测试 - 1000用户并发
locust -f tests/perf/locustfile.py --users 1000 --spawn-rate 50
```

### Manual Verification
1. Docker Compose 启动全部基础设施（PG/Redis/Neo4j）
2. 数据库迁移成功（`alembic upgrade head`）
3. 企业级用户注册→登录→权限分配→任务创建→审计查询完整流程
4. 前端控制台企业管理页面功能验证
5. 现有单用户模式回归测试（不影响个人版功能）
