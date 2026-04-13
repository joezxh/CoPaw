好问题！让我详细说明双轨存储在**初始化启动**和**历史数据同步**时的完整执行流程：

## 🚀 双轨存储初始化与数据同步

### 一、全新环境初始化（从零开始）

#### 1. 数据库迁移初始化

```bash
# 步骤 1: 运行 Alembic 迁移创建所有表
alembic upgrade head

# 这会创建：
# - 004: storage_objects 表
# - 005: 7个业务元数据表
# - 006: ai_memories + pgvector扩展
# - 007: ai_tasks调度字段扩展
# - 008: 模型注册表
```

#### 2. 应用启动时的自动初始化

```python
# src/copaw/app/lifespan.py

from contextlib import asynccontextmanager
from copaw.storage.write_hook import setup_write_hooks
from copaw.enterprise.scheduler import EnterpriseScheduler

@asynccontextmanager
async def lifespan(app):
    """应用生命周期管理"""
    
    # === 启动时初始化 ===
    
    # 1. 检查并初始化存储提供者
    storage_provider = await init_storage_provider()
    
    # 2. 注册 WriteHook（文件上传自动双写）
    await setup_write_hooks(storage_provider)
    
    # 3. 启动企业调度器（如果有定时任务）
    if os.getenv("COPAW_ENTERPRISE_ENABLED") == "true":
        scheduler = EnterpriseScheduler()
        await scheduler.start()
        app.state.scheduler = scheduler
    
    yield
    
    # === 关闭时清理 ===
    if hasattr(app.state, 'scheduler'):
        await app.state.scheduler.stop()

# FastAPI 应用
app = FastAPI(lifespan=lifespan)
```

#### 3. 存储提供者初始化

```python
# src/copaw/storage/provider_factory.py

async def init_storage_provider() -> ObjectStorageProvider:
    """根据配置初始化存储提供者"""
    
    provider_type = os.getenv("COPAW_STORAGE_PROVIDER", "local")
    
    if provider_type == "minio":
        from copaw.storage.minio_provider import MinIOProvider
        return MinIOProvider(
            endpoint=os.getenv("MINIO_ENDPOINT"),
            access_key=os.getenv("MINIO_ACCESS_KEY"),
            secret_key=os.getenv("MINIO_SECRET_KEY"),
            bucket=os.getenv("MINIO_BUCKET", "copaw-data"),
        )
    
    elif provider_type == "s3":
        from copaw.storage.s3_provider import S3Provider
        return S3Provider(
            region=os.getenv("AWS_REGION"),
            bucket=os.getenv("AWS_BUCKET"),
        )
    
    else:  # local (个人版)
        from copaw.storage.local_provider import LocalStorageProvider
        return LocalStorageProvider(
            base_path=os.getenv("COPAW_WORKING_DIR", "working")
        )
```

---

### 二、历史数据同步（从个人版迁移）

这是**最关键的场景**：将已有的个人版 CoPaw 数据迁移到企业版双轨存储。

#### 场景 1：SQLite → PostgreSQL 完整迁移

```bash
# 执行迁移脚本
python scripts/migrate_sqlite_to_postgres.py \
    --sqlite-db working/copaw.db \
    --pg-dsn postgresql://user:pass@localhost/copaw \
    --tenant-id acme-corp
```

**迁移脚本详细流程**：

```python
# scripts/migrate_sqlite_to_postgres.py

class SQLiteToPostgresMigrator:
    async def migrate(self) -> dict:
        """完整迁移流程"""
        
        stats = {
            "agents": 0,
            "skills": 0,
            "conversations": 0,
            "messages": 0,
            "errors": [],
        }
        
        # === 第 1 步：连接源数据库（SQLite）===
        sqlite_conn = sqlite3.connect(self.sqlite_db_path)
        sqlite_conn.row_factory = sqlite3.Row
        
        try:
            # === 第 2 步：迁移 Agent 配置 ===
            logger.info("开始迁移 Agent 配置...")
            stats["agents"] = await self._migrate_agents(sqlite_conn)
            
            # === 第 3 步：迁移 Skill 配置 ===
            logger.info("开始迁移 Skill 配置...")
            stats["skills"] = await self._migrate_skills(sqlite_conn)
            
            # === 第 4 步：迁移对话和消息 ===
            logger.info("开始迁移对话...")
            stats["conversations"], stats["messages"] = await self._migrate_conversations(
                sqlite_conn
            )
            
            # === 第 5 步：验证数据一致性 ===
            await self._verify_migration()
            
            logger.info(f"✅ 迁移完成: {stats}")
            return stats
            
        except Exception as e:
            stats["errors"].append(str(e))
            logger.error(f"❌ 迁移失败: {e}")
            return stats
        finally:
            sqlite_conn.close()
    
    async def _migrate_agents(self, sqlite_conn) -> int:
        """
        迁移 Agent 配置
        
        流程：
        1. 从 SQLite 读取 agent.json 数据
        2. 计算内容哈希
        3. 构建对象存储键
        4. 如果对象存储中没有文件，先上传
        5. 写入 PostgreSQL 元数据
        """
        from copaw.db.models.storage_meta import AgentConfig
        from copaw.storage.key_builder import StorageKeyBuilder
        from copaw.storage.metadata_extractor import MetadataExtractor
        
        cursor = sqlite_conn.cursor()
        cursor.execute("SELECT * FROM agents")
        agents = cursor.fetchall()
        
        count = 0
        async with async_session_maker() as session:
            for agent in agents:
                agent_data = json.loads(agent.get("config", "{}"))
                
                # 1. 提取元数据
                extracted = MetadataExtractor.extract_agent_config(agent_data)
                
                # 2. 构建对象键
                workspace_id = agent.get("workspace_id", "default")
                key = StorageKeyBuilder.build(
                    tenant_id=self.tenant_id,
                    workspace_id=workspace_id,
                    category="workspace",
                    resource_path=f"{agent.get('id')}/agent.json",
                )
                
                # 3. 计算内容哈希
                content_hash = MetadataExtractor.compute_content_hash(
                    json.dumps(agent_data).encode()
                )
                
                # 4. 检查对象存储中是否存在
                storage_provider = await init_storage_provider()
                if not await storage_provider.exists(key):
                    # 上传到对象存储
                    await storage_provider.put_object(
                        key=key,
                        data=json.dumps(agent_data, ensure_ascii=False).encode(),
                        metadata={"content_type": "application/json"},
                    )
                    logger.info(f"  上传到对象存储: {key}")
                
                # 5. 创建 PostgreSQL 记录
                config = AgentConfig(
                    tenant_id=self.tenant_id,
                    workspace_id=workspace_id,
                    agent_id=extracted["agent_id"],
                    name=extracted["name"],
                    description=extracted.get("description"),
                    model_provider=extracted.get("model_provider"),
                    model_name=extracted.get("model_name"),
                    storage_key=key,
                    content_hash=content_hash,
                    status="active",
                )
                session.add(config)
                count += 1
            
            await session.commit()
        
        logger.info(f"  迁移了 {count} 个 Agent 配置")
        return count
```

---

#### 场景 2：工作空间文件批量索引

```bash
# 扫描 working/workspaces 目录，将元数据索引到 PostgreSQL
python scripts/batch_index.py \
    --workspace-root working/workspaces \
    --tenant-id acme-corp
```

**批量索引详细流程**：

```python
# scripts/batch_index.py

class BatchIndexer:
    async def index_all(self) -> dict:
        """批量索引所有工作空间文件"""
        
        stats = {
            "workspaces": 0,
            "agent_configs": 0,
            "skill_configs": 0,
            "conversations": 0,
            "memory_docs": 0,
            "errors": [],
        }
        
        if not self.workspace_root.exists():
            logger.warning(f"工作空间根目录不存在: {self.workspace_root}")
            return stats
        
        # === 遍历所有工作空间 ===
        for workspace_dir in self.workspace_root.iterdir():
            if not workspace_dir.is_dir():
                continue
            
            logger.info(f"索引工作空间: {workspace_dir.name}")
            stats["workspaces"] += 1
            
            try:
                # 1. 索引 agent.json
                stats["agent_configs"] += await self._index_agent_configs(workspace_dir)
                
                # 2. 索引 skill_pool/
                stats["skill_configs"] += await self._index_skills(workspace_dir)
                
                # 3. 索引 chats.json
                stats["conversations"] += await self._index_conversations(workspace_dir)
                
                # 4. 索引 memory/*.md
                stats["memory_docs"] += await self._index_memory_docs(workspace_dir)
                
            except Exception as e:
                error_msg = f"索引工作空间 {workspace_dir.name} 失败: {e}"
                stats["errors"].append(error_msg)
                logger.error(error_msg)
        
        logger.info(f"✅ 批量索引完成: {stats}")
        return stats
    
    async def _index_agent_configs(self, workspace_dir: Path) -> int:
        """
        索引单个 agent.json
        
        流程：
        1. 检查文件是否存在
        2. 读取并解析 JSON
        3. 计算内容哈希（用于去重）
        4. 构建对象存储键
        5. 上传到对象存储（如果不存在）
        6. 写入 PostgreSQL 元数据
        """
        from copaw.db.models.storage_meta import AgentConfig
        from copaw.storage.key_builder import StorageKeyBuilder
        from copaw.storage.metadata_extractor import MetadataExtractor
        
        agent_json = workspace_dir / "agent.json"
        if not agent_json.exists():
            return 0
        
        # 1. 读取文件
        with open(agent_json, "r", encoding="utf-8") as f:
            data = json.load(f)
        
        # 2. 计算内容哈希
        content_hash = self._compute_hash(agent_json)
        
        # 3. 构建对象键
        workspace_id = workspace_dir.name
        key = StorageKeyBuilder.build(
            tenant_id=self.tenant_id,
            workspace_id=workspace_id,
            category="workspace",
            resource_path="agent.json",
        )
        
        # 4. 上传到对象存储（幂等操作）
        storage_provider = await init_storage_provider()
        if not await storage_provider.exists(key):
            await storage_provider.put_object(
                key=key,
                data=agent_json.read_bytes(),
                metadata={"content_type": "application/json"},
            )
            logger.info(f"  上传: {key}")
        
        # 5. 写入 PostgreSQL
        async with async_session_maker() as session:
            config = AgentConfig(
                tenant_id=self.tenant_id,
                workspace_id=workspace_id,
                agent_id=data.get("id", workspace_id),
                name=data.get("name", "Unknown"),
                description=data.get("description"),
                model_provider=data.get("model_provider"),
                model_name=data.get("model_name"),
                storage_key=key,
                content_hash=content_hash,
            )
            session.add(config)
            await session.commit()
        
        return 1
    
    async def _index_conversations(self, workspace_dir: Path) -> int:
        """
        索引 chats.json（对话数据）
        
        流程：
        1. 读取 chats.json
        2. 逐条创建 Conversation 记录
        3. 可选：上传原始 chats.json 到对象存储
        """
        from copaw.db.models.storage_meta import Conversation
        
        chats_json = workspace_dir / "chats.json"
        if not chats_json.exists():
            return 0
        
        with open(chats_json, "r", encoding="utf-8") as f:
            data = json.load(f)
        
        # chats.json 格式: {chat_id: {title, messages, ...}}
        count = 0
        async with async_session_maker() as session:
            for chat_id, chat_data in data.items():
                conversation = Conversation(
                    tenant_id=self.tenant_id,
                    workspace_id=workspace_dir.name,
                    chat_id=chat_id,
                    title=chat_data.get("title"),
                    message_count=len(chat_data.get("messages", [])),
                    started_at=datetime.fromisoformat(
                        chat_data.get("started_at", datetime.utcnow().isoformat())
                    ),
                )
                session.add(conversation)
                count += 1
            
            await session.commit()
        
        return count
```

---

### 三、运行时自动同步（WriteHook）

新文件上传时的**实时同步**机制：

```python
# src/copaw/storage/write_hook.py

async def setup_write_hooks(provider: ObjectStorageProvider):
    """注册 WriteHook 到存储提供者"""
    
    # 保存原始方法
    original_put = provider.put_object
    
    async def put_object_with_hook(key, data, metadata=None, **kwargs):
        """带钩子的上传方法"""
        
        # 1. 先上传到对象存储
        result = await original_put(key, data, metadata, **kwargs)
        
        # 2. 触发元数据双写
        try:
            async with async_session_maker() as session:
                await on_file_uploaded(
                    key=key,
                    data=data,
                    metadata=metadata or {},
                    provider=provider,
                    db_session=session,
                    tenant_id=os.getenv("COPAW_TENANT_ID", "default-tenant"),
                )
        except Exception as e:
            logger.error(f"元数据双写失败: {e}")
            # 不抛出异常，避免影响文件上传
        
        return result
    
    # 替换原始方法
    provider.put_object = put_object_with_hook
    logger.info("✅ WriteHook 已注册")


async def on_file_uploaded(
    key: str,
    data: bytes,
    metadata: dict,
    provider: ObjectStorageProvider,
    db_session: AsyncSession,
    tenant_id: str,
    workspace_id: Optional[str] = None,
    user_id: Optional[str] = None,
) -> None:
    """
    文件上传后的元数据双写钩子
    
    执行流程：
    1. 计算内容哈希
    2. 提取文件类别
    3. 创建/更新 StorageObject
    4. 根据类别抽取业务元数据
    5. 更新全文搜索文本
    6. 提交事务
    """
    from copaw.db.models.storage_meta import StorageObject
    from copaw.storage.metadata_extractor import MetadataExtractor
    
    # 1. 计算内容哈希
    content_hash = MetadataExtractor.compute_content_hash(data)
    
    # 2. 提取文件类别
    category = MetadataExtractor.categorize_file(key)
    
    # 3. 创建/更新 StorageObject
    result = await db_session.execute(
        select(StorageObject).where(
            StorageObject.object_key == key,
            StorageObject.tenant_id == tenant_id,
        )
    )
    storage_obj = result.scalar_one_or_none()
    
    if storage_obj:
        # 更新现有记录
        storage_obj.file_size = len(data)
        storage_obj.content_hash = content_hash
        storage_obj.updated_at = datetime.utcnow()
    else:
        # 创建新记录
        storage_obj = StorageObject(
            tenant_id=tenant_id,
            object_key=key,
            file_name=key.split("/")[-1],
            file_size=len(data),
            category=category,
            content_hash=content_hash,
            workspace_id=workspace_id,
            user_id=user_id,
        )
        db_session.add(storage_obj)
    
    # 4. 根据类别抽取业务元数据
    if category == "workspace" and key.endswith("agent.json"):
        await _extract_and_save_agent_config(data, storage_obj, db_session, tenant_id, workspace_id)
    
    elif category == "workspace" and key.endswith("chats.json"):
        await _extract_and_save_conversations(data, storage_obj, db_session, tenant_id, workspace_id)
    
    elif category == "skill" and key.endswith("skill.json"):
        await _extract_and_save_skill_config(data, storage_obj, db_session, tenant_id, workspace_id)
    
    # 5. 提交事务
    await db_session.commit()
    logger.info(f"✅ 元数据双写成功: {key}")
```

---

### 四、数据一致性验证

迁移完成后验证双轨存储一致性：

```python
# scripts/verify_migration.py

async def verify_consistency():
    """验证对象存储和 PostgreSQL 的一致性"""
    
    from copaw.db.models.storage_meta import StorageObject
    from copaw.storage.metadata_extractor import MetadataExtractor
    
    # 1. 获取所有存储对象
    async with async_session_maker() as session:
        result = await session.execute(select(StorageObject))
        objects = result.scalars().all()
    
    provider = await init_storage_provider()
    consistent = 0
    inconsistent = 0
    
    # 2. 逐个验证
    for obj in objects:
        try:
            # 从对象存储读取
            if not await provider.exists(obj.object_key):
                logger.warning(f"❌ 对象存储中不存在: {obj.object_key}")
                inconsistent += 1
                continue
            
            file_data = await provider.get_object(obj.object_key)
            current_hash = MetadataExtractor.compute_content_hash(file_data)
            
            # 对比哈希
            if current_hash == obj.content_hash:
                consistent += 1
            else:
                logger.warning(f"❌ 哈希不匹配: {obj.object_key}")
                inconsistent += 1
        
        except Exception as e:
            logger.error(f"验证失败 {obj.object_key}: {e}")
            inconsistent += 1
    
    logger.info(f"✅ 一致性验证完成:")
    logger.info(f"  一致: {consistent}")
    logger.info(f"  不一致: {inconsistent}")
    
    return consistent, inconsistent
```

---

### 五、完整迁移执行示例

```bash
# === 完整迁移流程 ===

# 1. 停止个人版 CoPaw
copaw stop

# 2. 备份数据
cp -r working working.backup
cp working/copaw.db working.backup/copaw.db.bak

# 3. 安装企业版
pip install copaw[enterprise]

# 4. 运行数据库迁移
alembic upgrade head

# 5. 执行 SQLite → PostgreSQL 迁移
python scripts/migrate_sqlite_to_postgres.py \
    --sqlite-db working/copaw.db \
    --pg-dsn postgresql://user:pass@localhost/copaw \
    --tenant-id acme-corp

# 6. 批量索引工作空间文件
python scripts/batch_index.py \
    --workspace-root working/workspaces \
    --tenant-id acme-corp

# 7. 验证一致性
python scripts/verify_migration.py

# 8. 启动企业版
copaw app --enterprise
```

---

### 六、关键设计要点

| 机制 | 说明 | 代码位置 |
|------|------|----------|
| **幂等上传** | `put_object` 前检查 `exists`，避免重复 | `batch_index.py` |
| **内容哈希去重** | SHA-256 检测相同内容，跳过重复上传 | `metadata_extractor.py` |
| **事务保证** | 元数据双写使用数据库事务，失败回滚 | `write_hook.py` |
| **软删除** | `deleted_at` 字段标记删除，不物理删除 | `storage_meta.py` |
| **版本控制** | `version_id` + `is_latest` 支持多版本 | `storage_meta.py` |
| **错误容忍** | WriteHook 失败不阻断文件上传 | `write_hook.py` |

这样就保证了**初始化、迁移、运行时**三个场景下的数据完整同步！