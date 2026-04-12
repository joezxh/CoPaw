# Phase 1: 存储抽象层开发计划

## 前置条件
- 项目已有 `EnterpriseConfig` (config.py L60), 支持 `database` + `redis` 子配置
- 项目已有 `exceptions.py` 定义业务异常基类
- 项目已有 FastAPI lifespan 管理 (_app.py L163)
- `pyproject.toml` 已有 `[enterprise]` optional-dependencies
- `aiofiles` 已在核心依赖中

## 任务分解

### Task 1: 创建 storage 包和基础接口
**文件**: `src/copaw/storage/__init__.py`, `src/copaw/storage/base.py`

创建 `ObjectStorageProvider` 抽象基类，包含以下方法：
- `put(key, data, content_type, metadata, storage_class)` -> ObjectMetadata
- `get(key)` -> bytes
- `get_stream(key)` -> AsyncIterator[bytes]
- `delete(key)` -> bool
- `exists(key)` -> bool
- `copy(source_key, dest_key)` -> ObjectMetadata
- `list_objects(prefix, delimiter, max_keys, continuation_token)` -> ListResult
- `get_metadata(key)` -> ObjectMetadata
- `put_metadata(key, metadata)` -> ObjectMetadata
- `presign_url(key, expires_in)` -> str
- `initialize()` / `close()`

定义数据类：`ObjectMetadata`, `ListResult`, `StorageClass`(枚举)
定义异常：`StorageError`, `StorageNotFoundError`, `StoragePermissionError`, `StorageTimeoutError`

### Task 2: 实现 FileSystem 适配器
**文件**: `src/copaw/storage/filesystem_adapter.py`

- key 映射为 `base_dir / key` 的文件路径
- `put`: aiofiles 写入，metadata 存为 `.meta.json` 伴生文件
- `get`: aiofiles 读取
- `delete`: 删除文件 + meta文件
- `exists`: Path.exists()
- `list_objects`: os.scandir 递归
- `copy`: shutil.copy2
- `presign_url`: 返回 `file:///` URL（个人版不支持预签名，返回文件路径）
- 与现有 `~/.copaw/` 100% 兼容

### Task 3: 实现 S3 适配器
**文件**: `src/copaw/storage/s3_adapter.py`

- 使用 `aioboto3` 异步客户端
- 完整实现所有接口方法
- 支持分片上传（大文件）
- 支持 presign_url

### Task 4: 实现 MinIO 适配器
**文件**: `src/copaw/storage/minio_adapter.py`

- 使用 `miniopy-async` SDK
- MinIO 原生 API 优化路径
- bucket 自动创建

### Task 5: 实现 OSS 适配器
**文件**: `src/copaw/storage/oss_adapter.py`

- 使用 `oss2` SDK
- 实现 OSS 特有的签名 URL 生成

### Task 6: 实现 SFTP 适配器
**文件**: `src/copaw/storage/sftp_adapter.py`

- 使用 `asyncssh` 库
- key 映射为 SFTP 服务器上的相对路径
- 连接池管理

### Task 7: 创建 StorageConfig 配置模型
**文件**: `src/copaw/storage/config.py`

- Pydantic BaseModel，包含所有后端的配置字段
- 支持 `COPAW_STORAGE_*` 环境变量覆盖
- 集成到 `EnterpriseConfig` 中（修改 config.py）

### Task 8: 创建工厂方法和全局单例
**文件**: 修改 `src/copaw/storage/__init__.py`

- `create_storage_provider(config)` 工厂方法
- `get_storage_provider()` 全局单例获取
- `reset_storage_provider()` 测试用重置

### Task 9: FastAPI 生命周期集成
**文件**: 修改 `src/copaw/app/_app.py`

- 在 lifespan 的企业版初始化段落中加入 storage provider 初始化
- 在 shutdown 时调用 `storage.close()`
- 将 storage provider 挂载到 `app.state.storage`

### Task 10: 存储服务 REST API 路由
**文件**: `src/copaw/app/routers/storage.py`

实现以下端点：
- `PUT /api/enterprise/storage/{key:path}` - 上传文件
- `GET /api/enterprise/storage/{key:path}` - 下载文件
- `DELETE /api/enterprise/storage/{key:path}` - 删除文件
- `GET /api/enterprise/storage/list` - 列出文件
- `GET /api/enterprise/storage/presign/{key:path}` - 获取预签名URL
- `GET /api/enterprise/storage/metadata/{key:path}` - 获取元数据
- `GET /api/enterprise/storage/stats` - 存储统计

注册路由到主 app（修改 `src/copaw/app/routers/__init__.py`）

### Task 11: 添加依赖包
**文件**: 修改 `pyproject.toml`

在 `[project.optional-dependencies.enterprise]` 中添加：
- `aioboto3>=12.0`
- `miniopy-async>=1.0`
- `oss2>=2.18`
- `asyncssh>=2.14`

### Task 12: 编写验收测试
**文件**: `tests/unit/storage/` 目录

创建测试文件：
- `tests/unit/storage/__init__.py`
- `tests/unit/storage/test_base.py` - 接口定义和数据类测试
- `tests/unit/storage/test_filesystem_adapter.py` - FileSystem 适配器完整测试
- `tests/unit/storage/test_s3_adapter.py` - S3 适配器测试（mock boto3）
- `tests/unit/storage/test_minio_adapter.py` - MinIO 适配器测试（mock）
- `tests/unit/storage/test_oss_adapter.py` - OSS 适配器测试（mock）
- `tests/unit/storage/test_sftp_adapter.py` - SFTP 适配器测试（mock）
- `tests/unit/storage/test_config.py` - StorageConfig 配置测试
- `tests/unit/storage/test_factory.py` - 工厂方法和单例测试
- `tests/unit/storage/test_api.py` - REST API 端点测试

验收测试标记覆盖：
- **T-ARCH-001**: 双轨存储架构基础验证（4项）
- **T-STORAGE-001**: 5个适配器功能 + 工厂切换（7项）
- **T-STORAGE-002**: 接口方法验证（8项）
- **T-STORAGE-003**: 性能指标验证（5项）
- **T-STORAGE-004**: 错误处理验证（5项）

## 文件清单

| 操作 | 文件路径 | 说明 |
|------|----------|------|
| 新建 | `src/copaw/storage/__init__.py` | 包初始化 + 工厂方法 |
| 新建 | `src/copaw/storage/base.py` | 抽象接口 + 数据类 + 异常 |
| 新建 | `src/copaw/storage/config.py` | StorageConfig 配置模型 |
| 新建 | `src/copaw/storage/filesystem_adapter.py` | 本地文件系统适配器 |
| 新建 | `src/copaw/storage/s3_adapter.py` | S3 适配器 |
| 新建 | `src/copaw/storage/minio_adapter.py` | MinIO 适配器 |
| 新建 | `src/copaw/storage/oss_adapter.py` | 阿里云 OSS 适配器 |
| 新建 | `src/copaw/storage/sftp_adapter.py` | SFTP 适配器 |
| 新建 | `src/copaw/app/routers/storage.py` | 存储 REST API 路由 |
| 修改 | `src/copaw/config/config.py` | EnterpriseConfig 添加 storage 字段 |
| 修改 | `src/copaw/app/_app.py` | lifespan 集成 storage 初始化 |
| 修改 | `src/copaw/app/routers/__init__.py` | 注册 storage 路由 |
| 修改 | `pyproject.toml` | 添加 enterprise 依赖 |
| 新建 | `tests/unit/storage/__init__.py` | 测试包 |
| 新建 | `tests/unit/storage/test_base.py` | 基础接口测试 |
| 新建 | `tests/unit/storage/test_filesystem_adapter.py` | FileSystem 测试 |
| 新建 | `tests/unit/storage/test_s3_adapter.py` | S3 测试 |
| 新建 | `tests/unit/storage/test_minio_adapter.py` | MinIO 测试 |
| 新建 | `tests/unit/storage/test_oss_adapter.py` | OSS 测试 |
| 新建 | `tests/unit/storage/test_sftp_adapter.py` | SFTP 测试 |
| 新建 | `tests/unit/storage/test_config.py` | 配置模型测试 |
| 新建 | `tests/unit/storage/test_factory.py` | 工厂方法测试 |
| 新建 | `tests/unit/storage/test_api.py` | API 端点测试 |
