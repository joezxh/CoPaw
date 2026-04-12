# CoPaw Enterprise vs. 原生 CoPaw: 核心差异分析

本文档旨在对比 **CoPaw Enterprise (企业版)** 与 **原生 CoPaw** 在架构、功能、安全性及运维能力上的核心差异。

---

## 1. 基础设施与数据架构 (Infrastructure)

| 特性 | 原生 CoPaw | CoPaw Enterprise |
| :--- | :--- | :--- |
| **数据库** | SQLite 或基于文件的存储 | **PostgreSQL** (关系型业务数据 + pgvector向量扩展) |
| **缓存/会话** | 内存存储或文件系统 | **Redis** (分布式缓存、会话管理与分布式锁) |
| **对象存储** | 本地文件系统 | **双轨存储**: 对象存储(MinIO/S3) + PostgreSQL元数据索引 |
| **部署架构** | 单机部署，难以水平扩展 | **容器化 (Docker Compose)**，支持无状态服务横向扩展 |
| **数据一致性** | 弱，高并发下易失效 | 强，支持 RDBMS 事务保证与关系约束 |
| **向量搜索** | 不支持 | **pgvector IVFFlat索引**，余弦相似度高效检索 |

## 2. 租户与隔离模型 (Multi-Tenancy)

| 特性 | 原生 CoPaw | CoPaw Enterprise |
| :--- | :--- | :--- |
| **用户模式** | 单用户模式 | **多租户模式 (Multi-Tenant)** |
| **隔离策略** | 无 (或仅依靠不同实例隔离) | **逻辑隔离**: 所有表均携带 `tenant_id`，实现严格的数据边界 |
| **协作空间** | 无 | **Workspace**: 支持部门级的协作空间，Agent 可绑定至空间而非个人 |
| **资源限额** | 全局统一 | 可基于租户 (Tenant) 进行不同的资源配置与指标统计 |
| **对象键规范** | 无 | **分层命名**: `{tenant_id}/{dept_id}/shared/` 或 `{tenant_id}/users/{user_id}/` |
| **访问控制** | 基础文件权限 | **RBAC四级权限**: super_admin/tenant_admin/dept_admin/user |

## 3. 元数据与索引系统 (Metadata & Indexing)

| 特性 | 原生 CoPaw | CoPaw Enterprise |
| :--- | :--- | :--- |
| **文件索引** | 无，依赖文件系统扫描 | **自动双写**: 文件上传即抽取元数据入库 |
| **全文搜索** | 不支持 | **PostgreSQL GIN索引**: `to_tsvector` + `plainto_tsquery` |
| **元数据抽取** | 无 | **智能解析**: 从 agent.json/skill.json/chats.json 自动提取结构化字段 |
| **存储统计** | 无 | **按类别统计**: 文件大小、数量、标签分布 |
| **批量索引** | 手动 | **迁移工具**: SQLite→PostgreSQL + 工作空间批量扫描 |

## 4. 记忆系统 (Memory System)

| 特性 | 原生 CoPaw | CoPaw Enterprise |
| :--- | :--- | :--- |
| **存储后端** | SQLite (本地文件) | **PostgreSQL + pgvector** (向量数据库) |
| **向量搜索** | 不支持 | **IVFFlat索引**: 余弦相似度 Top-K 检索 |
| **记忆分类** | 简单标签 | **多维分类**: category/importance/tags/sessions |
| **会话上下文** | 无 | **记忆会话**: session-memory 关联，relevance_score 权重 |
| **后端选择** | 固定 | **智能工厂**: 根据 `COPAW_ENTERPRISE_ENABLED` 自动切换 |

## 5. 安全与合规 (Security & Governance)

| 特性 | 原生 CoPaw | CoPaw Enterprise |
| :--- | :--- | :--- |
| **权限控制** | 基础的文件读写权限 | **RBAC (角色访问控制)**: 预置 Admin/Editor/Viewer 角色 |
| **身份认证** | 基础用户名/密码 | **SSO (单点登录)**: 支持 OIDC 协议集成企业身份中心 (如 LDAP, Okta) |
| **审计日志** | 仅限于运行日志 (Debug logs) | **全方位审计**: 记录每一条指令、模型调用、权限变更及敏感操作 |
| **敏感数据保护** | 基础正则脱敏 | **DLP 引擎**: 多级敏感数据检测、自动脱敏 (Masking) 与行为阻断 (Blocking) |
| **通道消息审计** | 无 | **消息中间件**: 自动记录所有通道消息，支持DLP检查 |

## 6. 自动化与工作流 (Automated Workflow)

| 特性 | 原生 CoPaw | CoPaw Enterprise |
| :--- | :--- | :--- |
| **逻辑复杂性** | 扁平的指令-响应模式 | **复杂工作流编排**: 深度集成 **Dify** 平台 |
| **集成深度** | 无外接流程引擎 | **双向赋能**: CoPaw 可调用 Dify 工作流；Dify 可将 CoPaw Agent 作为原子节点 |
| **任务触发** | 手动触发 | 支持**定时任务 (Cron)**、事件监听及复杂业务逻辑触发 |
| **任务调度** | 简单定时 | **企业调度器**: croniter + Redis分布式锁 + 失败重试 + 超时控制 |

## 7. 技能生态系统 (Ecosystem)

| 特性 | 原生 CoPaw | CoPaw Enterprise |
| :--- | :--- | :--- |
| **技能库 (Skills)** | 个性化用户自定义 | **企业级预置库**: 内置 HR、财务、IT、销售等 8 大领域专业技能 |
| **分发机制** | 拷贝文件 | **企业技能商店 (Skill Store)**: 内置技能搜索、版本管理、一键分发与安装 |
| **开发者体验** | 纯 Python/YAML 编码 | 提供企业级 Mock SSO 环境与标准化的 Skill 开发范式 |
| **元数据管理** | 无 | **Skill注册表**: 版本控制、激活状态、存储键索引 |

## 8. 运维与可观测性 (Observability)

| 特性 | 原生 CoPaw | CoPaw Enterprise |
| :--- | :--- | :--- |
| **系统监控** | 无原生监控接口 | **Prometheus 集成**: 主动暴露系统运行指标 |
| **可视化看板** | 无 | **Grafana Dashboard**: 支持租户级流量统计、Skill 使用分布及系统负载看板 |
| **错误追踪** | 查阅磁盘日志 | 结构化审计与监控指标告警，支持运维团队主动干预 |

## 9. API与开发接口 (API & Development)

| 特性 | 原生 CoPaw | CoPaw Enterprise |
| :--- | :--- | :--- |
| **REST API** | 基础聊天和管理 | **企业API**: 元数据查询、全文搜索、统计报表、Agent/Skill管理 |
| **数据访问** | 直接文件操作 | **Repository层**: 统一数据访问接口，租户隔离 |
| **迁移工具** | 无 | **CLI工具**: `migrate_sqlite_to_postgres.py` + `batch_index.py` |
| **模型注册** | 配置式 | **模型注册表**: 架构、量化、健康状态、推理任务管理 |

---

## 总结

**原生 CoPaw** 是一款优秀的个人或小团队本地 AI 工具，侧重于灵活性与快速验证。

**CoPaw Enterprise** 则完成了向**"平台级"**产品的跨越。通过引入多租户基座、双轨存储架构、金融级安全扫描、深度流程编排、向量记忆系统以及标准化的运维体系，它能够承载大型企业的业务数据，在确保合规与安全的前提下，将 Agent 能力沉淀为企业的数字资产。

### 企业版核心新增功能 (Phase 2-4)

✅ **多租户分层存储** - 对象键命名规范 + RBAC访问控制  
✅ **双轨存储架构** - 对象存储(原始文件) + PostgreSQL(元数据索引)  
✅ **元数据自动抽取** - 从 agent.json/skill.json/chats.json 智能解析  
✅ **全文搜索服务** - PostgreSQL GIN索引，支持类别/标签/大小过滤  
✅ **向量记忆系统** - pgvector IVFFlat索引，余弦相似度检索  
✅ **企业任务调度** - croniter + Redis分布式锁 + 失败重试  
✅ **通道消息审计** - 自动记录所有通道消息，支持DLP检查  
✅ **迁移工具链** - SQLite→PostgreSQL迁移 + 批量索引  
✅ **模型注册表** - 架构管理、健康监控、推理任务  
✅ **Repository层** - 统一数据访问，租户隔离  

### 数据库表扩展

- **新增16个表**: storage_objects, ai_agent_configs, ai_skill_configs, ai_conversations, ai_memories, ai_model_registry 等
- **扩展1个表**: ai_tasks (调度字段)
- **pgvector扩展**: 向量相似度搜索支持
