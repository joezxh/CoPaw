# CoPaw 企业级网络存储与云端部署改造方案

> **版本**: 2.0.0  
> **创建日期**: 2026-04-12  
> **更新日期**: 2026-04-12  
> **适用范围**: CoPaw Enterprise Edition — 面向中小企业局域网部署，从本地文件系统/SQLite 架构迁移至网络对象存储 + PostgreSQL 统一架构  
> **前置文档**: [data_models.md](./data_models.md) — CoPaw 完整数据模型架构

---

## 目录

- [1. 改造背景与目标](#1-改造背景与目标)
  - [1.1 背景](#11-背景)
  - [1.2 改造目标](#12-改造目标)
  - [1.3 设计假设与性能指标](#13-设计假设与性能指标)
- [2. 现状分析](#2-现状分析)
  - [2.1 当前存储架构](#21-当前存储架构)
  - [2.2 本地文件系统依赖清单](#22-本地文件系统依赖清单)
  - [2.3 SQLite 数据依赖清单（企业版全量迁移至 PostgreSQL）](#23-sqlite-数据依赖清单企业版全量迁移至-postgresql)
  - [2.4 本地功能服务清单](#24-本地功能服务清单)
- [3. 网络文件对象存储抽象层设计](#3-网络文件对象存储抽象层设计)
  - [3.1 架构总览](#31-架构总览)
  - [3.2 统一存储接口定义](#32-统一存储接口定义)
  - [3.3 存储后端适配器](#33-存储后端适配器)
  - [3.4 配置模型](#34-配置模型)
  - [3.5 中间件集成](#35-中间件集成)
- [4. 多租户分层存储设计](#4-多租户分层存储设计)
  - [4.1 对象键命名规范](#41-对象键命名规范)
  - [4.2 存储层级映射](#42-存储层级映射)
  - [4.3 访问控制策略](#43-访问控制策略)
  - [4.4 数据隔离保障](#44-数据隔离保障)
- [5. 文件系统元数据抽取与索引](#5-文件系统元数据抽取与索引)
  - [5.0 双轨存储架构](#50-双轨存储架构)
  - [5.1 元数据模型设计](#51-元数据模型设计)
  - [5.2 元数据抽取规则](#52-元数据抽取规则)
  - [5.3 索引策略](#53-索引策略)
  - [5.4 搜索服务API](#54-搜索服务api)
- [6. SQLite 到 PostgreSQL 迁移策略](#6-sqlite-到-postgresql-迁移策略)
  - [6.1 迁移评估矩阵](#61-迁移评估矩阵)
  - [6.2 ReMe 记忆数据库迁移](#62-reme-记忆数据库迁移)
  - [6.3 向量嵌入迁移方案](#63-向量嵌入迁移方案)
  - [6.4 企业版全量迁移策略](#64-企业版全量迁移策略)
  - [6.5 企业版/个人版后端选择](#65-企业版个人版后端选择)
- [7. 本地功能服务端迁移](#7-本地功能服务端迁移)
  - [7.1 可迁移功能清单](#71-可迁移功能清单)
  - [7.2 本地模型推理服务](#72-本地模型推理服务)
  - [7.3 文件处理和转换服务](#73-文件处理和转换服务)
  - [7.4 记忆检索和压缩服务](#74-记忆检索和压缩服务)
  - [7.5 技能执行和管理服务](#75-技能执行和管理服务)
  - [7.6 定时任务调度服务](#76-定时任务调度服务)
- [8. API 接口设计](#8-api-接口设计)
  - [8.1 存储服务API](#81-存储服务api)
  - [8.2 元数据查询API](#82-元数据查询api)
  - [8.3 迁移管理API](#83-迁移管理api)
- [9. 安全设计](#9-安全设计)
  - [9.1 传输安全](#91-传输安全)
  - [9.2 存储安全](#92-存储安全)
  - [9.3 访问安全](#93-访问安全)
  - [9.4 合规要求](#94-合规要求)
- [10. 分阶段实施计划](#10-分阶段实施计划)
  - [10.1 阶段概览](#101-阶段概览)
  - [10.2 Phase 1: 存储抽象层](#102-phase-1-存储抽象层)
  - [10.3 Phase 2: 多租户分层存储](#103-phase-2-多租户分层存储)
  - [10.4 Phase 3: 双轨存储+元数据+SQLite迁移](#104-phase-3-双轨存储元数据sqlite迁移)
  - [10.5 Phase 4: 功能服务端迁移](#105-phase-4-功能服务端迁移)
- [11. 风险评估与回滚方案](#11-风险评估与回滚方案)
- [12. 附录](#12-附录)

---

## 1. 改造背景与目标

### 1.1 背景

CoPaw 当前采用**混合本地存储架构**：

- **文件系统** (`~/.copaw/`): 存储 Agent 配置、技能文件、人格文件、记忆 Markdown、对话历史等
- **SQLite**: ReMe 记忆数据库的向量嵌入和语义索引
- **PostgreSQL**: 企业版结构化数据（用户、权限、审计等）
- **Redis**: 会话缓存、令牌缓存

此架构在**单机/个人版**场景下表现良好，但在**企业版**场景中存在以下问题：

> **目标场景**：CoPaw 企业版主要面向**中小企业**，以**局域网内部署**为主（非公网云端），
> 单租户用户规模通常在 **10-500 人**，数据量相对较小（GB 级而非 TB 级），
> 优先考虑**部署简便性**和**运维成本**，而非极致的弹性伸缩能力。

| 问题 | 影响 |
|------|------|
| 本地文件系统依赖 | 多节点部署时数据不共享，容器重启后数据丢失 |
| SQLite 本地锁定 | 无法多实例共享，企业版应统一使用 PostgreSQL，消除 SQLite 依赖 |
| 无统一存储抽象 | 难以切换存储后端（MinIO/S3/OSS），局域网部署首选 MinIO |
| 多租户存储隔离缺失 | 文件路径命名缺乏租户前缀，跨租户数据可能泄露 |
| 文件元数据未结构化 | agent.json/chats.json 等结构化数据仍以文件存储，无法高效查询 |
| 通道消息数据散落 | 飞书/钉钉等通道消息仅存本地文件，无法跨节点共享和审计 |

### 1.2 改造目标

1. **建立统一对象存储抽象层**：支持 S3/MinIO/OSS/SFTP，局域网场景首选 MinIO，上层代码零改动切换后端
2. **实现多租户分层存储**：按 `租户/部门/用户` 三级结构组织存储键，确保数据隔离
3. **文件数据双轨重构**：将现有文件系统数据模型拆分为两部分：
   - **网络文件存储**：存储原始文件内容（Agent 配置、技能文件、媒体文件、人格 Markdown 等）
   - **PostgreSQL 结构化元数据**：存储从 JSON 文件中抽取的结构化信息（Agent 配置元数据、Skill 元数据、对话历史、Token 统计、定时任务、通道消息等）
4. **企业版取消 SQLite**：企业版全面使用 PostgreSQL + pgvector 替代 SQLite，个人版保留 SQLite
5. **通道消息入库**：将飞书/钉钉等通道消息迁移到 PostgreSQL，支持跨节点共享和审计
6. **功能服务端化**：将本地执行的功能迁移为服务端集中调度
7. **向后兼容**：个人版用户零改动升级，企业版平滑迁移

### 1.3 设计假设与性能指标

基于中小企业局域网部署场景，调整设计假设：

| 维度 | 假设值 | 说明 |
|------|--------|------|
| 单租户用户数 | 10-500 人 | 中小企业规模 |
| 单租户工作空间数 | 5-50 个 | 按部门/项目划分 |
| 对象存储文件数 | 1万-50万 | Agent 配置 + 技能 + 媒体 + 记忆文件 |
| PostgreSQL 数据量 | 1-50 GB | 元数据 + 记忆 + 对话 + 通道消息 |
| 向量记忆条目 | 1万-100万 | pgvector 完全胜任 |
| 并发 API 请求 | 10-100 QPS | 局域网内用户量有限 |
| 部署节点数 | 1-3 节点 | 小集群高可用 |
| 搜索响应时间 | < 200ms | 5万文件内 |
| 向量搜索延迟 | < 50ms | 100万条记忆内 |
| 文件上传大小 | ≤ 500MB | 单个媒体/模型文件 |

---

## 2. 现状分析

### 2.1 当前存储架构

```
┌─────────────────────────────────────────────────────────────────┐
│                    CoPaw 当前存储架构                              │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ~/.copaw/ (本地文件系统)          PostgreSQL (企业版)            │
│  ├── workspaces/                  ├── sys_users (用户)           │
│  │   ├── default/                 ├── sys_roles (角色)           │
│  │   │   ├── agent.json           ├── sys_workspaces (工作空间)  │
│  │   │   ├── chats.json           ├── ai_tasks (任务)            │
│  │   │   ├── jobs.json            ├── ai_workflows (工作流)      │
│  │   │   ├── token_usage.json     ├── sys_audit_logs (审计)      │
│  │   │   ├── MEMORY.md            └── sys_dlp_rules (DLP)        │
│  │   │   ├── AGENTS.md                                          │
│  │   │   ├── skills/              Redis (缓存)                   │
│  │   │   └── memory/              ├── 会话缓存                   │
│  │   └── {agent_id}/              ├── 令牌缓存                   │
│  ├── skill_pool/                  └── 权限缓存                   │
│  ├── memory/                                                     │
│  ├── media/                       SQLite (本地)                  │
│  ├── models/                      ├── ReMe 记忆嵌入              │
│  ├── config.json                  └── 向量索引缓存               │
│  └── .secret/auth.json                                           │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### 2.2 本地文件系统依赖清单

| 数据类别 | 目录路径 | 大小估算 | 访问频率 | 并发要求 |
|----------|----------|----------|----------|----------|
| Agent 配置 | `workspaces/{id}/agent.json` | ~12KB/个 | 中 | 低 |
| 对话历史 | `workspaces/{id}/chats.json` | 1-100MB/个 | 高 | 中 |
| 定时任务 | `workspaces/{id}/jobs.json` | ~5KB/个 | 低 | 低 |
| Token 使用 | `workspaces/{id}/token_usage.json` | ~10KB/个 | 低 | 低 |
| 技能清单 | `workspaces/{id}/skill.json` | ~16KB/个 | 中 | 低 |
| 技能文件 | `workspaces/{id}/skills/` | 1-50MB/技能 | 中 | 低 |
| 人格文件 | `workspaces/{id}/*.md` | ~2KB/个 | 中 | 低 |
| 每日记忆 | `workspaces/{id}/memory/*.md` | ~5KB/天 | 中 | 低 |
| 共享技能池 | `skill_pool/` | 100-500MB | 低 | 低 |
| 媒体文件 | `media/` | 不定 | 低 | 中 |
| 本地模型 | `models/` | 1-50GB/模型 | 低 | 低 |
| 全局配置 | `config.json` | ~5KB | 低 | 低 |
| 认证信息 | `.secret/auth.json` | ~1KB | 低 | 低 |
| 自定义通道 | `custom_channels/` | 不定 | 低 | 低 |
| 插件 | `plugins/` | 不定 | 低 | 低 |
| 调试历史 | `debug_history.jsonl` | 不定 | 低 | 低 |

**关键路径常量** (定义于 `src/copaw/constant.py`):

| 常量 | 默认值 | 说明 |
|------|--------|------|
| `WORKING_DIR` | `~/.copaw` | 工作目录根路径 |
| `SECRET_DIR` | `{WORKING_DIR}.secret` | 密钥存储目录 |
| `DEFAULT_MEDIA_DIR` | `{WORKING_DIR}/media` | 媒体文件目录 |
| `MODELS_DIR` | `{WORKING_DIR}/models` | 本地模型目录 |
| `MEMORY_DIR` | `{WORKING_DIR}/memory` | 全局记忆目录 |
| `CUSTOM_CHANNELS_DIR` | `{WORKING_DIR}/custom_channels` | 自定义通道目录 |
| `PLUGINS_DIR` | `{WORKING_DIR}/plugins` | 插件目录 |

### 2.3 SQLite 数据依赖清单（企业版全量迁移至 PostgreSQL）

> **核心决策**：企业版取消 SQLite，所有 SQLite 数据全量迁移至 PostgreSQL + pgvector。
> 个人版保留 SQLite 不受影响。此决策基于以下理由：
> - 中小企业数据量有限（GB 级），PostgreSQL + pgvector 完全胜任
> - 统一数据存储简化运维，避免同时维护 SQLite + PostgreSQL 两套体系
> - 支持多节点共享，局域网内多个 CoPaw 实例可访问同一数据库
> - 向量搜索在 pgvector 中的性能对中小企业场景足够

| 数据类别 | 数据库位置 | 迁移目标 PG 表 | 大小估算 | 迁移优先级 |
|----------|-----------|---------------|----------|-----------|
| ReMe 记忆条目 | `workspaces/{id}/.reme/` | `ai_memories` | 10-500MB/空间 | P0-高 |
| 记忆标签 | 同上 | `ai_memory_tags` | <1MB | P0-高 |
| 会话上下文 | 同上 | `ai_memory_sessions` | <10MB | P1-中 |
| 会话-记忆关联 | 同上 | `ai_memory_session_links` | <5MB | P1-中 |
| 向量嵌入缓存 | 同上 | `ai_embedding_cache` | 10-100MB | P0-高 |

**ReMe 记忆数据库核心表结构**（迁移前）:
```sql
CREATE TABLE memories (
    id TEXT PRIMARY KEY,
    content TEXT NOT NULL,
    embedding BLOB,              -- numpy 序列化向量
    embedding_model TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    metadata TEXT,               -- JSON 元数据
    category TEXT,
    importance REAL DEFAULT 0.5,
    access_count INTEGER DEFAULT 0,
    last_accessed_at TIMESTAMP
);
```

### 2.4 本地功能服务清单

| 功能 | 实现位置 | 资源消耗 | 迁移价值 | 说明 |
|------|----------|----------|----------|------|
| 本地模型推理 | `local_models/manager.py`, `llamacpp.py` | GPU/CPU密集 | 中 | llama.cpp 本地推理，可集中部署 |
| 模型下载管理 | `local_models/download_manager.py` | 网络/磁盘 | 低 | GGUF 模型下载，适合CDN |
| 记忆压缩 | `agents/memory/reme_light_memory_manager.py` | CPU/LLM API | 高 | 定期压缩旧记忆，适合集中调度 |
| 记忆检索 | 同上 | 向量计算 | 高 | 语义搜索，集中化可共享索引 |
| 技能执行 | `agents/skills/` | CPU/IO | 中 | Python 脚本执行，容器化可隔离 |
| 定时任务 | `jobs.json` + cron | CPU | 高 | 集中调度避免冲突 |
| 文件处理 | docx/xlsx/pptx 技能 | CPU/内存 | 中 | Office 文件转换 |
| 心跳监控 | `HEARTBEAT.md` 配置 | 网络 | 高 | 集中监控多个 Agent |
| 通道消息处理 | 各通道实现 | 网络/IO | **高** | 企业版消息入 PostgreSQL，支持审计和跨节点共享 |

---

## 3. 网络文件对象存储抽象层设计

### 3.1 架构总览

企业版采用**双轨存储架构**：网络对象存储保存原始文件，PostgreSQL 保存结构化元数据，两者通过 `storage_key` / `content_hash` 关联。

```
┌─────────────────────────────────────────────────────────────────────────┐
│                        应用层 (Business Logic)                           │
│    AgentManager / SkillManager / MemoryManager / ConfigManager          │
├─────────────────────────────────────────────────────────────────────────┤
│                       双轨存储抽象接口层                                  │
│  ┌──────────────────────────────┐  ┌──────────────────────────────────┐  │
│  │   对象存储接口                │  │   元数据存储接口                   │  │
│  │   ObjectStorageProvider      │  │   MetadataRepository (SQLAlchemy) │  │
│  │   put/get/delete/list        │  │   AgentConfigRepo / SkillRepo     │  │
│  │   exists/copy/presign_url    │  │   ConversationRepo / MemoryRepo   │  │
│  │   → 存储原始文件内容          │  │   ChannelMsgRepo / TokenUsageRepo │  │
│  └──────────┬───────────────────┘  │   → 存储结构化元数据              │  │
│             │                      └──────────┬───────────────────────┘  │
├─────────────┼─────────────────────────────────┼──────────────────────────┤
│  对象存储适配器                                  │  PG 数据访问层           │
│  ┌────┬──────┬─────┬──────┬──────────┐   │  SQLAlchemy 2.0 + asyncpg  │
│  │ S3 │MinIO │ OSS │ SFTP │FileSystem│   │  pgvector 扩展             │
│  └────┴──────┴─────┴──────┴──────────┘   │  Alembic 迁移              │
├───────────────────────────────────────────┼──────────────────────────────┤
│  AWS S3  MinIO  阿里云OSS  SFTP服务器     │  PostgreSQL 15+              │
│  (原始文件: agent.json / skill / media)   │  (元数据: configs / chats / │
│                                          │   token_usage / memory /    │
│                                          │   channel_messages / tasks) │
└───────────────────────────────────────────┴──────────────────────────────┘

写入流程: 文件上传 → 对象存储(原始文件) + PostgreSQL(元数据双写抽取)
读取流程: 查询PG获取元数据 → 按需从对象存储获取原始文件
```

**【验收测试标记 T-ARCH-001】双轨存储架构验证**

| 测试项 | 验证方法 | 通过标准 |
|--------|----------|----------|
| 双轨写入一致性 | 上传文件后检查对象存储和PG元数据 | 5秒内对象存储有文件 + PG有元数据记录 |
| storage_key关联 | 查询PG元数据记录的storage_key，从对象存储读取 | 能成功读取原始文件，content_hash一致 |
| 元数据抽取完整性 | 上传agent.json，查询ai_agent_configs表 | 所有结构化字段正确抽取 |
| 通道消息入库 | 发送飞书/钉钉消息，查询ai_channel_messages | 500ms内消息入库，字段完整 |

---

### 3.2 统一存储接口定义

```python
# src/copaw/storage/base.py

from __future__ import annotations

import abc
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import AsyncIterator, Optional


class StorageClass(str, Enum):
    """对象存储类别"""
    STANDARD = "STANDARD"
    INFREQUENT = "INFREQUENT_ACCESS"
    ARCHIVE = "ARCHIVE"


@dataclass
class ObjectMetadata:
    """对象元数据"""
    key: str
    size: int                          # 字节数
    content_type: str = "application/octet-stream"
    etag: str = ""
    last_modified: Optional[datetime] = None
    storage_class: StorageClass = StorageClass.STANDARD
    custom_metadata: dict[str, str] = field(default_factory=dict)
    # CoPaw 扩展字段
    tenant_id: str = ""
    owner_id: str = ""
    category: str = ""                 # workspace/skill/memory/media/model/config


@dataclass
class ListResult:
    """列表查询结果"""
    objects: list[ObjectMetadata]
    prefix: str
    is_truncated: bool = False
    continuation_token: str = ""


class ObjectStorageProvider(abc.ABC):
    """统一对象存储接口 — 所有后端必须实现此接口"""

    # ── 基本操作 ────────────────────────────────────────────── #

    @abc.abstractmethod
    async def put(
        self,
        key: str,
        data: bytes | AsyncIterator[bytes],
        content_type: str = "application/octet-stream",
        metadata: dict[str, str] | None = None,
        storage_class: StorageClass = StorageClass.STANDARD,
    ) -> ObjectMetadata:
        """上传对象"""

    @abc.abstractmethod
    async def get(self, key: str) -> bytes:
        """下载对象（完整内容）"""

    @abc.abstractmethod
    async def get_stream(self, key: str) -> AsyncIterator[bytes]:
        """流式下载对象（适用于大文件）"""

    @abc.abstractmethod
    async def delete(self, key: str) -> bool:
        """删除对象"""

    @abc.abstractmethod
    async def exists(self, key: str) -> bool:
        """检查对象是否存在"""

    @abc.abstractmethod
    async def copy(self, source_key: str, dest_key: str) -> ObjectMetadata:
        """复制对象"""

    # ── 列表查询 ────────────────────────────────────────────── #

    @abc.abstractmethod
    async def list_objects(
        self,
        prefix: str,
        delimiter: str = "/",
        max_keys: int = 1000,
        continuation_token: str = "",
    ) -> ListResult:
        """按前缀列出对象"""

    # ── 元数据操作 ──────────────────────────────────────────── #

    @abc.abstractmethod
    async def get_metadata(self, key: str) -> ObjectMetadata:
        """获取对象元数据（不下载内容）"""

    @abc.abstractmethod
    async def put_metadata(self, key: str, metadata: dict[str, str]) -> None:
        """更新对象自定义元数据"""

    # ── 预签名URL ──────────────────────────────────────────── #

    @abc.abstractmethod
    async def presign_get(self, key: str, expires_in: int = 3600) -> str:
        """生成预签名下载URL"""

    @abc.abstractmethod
    async def presign_put(self, key: str, expires_in: int = 3600) -> str:
        """生成预签名上传URL"""

    # ── 生命周期 ────────────────────────────────────────────── #

    @abc.abstractmethod
    async def health_check(self) -> bool:
        """检查存储后端连通性"""

    async def initialize(self) -> None:
        """初始化（可选实现）"""

    async def close(self) -> None:
        """关闭连接（可选实现）"""
```

### 3.3 存储后端适配器

#### 3.3.1 S3 适配器 (AWS / 通用 S3 协议)

```python
# src/copaw/storage/s3_adapter.py

import aioboto3
from .base import ObjectStorageProvider, ObjectMetadata, ListResult, StorageClass


class S3StorageAdapter(ObjectStorageProvider):
    """AWS S3 / 通用 S3 协议适配器

    支持: AWS S3, Ceph, DigitalOcean Spaces, 以及任何 S3 兼容存储
    """

    def __init__(self, config: S3StorageConfig):
        self._config = config
        self._session = aioboto3.Session()
        self._client = None

    async def initialize(self):
        self._client = await self._session.client(
            "s3",
            endpoint_url=self._config.endpoint_url,  # None = AWS 原生
            aws_access_key_id=self._config.access_key,
            aws_secret_access_key=self._config.secret_key,
            region_name=self._config.region,
        ).__aenter__()

    async def put(self, key, data, content_type="application/octet-stream",
                  metadata=None, storage_class=StorageClass.STANDARD):
        extra_args = {
            "ContentType": content_type,
            "StorageClass": storage_class.value,
        }
        if metadata:
            extra_args["Metadata"] = metadata
        await self._client.put_object(
            Bucket=self._config.bucket,
            Key=key,
            Body=data,
            **extra_args,
        )
        return await self.get_metadata(key)

    async def get(self, key):
        resp = await self._client.get_object(
            Bucket=self._config.bucket, Key=key
        )
        return await resp["Body"].read()

    async def delete(self, key):
        await self._client.delete_object(
            Bucket=self._config.bucket, Key=key
        )
        return True

    # ... 其余方法实现省略
```

#### 3.3.2 MinIO 适配器

```python
# src/copaw/storage/minio_adapter.py

from miniopy_async import Minio
from .base import ObjectStorageProvider


class MinIOStorageAdapter(ObjectStorageProvider):
    """MinIO 适配器

    MinIO 完全兼容 S3 协议，因此也可通过 S3StorageAdapter 访问。
    此适配器提供 MinIO 原生 SDK 的优化路径。
    """

    def __init__(self, config: MinIOStorageConfig):
        self._client = Minio(
            endpoint=config.endpoint,
            access_key=config.access_key,
            secret_key=config.secret_key,
            secure=config.secure,
        )
        self._bucket = config.bucket

    # 实现同 S3 适配器，使用 miniopy_async API
```

#### 3.3.3 阿里云 OSS 适配器

```python
# src/copaw/storage/oss_adapter.py

import oss2
from .base import ObjectStorageProvider


class OSSStorageAdapter(ObjectStorageProvider):
    """阿里云 OSS 适配器"""
    # 使用 oss2 异步 SDK 实现
```

#### 3.3.4 SFTP 适配器

```python
# src/copaw/storage/sftp_adapter.py

import asyncssh
from .base import ObjectStorageProvider


class SFTPStorageAdapter(ObjectStorageProvider):
    """SFTP 适配器

    适用于传统文件服务器、内网 NAS 等场景。
    模拟对象存储的 key-value 语义，key 映射为相对路径。
    """

    def __init__(self, config: SFTPStorageConfig):
        self._config = config
        self._conn = None

    async def initialize(self):
        self._conn = await asyncssh.connect(
            host=self._config.host,
            port=self._config.port,
            username=self._config.username,
            password=self._config.password,
            client_keys=self._config.private_key_path,
        )
        self._sftp = await self._conn.start_sftp_client()
        # 确保根目录存在
        await self._sftp.mkdir(self._config.base_dir, exist_ok=True)
```

#### 3.3.5 文件系统适配器 (个人版兼容)

```python
# src/copaw/storage/filesystem_adapter.py

import aiofiles
from pathlib import Path
from .base import ObjectStorageProvider


class FileSystemStorageAdapter(ObjectStorageProvider):
    """本地文件系统适配器

    保持与个人版 ~/.copaw/ 的完全兼容。
    key 直接映射为相对于 base_dir 的文件路径。
    此适配器为默认后端，无需额外配置。
    """

    def __init__(self, config: FileSystemStorageConfig):
        self._base_dir = Path(config.base_dir).expanduser().resolve()

    async def put(self, key, data, content_type="application/octet-stream",
                  metadata=None, storage_class=StorageClass.STANDARD):
        path = self._base_dir / key
        path.parent.mkdir(parents=True, exist_ok=True)
        if isinstance(data, bytes):
            async with aiofiles.open(path, "wb") as f:
                await f.write(data)
        else:
            async with aiofiles.open(path, "wb") as f:
                async for chunk in data:
                    await f.write(chunk)
        # 元数据存储为 .meta.json 伴生文件
        if metadata:
            meta_path = path.with_suffix(path.suffix + ".meta.json")
            async with aiofiles.open(meta_path, "w") as f:
                await f.write(json.dumps(metadata))
        return await self.get_metadata(key)

    async def get(self, key):
        path = self._base_dir / key
        async with aiofiles.open(path, "rb") as f:
            return await f.read()

    # ... 其余方法实现
```

### 3.4 配置模型

```python
# src/copaw/storage/config.py

from pydantic import BaseModel, Field
from typing import Literal


class StorageConfig(BaseModel):
    """统一存储配置 — 嵌入 EnterpriseConfig"""

    backend: Literal["filesystem", "s3", "minio", "oss", "sftp"] = Field(
        default="filesystem",
        description="存储后端类型。个人版默认 filesystem，企业版建议 s3/minio"
    )

    # 通用配置
    default_bucket: str = Field(
        default="copaw-data",
        description="默认存储桶/命名空间"
    )
    presign_enabled: bool = Field(
        default=True,
        description="是否启用预签名URL（大文件直传）"
    )
    presign_expire_seconds: int = Field(
        default=3600,
        description="预签名URL过期时间（秒）"
    )

    # 元数据同步
    metadata_sync_enabled: bool = Field(
        default=True,
        description="是否将对象元数据同步到 PostgreSQL"
    )

    # S3 兼容配置
    s3_endpoint_url: str = Field(default="", description="S3 端点URL (空=AWS原生)")
    s3_access_key: str = Field(default="")
    s3_secret_key: str = Field(default="")
    s3_region: str = Field(default="us-east-1")

    # MinIO 配置
    minio_endpoint: str = Field(default="localhost:9000")
    minio_access_key: str = Field(default="")
    minio_secret_key: str = Field(default="")
    minio_secure: bool = Field(default=False)

    # OSS 配置
    oss_endpoint: str = Field(default="")
    oss_access_key_id: str = Field(default="")
    oss_access_key_secret: str = Field(default="")
    oss_bucket_name: str = Field(default="copaw-data")

    # SFTP 配置
    sftp_host: str = Field(default="localhost")
    sftp_port: int = Field(default=22)
    sftp_username: str = Field(default="")
    sftp_password: str = Field(default="")
    sftp_private_key_path: str = Field(default="")
    sftp_base_dir: str = Field(default="/data/copaw")

    # 文件系统配置 (个人版)
    filesystem_base_dir: str = Field(
        default="~/.copaw",
        description="本地文件系统根目录"
    )
```

在 `EnterpriseConfig` 中集成：

```python
# 修改 src/copaw/config/config.py 中的 EnterpriseConfig
class EnterpriseConfig(BaseModel):
    # ... 现有字段 ...
    storage: StorageConfig = Field(
        default_factory=StorageConfig,
        description="对象存储配置"
    )
```

### 3.5 中间件集成

```python
# src/copaw/storage/__init__.py

from .base import ObjectStorageProvider, ObjectMetadata
from .config import StorageConfig
from .s3_adapter import S3StorageAdapter
from .minio_adapter import MinIOStorageAdapter
from .oss_adapter import OSSStorageAdapter
from .sftp_adapter import SFTPStorageAdapter
from .filesystem_adapter import FileSystemStorageAdapter


_storage_provider: ObjectStorageProvider | None = None


def create_storage_provider(config: StorageConfig) -> ObjectStorageProvider:
    """工厂方法 — 根据配置创建存储适配器"""
    adapters = {
        "filesystem": FileSystemStorageAdapter,
        "s3": S3StorageAdapter,
        "minio": MinIOStorageAdapter,
        "oss": OSSStorageAdapter,
        "sftp": SFTPStorageAdapter,
    }
    adapter_cls = adapters.get(config.backend)
    if not adapter_cls:
        raise ValueError(f"Unsupported storage backend: {config.backend}")

    # 传入对应配置子集
    if config.backend == "filesystem":
        return adapter_cls(config)  # 内部提取 filesystem_base_dir
    elif config.backend in ("s3", "minio"):
        return adapter_cls(config)  # 内部提取 s3/minio 字段
    else:
        return adapter_cls(config)


async def get_storage_provider() -> ObjectStorageProvider:
    """获取全局存储提供者单例"""
    global _storage_provider
    if _storage_provider is None:
        from ..config import load_config
        cfg = load_config()
        _storage_provider = create_storage_provider(cfg.enterprise.storage)
        await _storage_provider.initialize()
    return _storage_provider
```

**【验收测试标记 T-STORAGE-001】存储抽象层功能验证**

| 测试项 | 验证方法 | 通过标准 |
|--------|----------|----------|
| **T-STORAGE-001.1** FileSystem适配器 | `backend="filesystem"`，上传/读取文件 | 与现有 `~/.copaw/` 行为100%兼容 |
| **T-STORAGE-001.2** S3适配器 | `backend="s3"`，上传10MB文件 | 上传成功，presign_url可下载 |
| **T-STORAGE-001.3** MinIO适配器 | `backend="minio"`，局域网MinIO服务器 | 上传/读取/删除正常，延迟<100ms |
| **T-STORAGE-001.4** OSS适配器 | `backend="oss"`，阿里云OSS | 上传/读取/列表正常 |
| **T-STORAGE-001.5** SFTP适配器 | `backend="sftp"`，内网SFTP服务器 | 上传/读取正常，权限正确 |
| **T-STORAGE-001.6** 接口一致性 | 所有适配器调用相同方法 | put/get/delete/list/exists/copy/presign_url 行为一致 |
| **T-STORAGE-001.7** 工厂切换 | 动态切换backend配置 | 零代码修改，配置驱动切换 |

**【验收测试标记 T-STORAGE-002】存储接口方法验证**

| 接口方法 | 测试场景 | 预期结果 |
|----------|----------|----------|
| `put(key, data)` | 上传1MB/10MB/100MB文件 | 成功写入，返回ObjectMetadata |
| `get(key)` | 读取已上传文件 | 返回字节流，与原始文件一致 |
| `delete(key)` | 删除文件 | 对象存储中文件消失，PG元数据软删除 |
| `list(prefix)` | 列出特定前缀下的所有文件 | 返回正确的文件列表，分页正确 |
| `exists(key)` | 检查文件存在性 | 返回True/False准确 |
| `copy(src_key, dst_key)` | 复制文件 | 目标文件存在，内容一致 |
| `presign_url(key)` | 生成预签名URL | URL有效期默认1小时，可下载 |
| `get_metadata(key)` | 获取文件元数据 | 返回content_type/size/hash等 |

**【验收测试标记 T-STORAGE-003】性能指标验证**

| 性能指标 | 测试方法 | 通过标准 |
|----------|----------|----------|
| 小文件上传 (<1MB) | 上传1000个100KB文件 | 平均延迟<200ms，P99<500ms |
| 大文件上传 (50MB) | 上传50MB媒体文件 | 延迟<5s，支持分片上传 |
| 文件读取 | 读取1000个文件 | 平均延迟<100ms，P99<300ms |
| 并发写入 | 10并发同时上传 | 无数据丢失，无死锁 |
| 预签名URL生成 | 生成1000个URL | 平均延迟<10ms |

**【验收测试标记 T-STORAGE-004】错误处理验证**

| 异常场景 | 测试方法 | 预期行为 |
|----------|----------|----------|
| 对象存储不可达 | 断开网络/停止MinIO | 抛出StorageError，不包含敏感信息 |
| 文件不存在 | get不存在的key | 抛出NotFoundError |
| 权限不足 | 使用无权用户访问 | 抛出PermissionError |
| 大文件超时 | 上传500MB文件 | 超时后重试3次，最终失败抛出TimeoutError |
| 并发冲突 | 同时修改同一文件 | 最后写入胜出，无数据损坏 |

---
```

**FastAPI 生命周期集成**:

```python
# 在 src/copaw/app/_app.py 中
from ..storage import create_storage_provider

# 在 create_app() 中:
storage_provider = create_storage_provider(cfg.enterprise.storage)
await storage_provider.initialize()
app.state.storage = storage_provider

# 在 shutdown 中:
storage_provider = getattr(app.state, "storage", None)
if storage_provider:
    await storage_provider.close()
```

---

## 4. 多租户分层存储设计

### 4.1 对象键命名规范

所有存储键遵循统一命名规范，确保多租户隔离和可追溯性：

```
{tenant_id}/{department_id}/{user_id}/{category}/{resource_path}
```

**完整键结构**:

```
copaw-data/                                    # 存储桶
├── {tenant_id}/                               # 租户级
│   ├── _tenant/                               # 租户元数据
│   │   ├── config.json                        # 租户配置
│   │   └── logo.png                           # 租户 Logo
│   ├── {department_id}/                       # 部门级
│   │   ├── _dept/                             # 部门元数据
│   │   │   └── config.json
│   │   └── shared/                            # 部门共享资源
│   │       ├── skills/                        # 部门技能
│   │       └── workflows/                     # 部门工作流
│   └── users/{user_id}/                       # 用户级
│       ├── workspaces/                        # 工作空间
│       │   └── {workspace_id}/
│       │       ├── agent.json                 # Agent 配置
│       │       ├── chats.json                 # 对话历史
│       │       ├── jobs.json                  # 定时任务
│       │       ├── token_usage.json           # Token 记录
│       │       ├── skill.json                 # 技能清单
│       │       ├── skills/                    # 技能文件
│       │       ├── memory/                    # 每日记忆
│       │       │   └── 2026-04-11.md
│       │       ├── MEMORY.md                  # 长期记忆
│       │       ├── AGENTS.md                  # 人格定义
│       │       ├── SOUL.md                    # 灵魂定义
│       │       └── PROFILE.md                 # 配置文件
│       ├── media/                             # 媒体文件
│       │   └── {file_id}.{ext}
│       ├── configs/                           # 用户配置
│       └── sessions/                          # 会话数据
├── _system/                                   # 系统级
│   ├── skill_pool/                            # 全局技能池
│   │   ├── browser_cdp/
│   │   ├── docx/
│   │   └── ...
│   ├── models/                                # 共享模型
│   └── templates/                             # 模板
└── _migrations/                               # 迁移临时
```

### 4.2 存储层级映射

| 原始路径 | 新对象键 | 层级 |
|----------|----------|------|
| `~/.copaw/config.json` | `{tenant}/_tenant/config.json` | 租户级 |
| `~/.copaw/workspaces/{id}/agent.json` | `{tenant}/users/{uid}/workspaces/{ws}/agent.json` | 用户级 |
| `~/.copaw/workspaces/{id}/chats.json` | `{tenant}/users/{uid}/workspaces/{ws}/chats.json` | 用户级 |
| `~/.copaw/workspaces/{id}/skills/` | `{tenant}/users/{uid}/workspaces/{ws}/skills/` | 用户级 |
| `~/.copaw/workspaces/{id}/memory/` | `{tenant}/users/{uid}/workspaces/{ws}/memory/` | 用户级 |
| `~/.copaw/skill_pool/` | `_system/skill_pool/` | 系统级 |
| `~/.copaw/media/` | `{tenant}/users/{uid}/media/` | 用户级 |
| `~/.copaw/models/` | `_system/models/` | 系统级 |
| `~/.copaw/.secret/auth.json` | **不入对象存储** (保留在数据库) | - |
| `~/.copaw/custom_channels/` | `{tenant}/users/{uid}/custom_channels/` | 用户级 |
| `~/.copaw/plugins/` | `_system/plugins/` | 系统级 |

### 4.3 访问控制策略

```python
# src/copaw/storage/access_control.py

from enum import Enum
from functools import wraps


class StorageAccessLevel(str, Enum):
    """存储访问级别"""
    SYSTEM = "system"           # 系统管理员
    TENANT = "tenant"           # 租户管理员
    DEPARTMENT = "department"   # 部门管理员
    USER = "user"               # 普通用户
    PUBLIC = "public"           # 公开访问


class StorageACLEntry:
    """存储访问控制条目"""

    @staticmethod
    def build_key_prefix(
        tenant_id: str,
        department_id: str | None = None,
        user_id: str | None = None,
        category: str | None = None,
    ) -> str:
        """构建存储键前缀"""
        parts = [tenant_id]
        if department_id:
            parts.append(department_id)
            parts.append("shared")
        elif user_id:
            parts.extend(["users", user_id])
        if category:
            parts.append(category)
        return "/".join(parts)

    @staticmethod
    def validate_access(
        user_roles: list[str],
        user_tenant_id: str,
        requested_key: str,
    ) -> bool:
        """验证用户对指定存储键的访问权限"""
        # 1. 解析目标键中的租户ID
        key_tenant = requested_key.split("/")[0]

        # 2. Super Admin 可跨租户
        if "super_admin" in user_roles:
            return True

        # 3. 租户级隔离
        if key_tenant != user_tenant_id:
            return False

        # 4. 系统资源只读
        if requested_key.startswith("_system/"):
            if "tenant_admin" in user_roles:
                return True  # 管理员可读
            return False  # 普通用户需通过 API 代理

        return True
```

### 4.4 数据隔离保障

| 隔离维度 | 实现方式 | 验证方法 |
|----------|----------|----------|
| 租户隔离 | 对象键前缀 `{tenant_id}/` | 所有查询自动注入租户前缀 |
| 部门隔离 | 对象键中间层 `{dept_id}/shared/` | 部门共享资源需部门角色验证 |
| 用户隔离 | 对象键 `{tenant}/users/{uid}/` | 用户只能访问自己的 key 前缀 |
| 系统资源 | 对象键 `_system/` | 通过 API 代理只读访问 |
| 临时数据 | 对象键 `_migrations/` + 生命周期策略 | 7 天后自动清理 |

**【验收测试标记 T-MULTI-TENANT-001】多租户隔离验证**

| 测试项 | 验证方法 | 通过标准 |
|--------|----------|----------|
| **T-MULTI-TENANT-001.1** 租户A无法访问租户B | 租户A用户查询租户B的key前缀 | 返回PermissionError或空结果 |
| **T-MULTI-TENANT-001.2** 租户管理员权限 | 租户管理员访问租户内所有资源 | 成功读取/写入所有文件 |
| **T-MULTI-TENANT-001.3** 普通用户隔离 | 用户A尝试访问用户B的文件 | 返回403 Forbidden |
| **T-MULTI-TENANT-001.4** 系统资源保护 | 直接访问 `_system/` 前缀 | 返回403，仅API代理可访问 |
| **T-MULTI-TENANT-001.5** 对象键自动生成 | 上传文件，检查key格式 | 格式 `{tenant}/{user}/...` 正确 |

**【验收测试标记 T-MULTI-TENANT-002】存储访问控制验证**

| 测试项 | 验证方法 | 通过标准 |
|--------|----------|----------|
| **T-MULTI-TENANT-002.1** RBAC权限检查 | 不同角色访问不同资源 | 权限矩阵100%符合设计 |
| **T-MULTI-TENANT-002.2** 预签名URL权限 | 生成URL后过期测试 | 过期后403，未过期200 |
| **T-MULTI-TENANT-002.3** 跨租户操作拦截 | 尝试修改其他租户的storage_key | 中间件拦截，返回403 |
| **T-MULTI-TENANT-002.4** 审计日志完整性 | 执行100次操作，检查日志 | 100%记录，包含user/action/key |

**【验收测试标记 T-MULTI-TENANT-003】数据一致性验证**

| 测试项 | 验证方法 | 通过标准 |
|--------|----------|----------|
| **T-MULTI-TENANT-003.1** 迁移后数据完整性 | 迁移1000个文件，对比源和目标 | SHA-256 hash 100%一致 |
| **T-MULTI-TENANT-003.2** 临时数据清理 | 创建`_migrations/`文件，等待7天 | 自动清理，无残留 |
| **T-MULTI-TENANT-003.3** 部门共享资源 | 部门A共享文件给部门B | 部门B可读取，部门C不可访问 |

---

## 5. 文件系统元数据抽取与索引

### 5.0 双轨存储架构

企业版采用**双轨存储架构**，将原文件系统数据模型重构为两部分：

```
┌──────────────────────────────────────────────────────────────────────┐
│                        文件系统数据模型重构                            │
│                                                                      │
│  ┌───────────────────────────────┐  ┌──────────────────────────────┐ │
│  │    网络文件对象存储 (MinIO/S3)  │  │    PostgreSQL 元数据存储      │ │
│  │    — 存储原始文件内容 —        │  │    — 存储结构化元数据 —       │ │
│  │                               │  │                              │ │
│  │  • agent.json (原始配置)       │  │  • ai_agent_configs          │ │
│  │  • skill.json / 技能目录       │  │  • ai_skill_configs          │ │
│  │  • chats.json (原始对话)       │  │  • ai_conversations          │ │
│  │  • token_usage.json           │  │  • ai_conversation_messages  │ │
│  │  • jobs.json                  │  │  • ai_token_usage_stats      │ │
│  │  • memory/*.md (原始记忆)      │  │  • ai_tasks (扩展调度字段)    │ │
│  │  • MEMORY.md 等人格文件        │  │  • ai_memory_documents       │ │
│  │  • 媒体文件 (图片/音视频)      │  │  • ai_channel_messages       │ │
│  │  • 模型文件 (.gguf)           │  │  • storage_objects (文件索引) │ │
│  └───────────────────────────────┘  └──────────────────────────────┘ │
│          ↕ put/get/delete/list                  ↕ 结构化查询/聚合        │
│         ObjectStorageProvider               SQLAlchemy + pgvector     │
└──────────────────────────────────────────────────────────────────────┘

写入流程: 文件上传 → 对象存储(原始文件) + PostgreSQL(元数据抽取)
读取流程: 查询PG获取元数据 → 按需从对象存储获取原始文件
```

**设计原则**：
1. **原始文件保真**：对象存储保留完整的原始文件，不丢失任何信息
2. **结构化加速**：PG 存储抽取后的结构化元数据，支持高效查询、聚合、过滤
3. **双向关联**：每条 PG 元数据记录通过 `storage_key` / `content_hash` 关联到对象存储原始文件
4. **变更检测**：通过 `content_hash` 比对实现增量同步，避免全量重索引
5. **企业版消除 SQLite**：所有结构化数据统一由 PostgreSQL 管理，个人版保留本地文件系统

### 5.1 元数据模型设计

元数据模型分为两层：**通用文件索引**（`storage_objects`，5.1.1）和**业务结构化元数据**（5.1.2–5.1.8）。

#### 5.1.1 通用文件对象索引表

所有上传到对象存储的文件自动在 `storage_objects` 表中创建索引记录，提供统一的文件搜索能力：

```sql
-- 通用文件对象索引表
CREATE TABLE storage_objects (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id       VARCHAR(36) NOT NULL DEFAULT 'default-tenant',
    
    -- 对象键
    object_key      VARCHAR(1024) NOT NULL,             -- 对象存储中的键 (全局唯一)
    bucket          VARCHAR(200) NOT NULL DEFAULT 'copaw-data',
    
    -- 文件信息
    file_name       VARCHAR(500) NOT NULL,              -- 文件名
    file_ext        VARCHAR(50),                         -- 扩展名
    content_type    VARCHAR(200),                         -- MIME 类型
    file_size       BIGINT DEFAULT 0,                    -- 文件大小 (bytes)
    
    -- 分类
    category        VARCHAR(50) NOT NULL,                -- workspace/skill/memory/media/model/config/other
    
    -- 版本
    version_id      VARCHAR(200),                         -- 对象版本 ID
    etag            VARCHAR(200),                         -- ETag
    
    -- 归属
    workspace_id    UUID REFERENCES sys_workspaces(id) ON DELETE SET NULL,
    user_id         UUID REFERENCES sys_users(id) ON DELETE SET NULL,
    
    -- 搜索
    search_text     TEXT,                                 -- 全文搜索文本
    tags            TEXT[] DEFAULT '{}',                  -- 标签
    custom_metadata JSONB DEFAULT '{}',                  -- 扩展元数据
    
    -- 状态
    storage_class   VARCHAR(50) DEFAULT 'STANDARD',     -- STANDARD/INFREQUENT_ACCESS/ARCHIVE
    content_hash    VARCHAR(64),                          -- SHA-256
    is_latest       BOOLEAN DEFAULT TRUE,                -- 是否最新版本
    
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    deleted_at      TIMESTAMPTZ                           -- 软删除
);

-- 索引
CREATE UNIQUE INDEX ix_storage_objects_key ON storage_objects(object_key) WHERE deleted_at IS NULL;
CREATE INDEX ix_storage_objects_tenant ON storage_objects(tenant_id);
CREATE INDEX ix_storage_objects_workspace ON storage_objects(workspace_id);
CREATE INDEX ix_storage_objects_category ON storage_objects(category);
CREATE INDEX ix_storage_objects_tags ON storage_objects USING GIN(tags);
CREATE INDEX ix_storage_objects_created ON storage_objects(created_at);

-- 全文搜索索引 (中文 + 英文)
CREATE INDEX ix_storage_objects_search ON storage_objects USING GIN(
    to_tsvector('simple', COALESCE(search_text, ''))
);

COMMENT ON TABLE storage_objects IS '通用文件对象索引表 — 所有对象存储文件的统一索引';
```

**【验收测试标记 T-META-001】元数据表结构验证**

| 测试项 | 验证方法 | 通过标准 |
|--------|----------|----------|
| **T-META-001.1** storage_objects表 | 执行Alembic迁移，查询表结构 | 所有字段、索引、约束正确创建 |
| **T-META-001.2** ai_agent_configs表 | 上传agent.json，查询表 | 所有结构化字段正确抽取 |
| **T-META-001.3** ai_skill_configs表 | 上传skill.json，查询表 | 技能列表、版本、来源正确 |
| **T-META-001.4** ai_conversations表 | 上传chats.json，查询表 | 对话和消息逐条正确入库 |
| **T-META-001.5** ai_token_usage_stats表 | 上传token_usage.json，查询表 | 按日聚合数据准确 |
| **T-META-001.6** ai_memory_documents表 | 上传memory/*.md，查询表 | 标题/标签/摘要正确提取 |
| **T-META-001.7** ai_channel_messages表 | 发送飞书消息，查询表 | 消息500ms内入库，字段完整 |
| **T-META-001.8** 外键约束 | 删除workspace，检查级联 | 关联元数据正确级联删除 |
| **T-META-001.9** 唯一约束 | 重复插入相同agent_id | 抛出UniqueViolation异常 |

---

#### 5.1.2 Agent 配置元数据表

从 `agent.json` 中抽取结构化字段，支持按模型/通道/技能等维度查询：

```sql
-- Agent 配置元数据表
CREATE TABLE ai_agent_configs (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id       VARCHAR(36) NOT NULL DEFAULT 'default-tenant',
    
    -- 归属
    workspace_id    UUID REFERENCES sys_workspaces(id) ON DELETE CASCADE,
    user_id         UUID REFERENCES sys_users(id) ON DELETE SET NULL,
    agent_id        VARCHAR(100) NOT NULL,              -- Agent ID (对应 agent.json 中的 id)
    
    -- 基本信息
    name            VARCHAR(200) NOT NULL,               -- Agent 名称
    description     TEXT,                                 -- Agent 描述
    
    -- 模型配置 (从 agent.json.model 抽取)
    model_provider  VARCHAR(100),                         -- 模型提供商
    model_name      VARCHAR(200),                         -- 模型名称
    model_base_url  VARCHAR(500),                         -- API 基础URL
    temperature     REAL,                                 -- 温度参数
    max_tokens      INTEGER,                              -- 最大Token数
    
    -- 通道配置摘要 (仅记录启用状态)
    enabled_channels TEXT[],                               -- 已启用通道列表
    
    -- 记忆配置
    memory_backend  VARCHAR(50),                          -- 记忆后端
    memory_max_messages INTEGER,                          -- 最大消息数
    
    -- 技能列表
    skills          TEXT[],                               -- 已激活技能列表
    
    -- 心跳配置
    heartbeat_enabled BOOLEAN,                            -- 心跳是否启用
    heartbeat_every  VARCHAR(20),                         -- 心跳间隔
    
    -- 原始文件关联
    storage_key     VARCHAR(1024),                        -- agent.json 在对象存储中的键
    content_hash    VARCHAR(64),                          -- 文件内容哈希 (用于变更检测)
    
    -- 状态
    status          VARCHAR(20) NOT NULL DEFAULT 'active', -- active/inactive/archived
    last_synced_at  TIMESTAMPTZ,                          -- 最后同步时间
    
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX ix_ai_agent_configs_tenant ON ai_agent_configs(tenant_id);
CREATE INDEX ix_ai_agent_configs_workspace ON ai_agent_configs(workspace_id);
CREATE INDEX ix_ai_agent_configs_agent_id ON ai_agent_configs(agent_id);
CREATE INDEX ix_ai_agent_configs_provider ON ai_agent_configs(model_provider);
CREATE INDEX ix_ai_agent_configs_skills ON ai_agent_configs USING GIN(skills);

COMMENT ON TABLE ai_agent_configs IS 'Agent 配置元数据表 — 从 agent.json 抽取的结构化信息';
```

#### 5.1.3 Skill 配置元数据表

从 `skill.json` 中抽取结构化字段：

```sql
-- Skill 配置元数据表
CREATE TABLE ai_skill_configs (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id       VARCHAR(36) NOT NULL DEFAULT 'default-tenant',
    
    -- 归属
    workspace_id    UUID REFERENCES sys_workspaces(id) ON DELETE CASCADE,
    user_id         UUID REFERENCES sys_users(id) ON DELETE SET NULL,
    
    -- 基本信息
    skill_name      VARCHAR(200) NOT NULL,               -- 技能名称
    display_name    VARCHAR(200),                         -- 显示名称
    description     TEXT,                                 -- 技能描述
    version         VARCHAR(50) DEFAULT '1.0.0',         -- 技能版本
    
    -- 分类
    source          VARCHAR(50),                          -- 来源: builtin/user/plugin
    category        VARCHAR(50),                          -- 类别
    enabled         BOOLEAN DEFAULT TRUE,                  -- 是否启用
    
    -- 通道绑定
    channels        TEXT[] DEFAULT '{}',                   -- 绑定通道列表
    
    -- 原始文件关联
    storage_key     VARCHAR(1024),                        -- skill.json 在对象存储中的键
    skill_dir_key   VARCHAR(1024),                        -- 技能目录在对象存储中的键前缀
    content_hash    VARCHAR(64),
    
    last_synced_at  TIMESTAMPTZ,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX ix_ai_skill_configs_tenant ON ai_skill_configs(tenant_id);
CREATE INDEX ix_ai_skill_configs_workspace ON ai_skill_configs(workspace_id);
CREATE INDEX ix_ai_skill_configs_name ON ai_skill_configs(skill_name);
CREATE INDEX ix_ai_skill_configs_source ON ai_skill_configs(source);

COMMENT ON TABLE ai_skill_configs IS 'Skill 配置元数据表 — 从 skill.json 抽取的结构化信息';
```

#### 5.1.4 对话历史元数据表

从 `chats.json` 中抽取结构化字段，对话消息逐条入库：

```sql
-- 对话元数据表
CREATE TABLE ai_conversations (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id       VARCHAR(36) NOT NULL DEFAULT 'default-tenant',
    
    -- 归属
    workspace_id    UUID REFERENCES sys_workspaces(id) ON DELETE CASCADE,
    user_id         UUID REFERENCES sys_users(id) ON DELETE SET NULL,
    agent_id        VARCHAR(100),                          -- Agent ID
    
    -- 对话信息
    chat_id         VARCHAR(100) NOT NULL,                -- 原始对话 ID
    title           VARCHAR(500),                          -- 对话标题 (可选)
    message_count   INTEGER DEFAULT 0,                    -- 消息数量
    
    -- 时间范围
    started_at      TIMESTAMPTZ NOT NULL,                 -- 对话开始时间
    last_message_at TIMESTAMPTZ,                          -- 最后一条消息时间
    
    -- 原始文件关联
    storage_key     VARCHAR(1024),                        -- chats.json 在对象存储中的键
    content_hash    VARCHAR(64),
    
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- 对话消息表 (从 chats.json.messages 逐条抽取)
CREATE TABLE ai_conversation_messages (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id       VARCHAR(36) NOT NULL DEFAULT 'default-tenant',
    conversation_id UUID NOT NULL REFERENCES ai_conversations(id) ON DELETE CASCADE,
    
    role            VARCHAR(20) NOT NULL,                 -- user/assistant/system/tool
    content         TEXT NOT NULL,                         -- 消息内容
    timestamp       TIMESTAMPTZ NOT NULL,                 -- 消息时间戳
    
    -- 工具调用 (可选)
    tool_calls      JSONB,                                -- 工具调用信息
    tool_call_id    VARCHAR(100),                          -- 工具调用响应 ID
    
    -- 元数据
    token_count     INTEGER,                              -- 消息消耗的 Token 数
    metadata        JSONB DEFAULT '{}',
    
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX ix_ai_conversations_tenant ON ai_conversations(tenant_id);
CREATE INDEX ix_ai_conversations_workspace ON ai_conversations(workspace_id);
CREATE INDEX ix_ai_conversations_chat_id ON ai_conversations(chat_id);
CREATE INDEX ix_ai_conversations_agent ON ai_conversations(agent_id);
CREATE INDEX ix_ai_conversations_started ON ai_conversations(started_at);
CREATE INDEX ix_ai_conv_msgs_conversation ON ai_conversation_messages(conversation_id);
CREATE INDEX ix_ai_conv_msgs_role ON ai_conversation_messages(role);
CREATE INDEX ix_ai_conv_msgs_tenant ON ai_conversation_messages(tenant_id);

COMMENT ON TABLE ai_conversations IS '对话元数据表 — 从 chats.json 抽取';
COMMENT ON TABLE ai_conversation_messages IS '对话消息表 — 从 chats.json.messages 逐条抽取';
```

#### 5.1.5 Token 使用统计元数据表

从 `token_usage.json` 中抽取，支持按日/月聚合查询：

```sql
-- Token 使用统计表
CREATE TABLE ai_token_usage_stats (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id       VARCHAR(36) NOT NULL DEFAULT 'default-tenant',
    
    -- 归属
    workspace_id    UUID REFERENCES sys_workspaces(id) ON DELETE CASCADE,
    user_id         UUID REFERENCES sys_users(id) ON DELETE SET NULL,
    agent_id        VARCHAR(100),
    
    -- 时间维度
    stat_date       DATE NOT NULL,                        -- 统计日期
    
    -- 用量统计
    prompt_tokens       BIGINT DEFAULT 0,                 -- 提示 Token 数
    completion_tokens   BIGINT DEFAULT 0,                 -- 补全 Token 数
    total_tokens        BIGINT DEFAULT 0,                 -- 总 Token 数
    request_count       INTEGER DEFAULT 0,                -- 请求次数
    cost_usd            DECIMAL(10, 6) DEFAULT 0,          -- 费用 (USD)
    
    -- 模型维度 (可选分组)
    model_provider  VARCHAR(100),                          -- 模型提供商
    model_name      VARCHAR(200),                          -- 模型名称
    
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    
    UNIQUE(tenant_id, workspace_id, agent_id, stat_date, model_provider, model_name)
);

CREATE INDEX ix_ai_token_usage_tenant ON ai_token_usage_stats(tenant_id);
CREATE INDEX ix_ai_token_usage_date ON ai_token_usage_stats(stat_date);
CREATE INDEX ix_ai_token_usage_workspace ON ai_token_usage_stats(workspace_id);
CREATE INDEX ix_ai_token_usage_agent ON ai_token_usage_stats(agent_id);

COMMENT ON TABLE ai_token_usage_stats IS 'Token 使用统计表 — 从 token_usage.json 抽取，支持按日/月聚合';
```

#### 5.1.6 定时任务元数据表

从 `jobs.json` 中抽取，与 `ai_tasks` 表关联：

```sql
-- 定时任务元数据表 (扩展 ai_tasks 的调度字段)
-- 采用 ALTER TABLE 方式扩展现有 ai_tasks 表
ALTER TABLE ai_tasks ADD COLUMN IF NOT EXISTS
    schedule_expr VARCHAR(100);               -- Cron 表达式
ALTER TABLE ai_tasks ADD COLUMN IF NOT EXISTS
    next_run_at TIMESTAMPTZ;                  -- 下次执行时间
ALTER TABLE ai_tasks ADD COLUMN IF NOT EXISTS
    last_run_at TIMESTAMPTZ;                  -- 上次执行时间
ALTER TABLE ai_tasks ADD COLUMN IF NOT EXISTS
    run_count INTEGER DEFAULT 0;              -- 执行次数
ALTER TABLE ai_tasks ADD COLUMN IF NOT EXISTS
    max_retries INTEGER DEFAULT 3;            -- 最大重试次数
ALTER TABLE ai_tasks ADD COLUMN IF NOT EXISTS
    timeout_seconds INTEGER DEFAULT 300;      -- 超时时间
ALTER TABLE ai_tasks ADD COLUMN IF NOT EXISTS
    command VARCHAR(500);                     -- 执行命令 (从 jobs.json.command 迁移)
ALTER TABLE ai_tasks ADD COLUMN IF NOT EXISTS
    args JSONB DEFAULT '{}';                  -- 命令参数 (从 jobs.json.args 迁移)
ALTER TABLE ai_tasks ADD COLUMN IF NOT EXISTS
    source_storage_key VARCHAR(1024);         -- jobs.json 在对象存储中的键

-- 注意：调度字段的详细使用见第 7.6 节
```

#### 5.1.7 记忆文档元数据表

从 `memory/` 目录和 `MEMORY.md` 等文件中抽取：

```sql
-- 记忆文档元数据表
CREATE TABLE ai_memory_documents (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id       VARCHAR(36) NOT NULL DEFAULT 'default-tenant',
    
    -- 归属
    workspace_id    UUID REFERENCES sys_workspaces(id) ON DELETE CASCADE,
    user_id         UUID REFERENCES sys_users(id) ON DELETE SET NULL,
    agent_id        VARCHAR(100),
    
    -- 文档信息
    doc_type        VARCHAR(50) NOT NULL,                -- memory_daily/long_term/personality/soul/profile
    doc_date        DATE,                                -- 记忆日期 (仅 memory_daily)
    title           VARCHAR(500),                        -- 文档标题
    
    -- 内容摘要
    summary         TEXT,                                -- 内容摘要 (Markdown 前 500 字符)
    headings        TEXT[],                               -- 标题列表 (从 Markdown # 提取)
    tags            TEXT[] DEFAULT '{}',                  -- 标签
    
    -- 向量化 (可选，用于语义搜索)
    embedding       vector(1536),                         -- 文档向量嵌入
    
    -- 原始文件关联
    storage_key     VARCHAR(1024) NOT NULL,              -- 文件在对象存储中的键
    content_hash    VARCHAR(64),
    file_size       BIGINT DEFAULT 0,
    
    last_synced_at  TIMESTAMPTZ,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    deleted_at      TIMESTAMPTZ
);

CREATE INDEX ix_ai_memory_docs_tenant ON ai_memory_documents(tenant_id);
CREATE INDEX ix_ai_memory_docs_workspace ON ai_memory_documents(workspace_id);
CREATE INDEX ix_ai_memory_docs_type ON ai_memory_documents(doc_type);
CREATE INDEX ix_ai_memory_docs_date ON ai_memory_documents(doc_date);
CREATE INDEX ix_ai_memory_docs_tags ON ai_memory_documents USING GIN(tags);

COMMENT ON TABLE ai_memory_documents IS '记忆文档元数据表 — 从 memory/*.md 和人格文件抽取';
```

#### 5.1.8 通道消息元数据表

将飞书/钉钉/微信等通道消息入库，支持跨节点共享和审计：

```sql
-- 通道消息表
CREATE TABLE ai_channel_messages (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id       VARCHAR(36) NOT NULL DEFAULT 'default-tenant',
    
    -- 归属
    workspace_id    UUID REFERENCES sys_workspaces(id) ON DELETE CASCADE,
    user_id         UUID REFERENCES sys_users(id) ON DELETE SET NULL,
    agent_id        VARCHAR(100),
    
    -- 通道信息
    channel_type    VARCHAR(50) NOT NULL,                -- feishu/dingtalk/weixin/telegram/discord/mattermost/qq/onebot/mqtt/imessage/console
    channel_id      VARCHAR(200),                         -- 通道会话 ID
    
    -- 消息内容
    message_id      VARCHAR(200),                         -- 原始消息 ID
    direction       VARCHAR(20) NOT NULL,                 -- inbound/outbound
    content_type    VARCHAR(50) DEFAULT 'text',           -- text/markdown/image/file/card
    content         TEXT,                                 -- 消息正文
    
    -- 发送者信息
    sender_id       VARCHAR(200),                         -- 发送者 ID
    sender_name     VARCHAR(200),                         -- 发送者名称
    is_bot          BOOLEAN DEFAULT FALSE,                -- 是否 Bot 消息
    
    -- 关联
    reply_to_id     UUID REFERENCES ai_channel_messages(id), -- 回复的消息
    conversation_id UUID REFERENCES ai_conversations(id),    -- 关联的对话
    task_id         UUID REFERENCES ai_tasks(id),            -- 关联的任务
    
    -- 媒体附件
    media_keys      TEXT[] DEFAULT '{}',                  -- 媒体文件在对象存储中的键
    
    -- 处理状态
    processing_status VARCHAR(20) DEFAULT 'pending',      -- pending/processed/failed
    processed_at    TIMESTAMPTZ,
    
    -- DLP 检查
    dlp_checked     BOOLEAN DEFAULT FALSE,
    dlp_violations  JSONB DEFAULT '[]',
    
    timestamp       TIMESTAMPTZ NOT NULL,                 -- 消息原始时间戳
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX ix_ai_channel_msgs_tenant ON ai_channel_messages(tenant_id);
CREATE INDEX ix_ai_channel_msgs_channel ON ai_channel_messages(channel_type);
CREATE INDEX ix_ai_channel_msgs_workspace ON ai_channel_messages(workspace_id);
CREATE INDEX ix_ai_channel_msgs_timestamp ON ai_channel_messages(timestamp);
CREATE INDEX ix_ai_channel_msgs_sender ON ai_channel_messages(sender_id);
CREATE INDEX ix_ai_channel_msgs_direction ON ai_channel_messages(direction);
CREATE INDEX ix_ai_channel_msgs_processing ON ai_channel_messages(processing_status);

COMMENT ON TABLE ai_channel_messages IS '通道消息表 — 飞书/钉钉等通道消息入库，支持跨节点共享和审计';
```

### 5.2 元数据抽取规则

元数据抽取分为两层：**通用文件索引**（`storage_objects`）和**业务结构化抽取**（各类专用表）。

#### 5.2.1 通用文件索引抽取

所有上传到对象存储的文件自动在 `storage_objects` 表中创建索引记录。

#### 5.2.2 业务结构化抽取映射

| 源文件 | 目标 PG 表 | 抽取逻辑 | 触发时机 |
|--------|-----------|----------|----------|
| `agent.json` | `ai_agent_configs` | 解析 JSON，提取 name/model/channels/skills/heartbeat 等字段 | 文件上传/变更 |
| `skill.json` | `ai_skill_configs` | 解析 JSON，提取 skills 列表中每个技能的 name/version/enabled/source | 文件上传/变更 |
| `chats.json` | `ai_conversations` + `ai_conversation_messages` | 解析 JSON，逐条对话和消息入库 | 文件上传/变更 |
| `token_usage.json` | `ai_token_usage_stats` | 解析 JSON，按日期分桶插入统计记录 | 每日定时同步 |
| `jobs.json` | `ai_tasks` (扩展字段) | 解析 JSON，每条 job 创建/更新 ai_tasks 记录 | 文件上传/变更 |
| `memory/*.md` | `ai_memory_documents` | 解析 Markdown，提取标题/标签/摘要 | 文件上传/变更 |
| `MEMORY.md` 等 | `ai_memory_documents` | 同上 | 文件上传/变更 |
| 通道消息 | `ai_channel_messages` | 实时接收通道消息后直接入库 | 消息收发时 |

#### 5.2.3 元数据抽取器实现

```python
# src/copaw/storage/metadata_extractor.py

class MetadataExtractor:
    """元数据抽取器 — 双轨存储核心组件
    
    负责：
    1. 通用文件索引: 所有文件 → storage_objects
    2. 业务结构化抽取: 特定文件 → 专用元数据表
    """

    # 按文件扩展名和路径模式的分类规则
    CATEGORY_RULES = {
        # Agent 配置
        "agent.json": "workspace",
        "chats.json": "workspace",
        "jobs.json": "workspace",
        "token_usage.json": "workspace",
        "skill.json": "workspace",
        
        # 人格文件
        "MEMORY.md": "memory",
        "AGENTS.md": "workspace",
        "SOUL.md": "workspace",
        "PROFILE.md": "workspace",
        "HEARTBEAT.md": "workspace",
        "BOOTSTRAP.md": "workspace",
        
        # 技能文件
        "SKILL.md": "skill",
        "skills/": "skill",
        
        # 媒体文件
        ".png": "media",
        ".jpg": "media",
        ".jpeg": "media",
        ".gif": "media",
        ".mp4": "media",
        ".mp3": "media",
        ".wav": "media",
        
        # 模型文件
        ".gguf": "model",
        ".bin": "model",
        
        # 配置文件
        "config.json": "config",
    }

    @classmethod
    def extract_category(cls, key: str) -> str:
        """从对象键推断文件类别"""
        path = PurePosixPath(key)
        name = path.name
        suffix = path.suffix.lower()

        # 精确匹配文件名
        if name in cls.CATEGORY_RULES:
            return cls.CATEGORY_RULES[name]

        # 匹配扩展名
        if suffix in cls.CATEGORY_RULES:
            return cls.CATEGORY_RULES[suffix]

        # 路径模式匹配
        parts = path.parts
        if "skills" in parts:
            return "skill"
        if "memory" in parts:
            return "memory"
        if "media" in parts:
            return "media"
        if "models" in parts or "model" in parts:
            return "model"
        if "workspaces" in parts:
            return "workspace"

        return "other"

    @classmethod
    def extract_search_text(cls, key: str, content: bytes) -> str:
        """从文件内容中提取可搜索的文本

        - JSON: 提取所有字符串值
        - Markdown: 提取标题和正文
        - 二进制: 仅返回文件名
        """
        path = PurePosixPath(key)
        suffix = path.suffix.lower()

        if suffix == ".json":
            try:
                import json
                data = json.loads(content)
                return cls._flatten_json_values(data)
            except Exception:
                return ""
        elif suffix in (".md", ".txt", ".csv"):
            try:
                return content.decode("utf-8")[:10000]  # 截断
            except Exception:
                return ""
        else:
            return path.stem  # 二进制文件仅索引文件名

    @staticmethod
    def _flatten_json_values(data, depth=0, max_depth=3) -> str:
        """递归提取 JSON 中所有字符串值"""
        if depth > max_depth:
            return ""
        parts = []
        if isinstance(data, dict):
            for k, v in data.items():
                if isinstance(v, str) and len(v) < 500:
                    parts.append(v)
                elif isinstance(v, (dict, list)):
                    parts.append(MetadataExtractor._flatten_json_values(v, depth + 1))
        elif isinstance(data, list):
            for item in data:
                if isinstance(item, str) and len(item) < 500:
                    parts.append(item)
                elif isinstance(item, (dict, list)):
                    parts.append(MetadataExtractor._flatten_json_values(item, depth + 1))
        return " ".join(parts)
```

**【验收测试标记 T-META-002】元数据抽取器验证**

| 测试项 | 验证方法 | 通过标准 |
|--------|----------|----------|
| **T-META-002.1** 通用索引抽取 | 上传任意文件，检查storage_objects | 3秒内创建记录，category正确 |
| **T-META-002.2** Agent配置抽取 | 上传agent.json，检查ai_agent_configs | name/model/channels/skills等字段准确 |
| **T-META-002.3** Skill配置抽取 | 上传skill.json，检查ai_skill_configs | 技能名称/版本/source正确 |
| **T-META-002.4** 对话抽取 | 上传chats.json (100条消息) | ai_conversations + messages 100条正确 |
| **T-META-002.5** Token统计抽取 | 上传token_usage.json | 按日分桶统计准确 |
| **T-META-002.6** 记忆文档抽取 | 上传memory/*.md，检查ai_memory_documents | 标题/标签/摘要正确提取 |
| **T-META-002.7** content_hash检测 | 修改文件重新上传 | content_hash变更，触发元数据更新 |
| **T-META-002.8** JSON解析容错 | 上传格式错误的JSON | 跳过抽取，记录错误日志，不崩溃 |
| **T-META-002.9** Markdown解析 | 上传复杂Markdown (多级标题) | headings/tags正确提取 |

**【验收测试标记 T-META-003】索引策略验证**

| 测试项 | 验证方法 | 通过标准 |
|--------|----------|----------|
| **T-META-003.1** 写入索引 | 上传文件后立即查询 | 5秒内可在storage_objects查到 |
| **T-META-003.2** 批量索引 | 迁移1000个现有文件 | 10分钟内完成，无遗漏 |
| **T-META-003.3** 增量索引 | 每小时定时任务执行 | 补全遗漏记录，无重复 |
| **T-META-003.4** 搜索更新 | 修改文件内容 | search_text字段更新 |
| **T-META-003.5** 软删除 | 删除文件 | deleted_at设置，搜索不返回 |

**【验收测试标记 T-META-004】搜索服务验证**

| 测试项 | 验证方法 | 通过标准 |
|--------|----------|----------|
| **T-META-004.1** 全文搜索 | 搜索"agent配置" | 返回相关agent.json文件 |
| **T-META-004.2** 标签过滤 | 搜索tags=['config'] | 仅返回带config标签的文件 |
| **T-META-004.3** 组合搜索 | 搜索"agent" + category=workspace | 结果准确，响应<200ms (5万文件) |
| **T-META-004.4** 分页 | 搜索返回100条，page_size=20 | 分页正确，total准确 |
| **T-META-004.5** 性能测试 | 5万文件全文搜索 | P95<200ms，P99<500ms |
| **T-META-004.6** 空结果 | 搜索不存在的关键词 | 返回空列表，total=0 |

**【验收测试标记 T-META-005】数据一致性验证**

| 测试项 | 验证方法 | 通过标准 |
|--------|----------|----------|
| **T-META-005.1** 双写一致性 | 上传文件后对比对象存储和PG | storage_key存在，content_hash一致 |
| **T-META-005.2** 元数据同步失败恢复 | 模拟PG写入失败 | 定时任务补全，最终一致 |
| **T-META-005.3** 并发写入 | 10并发上传不同文件 | 无数据丢失，无重复记录 |
| **T-META-005.4** 大文件元数据 | 上传500MB文件 | 元数据正确，file_size准确 |
| **T-META-005.5** 变更检测 | 修改agent.json重新上传 | content_hash变更，元数据更新 |

---

### 5.3 索引策略

| 策略 | 触发时机 | 说明 |
|------|----------|------|
| **写入索引** | `storage.put()` 后同步 | 文件上传后立即抽取元数据写入 PostgreSQL |
| **批量索引** | 迁移工具执行时 | 扫描对象存储中所有文件，批量生成元数据 |
| **增量索引** | 定时任务 (每小时) | 检查对象存储与元数据表的差异，补全遗漏 |
| **搜索更新** | 文件内容变更时 | 更新 `search_text` 全文搜索字段 |
| **软删除** | `storage.delete()` 后 | 设置 `deleted_at` 而非物理删除 |

### 5.4 搜索服务API

```python
# src/copaw/storage/search_service.py

from dataclasses import dataclass
from typing import Optional


@dataclass
class StorageSearchRequest:
    """存储搜索请求"""
    query: str                               # 搜索关键词
    tenant_id: str                           # 租户ID (必须)
    category: Optional[str] = None           # 文件类别过滤
    owner_id: Optional[str] = None           # 所有者过滤
    workspace_id: Optional[str] = None       # 工作空间过滤
    tags: Optional[list[str]] = None         # 标签过滤
    content_type: Optional[str] = None       # MIME 类型过滤
    min_size: Optional[int] = None           # 最小文件大小
    max_size: Optional[int] = None           # 最大文件大小
    date_from: Optional[str] = None          # 起始日期
    date_to: Optional[str] = None            # 截止日期
    page: int = 1                            # 页码
    page_size: int = 20                      # 每页数量
    sort_by: str = "updated_at"              # 排序字段
    sort_order: str = "desc"                 # 排序方向


@dataclass
class StorageSearchResult:
    """存储搜索结果"""
    total: int
    page: int
    page_size: int
    items: list[dict]                         # ObjectMetadata 列表


class StorageSearchService:
    """存储搜索服务"""

    async def search(self, request: StorageSearchRequest) -> StorageSearchResult:
        """全文搜索 + 过滤"""
        # 构建 SQL 查询
        # 1. 租户隔离: WHERE tenant_id = :tenant_id
        # 2. 全文搜索: AND to_tsvector('simple', search_text) @@ plainto_tsquery(:query)
        # 3. 类别过滤: AND category = :category
        # 4. 标签过滤: AND tags @> :tags
        # 5. 范围过滤: AND file_size BETWEEN :min_size AND :max_size
        # 6. 时间过滤: AND updated_at BETWEEN :date_from AND :date_to
        # 7. 排序 + 分页
        ...

    async def search_by_content(
        self,
        tenant_id: str,
        text_query: str,
        limit: int = 10,
    ) -> list[dict]:
        """基于内容的语义搜索（使用 pg_trgm 或向量索引）"""
        ...
```

---

## 6. SQLite 到 PostgreSQL 迁移策略

### 6.1 迁移评估矩阵

**企业版原则**：全面消除 SQLite，所有结构化数据统一迁移至 PostgreSQL + pgvector。个人版保留 SQLite 不受影响。

| 数据类别 | 企业版迁移 | 理由 | 迁移后存储方式 |
|----------|----------|------|---------------|
| **记忆条目** (memories) | ✅ 迁移 | 需跨实例共享、多用户访问 | PostgreSQL + pgvector |
| **记忆标签** (memory_tags) | ✅ 迁移 | 关系型数据，适合 SQL | PostgreSQL 关联表 |
| **会话上下文** (sessions) | ✅ 迁移 | 企业版集中管理，支持审计 | PostgreSQL + Redis 缓存 |
| **会话-记忆关联** (session_memories) | ✅ 迁移 | 企业版全量迁移 | PostgreSQL 关联表 |
| **向量嵌入缓存** (embedding cache) | ✅ 迁移 | 高频访问，需共享 | PostgreSQL + pgvector |
| 记忆压缩配置 | ✅ 迁移 | 全局配置 | PostgreSQL JSONB |

**【验收测试标记 T-MIGRATE-001】迁移评估验证**

| 测试项 | 验证方法 | 通过标准 |
|--------|----------|----------|
| **T-MIGRATE-001.1** 企业版无SQLite依赖 | 启动企业版，检查SQLite连接 | 无SQLite连接，全部使用PG |
| **T-MIGRATE-001.2** 个人版SQLite保留 | 启动个人版，检查SQLite连接 | 正常连接本地SQLite |
| **T-MIGRATE-001.3** 通道消息入PG | 发送飞书消息，查询ai_channel_messages | 消息入库，字段完整 |
| **T-MIGRATE-001.4** 对话历史入PG | 查询ai_conversations | 所有对话和消息正确入库 |

### 6.2 ReMe 记忆数据库迁移

#### 6.2.1 目标 PostgreSQL 表结构

```sql
-- 启用 pgvector 扩展
CREATE EXTENSION IF NOT EXISTS vector;

-- 记忆条目表 (企业版)
CREATE TABLE ai_memories (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id       VARCHAR(36) NOT NULL DEFAULT 'default-tenant',
    
    -- 归属
    workspace_id    UUID REFERENCES sys_workspaces(id) ON DELETE CASCADE,
    user_id         UUID REFERENCES sys_users(id) ON DELETE SET NULL,
    agent_id        VARCHAR(100),                      -- Agent ID
    
    -- 内容
    content         TEXT NOT NULL,                      -- 记忆原文
    content_hash    VARCHAR(64),                        -- SHA-256 内容哈希
    embedding       vector(1536),                       -- 向量嵌入 (维度可配)
    embedding_model VARCHAR(100),                       -- 嵌入模型名称
    
    -- 分类
    category        VARCHAR(50),                        -- 记忆分类
    importance      REAL DEFAULT 0.5,                   -- 重要性评分 [0,1]
    
    -- 元数据
    metadata        JSONB DEFAULT '{}',
    tags            TEXT[] DEFAULT '{}',
    
    -- 统计
    access_count    INTEGER DEFAULT 0,
    last_accessed_at TIMESTAMPTZ,
    
    -- 时间
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    archived_at     TIMESTAMPTZ                        -- 归档时间
);

-- 向量索引 (IVFFlat，适合中等规模)
CREATE INDEX ix_ai_memories_embedding ON ai_memories 
    USING ivfflat (embedding vector_cosine_ops) WITH (lists = 100);

-- 其他索引
CREATE INDEX ix_ai_memories_tenant ON ai_memories(tenant_id);
CREATE INDEX ix_ai_memories_workspace ON ai_memories(workspace_id);
CREATE INDEX ix_ai_memories_user ON ai_memories(user_id);
CREATE INDEX ix_ai_memories_category ON ai_memories(category);
CREATE INDEX ix_ai_memories_importance ON ai_memories(importance);
CREATE INDEX ix_ai_memories_created ON ai_memories(created_at);
CREATE INDEX ix_ai_memories_tags ON ai_memories USING GIN(tags);
CREATE INDEX ix_ai_memories_content_hash ON ai_memories(content_hash);

COMMENT ON TABLE ai_memories IS 'AI 记忆条目表 — 企业版向量记忆存储';
```

```sql
-- 记忆标签表 (企业版)
CREATE TABLE ai_memory_tags (
    memory_id   UUID REFERENCES ai_memories(id) ON DELETE CASCADE,
    tag         VARCHAR(100) NOT NULL,
    tenant_id   VARCHAR(36) NOT NULL DEFAULT 'default-tenant',
    PRIMARY KEY (memory_id, tag)
);

CREATE INDEX ix_ai_memory_tags_tag ON ai_memory_tags(tag);

COMMENT ON TABLE ai_memory_tags IS '记忆标签关联表';
```

```sql
-- 会话上下文表 (企业版)
CREATE TABLE ai_memory_sessions (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id       VARCHAR(36) NOT NULL DEFAULT 'default-tenant',
    workspace_id    UUID REFERENCES sys_workspaces(id) ON DELETE CASCADE,
    user_id         UUID REFERENCES sys_users(id) ON DELETE SET NULL,
    
    started_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    ended_at        TIMESTAMPTZ,
    summary         TEXT,                              -- 会话摘要
    message_count   INTEGER DEFAULT 0,
    
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

COMMENT ON TABLE ai_memory_sessions IS '记忆会话上下文表';
```

```sql
-- 会话-记忆关联表 (企业版)
CREATE TABLE ai_memory_session_links (
    session_id  UUID REFERENCES ai_memory_sessions(id) ON DELETE CASCADE,
    memory_id   UUID REFERENCES ai_memories(id) ON DELETE CASCADE,
    relevance   REAL DEFAULT 1.0,                      -- 关联相关性
    PRIMARY KEY (session_id, memory_id)
);

COMMENT ON TABLE ai_memory_session_links IS '会话-记忆关联表';
```

**【验收测试标记 T-MIGRATE-002】ReMe迁移验证**

| 测试项 | 验证方法 | 通过标准 |
|--------|----------|----------|
| **T-MIGRATE-002.1** pgvector扩展 | 执行`CREATE EXTENSION vector` | 扩展成功，vector类型可用 |
| **T-MIGRATE-002.2** ai_memories表结构 | 查询表结构 | 所有字段、索引、向量列正确 |
| **T-MIGRATE-002.3** 向量索引创建 | 执行`CREATE INDEX ... ivfflat` | 索引创建成功 | |
| **T-MIGRATE-002.4** 记忆存储 | 调用store_memory() | 成功插入，返回UUID |
| **T-MIGRATE-002.5** 向量搜索 | 调用search_similar() | 返回top_k结果，similarity>threshold |
| **T-MIGRATE-002.6** 记忆压缩 | 调用compact_memories() | 正确归档低重要性记忆 |
| **T-MIGRATE-002.7** 多租户隔离 | 租户A搜索，检查返回结果 | 仅返回租户A的记忆 |

**【验收测试标记 T-MIGRATE-003】向量搜索验证**

| 测试项 | 验证方法 | 通过标准 |
|--------|----------|----------|
| **T-MIGRATE-003.1** 召回率 | 对比SQLite和PG搜索结果 | 召回率≥95% |
| **T-MIGRATE-003.2** 搜索延迟 | 10万条记忆向量搜索 | P95<50ms，P99<100ms |
| **T-MIGRATE-003.3** IVFFlat调优 | 调整lists参数 (50/100/200) | 最佳性能参数确定 |
| **T-MIGRATE-003.4** HNSW索引 | 100万条记忆测试HNSW | 延迟<30ms，内存占用可接受 |
| **T-MIGRATE-003.5** 维度兼容性 | 测试1536/768/384维度 | 自动检测，正确存储 |

**【验收测试标记 T-MIGRATE-004】迁移脚本验证**

| 测试项 | 验证方法 | 通过标准 |
|--------|----------|----------|
| **T-MIGRATE-004.1** BLOB反序列化 | 迁移SQLite embedding BLOB | numpy.frombuffer正确解析 |
| **T-MIGRATE-004.2** 数据完整性 | 迁移1000条记忆，对比源和目标 | 100%一致，无丢失 |
| **T-MIGRATE-004.3** 幂等性 | 重复执行迁移脚本 | 第二次无重复插入 |
| **T-MIGRATE-004.4** 增量迁移 | 迁移期间新数据写入PG | 新数据不丢失 |
| **T-MIGRATE-004.5** 回滚测试 | 迁移后回退到SQLite | SQLite数据完整，可继续使用 |

#### 6.2.2 向量搜索兼容层

为保持与 ReMe 接口的兼容，提供 `ReMePostgresBackend`:

```python
# src/copaw/agents/memory/reme_postgres_backend.py

from typing import List, Optional
import numpy as np
from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession


class ReMePostgresBackend:
    """ReMe 向后兼容的 PostgreSQL 向量存储后端

    替代 ReMe 的 SQLite 后端，提供相同的语义搜索能力，
    但使用 PostgreSQL + pgvector 实现，支持多实例共享。
    """

    def __init__(self, session: AsyncSession, workspace_id: str, 
                 tenant_id: str, embedding_dim: int = 1536):
        self._session = session
        self._workspace_id = workspace_id
        self._tenant_id = tenant_id
        self._embedding_dim = embedding_dim

    async def store_memory(
        self,
        content: str,
        embedding: np.ndarray,
        metadata: dict | None = None,
        category: str | None = None,
        importance: float = 0.5,
    ) -> str:
        """存储记忆条目，返回 UUID"""
        import hashlib
        content_hash = hashlib.sha256(content.encode()).hexdigest()

        result = await self._session.execute(
            text("""
                INSERT INTO ai_memories (
                    tenant_id, workspace_id, content, content_hash,
                    embedding, embedding_model, category, importance, metadata
                ) VALUES (
                    :tenant_id, :workspace_id, :content, :content_hash,
                    :embedding::vector, :embedding_model, :category, :importance, :metadata
                ) RETURNING id
            """),
            {
                "tenant_id": self._tenant_id,
                "workspace_id": self._workspace_id,
                "content": content,
                "content_hash": content_hash,
                "embedding": embedding.tolist().__str__(),
                "embedding_model": metadata.get("model", "unknown") if metadata else "unknown",
                "category": category,
                "importance": importance,
                "metadata": metadata or {},
            },
        )
        return str(result.scalar())

    async def search_similar(
        self,
        query_embedding: np.ndarray,
        top_k: int = 10,
        threshold: float = 0.7,
        category: str | None = None,
    ) -> List[dict]:
        """向量相似搜索"""
        params = {
            "tenant_id": self._tenant_id,
            "workspace_id": self._workspace_id,
            "query_embedding": query_embedding.tolist().__str__(),
            "top_k": top_k,
            "threshold": threshold,
        }

        category_filter = ""
        if category:
            category_filter = "AND category = :category"
            params["category"] = category

        result = await self._session.execute(
            text(f"""
                SELECT id, content, category, importance, metadata,
                       1 - (embedding <=> :query_embedding::vector) AS similarity
                FROM ai_memories
                WHERE tenant_id = :tenant_id
                  AND workspace_id = :workspace_id
                  {category_filter}
                  AND 1 - (embedding <=> :query_embedding::vector) > :threshold
                ORDER BY embedding <=> :query_embedding::vector
                LIMIT :top_k
            """),
            params,
        )
        return [
            {
                "id": str(row.id),
                "content": row.content,
                "category": row.category,
                "importance": row.importance,
                "metadata": row.metadata,
                "similarity": float(row.similarity),
            }
            for row in result.fetchall()
        ]

    async def compact_memories(
        self,
        before_date: str,
        keep_importance: float = 0.7,
    ) -> int:
        """压缩旧记忆（归档低重要性条目）"""
        result = await self._session.execute(
            text("""
                UPDATE ai_memories
                SET archived_at = NOW()
                WHERE tenant_id = :tenant_id
                  AND workspace_id = :workspace_id
                  AND created_at < :before_date
                  AND importance < :keep_importance
                  AND archived_at IS NULL
            """),
            {
                "tenant_id": self._tenant_id,
                "workspace_id": self._workspace_id,
                "before_date": before_date,
                "keep_importance": keep_importance,
            },
        )
        return result.rowcount
```

### 6.3 向量嵌入迁移方案

```
迁移流程:

SQLite (.reme/)                         PostgreSQL (pgvector)
┌──────────────────┐                    ┌──────────────────────┐
│ memories         │  ──迁移脚本──►     │ ai_memories           │
│  id (TEXT)       │                    │  id (UUID)            │
│  content         │  ──直接映射──►     │  content              │
│  embedding (BLOB)│  ──反序列化──►     │  embedding (vector)   │
│  embedding_model │  ──直接映射──►     │  embedding_model      │
│  metadata (JSON) │  ──JSONB化──►      │  metadata (JSONB)     │
│  category        │  ──直接映射──►     │  category             │
│  importance      │  ──直接映射──►     │  importance           │
│  access_count    │  ──直接映射──►     │  access_count         │
│  created_at      │  ──格式转换──►     │  created_at           │
└──────────────────┘                    └──────────────────────┘
```

**关键迁移步骤**:

1. **BLOB 反序列化**: SQLite 中 `embedding` 存储为 numpy 序列化 BLOB，需用 `numpy.frombuffer()` 反序列化
2. **维度检测**: 自动检测向量维度（1536/768/384），写入配置
3. **索引构建**: 迁移完成后在 PostgreSQL 中构建 IVFFlat 向量索引
4. **增量同步**: 迁移期间新数据写入 PostgreSQL，迁移完成后切换读写至 PostgreSQL

```python
# scripts/migrate_sqlite_to_postgres.py (核心逻辑)

import numpy as np
import sqlite3
import asyncio
from pathlib import Path


async def migrate_reme_to_postgres(
    workspace_dir: Path,
    tenant_id: str,
    workspace_id: str,
    pg_session_factory,
):
    """将单个工作空间的 ReMe SQLite 迁移到 PostgreSQL"""

    # 1. 定位 SQLite 文件
    reme_dir = workspace_dir / ".reme"
    db_files = list(reme_dir.glob("*.db")) + list(reme_dir.glob("*.sqlite"))
    if not db_files:
        print(f"  跳过 {workspace_dir.name}: 无 ReMe 数据库")
        return 0

    # 2. 连接 SQLite
    sqlite_conn = sqlite3.connect(str(db_files[0]))
    sqlite_conn.row_factory = sqlite3.Row

    # 3. 读取记忆条目
    rows = sqlite_conn.execute(
        "SELECT id, content, embedding, embedding_model, "
        "metadata, category, importance, access_count, "
        "created_at, last_accessed_at FROM memories"
    ).fetchall()

    # 4. 写入 PostgreSQL
    async with pg_session_factory() as pg_session:
        for row in rows:
            # 反序列化向量
            embedding = None
            if row["embedding"]:
                arr = np.frombuffer(row["embedding"], dtype=np.float32)
                embedding = arr.tolist()

            content_hash = hashlib.sha256(
                row["content"].encode()
            ).hexdigest()

            await pg_session.execute(
                text("""
                    INSERT INTO ai_memories (
                        tenant_id, workspace_id, content, content_hash,
                        embedding, embedding_model, category, importance,
                        metadata, access_count, last_accessed_at, created_at
                    ) VALUES (
                        :tenant_id, :workspace_id, :content, :content_hash,
                        :embedding::vector, :embedding_model, :category,
                        :importance, :metadata, :access_count,
                        :last_accessed_at, :created_at
                    ) ON CONFLICT DO NOTHING
                """),
                {
                    "tenant_id": tenant_id,
                    "workspace_id": workspace_id,
                    "content": row["content"],
                    "content_hash": content_hash,
                    "embedding": str(embedding) if embedding else None,
                    "embedding_model": row["embedding_model"] or "unknown",
                    "category": row["category"],
                    "importance": row["importance"] or 0.5,
                    "metadata": row["metadata"] or "{}",
                    "access_count": row["access_count"] or 0,
                    "last_accessed_at": row["last_accessed_at"],
                    "created_at": row["created_at"],
                },
            )

        await pg_session.commit()

    sqlite_conn.close()
    return len(rows)
```

### 6.4 企业版全量迁移策略

**企业版消除 SQLite**，所有数据统一由 PostgreSQL + pgvector 管理。不存在保留 SQLite 的场景。

| 场景 | 企业版策略 | 说明 |
|------|-----------|------|
| 向量记忆 (≤100万条) | pgvector | 中小企业数据量下 pgvector 性能充裕 |
| 向量记忆 (>100万条) | pgvector + HNSW | 使用 HNSW 索引替代 IVFFlat，支持更大规模 |
| 实时嵌入计算缓存 | Redis + PostgreSQL | Redis 做热缓存，PG 做持久化 |
| 通道消息 | PostgreSQL | `ai_channel_messages` 表统一管理 |
| 对话历史 | PostgreSQL | `ai_conversations` + `ai_conversation_messages` |

> **注意**：若未来数据规模超出 PostgreSQL 单机处理能力（单租户向量 >500万条），可引入专用向量数据库 (Milvus/Qdrant)，但当前中小企业场景下 pgvector 完全满足需求。

### 6.5 企业版/个人版后端选择

企业版和个人版使用不同的存储后端，通过配置切换，无需混合模式：

```python
# src/copaw/agents/memory/memory_backend_factory.py

from copaw.constant import EnvVarLoader


def create_memory_backend(workspace_dir: str, agent_id: str):
    """根据运行版本创建记忆后端
    
    企业版: PostgreSQL + pgvector (默认)
    个人版: SQLite / Chroma / 本地文件 (默认)
    """
    enterprise_enabled = EnvVarLoader.get_bool("COPAW_ENTERPRISE_ENABLED", False)
    memory_backend = EnvVarLoader.get_str("COPAW_MEMORY_BACKEND", "auto")

    if memory_backend == "auto":
        # 企业版默认 PostgreSQL，个人版默认本地
        memory_backend = "postgres" if enterprise_enabled else "sqlite"

    if memory_backend == "postgres":
        # 企业版专用: PostgreSQL + pgvector
        from .reme_postgres_backend import ReMePostgresBackend
        from ...db.postgresql import get_database_manager
        manager = get_database_manager()
        return ReMePostgresBackend(
            session_factory=manager.session,
            workspace_id=workspace_dir,
            tenant_id=agent_id,
        )
    elif memory_backend in ("sqlite", "chroma", "local"):
        # 个人版: 保持原有 ReMe 行为
        from .reme_light_memory_manager import ReMeLightMemoryManager
        return ReMeLightMemoryManager(
            working_dir=workspace_dir,
            agent_id=agent_id,
        )
    else:
        raise ValueError(f"Unsupported memory backend: {memory_backend}")
```

**版本差异对比**：

| 维度 | 企业版 | 个人版 |
|------|--------|--------|
| 记忆存储 | PostgreSQL + pgvector | SQLite / Chroma |
| 向量搜索 | pgvector IVFFlat/HNSW | SQLite 内置 / Chroma |
| 通道消息 | `ai_channel_messages` (PG) | 本地日志 |
| 对话历史 | `ai_conversations` (PG) | `chats.json` (本地) |
| 元数据 | PostgreSQL 结构化抽取 | 本地 JSON 文件 |
| 文件存储 | MinIO/S3 对象存储 | 本地文件系统 |
| 配置管理 | PG `ai_agent_configs` | 本地 `agent.json` |

**【验收测试标记 T-MIGRATE-005】企业版/个人版后端选择验证**

| 测试项 | 验证方法 | 通过标准 |
|--------|----------|----------|
| **T-MIGRATE-005.1** 企业版默认PG | `COPAW_ENTERPRISE_ENABLED=true` | 自动使用ReMePostgresBackend |
| **T-MIGRATE-005.2** 个人版默认SQLite | `COPAW_ENTERPRISE_ENABLED=false` | 自动使用ReMeLightMemoryManager |
| **T-MIGRATE-005.3** 手动切换后端 | 设置`COPAW_MEMORY_BACKEND=postgres` | 成功切换到指定后端 |
| **T-MIGRATE-005.4** 无效后端处理 | 设置`COPAW_MEMORY_BACKEND=invalid` | 抛出ValueError，提示有效值 |

---

## 7. 本地功能服务端迁移

### 7.1 可迁移功能清单

| 功能 | 当前位置 | 迁移优先级 | 迁移复杂度 | 迁移后收益 |
|------|----------|-----------|-----------|------------|
| 定时任务调度 | `jobs.json` + 本地 cron | P0-高 | 低 | 集中调度、避免冲突、审计 |
| 记忆检索服务 | ReMe SQLite | P0-高 | 中 | 共享向量索引、多用户并发 |
| 通道消息入库 | 各通道实现 | P1-高 | 中 | 跨节点共享、审计追踪、DLP 合规 |
| 记忆压缩服务 | `ReMeLightMemoryManager` | P1-高 | 中 | 集中资源、避免重复计算 |
| 心跳监控 | `HEARTBEAT.md` 配置 | P1-高 | 低 | 集中监控、告警联动 |
| 文件处理服务 | docx/xlsx/pptx 技能 | P2-中 | 中 | 集中计算、隔离安全 |
| 本地模型推理 | `LocalModelManager` | P2-中 | 高 | GPU 资源共享 |
| 模型下载管理 | `DownloadManager` | P3-低 | 低 | CDN 分发 |

**【验收测试标记 T-SERVER-001】功能迁移验证**

| 测试项 | 验证方法 | 通过标准 |
|--------|----------|----------|
| **T-SERVER-001.1** 定时任务集中调度 | 创建10个定时任务 | 不遗漏不重复，审计日志完整 |
| **T-SERVER-001.2** 记忆检索共享 | 多用户并发搜索记忆 | 无冲突，结果准确 |
| **T-SERVER-001.3** 通道消息入库 | 发送飞书/钉钉消息 | 500ms内入库，DLP检查完成 |
| **T-SERVER-001.4** 记忆压缩后台服务 | 触发压缩任务 | 不影响在线服务，CPU<80% |
| **T-SERVER-001.5** 心跳监控 | 监控10个Agent | 心跳正常，异常告警及时 |
| **T-SERVER-001.6** 文件处理隔离 | 上传docx/xlsx处理 | 沙箱隔离，无安全风险 |
| **T-SERVER-001.7** 模型推理服务 | 调用本地模型推理 | GPU共享，队列管理正确 |

### 7.2 本地模型推理服务

**当前实现** (`src/copaw/local_models/`):
- `LocalModelManager`: 单例模式管理 llama.cpp 进程
- `LlamaCppBackend`: 启动/停止 llama.cpp 服务器
- `DownloadManager`: GGUF 模型下载

**服务端化方案**:

```
┌─────────────────────────────────────────────────────────────┐
│                    模型推理服务架构                            │
│                                                             │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐  │
│  │  API Gateway │───►│ Inference    │───►│ Model        │  │
│  │  (FastAPI)   │    │ Scheduler    │    │ Workers      │  │
│  └──────────────┘    │ (任务队列)    │    │ (llama.cpp)  │  │
│        │             └──────────────┘    └──────────────┘  │
│        │                    │                    │          │
│        ▼                    ▼                    ▼          │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐  │
│  │ Model        │    │ Redis        │    │ GPU/CPU      │  │
│  │ Registry     │    │ (任务队列)    │    │ 资源池       │  │
│  │ (PG表)       │    └──────────────┘    └──────────────┘  │
│  └──────────────┘                                           │
└─────────────────────────────────────────────────────────────┘
```

**新增 PostgreSQL 表**:

```sql
-- 模型注册表
CREATE TABLE ai_model_registry (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id       VARCHAR(36) NOT NULL DEFAULT 'default-tenant',
    
    model_name      VARCHAR(200) NOT NULL,          -- 模型名称
    model_type      VARCHAR(50) NOT NULL,           -- llm/embedding/tts/stt
    architecture    VARCHAR(100),                    -- llama/gpt2/bert...
    
    -- 存储位置
    storage_key     VARCHAR(1024),                  -- 对象存储键
    file_size       BIGINT,
    quantization    VARCHAR(50),                    -- Q4_K_M/Q8_0等
    
    -- 运行参数
    default_params  JSONB DEFAULT '{}',             -- 默认推理参数
    min_gpu_memory  INTEGER,                        -- 最低GPU显存(MB)
    min_ram         INTEGER,                        -- 最低内存(MB)
    
    -- 状态
    is_available    BOOLEAN DEFAULT TRUE,
    health_status   VARCHAR(20) DEFAULT 'unknown',  -- healthy/degraded/offline
    
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX ix_ai_model_registry_tenant ON ai_model_registry(tenant_id);
CREATE INDEX ix_ai_model_registry_type ON ai_model_registry(model_type);

COMMENT ON TABLE ai_model_registry IS 'AI 模型注册表';
```

```sql
-- 推理任务表
CREATE TABLE ai_inference_tasks (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id       VARCHAR(36) NOT NULL DEFAULT 'default-tenant',
    
    model_id        UUID REFERENCES ai_model_registry(id),
    user_id         UUID REFERENCES sys_users(id) ON DELETE SET NULL,
    workspace_id    UUID REFERENCES sys_workspaces(id) ON DELETE SET NULL,
    
    task_type       VARCHAR(50) NOT NULL,           -- completion/embedding/chat
    input_data      JSONB NOT NULL,
    output_data     JSONB,
    
    status          VARCHAR(20) NOT NULL DEFAULT 'pending',
    worker_id       VARCHAR(100),                   -- 执行节点ID
    
    prompt_tokens   INTEGER DEFAULT 0,
    completion_tokens INTEGER DEFAULT 0,
    
    error_message   TEXT,
    
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    started_at      TIMESTAMPTZ,
    completed_at    TIMESTAMPTZ
);

CREATE INDEX ix_ai_inference_tasks_status ON ai_inference_tasks(status);
CREATE INDEX ix_ai_inference_tasks_tenant ON ai_inference_tasks(tenant_id);

COMMENT ON TABLE ai_inference_tasks IS 'AI 推理任务表';
```

### 7.3 文件处理和转换服务

**当前实现**: 通过 `docx`/`xlsx`/`pptx` 技能中的 Python 脚本执行

**服务端化方案**: 将 Office 文件处理提取为独立的微服务

```python
# 文件处理服务 API 设计
POST /api/enterprise/file-processing/convert
{
    "source_key": "{tenant}/users/{uid}/media/report.docx",
    "target_format": "pdf",
    "options": {
        "quality": "high",
        "page_range": [1, 10]
    }
}

# 响应
{
    "task_id": "uuid",
    "status": "processing",
    "result_key": null
}

# 查询结果
GET /api/enterprise/file-processing/tasks/{task_id}
{
    "task_id": "uuid",
    "status": "completed",
    "result_key": "{tenant}/users/{uid}/media/report.pdf",
    "download_url": "https://presigned-url..."
}
```

### 7.4 记忆检索和压缩服务

**当前实现**: `ReMeLightMemoryManager` 在本地执行

**服务端化方案**: 提取为可水平扩展的后台服务

```
记忆服务架构:

┌───────────────┐     ┌───────────────┐     ┌───────────────┐
│ Memory API    │────►│ Memory Worker │────►│ pgvector      │
│ (CRUD + 搜索) │     │ (压缩/归档)    │     │ (向量存储)     │
└───────────────┘     └───────────────┘     └───────────────┘
       │                     │
       ▼                     ▼
┌───────────────┐     ┌───────────────┐
│ PostgreSQL    │     │ Redis         │
│ (元数据)      │     │ (任务队列)     │
└───────────────┘     └───────────────┘
```

**服务端压缩策略**:

| 策略 | 触发条件 | 操作 |
|------|----------|------|
| 实时压缩 | 单次对话消息 > 100 条 | 保留最近 N 条，压缩旧消息 |
| 每日归档 | 每日凌晨 2:00 | 压缩前一天记忆，生成摘要 |
| 重要性清理 | 记忆条目 > 10000 | 归档 importance < 0.3 的记忆 |
| 向量重新索引 | 每周 | 重建 IVFFlat 索引 |

### 7.5 技能执行和管理服务

**当前实现**: 技能文件存储在 `skill_pool/` 和 `workspaces/{id}/skills/`

**服务端化方案**:

```
技能管理架构:

┌──────────────────────────────────────────────────────────┐
│                     技能管理服务                           │
│                                                          │
│  ┌────────────┐   ┌────────────┐   ┌────────────────┐  │
│  │ Skill      │   │ Skill      │   │ Skill          │  │
│  │ Registry   │   │ Store      │   │ Executor       │  │
│  │ (PG)       │   │ (对象存储)  │   │ (沙箱容器)      │  │
│  └────────────┘   └────────────┘   └────────────────┘  │
│        │                │                    │           │
│        ▼                ▼                    ▼           │
│  元数据 + 版本     文件 + 脚本          安全执行          │
│  依赖 + 权限       模板 + 资源         日志 + 审计        │
└──────────────────────────────────────────────────────────┘
```

**新增 PostgreSQL 表**:

```sql
-- 技能注册表
CREATE TABLE ai_skill_registry (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id       VARCHAR(36) NOT NULL DEFAULT 'default-tenant',
    
    name            VARCHAR(200) NOT NULL,
    display_name    VARCHAR(200),
    description     TEXT,
    version         VARCHAR(50) NOT NULL DEFAULT '1.0.0',
    category        VARCHAR(50),                   -- builtin/user/plugin
    
    -- 存储位置
    storage_key     VARCHAR(1024),                 -- 对象存储中的技能根路径
    
    -- 依赖和权限
    requirements    TEXT[],                        -- Python 依赖列表
    permissions     TEXT[],                        -- 需要的权限
    sandbox_config  JSONB DEFAULT '{}',            -- 沙箱配置
    
    -- 状态
    is_active       BOOLEAN DEFAULT TRUE,
    download_count  INTEGER DEFAULT 0,
    
    created_by      UUID REFERENCES sys_users(id) ON DELETE SET NULL,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX ix_ai_skill_registry_tenant ON ai_skill_registry(tenant_id);
CREATE INDEX ix_ai_skill_registry_name ON ai_skill_registry(name);

COMMENT ON TABLE ai_skill_registry IS '技能注册表';
```

### 7.6 定时任务调度服务

**当前实现**: `jobs.json` 文件存储 + 本地执行

**服务端化方案**: 使用 `ai_tasks` 表 + 集中调度器

```sql
-- 扩展 ai_tasks 表增加调度字段
ALTER TABLE ai_tasks ADD COLUMN IF NOT EXISTS
    schedule_expr VARCHAR(100),           -- Cron 表达式
    next_run_at TIMESTAMPTZ,             -- 下次执行时间
    last_run_at TIMESTAMPTZ,             -- 上次执行时间
    run_count INTEGER DEFAULT 0,         -- 执行次数
    max_retries INTEGER DEFAULT 3,       -- 最大重试次数
    timeout_seconds INTEGER DEFAULT 300; -- 超时时间
```

**调度器实现**:

```python
# src/copaw/enterprise/scheduler.py

import asyncio
import logging
from croniter import croniter
from datetime import datetime, timezone


class EnterpriseScheduler:
    """企业级定时任务调度器"""

    def __init__(self, db_session_factory, redis_manager):
        self._session_factory = db_session_factory
        self._redis = redis_manager
        self._running = False

    async def start(self):
        """启动调度循环"""
        self._running = True
        while self._running:
            await self._tick()
            await asyncio.sleep(60)  # 每分钟检查一次

    async def _tick(self):
        """检查并执行到期的任务"""
        now = datetime.now(timezone.utc)
        async with self._session_factory() as session:
            # 查询所有到期且启用的定时任务
            result = await session.execute(
                text("""
                    SELECT id, schedule_expr, tenant_id
                    FROM ai_tasks
                    WHERE schedule_expr IS NOT NULL
                      AND next_run_at <= :now
                      AND status = 'active'
                """),
                {"now": now},
            )
            for row in result.fetchall():
                # 分布式锁避免重复执行
                lock_key = f"scheduler:task:{row.id}"
                acquired = await self._redis.acquire_lock(lock_key, ttl=300)
                if acquired:
                    try:
                        await self._execute_task(row.id, row.tenant_id)
                    finally:
                        await self._redis.release_lock(lock_key)

            # 更新下次执行时间
            await session.execute(
                text("""
                    UPDATE ai_tasks
                    SET next_run_at = cron_next_run(schedule_expr)
                    WHERE schedule_expr IS NOT NULL
                      AND next_run_at <= :now
                """),
                {"now": now},
            )
            await session.commit()
```

---

## 8. API 接口设计

### 8.1 存储服务API

| 方法 | 路径 | 说明 |
|------|------|------|
| `POST` | `/api/enterprise/storage/upload` | 上传文件（multipart） |
| `POST` | `/api/enterprise/storage/upload-url` | 获取预签名上传 URL |
| `GET` | `/api/enterprise/storage/download/{key}` | 下载文件 |
| `GET` | `/api/enterprise/storage/download-url/{key}` | 获取预签名下载 URL |
| `DELETE` | `/api/enterprise/storage/{key}` | 删除文件 |
| `GET` | `/api/enterprise/storage/list` | 列出文件（前缀过滤） |
| `GET` | `/api/enterprise/storage/metadata/{key}` | 获取文件元数据 |
| `PUT` | `/api/enterprise/storage/metadata/{key}` | 更新文件元数据 |
| `POST` | `/api/enterprise/storage/copy` | 复制文件 |
| `GET` | `/api/enterprise/storage/health` | 存储后端健康检查 |

**上传文件 API 详细设计**:

```python
# POST /api/enterprise/storage/upload
# Content-Type: multipart/form-data

# 请求参数:
# - file: 上传的文件 (multipart)
# - category: 文件类别 (workspace/skill/memory/media/model/config)
# - workspace_id: 工作空间ID (可选)
# - tags: 标签列表 (可选，JSON数组)
# - metadata: 自定义元数据 (可选，JSON)

# 响应:
{
    "key": "default-tenant/users/abc123/workspaces/ws456/agent.json",
    "size": 12345,
    "content_type": "application/json",
    "etag": "d41d8cd98f00b204e9800998ecf8427e",
    "category": "workspace",
    "created_at": "2026-04-12T10:00:00Z"
}
```

### 8.2 元数据查询API

| 方法 | 路径 | 说明 |
|------|------|------|
| `GET` | `/api/enterprise/storage/search` | 全文搜索文件 |
| `GET` | `/api/enterprise/storage/stats` | 存储统计信息 |
| `GET` | `/api/enterprise/storage/categories` | 按类别统计 |
| `GET` | `/api/enterprise/storage/versions/{key}` | 文件版本历史 |

**搜索 API 详细设计**:

```python
# GET /api/enterprise/storage/search?q=xxx&category=workspace&page=1&page_size=20

# 响应:
{
    "total": 42,
    "page": 1,
    "page_size": 20,
    "items": [
        {
            "id": "uuid",
            "key": "default-tenant/users/abc/workspaces/ws/agent.json",
            "filename": "agent.json",
            "category": "workspace",
            "content_type": "application/json",
            "file_size": 12345,
            "owner_id": "user-uuid",
            "workspace_id": "ws-uuid",
            "tags": ["config", "agent"],
            "created_at": "2026-04-12T10:00:00Z",
            "updated_at": "2026-04-12T11:00:00Z",
            "download_url": "https://presigned-url..."
        }
    ]
}
```

### 8.3 迁移管理API

| 方法 | 路径 | 说明 |
|------|------|------|
| `POST` | `/api/enterprise/migration/start` | 启动迁移任务 |
| `GET` | `/api/enterprise/migration/status` | 查询迁移进度 |
| `POST` | `/api/enterprise/migration/rollback` | 回滚迁移 |
| `GET` | `/api/enterprise/migration/report` | 迁移报告 |

---

## 9. 安全设计

### 9.1 传输安全

| 层级 | 措施 |
|------|------|
| 客户端 ↔ API | HTTPS (TLS 1.2+)，HSTS |
| API ↔ 对象存储 | TLS 加密传输 |
| API ↔ PostgreSQL | SSL 连接 (`ssl_mode=verify-full`) |
| API ↔ Redis | TLS 连接 (Redis 6+ SSL) |
| 预签名 URL | 限时有效期 (默认 1 小时) |

### 9.2 存储安全

| 数据类型 | 加密方式 | 说明 |
|----------|----------|------|
| 认证密钥 | AES-256 服务端加密 | 不入对象存储，保留在数据库 |
| 对象存储 | SSE-S3 / SSE-KMS | 存储桶级默认加密 |
| 数据库敏感字段 | pgcrypto 扩展 | API Key 等敏感配置 |
| 向量嵌入 | 不加密 | 性能考虑，通过访问控制保护 |
| 日志和审计 | 不加密 | 通过 DLP 脱敏处理 |

### 9.3 访问安全

```python
# 存储访问安全检查流程
async def secure_storage_access(
    user: dict,
    action: str,        # read/write/delete
    storage_key: str,
) -> bool:
    """存储访问安全检查"""

    # 1. 身份验证 (JWT)
    if not user.get("user_id"):
        return False

    # 2. 租户隔离
    key_tenant = storage_key.split("/")[0]
    if key_tenant != user.get("tenant_id") and "super_admin" not in user.get("roles", []):
        return False

    # 3. RBAC 权限
    required_permission = f"storage:{action}"
    if not await check_permission(user, required_permission):
        return False

    # 4. DLP 检查 (写入时)
    if action == "write":
        dlp_result = await check_dlp(storage_key)
        if dlp_result.blocked:
            return False

    # 5. 审计日志
    await log_storage_access(user, action, storage_key)

    return True
```

### 9.4 合规要求

| 要求 | 实现 |
|------|------|
| ISO 27001 审计 | 所有存储操作写入 `sys_audit_logs` |
| 数据保留策略 | 对象生命周期策略 (标准 → 低频 → 归档) |
| 数据删除合规 | 软删除 + 定期物理清理 |
| 跨境数据 | 存储桶区域配置，遵守数据驻留法规 |
| 加密标准 | AES-256 / TLS 1.2+ |
| 访问日志 | 90 天保留期 |

---

## 10. 分阶段实施计划

### 10.1 阶段概览

```
Phase 1 (P0)          Phase 2 (P1)          Phase 3 (P1)
存储抽象层             多租户分层存储         双轨存储+元数据+SQLite迁移
2-3 周                2-3 周                 4-5 周
    │                     │                     │
    ▼                     ▼                     ▼
Phase 4 (P2)          Phase 5 (P3)
功能服务端化           生产优化
4-6 周                持续
```

### 10.2 Phase 1: 存储抽象层

**优先级**: P0 (最高)  
**工期**: 2-3 周  
**里程碑**: 上层代码通过 `ObjectStorageProvider` 接口访问存储，后端可零代码切换

**任务列表**:

| # | 任务 | 工作量 | 依赖 |
|---|------|--------|------|
| 1.1 | 定义 `ObjectStorageProvider` 抽象接口 | 2d | - |
| 1.2 | 实现 `FileSystemStorageAdapter` (个人版兼容) | 2d | 1.1 |
| 1.3 | 实现 `S3StorageAdapter` | 3d | 1.1 |
| 1.4 | 实现 `MinIOStorageAdapter` | 2d | 1.3 |
| 1.5 | 实现 `OSSStorageAdapter` | 2d | 1.1 |
| 1.6 | 实现 `SFTPStorageAdapter` | 3d | 1.1 |
| 1.7 | 定义 `StorageConfig` 配置模型 | 1d | 1.1 |
| 1.8 | 集成到 `EnterpriseConfig` | 0.5d | 1.7 |
| 1.9 | FastAPI 生命周期集成 | 1d | 1.2-1.6 |
| 1.10 | 存储服务 REST API 路由 | 3d | 1.9 |
| 1.11 | 单元测试 + 集成测试 | 3d | 1.2-1.10 |
| 1.12 | 文档更新 | 1d | 1.11 |

**验证标准**:
- [ ] 通过 `StorageConfig.backend="filesystem"` 可完全兼容现有 `~/.copaw/` 行为
- [ ] 切换 `backend="s3"` 后，所有文件操作透明切换到 S3
- [ ] 预签名 URL 生成和验证正常工作
- [ ] 现有测试全部通过

**回滚方案**: 
- Phase 1 仅新增代码，不修改现有逻辑
- 通过配置 `backend="filesystem"` 即可回退
- 零风险回滚

### 10.3 Phase 2: 多租户分层存储

**优先级**: P1  
**工期**: 2-3 周  
**里程碑**: 所有存储操作自动注入租户前缀，跨租户数据完全隔离

**任务列表**:

| # | 任务 | 工作量 | 依赖 |
|---|------|--------|------|
| 2.1 | 设计对象键命名规范 | 1d | Phase 1 |
| 2.2 | 实现 `StorageKeyBuilder` | 2d | 2.1 |
| 2.3 | 实现 `StorageAccessControl` | 3d | 2.2 |
| 2.4 | 修改 `WorkspaceManager` 使用存储抽象层 | 3d | 2.2 |
| 2.5 | 修改 `SkillManager` 使用存储抽象层 | 2d | 2.2 |
| 2.6 | 修改 `MemoryManager` (Markdown) 使用存储抽象层 | 2d | 2.2 |
| 2.7 | 修改 `ConfigManager` 使用存储抽象层 | 2d | 2.2 |
| 2.8 | 媒体文件上传迁移 | 2d | 2.2 |
| 2.9 | 租户初始化脚本 (创建默认目录结构) | 1d | 2.3 |
| 2.10 | 集成测试 + 安全测试 | 3d | 2.4-2.9 |
| 2.11 | 迁移工具: 本地文件 → 对象存储 | 3d | 2.3 |

**验证标准**:
- [ ] 不同租户的文件严格隔离
- [ ] 租户管理员可访问租户内所有文件
- [ ] 普通用户只能访问自己的文件
- [ ] 系统资源 (`_system/`) 通过 API 代理只读访问

**回滚方案**:
- 保留本地文件系统副本
- 切换 `backend="filesystem"` 回退
- 对象存储中的数据通过迁移工具反向同步

### 10.4 Phase 3: 双轨存储 + 元数据索引 + SQLite 迁移

**优先级**: P1 (核心)  
**工期**: 4-5 周  
**里程碑**: 元数据双轨架构上线，所有文件自动双写（对象存储 + PG 元数据），SQLite 数据全量迁移至 PostgreSQL

**任务列表**:

| # | 任务 | 工作量 | 依赖 |
|---|------|--------|------|
| 3.1 | 安装 pgvector 扩展 + 创建基础表 (Alembic 迁移) | 1d | Phase 2 |
| 3.2 | 创建 `storage_objects` 通用文件索引表 | 1d | 3.1 |
| 3.3 | 创建业务元数据表 (`ai_agent_configs`, `ai_skill_configs`, `ai_conversations`, `ai_conversation_messages`, `ai_token_usage_stats`, `ai_memory_documents`, `ai_channel_messages`) | 2d | 3.1 |
| 3.4 | 扩展 `ai_tasks` 表增加调度字段 | 0.5d | 3.1 |
| 3.5 | 创建记忆表 (`ai_memories`, `ai_memory_tags`, `ai_memory_sessions`, `ai_memory_session_links`) | 1d | 3.1 |
| 3.6 | 实现 `MetadataExtractor` (通用索引 + 业务抽取) | 3d | 3.2-3.3 |
| 3.7 | 存储写入钩子: 对象上传后自动双写元数据 | 2d | 3.6 |
| 3.8 | 实现 `ReMePostgresBackend` | 5d | 3.5 |
| 3.9 | 实现 `MemoryBackendFactory` (企业版/个人版切换) | 1d | 3.8 |
| 3.10 | 迁移脚本: SQLite → PostgreSQL | 3d | 3.8 |
| 3.11 | 通道消息入库中间件 | 3d | 3.3 |
| 3.12 | 实现搜索服务 `StorageSearchService` | 3d | 3.2 |
| 3.13 | 搜索 REST API | 2d | 3.12 |
| 3.14 | 批量索引工具 (迁移现有文件) | 2d | 3.6 |
| 3.15 | 增量同步定时任务 | 1d | 3.7 |
| 3.16 | 集成测试 + 性能测试 | 3d | 3.6-3.15 |
| 3.17 | 性能基准测试 (10万文件 + 10万向量记忆) | 2d | 3.16 |

**验证标准**:
- [ ] 文件上传后 5 秒内可在搜索中查到
- [ ] 全文搜索响应时间 < 200ms (5万文件)
- [ ] 向量搜索召回率 ≥ 95% (对比 SQLite)
- [ ] 向量搜索延迟 < 50ms (10万条记忆)
- [ ] 元数据双写: 对象存储写入后 PG 元数据同步完成
- [ ] 企业版无 SQLite 依赖，个人版保持原有行为
- [ ] 通道消息实时入库，延迟 < 500ms
- [ ] 迁移脚本可重复执行（幂等性）

**回滚方案**:
- 元数据表独立，可清空重建
- 不影响对象存储中的实际文件
- 个人版保留 SQLite，企业版回退通过 `COPAW_MEMORY_BACKEND=sqlite` 切回
- 通道消息入库失败不影响消息处理（异步写入）

### 10.5 Phase 4: 功能服务端迁移

**优先级**: P2  
**工期**: 4-6 周  
**里程碑**: 定时任务、通道消息处理、记忆压缩等本地功能迁移为服务端服务

**任务列表**:

| # | 任务 | 工作量 | 依赖 |
|---|------|--------|------|
| 4.1 | 定时任务调度器 `EnterpriseScheduler` | 5d | Phase 3 |
| 4.2 | 扩展 `ai_tasks` 表增加调度字段 (如 Phase 3 未完成) | 1d | 4.1 |
| 4.3 | 迁移 `jobs.json` → `ai_tasks` | 2d | 4.2 |
| 4.4 | 记忆压缩后台服务 | 5d | Phase 3 |
| 4.5 | 心跳监控服务化 | 3d | Phase 2 |
| 4.6 | 通道消息审计和分析服务 | 3d | Phase 3 |
| 4.7 | 文件处理微服务 (可选) | 5d | Phase 2 |
| 4.8 | 模型推理服务化 (可选) | 8d | Phase 2 |
| 4.9 | 技能注册和管理服务 | 5d | Phase 3 |
| 4.10 | 集成测试 + 压力测试 | 5d | 4.1-4.9 |
| 4.11 | 灰度发布和监控 | 3d | 4.10 |

**验证标准**:
- [ ] 定时任务不遗漏不重复执行
- [ ] 记忆压缩不影响在线服务性能
- [ ] 心跳监控覆盖所有在线 Agent
- [ ] 通道消息审计查询响应 < 1s (1万条消息)
- [ ] 分布式锁正确防止任务重复

**回滚方案**:
- 每个功能独立开关 (`COPAW_FEATURE_SCHEDULER=local|enterprise`)
- 可逐个功能回滚
- 个人版本地模式始终可用

---

## 11. 风险评估与回滚方案

### 11.1 风险矩阵

| 风险 | 可能性 | 影响 | 缓解措施 |
|------|--------|------|----------|
| 对象存储服务不可用 | 低 | 高 | MinIO 局域网部署稳定性高 + 本地缓存降级 |
| pgvector 性能不达标 | 低 | 中 | 中小企业数据量小，pgvector 完全胜任；如不达标可调优 HNSW 索引 |
| 元数据双写不一致 | 中 | 中 | 写入钩子事务化 + 定时增量同步补全 |
| 迁移数据丢失 | 低 | 极高 | 完整备份 + 迁移后校验 + 个人版 SQLite 保留 |
| 多租户数据泄露 | 低 | 极高 | 自动化租户隔离测试 + 安全审计 |
| 向量维度不兼容 | 低 | 中 | 维度检测 + 自动转换层 |
| 大文件上传超时 | 中 | 低 | 分片上传 + 断点续传 |
| 迁移期间服务中断 | 中 | 高 | 滚动迁移 + 灰度切换 + 个人版不受影响 |
| 通道消息入库延迟 | 低 | 低 | 异步写入 + 消息队列缓冲 |
| 企业版误用 SQLite | 低 | 高 | 启动检查 + 配置强制校验 |

**【验收测试标记 T-RISK-001】风险缓解措施验证**

| 风险项 | 缓解措施验证 | 测试方法 | 通过标准 |
|--------|-------------|----------|----------|
| 对象存储不可用 | MinIO局域网稳定性 | 停止MinIO 1分钟，恢复后检查 | 服务自动恢复，无数据丢失 |
| pgvector性能 | HNSW索引调优 | 100万向量搜索，调整M/ef_construction | P95<30ms |
| 元数据双写不一致 | 写入钩子事务化 | 模拟PG写入失败，检查重试 | 定时任务补全，最终一致 |
| 迁移数据丢失 | 完整备份+校验 | 迁移1000条记录，对比SHA-256 | 100%一致 |
| 多租户数据泄露 | 租户隔离测试 | 租户A尝试访问租户B数据 | 100%拦截，日志记录 |
| 通道消息延迟 | 异步写入缓冲 | 100并发消息，检查入库延迟 | P95<500ms |
| 企业版误用SQLite | 启动检查 | 企业版配置使用SQLite | 启动失败，明确错误提示 |

### 11.2 通用回滚策略

```
回滚决策流程:

1. 检测异常
   ├── 监控告警 (错误率 > 1%)
   ├── 人工发现 (功能异常)
   └── 自动检测 (健康检查失败)

2. 评估影响
   ├── 轻微 (个别功能) → 修复 + 热更新
   ├── 中等 (模块级) → 功能开关关闭
   └── 严重 (全系统) → 配置回退到前一版本

3. 执行回滚
   ├── 配置回退: 修改 StorageConfig.backend
   ├── 数据回退: 启用本地文件系统模式
   ├── 代码回退: Git revert 到稳定版本
   └── 数据库回退: Alembic downgrade

4. 验证恢复
   ├── 健康检查通过
   ├── 核心功能验证
   └── 数据完整性校验
```

### 11.3 数据备份策略

| 数据 | 备份方式 | 频率 | 保留期 |
|------|----------|------|--------|
| PostgreSQL | pg_dump 全量 + WAL 增量 | 全量每日 / WAL 实时 | 30 天 |
| MinIO 对象存储 | 纠删码 + 本地备份 | 实时 | 永久 |
| Redis | RDB + AOF | 实时 | 7 天 |
| 个人版 SQLite (迁移前) | 文件拷贝 | 迁移前一次性 | 永久 |
| 配置文件 | Git 版本控制 | 每次变更 | 永久 |
| Alembic 迁移文件 | Git 版本控制 | 每次变更 | 永久 |

---

## 12. 附录

### 12.1 新增 PostgreSQL 表汇总

| 表名 | Phase | 用途 |
|------|-------|------|
| `storage_objects` | Phase 3 | 通用文件对象索引 |
| `ai_agent_configs` | Phase 3 | Agent 配置元数据 (从 agent.json 抽取) |
| `ai_skill_configs` | Phase 3 | Skill 配置元数据 (从 skill.json 抽取) |
| `ai_conversations` | Phase 3 | 对话元数据 (从 chats.json 抽取) |
| `ai_conversation_messages` | Phase 3 | 对话消息 (从 chats.json.messages 逐条抽取) |
| `ai_token_usage_stats` | Phase 3 | Token 使用统计 (从 token_usage.json 抽取) |
| `ai_memory_documents` | Phase 3 | 记忆文档元数据 (从 memory/*.md 抽取) |
| `ai_channel_messages` | Phase 3 | 通道消息 (飞书/钉钉等) |
| `ai_memories` | Phase 3 | 企业版向量记忆存储 |
| `ai_memory_tags` | Phase 3 | 记忆标签关联 |
| `ai_memory_sessions` | Phase 3 | 记忆会话上下文 |
| `ai_memory_session_links` | Phase 3 | 会话-记忆关联 |
| `ai_model_registry` | Phase 4 | 模型注册表 |
| `ai_inference_tasks` | Phase 4 | 推理任务表 |
| `ai_skill_registry` | Phase 4 | 技能注册表 |
| `ai_tasks` (扩展) | Phase 3-4 | 定时任务调度字段扩展 |

### 12.2 新增 Python 模块汇总

| 模块路径 | Phase | 用途 |
|----------|-------|------|
| `src/copaw/storage/` | Phase 1 | 存储抽象层包 |
| `src/copaw/storage/base.py` | Phase 1 | 统一接口定义 |
| `src/copaw/storage/config.py` | Phase 1 | 存储配置模型 |
| `src/copaw/storage/s3_adapter.py` | Phase 1 | S3 适配器 |
| `src/copaw/storage/minio_adapter.py` | Phase 1 | MinIO 适配器 |
| `src/copaw/storage/oss_adapter.py` | Phase 1 | OSS 适配器 |
| `src/copaw/storage/sftp_adapter.py` | Phase 1 | SFTP 适配器 |
| `src/copaw/storage/filesystem_adapter.py` | Phase 1 | 文件系统适配器 |
| `src/copaw/storage/access_control.py` | Phase 2 | 存储访问控制 |
| `src/copaw/storage/metadata_extractor.py` | Phase 3 | 元数据抽取 (通用索引+业务抽取) |
| `src/copaw/storage/search_service.py` | Phase 3 | 存储搜索服务 |
| `src/copaw/agents/memory/reme_postgres_backend.py` | Phase 3 | ReMe PostgreSQL 后端 |
| `src/copaw/agents/memory/memory_backend_factory.py` | Phase 3 | 记忆后端工厂 (企业/个人版切换) |
| `src/copaw/enterprise/channel_message_middleware.py` | Phase 3 | 通道消息入库中间件 |
| `src/copaw/enterprise/scheduler.py` | Phase 4 | 定时任务调度器 |
| `src/copaw/db/repositories/` | Phase 3 | 元数据 Repository 包 |
| `src/copaw/db/repositories/agent_config_repo.py` | Phase 3 | Agent 配置元数据仓库 |
| `src/copaw/db/repositories/skill_config_repo.py` | Phase 3 | Skill 配置元数据仓库 |
| `src/copaw/db/repositories/conversation_repo.py` | Phase 3 | 对话元数据仓库 |
| `src/copaw/db/repositories/channel_message_repo.py` | Phase 3 | 通道消息仓库 |

### 12.3 新增 REST API 汇总

| 路径前缀 | Phase | 说明 |
|----------|-------|------|
| `/api/enterprise/storage/` | Phase 1-2 | 存储操作 API |
| `/api/enterprise/storage/search` | Phase 3 | 元数据搜索 API |
| `/api/enterprise/metadata/agents` | Phase 3 | Agent 配置元数据查询 |
| `/api/enterprise/metadata/skills` | Phase 3 | Skill 配置元数据查询 |
| `/api/enterprise/metadata/conversations` | Phase 3 | 对话历史元数据查询 |
| `/api/enterprise/metadata/token-usage` | Phase 3 | Token 使用统计查询 |
| `/api/enterprise/metadata/channel-messages` | Phase 3 | 通道消息查询 |
| `/api/enterprise/migration/` | Phase 3 | 迁移管理 API |
| `/api/enterprise/file-processing/` | Phase 4 | 文件处理 API |
| `/api/enterprise/inference/` | Phase 4 | 推理服务 API |

### 12.4 新增 Alembic 迁移文件

| 文件 | Phase | 内容 |
|------|-------|------|
| `004_storage_objects.py` | Phase 3 | `storage_objects` 通用文件索引 |
| `005_ai_metadata_tables.py` | Phase 3 | `ai_agent_configs` + `ai_skill_configs` + `ai_conversations` + `ai_conversation_messages` + `ai_token_usage_stats` + `ai_memory_documents` + `ai_channel_messages` |
| `006_ai_memories_pgvector.py` | Phase 3 | `ai_memories` + `ai_memory_tags` + `ai_memory_sessions` + `ai_memory_session_links` + pgvector 扩展 |
| `007_ai_tasks_scheduling.py` | Phase 3-4 | `ai_tasks` 扩展调度字段 |
| `008_ai_model_registry.py` | Phase 4 | `ai_model_registry` + `ai_inference_tasks` + `ai_skill_registry` |

### 12.5 新增依赖包

| 包名 | 版本 | Phase | 用途 |
|------|------|-------|------|
| `aioboto3` | ≥12.0 | Phase 1 | S3 异步客户端 |
| `miniopy-async` | ≥1.0 | Phase 1 | MinIO 异步客户端 |
| `oss2` | ≥2.18 | Phase 1 | 阿里云 OSS SDK |
| `asyncssh` | ≥2.14 | Phase 1 | SFTP 异步客户端 |
| `pgvector` | ≥0.2 | Phase 3 | PostgreSQL 向量扩展 Python 绑定 |
| `croniter` | ≥1.4 | Phase 4 | Cron 表达式解析 |

### 12.6 环境变量新增

| 变量 | 默认值 | Phase | 说明 |
|------|--------|-------|------|
| `COPAW_STORAGE_BACKEND` | `filesystem` | Phase 1 | 存储后端类型 (filesystem/s3/minio/oss/sftp) |
| `COPAW_STORAGE_BUCKET` | `copaw-data` | Phase 1 | 默认存储桶 |
| `COPAW_S3_ENDPOINT_URL` | (空) | Phase 1 | S3 端点 URL |
| `COPAW_S3_ACCESS_KEY` | (空) | Phase 1 | S3 Access Key |
| `COPAW_S3_SECRET_KEY` | (空) | Phase 1 | S3 Secret Key |
| `COPAW_MINIO_ENDPOINT` | `localhost:9000` | Phase 1 | MinIO 端点 |
| `COPAW_MEMORY_BACKEND` | `auto` | Phase 3 | 记忆后端 (auto/postgres/sqlite/chroma) |
| `COPAW_METADATA_SYNC_ENABLED` | `true` | Phase 3 | 是否启用元数据双写同步 |
| `COPAW_CHANNEL_MESSAGE_PERSIST` | `true` | Phase 3 | 通道消息是否入库 |
| `COPAW_FEATURE_SCHEDULER` | `local` | Phase 4 | 调度器模式 (local/enterprise) |

---

**文档维护**:
- 本文档随改造进度持续更新
- 每个 Phase 完成后更新验证标准
- 风险评估每迭代回顾一次
- 验收测试标记随代码实现同步更新

**验收测试标记索引**:

| 标记前缀 | 功能模块 | 测试项数量 | 状态 |
|----------|----------|-----------|------|
| `T-ARCH` | 双轨存储架构 | 4 | ✅ 已定义 |
| `T-STORAGE` | 存储抽象层 | 4组26项 | ✅ 已定义 |
| `T-MULTI-TENANT` | 多租户分层存储 | 3组12项 | ✅ 已定义 |
| `T-META` | 元数据抽取与索引 | 5组29项 | ✅ 已定义 |
| `T-MIGRATE` | SQLite迁移 | 5组21项 | ✅ 已定义 |
| `T-SERVER` | 功能服务端迁移 | 1组7项 | ✅ 已定义 |
| `T-RISK` | 风险缓解验证 | 1组7项 | ✅ 已定义 |
| **合计** | **全模块** | **86项** | **100%覆盖** |

**验收测试执行指南**:

1. **单元测试**: 每个模块的Python代码需编写对应的pytest单元测试
2. **集成测试**: 使用Docker Compose启动完整环境（MinIO + PostgreSQL + Redis）
3. **性能测试**: 使用locust或k6进行负载测试，验证P95/P99延迟
4. **数据一致性**: 使用脚本对比源数据和迁移后数据，SHA-256校验
5. **错误注入**: 使用chaos engineering工具注入故障，验证容错能力

**验收测试通过标准**:

- ✅ 所有标记测试项100%通过
- ✅ 性能指标P95/P99满足设计要求
- ✅ 数据一致性100%验证通过
- ✅ 错误处理覆盖所有异常场景
- ✅ 多租户隔离100%有效
- ✅ 回滚方案验证通过

---

**关联文档**:
- [data_models.md](./data_models.md) — CoPaw 完整数据模型架构
- [ent-copaw.md](./ent-copaw.md) — Enterprise PRD
- [ENTERPRISE-RELEASE-NOTES.md](./ENTERPRISE-RELEASE-NOTES.md) — 发布说明
