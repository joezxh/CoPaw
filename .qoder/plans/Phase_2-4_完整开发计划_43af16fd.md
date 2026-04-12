# Phase 2-4 完整开发计划

## 总览

| Phase | 模块 | 新增文件 | 测试项 |
|-------|------|----------|--------|
| Phase 2 | 多租户分层存储 | 4 个 | 12 项 |
| Phase 3 | 双轨存储+元数据+SQLite迁移 | 11 个 + 3 Alembic | 57 项 |
| Phase 4 | 功能服务端迁移 | 3 个 + 2 Alembic | 7 项 |
| 合计 | | 18+5 个 | 76 项 |

---

## Phase 2: 多租户分层存储 (12 项测试)

### Task 2.1: StorageKeyBuilder — 对象键命名规范构建器
**文件**: `src/copaw/storage/key_builder.py`

实现 `StorageKeyBuilder` 类，按规范 `{tenant_id}/{dept_id}/shared/` 或 `{tenant_id}/users/{user_id}/{category}/` 构建对象键前缀：
```python
class StorageKeyBuilder:
    @staticmethod
    def build(tenant_id, user_id=None, department_id=None, category=None, resource_path=None) -> str
    @staticmethod
    def parse(key: str) -> dict  # 解析键中的 tenant/dept/user/category
    @staticmethod
    def validate(key: str, tenant_id: str, user_id=None) -> bool  # 验证访问权限
```

### Task 2.2: StorageAccessControl — 存储访问控制
**文件**: `src/copaw/storage/access_control.py`

实现文档 4.3 节的 `StorageAccessLevel` 枚举和 `StorageACLEntry` 类：
- `build_key_prefix()` — 构建带权限的键前缀
- `validate_access()` — RBAC 权限验证（super_admin 跨租户、租户隔离、系统资源只读）
- 新增 `enforce_access()` — 抛出 `StoragePermissionError` 的强制版本

### Task 2.3: 存储中间件 — 自动注入租户前缀
**文件**: `src/copaw/storage/middleware.py`

FastAPI 中间件，拦截所有 `/api/enterprise/storage/` 请求：
- 从 JWT 提取 `tenant_id` / `user_id` / `roles`
- 自动重写请求路径中的 `key` 参数，注入租户前缀
- 验证跨租户操作，拒绝则返回 403
- 记录审计日志到 `ai_audit_logs`

### Task 2.4: 存储 API 增强
**修改**: `src/copaw/app/routers/storage.py`

- 添加 `POST /enterprise/storage/upload` — 多部分文件上传（自动注入租户前缀）
- 添加 `GET /enterprise/storage/search` — 占位端点（Phase 3 实现）
- 修改现有端点：从 `request.state` 获取 `tenant_id` / `user_id`，通过 `StorageKeyBuilder` 构建完整 key

### Task 2.5: 单元测试 — 多租户隔离
**文件**: `tests/unit/storage/test_key_builder.py`, `tests/unit/storage/test_access_control.py`, `tests/unit/storage/test_middleware.py`, `tests/unit/storage/test_multi_tenant.py`

覆盖 T-MULTI-TENANT-001~003 全部 12 项测试。

---

## Phase 3: 双轨存储 + 元数据索引 + SQLite迁移 (57 项测试)

### Task 3.1: PostgreSQL 元数据模型 (ORM)
**文件**: `src/copaw/db/models/storage_meta.py`

定义 7 个新 ORM 模型（对应文档 5.1.1-5.1.8）：
- `StorageObject` — `storage_objects` 通用文件索引
- `AgentConfig` — `ai_agent_configs`
- `SkillConfig` — `ai_skill_configs`
- `Conversation` + `ConversationMessage` — `ai_conversations` + `ai_conversation_messages`
- `TokenUsageStat` — `ai_token_usage_stats`
- `MemoryDocument` — `ai_memory_documents`
- `ChannelMessage` — `ai_channel_messages`

每个模型包含完整的 mapped_column 定义、索引、外键、comment。

### Task 3.2: 记忆向量模型 (pgvector)
**文件**: `src/copaw/db/models/memory.py`

定义 4 个 ORM 模型：
- `AIMemory` — `ai_memories`（含 `embedding` vector(1536) 字段）
- `MemoryTag` — `ai_memory_tags`
- `MemorySession` — `ai_memory_sessions`
- `MemorySessionLink` — `ai_memory_session_links`

> 注意：`vector` 类型需使用 `pgvector.sqlalchemy.Vector`，已在 `db/postgresql.py` 中注册类型。

### Task 3.3: Alembic 迁移文件
**文件**: `alembic/versions/004_storage_objects.py`
**文件**: `alembic/versions/005_ai_metadata_tables.py`
**文件**: `alembic/versions/006_ai_memories_pgvector.py`

- `004`: 创建 `storage_objects` 表 + 所有索引
- `005`: 创建 7 个业务元数据表（`ai_agent_configs` / `ai_skill_configs` / `ai_conversations` / `ai_conversation_messages` / `ai_token_usage_stats` / `ai_memory_documents` / `ai_channel_messages`）
- `006`: 启用 `pgvector` 扩展，创建 `ai_memories` / `ai_memory_tags` / `ai_memory_sessions` / `ai_memory_session_links`，IVFFlat 向量索引

### Task 3.4: MetadataExtractor — 元数据抽取器
**文件**: `src/copaw/storage/metadata_extractor.py`

实现文档 5.2 节的 `MetadataExtractor` 类：
- `extract_category(key)` — 从对象键推断文件类别
- `extract_search_text(key, content)` — 从文件内容提取可搜索文本
- `extract_agent_config(data)` → `dict` — 从 agent.json 抽取结构化字段
- `extract_skill_config(data)` → `dict` — 从 skill.json 抽取
- `extract_conversations(data)` → `list[dict]` — 从 chats.json 逐条抽取
- `extract_token_usage(data)` → `list[dict]` — 从 token_usage.json 按日分桶
- `extract_memory_document(content, doc_type)` → `dict` — 从 Markdown 抽取标题/标签/摘要
- `_flatten_json_values()` — 递归提取 JSON 字符串值
- `_parse_markdown_headings()` — 提取 Markdown 标题
- 所有抽取方法带完整异常处理，格式错误时记录日志不崩溃

### Task 3.5: 存储写入钩子 — 自动双写元数据
**文件**: `src/copaw/storage/write_hook.py`

在 `storage.put()` 后自动触发：
1. 创建 `StorageObject` 记录（通用索引）
2. 根据 category 调用 `MetadataExtractor` 对应方法
3. 插入/更新业务元数据表（upsert by `storage_key`）
4. 通过 `content_hash` 检测变更，仅更新变化的记录

异步实现 `async def on_file_uploaded(key, data, metadata, provider)`。

### Task 3.6: Metadata Repository 层
**文件**: `src/copaw/db/repositories/__init__.py`
**文件**: `src/copaw/db/repositories/agent_config_repo.py`
**文件**: `src/copaw/db/repositories/skill_config_repo.py`
**文件**: `src/copaw/db/repositories/conversation_repo.py`
**文件**: `src/copaw/db/repositories/channel_message_repo.py`

每个 Repository 包含 CRUD + 搜索方法，带租户隔离过滤。

### Task 3.7: ReMePostgresBackend — PostgreSQL 记忆后端
**文件**: `src/copaw/agents/memory/reme_postgres_backend.py`

实现基于 PostgreSQL + pgvector 的记忆后端：
- `add_memory(content, embedding, metadata)` — 添加记忆
- `search_memories(query_embedding, top_k, filter)` — 向量相似度搜索
- `get_memory(memory_id)` / `delete_memory(memory_id)` / `update_memory()`
- `archive_old_memories(before_date, keep_importance)` — 归档旧记忆
- 使用 `ivfflat` 索引进行余弦相似度搜索

### Task 3.8: MemoryBackendFactory — 企业版/个人版切换
**文件**: `src/copaw/agents/memory/memory_backend_factory.py`

实现文档 6.5 节的工厂方法：
```python
def create_memory_backend(workspace_dir, agent_id, tenant_id=None, workspace_id=None):
    # COPAW_ENTERPRISE_ENABLED=true → ReMePostgresBackend
    # COPAW_ENTERPRISE_ENABLED=false → ReMeLightMemoryManager (原有行为)
    # COPAW_MEMORY_BACKEND=postgres/sqlite/chroma 手动覆盖
```

### Task 3.9: SQLite → PostgreSQL 迁移脚本
**文件**: `scripts/migrate_sqlite_to_postgres.py`

实现完整的迁移工具：
- 定位 `~/.copaw/` 和 `workspaces/{id}/.reme/` 下的 SQLite 数据库
- 读取 `memories` / `memory_tags` / `sessions` / `session_memories` 表
- 反序列化 numpy BLOB embedding → list[float]
- 自动检测向量维度
- 批量写入 PostgreSQL（`ON CONFLICT DO NOTHING` 幂等）
- 迁移完成后验证数据完整性（count 对比）
- 支持 `--dry-run` 模式

### Task 3.10: StorageSearchService — 存储搜索服务
**文件**: `src/copaw/storage/search_service.py`

实现文档 5.4 节的搜索服务：
- `search(StorageSearchRequest)` → `StorageSearchResult`
  - 全文搜索（`to_tsvector` + `plainto_tsquery`）
  - 类别/标签/大小/日期过滤
  - 分页 + 排序
- `search_by_content(tenant_id, text_query, limit)` — 基于 GIN 索引的搜索
- 强制租户隔离 `WHERE tenant_id = :tenant_id`

### Task 3.11: 搜索 REST API
**修改**: `src/copaw/app/routers/storage.py`（补充 Task 2.4 的占位）

实现 `POST /enterprise/storage/search` 端点，调用 `StorageSearchService.search()`。

### Task 3.12: 通道消息入库中间件
**文件**: `src/copaw/enterprise/channel_message_middleware.py`

在通道消息处理管道中自动将消息写入 `ai_channel_messages`：
- 异步写入，不影响消息处理延迟
- 自动关联 `conversation_id` / `task_id`
- DLP 检查结果同步记录

### Task 3.13: 元数据 REST API
**文件**: `src/copaw/app/routers/metadata.py`

新增 5 个查询端点：
- `GET /enterprise/metadata/agents` — Agent 配置查询
- `GET /enterprise/metadata/skills` — Skill 配置查询
- `GET /enterprise/metadata/conversations` — 对话历史查询
- `GET /enterprise/metadata/token-usage` — Token 统计查询
- `GET /enterprise/metadata/channel-messages` — 通道消息查询

所有端点带租户隔离过滤 + 分页。

### Task 3.14: 批量索引工具 + 增量同步
**文件**: `scripts/batch_index.py`

- `index_all_files(provider, bucket)` — 扫描对象存储所有文件，批量创建元数据记录
- `sync_missing_records(provider)` — 定时任务，补全遗漏记录

### Task 3.15: 单元测试 — Phase 3
**文件**: `tests/unit/storage/test_metadata_extractor.py`
**文件**: `tests/unit/storage/test_write_hook.py`
**文件**: `tests/unit/storage/test_search_service.py`
**文件**: `tests/unit/db/test_meta_models.py`
**文件**: `tests/unit/db/test_repositories.py`
**文件**: `tests/unit/agents/memory/test_postgres_backend.py`
**文件**: `tests/unit/agents/memory/test_backend_factory.py`
**文件**: `tests/unit/scripts/test_migrate_sqlite.py`
**文件**: `tests/unit/enterprise/test_channel_middleware.py`

覆盖 T-META-001~005 (29 项) + T-MIGRATE-001~005 (21 项) + T-RISK-001 部分。

---

## Phase 4: 功能服务端迁移 (7 项测试)

### Task 4.1: EnterpriseScheduler — 定时任务调度器
**文件**: `src/copaw/enterprise/scheduler.py`

基于 `ai_tasks` 表的调度字段 + `croniter` 实现：
- `start()` — 启动调度循环（每秒检查 `next_run_at`）
- `register_task(task_id, cron_expr, handler)` — 注册任务
- `_tick()` — 检查到期任务，提交到异步执行队列
- 分布式锁：Redis `SET NX` 防止多节点重复执行
- 执行历史：更新 `last_run_at` / `run_count` / `status`
- 超时控制 + 重试机制（`max_retries`）

### Task 4.2: ai_tasks 调度字段扩展 Alembic 迁移
**文件**: `alembic/versions/007_ai_tasks_scheduling.py`

扩展 `ai_tasks` 表：
- `schedule_expr`, `next_run_at`, `last_run_at`, `run_count`, `max_retries`, `timeout_seconds`, `command`, `args`, `source_storage_key`

### Task 4.3: 模型注册表 + 推理任务表
**文件**: `src/copaw/db/models/model_registry.py`

定义 `ModelRegistry` + `InferenceTask` ORM 模型。

**文件**: `alembic/versions/008_ai_model_registry.py`

创建 `ai_model_registry` / `ai_inference_tasks` / `ai_skill_registry` 表。

### Task 4.4: 心跳监控服务化
**修改**: `src/copaw/enterprise/task_service.py`（扩展）

新增 `HeartbeatMonitor` 类：
- 定期检查所有在线 Agent 心跳
- 异常 Agent 自动标记 + 发送告警
- 心跳数据写入 `ai_tasks.metadata` JSONB

### Task 4.5: 单元测试 — Phase 4
**文件**: `tests/unit/enterprise/test_scheduler.py`
**文件**: `tests/unit/enterprise/test_heartbeat.py`
**文件**: `tests/unit/db/test_model_registry.py`

覆盖 T-SERVER-001 (7 项) + T-RISK-001 剩余部分。

---

## 测试执行计划

所有测试文件创建完成后，统一执行：
```bash
python scripts/run_tests.py --path tests/unit/storage --path tests/unit/db --path tests/unit/enterprise --path tests/unit/agents/memory --path tests/unit/scripts
```

预期结果：
- Phase 2: 12 项通过（T-MULTI-TENANT-001~003）
- Phase 3: 57 项通过（T-META-001~005 + T-MIGRATE-001~005 + T-RISK-001 部分）
- Phase 4: 7 项通过（T-SERVER-001 + T-RISK-001 剩余）
- 总计 76 项新增测试全部通过
- 现有 602 项测试不受影响

---

## 依赖变更

**修改**: `pyproject.toml` enterprise 依赖添加：
```
"pgvector>=0.2",
"croniter>=1.4",
"numpy>=1.24",
```

---

## 文件清单（按创建顺序）

| # | 文件路径 | Phase | 类型 |
|---|----------|-------|------|
| 1 | `src/copaw/storage/key_builder.py` | 2 | 新建 |
| 2 | `src/copaw/storage/access_control.py` | 2 | 新建 |
| 3 | `src/copaw/storage/middleware.py` | 2 | 新建 |
| 4 | `src/copaw/app/routers/storage.py` | 2 | 修改 |
| 5 | `src/copaw/db/models/storage_meta.py` | 3 | 新建 |
| 6 | `src/copaw/db/models/memory.py` | 3 | 新建 |
| 7 | `alembic/versions/004_storage_objects.py` | 3 | 新建 |
| 8 | `alembic/versions/005_ai_metadata_tables.py` | 3 | 新建 |
| 9 | `alembic/versions/006_ai_memories_pgvector.py` | 3 | 新建 |
| 10 | `src/copaw/storage/metadata_extractor.py` | 3 | 新建 |
| 11 | `src/copaw/storage/write_hook.py` | 3 | 新建 |
| 12 | `src/copaw/db/repositories/__init__.py` | 3 | 新建 |
| 13-15 | `src/copaw/db/repositories/*.py` (3个) | 3 | 新建 |
| 16 | `src/copaw/agents/memory/reme_postgres_backend.py` | 3 | 新建 |
| 17 | `src/copaw/agents/memory/memory_backend_factory.py` | 3 | 新建 |
| 18 | `scripts/migrate_sqlite_to_postgres.py` | 3 | 新建 |
| 19 | `src/copaw/storage/search_service.py` | 3 | 新建 |
| 20 | `src/copaw/enterprise/channel_message_middleware.py` | 3 | 新建 |
| 21 | `src/copaw/app/routers/metadata.py` | 3 | 新建 |
| 22 | `scripts/batch_index.py` | 3 | 新建 |
| 23 | `src/copaw/enterprise/scheduler.py` | 4 | 新建 |
| 24 | `alembic/versions/007_ai_tasks_scheduling.py` | 4 | 新建 |
| 25 | `src/copaw/db/models/model_registry.py` | 4 | 新建 |
| 26 | `alembic/versions/008_ai_model_registry.py` | 4 | 新建 |
| 27 | `pyproject.toml` | 3 | 修改 |
| 28 | `src/copaw/db/models/__init__.py` | 3 | 修改 |
| 29 | `src/copaw/app/routers/__init__.py` | 3 | 修改 |

**测试文件**（约 15 个）：
- `tests/unit/storage/test_key_builder.py`
- `tests/unit/storage/test_access_control.py`
- `tests/unit/storage/test_middleware.py`
- `tests/unit/storage/test_multi_tenant.py`
- `tests/unit/storage/test_metadata_extractor.py`
- `tests/unit/storage/test_write_hook.py`
- `tests/unit/storage/test_search_service.py`
- `tests/unit/db/test_meta_models.py`
- `tests/unit/db/test_repositories.py`
- `tests/unit/db/test_model_registry.py`
- `tests/unit/agents/memory/test_postgres_backend.py`
- `tests/unit/agents/memory/test_backend_factory.py`
- `tests/unit/scripts/test_migrate_sqlite.py`
- `tests/unit/enterprise/test_channel_middleware.py`
- `tests/unit/enterprise/test_scheduler.py`
- `tests/unit/enterprise/test_heartbeat.py`
