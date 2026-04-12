# CoPaw 完整数据模型架构文档

> **版本**: 1.0.0  
> **更新日期**: 2026-04-12  
> **分析基于**: CoPaw v0.1beta1 (Enterprise Edition)  
> **文档范围**: 文件系统数据模型 + SQLite 数据模型 + PostgreSQL 企业版数据模型

---

## 目录

- [1. 架构概览](#1-架构概览)
- [2. 文件系统数据模型（个人版）](#2-文件系统数据模型个人版)
  - [2.1 目录结构总览](#21-目录结构总览)
  - [2.2 工作空间数据模型](#22-工作空间数据模型)
  - [2.3 技能池数据模型](#23-技能池数据模型)
  - [2.4 记忆数据模型](#24-记忆数据模型)
  - [2.5 配置文件数据模型](#25-配置文件数据模型)
  - [2.6 认证数据模型](#26-认证数据模型)
- [3. SQLite 数据模型](#3-sqlite-数据模型)
  - [3.1 ReMe 记忆数据库](#31-reme-记忆数据库)
  - [3.2 向量嵌入缓存](#32-向量嵌入缓存)
- [4. PostgreSQL 数据模型（企业版）](#4-postgresql-数据模型企业版)
  - [4.1 用户与组织管理](#41-用户与组织管理)
  - [4.2 权限与安全体系](#42-权限与安全体系)
  - [4.3 会话与令牌管理](#43-会话与令牌管理)
  - [4.4 工作空间管理](#44-工作空间管理)
  - [4.5 AI 任务与评论](#45-ai-任务与评论)
  - [4.6 工作流管理（Dify 集成）](#46-工作流管理dify-集成)
  - [4.7 审计日志（ISO 27001 合规）](#47-审计日志iso-27001-合规)
  - [4.8 数据安全与合规（DLP）](#48-数据安全与合规dlp)
  - [4.9 告警管理](#49-告警管理)
  - [4.10 租户管理](#410-租户管理)
- [5. 数据模型关系图](#5-数据模型关系图)
- [6. 个人版与企业版数据模型差异](#6-个人版与企业版数据模型差异)
- [7. 数据迁移策略](#7-数据迁移策略)
- [8. 数据存储最佳实践](#8-数据存储最佳实践)
- [9. 附录：数据库迁移记录](#9-附录数据库迁移记录)

---

## 1. 架构概览

CoPaw 采用了**混合存储架构**，根据数据特性选择最适合的存储方式：

```
┌─────────────────────────────────────────────────────────────┐
│                     CoPaw 数据存储架构                        │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐  │
│  │  文件系统     │    │  PostgreSQL  │    │    Redis     │  │
│  │              │    │              │    │              │  │
│  │ • Agent配置  │    │ • 用户管理   │    │ • 会话缓存   │  │
│  │ • 技能文件   │    │ • 权限体系   │    │ • 令牌缓存   │  │
│  │ • 人格文件   │    │ • 工作流定义 │    │ • 实时消息   │  │
│  │ • 记忆数据   │    │ • 审计日志   │    │ • 权限缓存   │  │
│  │ • 对话历史   │    │ • 任务管理   │    │              │  │
│  │ • 定时任务   │    │ • DLP规则   │    │              │  │
│  │ • Token记录  │    │ • 租户管理   │    │              │  │
│  └──────────────┘    └──────────────┘    └──────────────┘  │
│                                                             │
│  ┌──────────────┐    ┌──────────────┐                      │
│  │   SQLite     │    │  对象存储    │                      │
│  │              │    │  (可选)      │                      │
│  │ • ReMe记忆   │    │              │                      │
│  │ • 向量缓存   │    │ • 媒体文件   │                      │
│  │ • 嵌入索引   │    │ • 上传文件   │                      │
│  └──────────────┘    └──────────────┘                      │
└─────────────────────────────────────────────────────────────┘
```

**设计原则**：
- **结构化数据**（用户、权限、审计）→ PostgreSQL
- **非结构化数据**（代码、文档、配置）→ 文件系统
- **高速缓存**（会话、令牌）→ Redis
- **向量/语义数据**（记忆、嵌入）→ SQLite
- **大文件**（媒体、附件）→ 对象存储（可选）

---

## 2. 文件系统数据模型（个人版）

### 2.1 目录结构总览

所有个人版数据存储在 `~/.copaw/` 目录下（可通过 `COPAW_WORKING_DIR` 环境变量覆盖）：

```
~/.copaw/                                    # WORKING_DIR (工作目录)
├── workspaces/                              # 工作空间目录
│   ├── default/                             # 默认 Agent 工作空间
│   │   ├── agent.json                       # Agent 完整配置 (~12KB)
│   │   ├── skill.json                       # 技能配置清单 (~16KB)
│   │   ├── chats.json                       # 对话历史记录
│   │   ├── jobs.json                        # 定时任务定义
│   │   ├── token_usage.json                 # Token 使用记录
│   │   ├── MEMORY.md                        # 长期记忆 (Markdown)
│   │   ├── AGENTS.md                        # 人格定义 (Markdown)
│   │   ├── SOUL.md                          # 灵魂定义 (Markdown)
│   │   ├── PROFILE.md                       # 配置文件 (Markdown)
│   │   ├── BOOTSTRAP.md                     # 引导文档 (Markdown)
│   │   ├── HEARTBEAT.md                     # 心跳配置 (Markdown)
│   │   ├── skills/                          # 工作区技能目录
│   │   │   ├── browser_cdp/
│   │   │   │   ├── SKILL.md
│   │   │   │   └── scripts/
│   │   │   ├── cron/
│   │   │   ├── docx/
│   │   │   └── ... (14+ 个技能)
│   │   ├── active_skills/                   # 已激活技能链接
│   │   └── memory/                          # 每日记忆
│   │       └── 2026-04-11.md
│   │
│   └── CoPaw_QA_Agent_0.1beta1/             # 内置 QA Agent 工作空间
│       └── (同上结构)
│
├── skill_pool/                              # 共享技能池
│   ├── skill.json                           # 技能池清单
│   ├── browser_cdp/
│   ├── browser_visible/
│   ├── cron/
│   ├── docx/
│   └── ... (14+ 个内置技能)
│
├── memory/                                  # 全局记忆目录
├── media/                                   # 媒体文件 (DEFAULT_MEDIA_DIR)
├── models/                                  # 本地模型 (MODELS_DIR)
├── custom_channels/                         # 自定义通道模块
├── plugins/                                 # 插件目录
├── config.json                              # 全局配置 (CONFIG_FILE)
├── debug_history.jsonl                      # 调试历史
├── copaw.log                                # 运行日志
│
└── .secret/                                 # SECRET_DIR (权限: 0700)
    └── auth.json                            # 认证信息 (权限: 0600)
```

**关键路径常量**（定义于 `src/copaw/constant.py`）：

| 常量名 | 默认值 | 环境变量 | 说明 |
|--------|--------|----------|------|
| `WORKING_DIR` | `~/.copaw` | `COPAW_WORKING_DIR` | 工作目录根路径 |
| `SECRET_DIR` | `{WORKING_DIR}.secret` | `COPAW_SECRET_DIR` | 密钥存储目录 |
| `DEFAULT_MEDIA_DIR` | `{WORKING_DIR}/media` | - | 媒体文件目录 |
| `MODELS_DIR` | `{WORKING_DIR}/models` | - | 本地模型目录 |
| `CONFIG_FILE` | `config.json` | `COPAW_CONFIG_FILE` | 全局配置文件 |
| `CHATS_FILE` | `chats.json` | `COPAW_CHATS_FILE` | 对话历史文件 |
| `JOBS_FILE` | `jobs.json` | `COPAW_JOBS_FILE` | 定时任务文件 |
| `TOKEN_USAGE_FILE` | `token_usage.json` | `COPAW_TOKEN_USAGE_FILE` | Token 使用记录 |
| `HEARTBEAT_FILE` | `HEARTBEAT.md` | `COPAW_HEARTBEAT_FILE` | 心跳配置文件 |
| `MEMORY_DIR` | `{WORKING_DIR}/memory` | - | 全局记忆目录 |
| `CUSTOM_CHANNELS_DIR` | `{WORKING_DIR}/custom_channels` | - | 自定义通道目录 |
| `PLUGINS_DIR` | `{WORKING_DIR}/plugins` | - | 插件目录 |

---

### 2.2 工作空间数据模型

每个工作空间代表一个独立的 Agent 运行时环境，包含完整的配置、技能和状态。

#### 2.2.1 `agent.json` — Agent 配置

**文件位置**: `~/.copaw/workspaces/{agent_id}/agent.json`

**数据结构**:
```json
{
  "name": "Agent Name",
  "description": "Agent 描述",
  "model": {
    "provider": "openai",
    "model_name": "gpt-4",
    "api_key": "sk-xxx",
    "base_url": "https://api.openai.com/v1",
    "temperature": 0.7,
    "max_tokens": 4096
  },
  "channels": {
    "feishu": {
      "enabled": true,
      "app_id": "cli_xxx",
      "app_secret": "xxx"
    },
    "dingtalk": {
      "enabled": false
    }
  },
  "memory": {
    "backend": "remelight",
    "max_messages": 100,
    "compaction": {
      "keep_recent": 3,
      "ratio": 0.7
    }
  },
  "skills": ["browser_cdp", "docx", "cron"],
  "mcp_servers": [],
  "heartbeat": {
    "enabled": true,
    "every": "6h",
    "target": "main"
  }
}
```

**字段说明**:

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `name` | string | ✅ | Agent 显示名称 |
| `description` | string | ❌ | Agent 描述 |
| `model` | object | ✅ | LLM 模型配置 |
| `model.provider` | string | ✅ | 模型提供商 (openai, anthropic, dashscope 等) |
| `model.model_name` | string | ✅ | 模型名称 |
| `model.api_key` | string | ✅ | API 密钥 |
| `model.base_url` | string | ❌ | API 基础 URL |
| `model.temperature` | float | ❌ | 温度参数 (0-2) |
| `model.max_tokens` | int | ❌ | 最大 Token 数 |
| `channels` | object | ❌ | 通道配置 |
| `memory` | object | ❌ | 记忆管理配置 |
| `memory.backend` | string | ❌ | 记忆后端 (remelight) |
| `skills` | array | ❌ | 已激活技能列表 |
| `mcp_servers` | array | ❌ | MCP 服务器配置 |
| `heartbeat` | object | ❌ | 心跳配置 |

---

#### 2.2.2 `chats.json` — 对话历史

**文件位置**: `~/.copaw/workspaces/{agent_id}/chats.json`

**数据结构**:
```json
{
  "version": 1,
  "chats": [
    {
      "id": "chat_001",
      "created_at": "2026-04-11T10:00:00Z",
      "updated_at": "2026-04-11T10:30:00Z",
      "messages": [
        {
          "role": "user",
          "content": "你好",
          "timestamp": "2026-04-11T10:00:00Z"
        },
        {
          "role": "assistant",
          "content": "你好！有什么可以帮你的？",
          "timestamp": "2026-04-11T10:00:01Z"
        }
      ]
    }
  ]
}
```

**字段说明**:

| 字段 | 类型 | 说明 |
|------|------|------|
| `version` | int | 数据格式版本号 |
| `chats` | array | 对话列表 |
| `chats[].id` | string | 对话唯一 ID |
| `chats[].created_at` | string | 创建时间 (ISO 8601) |
| `chats[].updated_at` | string | 最后更新时间 |
| `chats[].messages` | array | 消息列表 |
| `chats[].messages[].role` | string | 角色 (user/assistant/system) |
| `chats[].messages[].content` | string | 消息内容 |
| `chats[].messages[].timestamp` | string | 消息时间戳 |

**存储特点**:
- 单文件存储，适合小规模对话历史
- 通过 `JsonChatRepository` 进行 CRUD 操作
- 企业版可扩展为 PostgreSQL 的 `ai_conversations` 表

---

#### 2.2.3 `jobs.json` — 定时任务

**文件位置**: `~/.copaw/workspaces/{agent_id}/jobs.json`

**数据结构**:
```json
{
  "version": 1,
  "jobs": [
    {
      "id": "job_001",
      "name": "每日报告生成",
      "schedule": "0 9 * * *",
      "command": "generate_report",
      "args": {"type": "daily"},
      "enabled": true,
      "last_run": "2026-04-11T09:00:00Z",
      "next_run": "2026-04-12T09:00:00Z"
    }
  ]
}
```

**字段说明**:

| 字段 | 类型 | 说明 |
|------|------|------|
| `version` | int | 数据格式版本号 |
| `jobs` | array | 任务列表 |
| `jobs[].id` | string | 任务唯一 ID |
| `jobs[].name` | string | 任务名称 |
| `jobs[].schedule` | string | Cron 表达式 |
| `jobs[].command` | string | 执行的命令 |
| `jobs[].args` | object | 命令参数 |
| `jobs[].enabled` | bool | 是否启用 |
| `jobs[].last_run` | string | 上次执行时间 |
| `jobs[].next_run` | string | 下次执行时间 |

**存储特点**:
- 通过 `JsonJobRepository` 管理
- 企业版对应 PostgreSQL 的 `ai_tasks` 表（支持更复杂的任务管理）

---

#### 2.2.4 `token_usage.json` — Token 使用记录

**文件位置**: `~/.copaw/workspaces/{agent_id}/token_usage.json`

**数据结构**:
```json
{
  "2026-04-11": {
    "prompt_tokens": 15000,
    "completion_tokens": 5000,
    "total_tokens": 20000,
    "requests": 45,
    "cost_usd": 0.045
  },
  "2026-04-10": {
    "prompt_tokens": 12000,
    "completion_tokens": 4000,
    "total_tokens": 16000,
    "requests": 38,
    "cost_usd": 0.036
  }
}
```

**字段说明**:

| 字段 | 类型 | 说明 |
|------|------|------|
| `{date}` | object | 日期键 (YYYY-MM-DD) |
| `prompt_tokens` | int | 提示 Token 数 |
| `completion_tokens` | int | 补全 Token 数 |
| `total_tokens` | int | 总 Token 数 |
| `requests` | int | 请求次数 |
| `cost_usd` | float | 预估费用 (USD) |

**存储特点**:
- 按日期分桶存储，便于统计和归档
- 企业版可扩展为独立的统计表或时序数据库

---

### 2.3 技能池数据模型

#### 2.3.1 `skill.json` — 技能清单

**文件位置**: 
- 共享技能池: `~/.copaw/skill_pool/skill.json`
- 工作区技能: `~/.copaw/workspaces/{agent_id}/skill.json`

**数据结构**:
```json
{
  "skills": {
    "browser_cdp": {
      "name": "Browser CDP",
      "description": "通过 Chrome DevTools Protocol 控制浏览器",
      "version": "1.0.0",
      "enabled": true,
      "source": "builtin",
      "path": "browser_cdp",
      "last_modified": "2026-04-11T10:00:00Z"
    },
    "docx": {
      "name": "Document Processing",
      "description": "Word 文档读写和处理",
      "version": "1.0.0",
      "enabled": true,
      "source": "builtin",
      "path": "docx",
      "last_modified": "2026-04-11T10:00:00Z"
    }
  }
}
```

**字段说明**:

| 字段 | 类型 | 说明 |
|------|------|------|
| `skills` | object | 技能字典 (key=技能名) |
| `skills.{name}.name` | string | 技能显示名称 |
| `skills.{name}.description` | string | 技能描述 |
| `skills.{name}.version` | string | 技能版本 |
| `skills.{name}.enabled` | bool | 是否启用 |
| `skills.{name}.source` | string | 来源 (builtin/user/plugin) |
| `skills.{name}.path` | string | 技能目录相对路径 |
| `skills.{name}.last_modified` | string | 最后修改时间 |

---

#### 2.3.2 技能目录结构

每个技能是一个独立的目录，包含以下文件：

```
{skill_name}/
├── SKILL.md              # 技能描述和指令 (必需)
├── scripts/              # 技能脚本 (可选)
│   ├── main.py
│   └── utils.py
├── assets/               # 技能资源文件 (可选)
│   └── templates/
└── requirements.txt      # Python 依赖 (可选)
```

**`SKILL.md` 格式**:
```markdown
---
name: browser_cdp
description: Control browser via Chrome DevTools Protocol
version: 1.0.0
---

# Browser CDP Skill

This skill allows you to control a web browser using the Chrome DevTools Protocol.

## Available Commands

- `navigate <url>`: Navigate to a URL
- `click <selector>`: Click an element
- `screenshot`: Take a screenshot
...
```

**技能管理流程**:
1. 技能池 (`skill_pool/`) 存储所有可用技能
2. 工作区 (`workspaces/{id}/skills/`) 存储已激活的技能（符号链接或副本）
3. `skill.json` 作为运行时事实来源 (source of truth)
4. 通过 `SkillsManager` 进行技能的激活、停用和版本管理

---

### 2.4 记忆数据模型

#### 2.4.1 长期记忆 (Markdown)

**文件位置**: `~/.copaw/workspaces/{agent_id}/MEMORY.md`

**格式**:
```markdown
# Memory

## User Profile
- 用户偏好: 简洁回答
- 常用语言: 中文
- 工作时间: 9:00-18:00

## Key Facts
- 项目名称: CoPaw
- 技术栈: Python, FastAPI, React
- 部署方式: Docker

## Recent Context
- 上次对话: 2026-04-11
- 当前任务: 企业版开发
```

**特点**:
- 纯 Markdown 格式，便于人类阅读和编辑
- Agent 自动维护和更新
- 支持手动编辑

---

#### 2.4.2 每日记忆

**文件位置**: `~/.copaw/workspaces/{agent_id}/memory/{date}.md`

**格式**:
```markdown
# Memory: 2026-04-11

## Conversations
- 10:00 - 用户询问项目架构
- 14:30 - 协助编写数据库迁移脚本

## Key Learnings
- 用户偏好详细的注释
- 需要使用临时文件避免引号冲突

## Action Items
- [ ] 完成数据模型文档
- [x] 修复认证死循环
```

**特点**:
- 按日期分文件，便于归档和清理
- 自动压缩：保留最近 N 天（`MEMORY_COMPACT_KEEP_RECENT=3`）
- 压缩比例：保留 70% 内容（`MEMORY_COMPACT_RATIO=0.7`）

---

#### 2.4.3 ReMe 记忆数据库 (SQLite)

**文件位置**: `~/.copaw/workspaces/{agent_id}/.reme/` (内部结构)

**说明**:
- ReMe (Retrieval Memory) 使用 SQLite 存储向量嵌入和索引
- 支持语义搜索和上下文检索
- 自动进行记忆压缩和归档
- 独立于 PostgreSQL，每个工作空间有自己的 SQLite 数据库

**典型表结构** (由 ReMe 内部管理):
```sql
-- 记忆条目表
CREATE TABLE memories (
    id TEXT PRIMARY KEY,
    content TEXT NOT NULL,
    embedding BLOB,              -- 向量嵌入 (序列化)
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    metadata TEXT                -- JSON 元数据
);

-- 索引表
CREATE INDEX idx_memories_created ON memories(created_at);
```

---

### 2.5 配置文件数据模型

#### 2.5.1 `config.json` — 全局配置

**文件位置**: `~/.copaw/config.json` (可通过 `COPAW_CONFIG_FILE` 覆盖)

**数据结构**:
```json
{
  "version": "1.0.0",
  "agent": {
    "default_workspace": "default",
    "auto_start": true
  },
  "models": {
    "default_provider": "openai",
    "providers": {
      "openai": {
        "api_key": "sk-xxx",
        "base_url": "https://api.openai.com/v1"
      },
      "dashscope": {
        "api_key": "sk-xxx",
        "base_url": "https://dashscope.aliyuncs.com/compatible-mode/v1"
      }
    }
  },
  "channels": {
    "feishu": {
      "enabled": false
    },
    "dingtalk": {
      "enabled": false
    }
  },
  "enterprise": {
    "enabled": true,
    "database": {
      "url": "postgresql+asyncpg://user:pass@localhost:5432/copaw",
      "pool_size": 10
    },
    "redis": {
      "url": "redis://localhost:6379/0"
    }
  }
}
```

**字段说明**:

| 字段 | 类型 | 说明 |
|------|------|------|
| `version` | string | 配置格式版本 |
| `agent.default_workspace` | string | 默认工作空间 ID |
| `agent.auto_start` | bool | 是否自动启动 |
| `models.default_provider` | string | 默认模型提供商 |
| `models.providers` | object | 所有模型提供商配置 |
| `channels` | object | 通道配置 |
| `enterprise.enabled` | bool | 是否启用企业版 |
| `enterprise.database.url` | string | PostgreSQL 连接字符串 |
| `enterprise.redis.url` | string | Redis 连接字符串 |

---

### 2.6 认证数据模型

#### 2.6.1 `auth.json` — 个人版认证

**文件位置**: `~/.copaw.secret/auth.json` (权限: 0600)

**数据结构** (加密后):
```json
{
  "user": {
    "username": "admin",
    "password_hash": "a1b2c3d4e5f6...",
    "password_salt": "1234567890abcdef"
  },
  "jwt_secret": "encrypted:AES256:..."
}
```

**数据结构** (解密后):
```json
{
  "user": {
    "username": "admin",
    "password_hash": "a1b2c3d4e5f6...",
    "password_salt": "1234567890abcdef"
  },
  "jwt_secret": "random_hex_64_chars"
}
```

**字段说明**:

| 字段 | 类型 | 加密 | 说明 |
|------|------|------|------|
| `user.username` | string | ❌ | 用户名 |
| `user.password_hash` | string | ❌ | SHA-256 密码哈希 |
| `user.password_salt` | string | ❌ | 密码盐值 (16 bytes hex) |
| `jwt_secret` | string | ✅ | JWT 签名密钥 (AES-256 加密) |

**安全特性**:
- 密码使用加盐 SHA-256 哈希存储
- JWT 密钥使用 AES-256 加密存储
- 文件权限限制为 0600 (仅所有者可读写)
- 目录权限限制为 0700 (仅所有者可访问)
- 支持自动将明文密码迁移为加密格式

**认证流程**:
1. 检查 `COPAW_AUTH_ENABLED` 环境变量
2. 首次注册：用户通过 Web 界面创建账户
3. 登录：验证密码哈希，返回 JWT Token
4. Token 有效期：7 天 (`TOKEN_EXPIRY_SECONDS`)
5. Token 格式：`base64(payload).hmac_signature`

---

## 3. SQLite 数据模型

### 3.1 ReMe 记忆数据库

ReMe (Retrieval Memory) 是 CoPaw 的记忆管理系统，使用 SQLite 作为本地存储后端。

**数据库位置**: `~/.copaw/workspaces/{agent_id}/.reme/`

**核心功能**:
- **语义记忆**: 使用向量嵌入实现语义搜索
- **时间线记忆**: 按时间组织记忆条目
- **记忆压缩**: 自动压缩旧记忆，保留关键信息
- **上下文检索**: 根据当前对话检索相关记忆

**典型表结构**:

```sql
-- 记忆条目表
CREATE TABLE memories (
    id TEXT PRIMARY KEY,
    content TEXT NOT NULL,                    -- 记忆内容
    embedding BLOB,                           -- 向量嵌入 (numpy 序列化)
    embedding_model TEXT,                     -- 嵌入模型名称
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    metadata TEXT,                            -- JSON 元数据
    category TEXT,                            -- 记忆分类
    importance REAL DEFAULT 0.5,              -- 重要性评分 (0-1)
    access_count INTEGER DEFAULT 0,           -- 访问次数
    last_accessed_at TIMESTAMP                -- 最后访问时间
);

-- 索引
CREATE INDEX idx_memories_created ON memories(created_at);
CREATE INDEX idx_memories_category ON memories(category);
CREATE INDEX idx_memories_importance ON memories(importance);

-- 记忆标签表
CREATE TABLE memory_tags (
    memory_id TEXT REFERENCES memories(id),
    tag TEXT NOT NULL,
    PRIMARY KEY (memory_id, tag)
);

-- 会话上下文表
CREATE TABLE sessions (
    id TEXT PRIMARY KEY,
    started_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    ended_at TIMESTAMP,
    summary TEXT,                             -- 会话摘要
    message_count INTEGER DEFAULT 0
);

-- 会话-记忆关联表
CREATE TABLE session_memories (
    session_id TEXT REFERENCES sessions(id),
    memory_id TEXT REFERENCES memories(id),
    PRIMARY KEY (session_id, memory_id)
);
```

**使用场景**:
- Agent 对话时检索相关历史记忆
- 长期记忆压缩和归档
- 跨会话上下文保持
- 个性化用户画像构建

---

### 3.2 向量嵌入缓存

为了加速语义搜索，ReMe 会缓存向量嵌入：

**缓存策略**:
- 相同内容不重复计算嵌入
- 使用 SQLite 的 BLOB 字段存储序列化向量
- 支持多种嵌入模型（可配置）

**嵌入流程**:
```
用户输入 → 检查缓存 → 未命中 → 调用嵌入模型 → 存储缓存 → 语义搜索
                        ↓
                      命中 → 直接使用缓存
```

---

## 4. PostgreSQL 数据模型（企业版）

企业版使用 PostgreSQL 作为主数据库，支持多租户、RBAC、审计等企业级功能。

### 4.1 用户与组织管理

#### 4.1.1 `sys_tenants` — 租户表

**用途**: 多租户隔离的基础，每个租户代表一个独立的组织实体。

**表结构**:
```sql
CREATE TABLE sys_tenants (
    id            VARCHAR(36) PRIMARY KEY,              -- 租户 ID
    name          VARCHAR(100) NOT NULL,                -- 租户名称
    domain        VARCHAR(100) UNIQUE,                  -- 租户域名/标识
    is_active     BOOLEAN DEFAULT TRUE,                 -- 是否激活
    created_at    TIMESTAMPTZ DEFAULT NOW(),            -- 创建时间
    updated_at    TIMESTAMPTZ                           -- 更新时间
);

COMMENT ON TABLE sys_tenants IS '租户表 - 多租户隔离的基础单元';
```

**字段说明**:

| 字段 | 类型 | 约束 | 默认值 | 说明 |
|------|------|------|--------|------|
| `id` | VARCHAR(36) | PRIMARY KEY | - | 租户唯一标识 |
| `name` | VARCHAR(100) | NOT NULL | - | 租户显示名称 |
| `domain` | VARCHAR(100) | UNIQUE | NULL | 租户域名或标识符 |
| `is_active` | BOOLEAN | - | TRUE | 租户是否激活 |
| `created_at` | TIMESTAMPTZ | - | NOW() | 创建时间 |
| `updated_at` | TIMESTAMPTZ | - | NULL | 最后更新时间 |

**使用场景**:
- 创建默认租户 (`domain='default'`)
- 企业版初始化时自动创建
- 所有核心表通过 `tenant_id` 外键关联

---

#### 4.1.2 `sys_users` — 用户表

**用途**: 存储企业所有用户的基本信息、认证凭据和状态。

**表结构**:
```sql
CREATE TABLE sys_users (
    id                UUID PRIMARY KEY DEFAULT gen_random_uuid(),  -- 用户 ID
    tenant_id         VARCHAR(36) DEFAULT 'default-tenant',        -- 租户 ID
    username          VARCHAR(100) NOT NULL UNIQUE,                -- 用户名
    email             VARCHAR(255) UNIQUE,                         -- 邮箱
    password_hash     VARCHAR(255) NOT NULL,                       -- 密码哈希
    password_salt     VARCHAR(64) NOT NULL,                        -- 密码盐值
    display_name      VARCHAR(200),                                -- 显示名称
    department_id     UUID REFERENCES sys_departments(id) ON DELETE SET NULL, -- 部门 ID
    status            VARCHAR(20) NOT NULL DEFAULT 'active',       -- 账户状态
    mfa_enabled       BOOLEAN NOT NULL DEFAULT FALSE,              -- MFA 开关
    mfa_secret        VARCHAR(200),                                -- MFA 密钥 (加密)
    last_login_at     TIMESTAMPTZ,                                 -- 最后登录时间
    created_at        TIMESTAMPTZ NOT NULL DEFAULT NOW(),          -- 创建时间
    updated_at        TIMESTAMPTZ NOT NULL DEFAULT NOW()           -- 更新时间
);

CREATE INDEX ix_sys_users_username ON sys_users(username);
CREATE INDEX ix_sys_users_email ON sys_users(email);
CREATE INDEX ix_sys_users_tenant_id ON sys_users(tenant_id);

COMMENT ON TABLE sys_users IS '企业用户账户表';
```

**字段说明**:

| 字段 | 类型 | 约束 | 默认值 | 说明 |
|------|------|------|--------|------|
| `id` | UUID | PRIMARY KEY | gen_random_uuid() | 用户唯一标识 |
| `tenant_id` | VARCHAR(36) | - | 'default-tenant' | 所属租户 ID |
| `username` | VARCHAR(100) | NOT NULL, UNIQUE | - | 登录用户名 |
| `email` | VARCHAR(255) | UNIQUE | NULL | 电子邮箱 |
| `password_hash` | VARCHAR(255) | NOT NULL | - | bcrypt 密码哈希 |
| `password_salt` | VARCHAR(64) | NOT NULL | - | 密码盐值 |
| `display_name` | VARCHAR(200) | - | NULL | 显示名称 |
| `department_id` | UUID | FK → sys_departments | NULL | 所属部门 |
| `status` | VARCHAR(20) | NOT NULL | 'active' | 状态: active/inactive/locked |
| `mfa_enabled` | BOOLEAN | NOT NULL | FALSE | 是否启用 MFA |
| `mfa_secret` | VARCHAR(200) | - | NULL | MFA 密钥 (加密存储) |
| `last_login_at` | TIMESTAMPTZ | - | NULL | 最后登录时间 |
| `created_at` | TIMESTAMPTZ | NOT NULL | NOW() | 创建时间 |
| `updated_at` | TIMESTAMPTZ | NOT NULL | NOW() | 更新时间 |

**关系**:
- **一对多**: `sys_user_roles` (用户角色关联)
- **一对多**: `sys_user_group_members` (用户组成员关联)
- **一对多**: `sys_user_sessions` (用户会话)
- **一对多**: `sys_audit_logs` (审计日志)
- **多对一**: `sys_departments` (所属部门)

---

#### 4.1.3 `sys_departments` — 部门表

**用途**: 使用邻接表模式实现树形部门结构。

**表结构**:
```sql
CREATE TABLE sys_departments (
    id            UUID PRIMARY KEY DEFAULT gen_random_uuid(),  -- 部门 ID
    tenant_id     VARCHAR(36) DEFAULT 'default-tenant',        -- 租户 ID
    name          VARCHAR(200) NOT NULL,                       -- 部门名称
    parent_id     UUID REFERENCES sys_departments(id) ON DELETE SET NULL, -- 父部门 ID
    manager_id    UUID REFERENCES sys_users(id) ON DELETE SET NULL,       -- 部门负责人 ID
    level         INTEGER DEFAULT 0,                           -- 层级深度
    description   VARCHAR(500),                                -- 部门描述
    created_at    TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at    TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX ix_sys_departments_name ON sys_departments(name);
CREATE INDEX ix_sys_departments_tenant_id ON sys_departments(tenant_id);

COMMENT ON TABLE sys_departments IS '部门表 - 层级结构使用邻接表模式';
```

**字段说明**:

| 字段 | 类型 | 约束 | 默认值 | 说明 |
|------|------|------|--------|------|
| `id` | UUID | PRIMARY KEY | gen_random_uuid() | 部门唯一标识 |
| `tenant_id` | VARCHAR(36) | - | 'default-tenant' | 所属租户 ID |
| `name` | VARCHAR(200) | NOT NULL | - | 部门名称 |
| `parent_id` | UUID | FK → sys_departments | NULL | 父部门 ID (自引用) |
| `manager_id` | UUID | FK → sys_users | NULL | 部门负责人 ID |
| `level` | INTEGER | - | 0 | 部门层级深度 |
| `description` | VARCHAR(500) | - | NULL | 部门描述 |
| `created_at` | TIMESTAMPTZ | NOT NULL | NOW() | 创建时间 |
| `updated_at` | TIMESTAMPTZ | NOT NULL | NOW() | 更新时间 |

**递归查询示例** (获取部门树):
```sql
WITH RECURSIVE tree AS (
    SELECT id, parent_id, name, 0 AS depth
    FROM sys_departments
    WHERE id = :root_id
  UNION ALL
    SELECT d.id, d.parent_id, d.name, t.depth + 1
    FROM sys_departments d
    JOIN tree t ON d.parent_id = t.id
)
SELECT * FROM tree;
```

**关系**:
- **自引用**: `parent_id` → `sys_departments.id` (实现树形结构)
- **一对多**: `sys_users` (部门成员)
- **一对一**: `manager_id` → `sys_users` (部门负责人)

---

#### 4.1.4 `sys_user_groups` — 用户组表

**用途**: 灵活的跨部门用户分组。

**表结构**:
```sql
CREATE TABLE sys_user_groups (
    id            UUID PRIMARY KEY DEFAULT gen_random_uuid(),  -- 用户组 ID
    tenant_id     VARCHAR(36) DEFAULT 'default-tenant',        -- 租户 ID
    name          VARCHAR(200) NOT NULL UNIQUE,                -- 用户组名称
    description   VARCHAR(500),                                -- 描述
    department_id UUID REFERENCES sys_departments(id) ON DELETE SET NULL, -- 关联部门
    created_at    TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at    TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

COMMENT ON TABLE sys_user_groups IS '用户组表 - 灵活的跨部门分组';
```

**关系**:
- **多对多**: `sys_user_group_members` (组成员)
- **多对一**: `sys_departments` (关联部门)

---

#### 4.1.5 `sys_user_group_members` — 用户组成员关联表

**用途**: 实现用户和用户组的多对多关系。

**表结构**:
```sql
CREATE TABLE sys_user_group_members (
    user_id   UUID REFERENCES sys_users(id) ON DELETE CASCADE,    -- 用户 ID
    group_id  UUID REFERENCES sys_user_groups(id) ON DELETE CASCADE, -- 用户组 ID
    joined_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),                 -- 加入时间
    PRIMARY KEY (user_id, group_id)
);

COMMENT ON TABLE sys_user_group_members IS '用户组成员关联表';
```

---

### 4.2 权限与安全体系

#### 4.2.1 `sys_roles` — 角色表

**用途**: 定义系统中的角色，用于 RBAC 权限管理。

**表结构**:
```sql
CREATE TABLE sys_roles (
    id               UUID PRIMARY KEY DEFAULT gen_random_uuid(),  -- 角色 ID
    tenant_id        VARCHAR(36) DEFAULT 'default-tenant',        -- 租户 ID
    name             VARCHAR(100) NOT NULL,                       -- 角色名称
    display_name     VARCHAR(200) NOT NULL,                       -- 显示名称
    is_system_role   BOOLEAN NOT NULL DEFAULT FALSE,              -- 是否系统角色
    created_at       TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at       TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX ix_sys_roles_name ON sys_roles(name);
CREATE INDEX ix_sys_roles_tenant_id ON sys_roles(tenant_id);

COMMENT ON TABLE sys_roles IS '角色表 - RBAC 权限管理';
```

**字段说明**:

| 字段 | 类型 | 约束 | 默认值 | 说明 |
|------|------|------|--------|------|
| `id` | UUID | PRIMARY KEY | gen_random_uuid() | 角色唯一标识 |
| `tenant_id` | VARCHAR(36) | - | 'default-tenant' | 所属租户 ID |
| `name` | VARCHAR(100) | NOT NULL | - | 角色名称 (唯一) |
| `display_name` | VARCHAR(200) | NOT NULL | - | 显示名称 |
| `is_system_role` | BOOLEAN | NOT NULL | FALSE | 是否系统内置角色 |
| `created_at` | TIMESTAMPTZ | NOT NULL | NOW() | 创建时间 |
| `updated_at` | TIMESTAMPTZ | NOT NULL | NOW() | 更新时间 |

**预定义角色**:
- **Super Admin**: 超级管理员，管理所有租户
- **Tenant Admin**: 租户管理员，管理单个租户
- **Developer**: 开发者，创建和发布 Agent/Skill
- **End User**: 普通用户，使用授权的 Agent/Skill

---

#### 4.2.2 `sys_permissions` — 权限表

**用途**: 定义系统中的所有权限点。

**表结构**:
```sql
CREATE TABLE sys_permissions (
    id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),  -- 权限 ID
    tenant_id   VARCHAR(36) DEFAULT 'default-tenant',        -- 租户 ID
    name        VARCHAR(100) NOT NULL,                       -- 权限名称
    resource    VARCHAR(100) NOT NULL,                       -- 资源类型
    action      VARCHAR(100) NOT NULL,                       -- 操作类型
    description VARCHAR(500),                                -- 描述
    created_at  TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at  TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

COMMENT ON TABLE sys_permissions IS '权限表 - 细粒度权限定义';
```

**权限点示例**:
- `agent:create` - 创建 Agent
- `agent:edit` - 编辑 Agent
- `agent:delete` - 删除 Agent
- `agent:share` - 共享 Agent
- `skill:install` - 安装 Skill
- `skill:develop` - 开发新 Skill
- `skill:publish` - 发布 Skill
- `workflow:create` - 创建工作流
- `workflow:execute` - 执行工作流
- `audit:view` - 查看审计日志

---

#### 4.2.3 `sys_role_permissions` — 角色权限关联表

**用途**: 实现角色和权限的多对多关系。

**表结构**:
```sql
CREATE TABLE sys_role_permissions (
    role_id       UUID REFERENCES sys_roles(id) ON DELETE CASCADE,        -- 角色 ID
    permission_id UUID REFERENCES sys_permissions(id) ON DELETE CASCADE,  -- 权限 ID
    PRIMARY KEY (role_id, permission_id)
);

COMMENT ON TABLE sys_role_permissions IS '角色权限关联表';
```

---

#### 4.2.4 `sys_user_roles` — 用户角色关联表

**用途**: 实现用户和角色的多对多关系。

**表结构**:
```sql
CREATE TABLE sys_user_roles (
    user_id     UUID REFERENCES sys_users(id) ON DELETE CASCADE,        -- 用户 ID
    role_id     UUID REFERENCES sys_roles(id) ON DELETE CASCADE,        -- 角色 ID
    assigned_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),                     -- 分配时间
    assigned_by UUID REFERENCES sys_users(id) ON DELETE SET NULL,       -- 分配人 ID
    PRIMARY KEY (user_id, role_id)
);

COMMENT ON TABLE sys_user_roles IS '用户角色关联表';
```

---

### 4.3 会话与令牌管理

#### 4.3.1 `sys_user_sessions` — 用户会话表

**用途**: 记录活跃的用户会话，支持会话管理和撤销。

**表结构**:
```sql
CREATE TABLE sys_user_sessions (
    id                UUID PRIMARY KEY DEFAULT gen_random_uuid(),  -- 会话 ID
    tenant_id         VARCHAR(36) DEFAULT 'default-tenant',        -- 租户 ID
    user_id           UUID NOT NULL REFERENCES sys_users(id) ON DELETE CASCADE, -- 用户 ID
    access_token_jti  VARCHAR(64) NOT NULL UNIQUE,                 -- JWT ID
    ip_address        VARCHAR(45),                                 -- 客户端 IP
    user_agent        VARCHAR(500),                                -- User-Agent
    created_at        TIMESTAMPTZ NOT NULL,                        -- 创建时间
    expires_at        TIMESTAMPTZ NOT NULL,                        -- 过期时间
    revoked           BOOLEAN NOT NULL DEFAULT FALSE,              -- 是否已撤销
    revoked_at        TIMESTAMPTZ                                  -- 撤销时间
);

CREATE INDEX ix_sys_user_sessions_user_id ON sys_user_sessions(user_id);
CREATE INDEX ix_sys_user_sessions_jti ON sys_user_sessions(access_token_jti);
CREATE INDEX ix_sys_user_sessions_expires_at ON sys_user_sessions(expires_at);
CREATE INDEX ix_sys_user_sessions_tenant_id ON sys_user_sessions(tenant_id);

COMMENT ON TABLE sys_user_sessions IS '用户会话表 - Redis 中也有镜像用于快速查找';
```

**字段说明**:

| 字段 | 类型 | 约束 | 默认值 | 说明 |
|------|------|------|--------|------|
| `id` | UUID | PRIMARY KEY | gen_random_uuid() | 会话唯一标识 |
| `tenant_id` | VARCHAR(36) | - | 'default-tenant' | 所属租户 ID |
| `user_id` | UUID | NOT NULL, FK → sys_users | - | 用户 ID |
| `access_token_jti` | VARCHAR(64) | NOT NULL, UNIQUE | - | JWT Token ID (用于撤销) |
| `ip_address` | VARCHAR(45) | - | NULL | 客户端 IP 地址 |
| `user_agent` | VARCHAR(500) | - | NULL | 客户端 User-Agent |
| `created_at` | TIMESTAMPTZ | NOT NULL | - | 会话创建时间 |
| `expires_at` | TIMESTAMPTZ | NOT NULL | - | 会话过期时间 |
| `revoked` | BOOLEAN | NOT NULL | FALSE | 是否已撤销 |
| `revoked_at` | TIMESTAMPTZ | - | NULL | 撤销时间 |

**关系**:
- **多对一**: `sys_users` (用户)
- **一对多**: `sys_refresh_tokens` (刷新令牌)

**使用场景**:
- 用户登录时创建新会话
- 用户登出时撤销会话
- 管理员强制用户下线
- 定期清理过期会话

---

#### 4.3.2 `sys_refresh_tokens` — 刷新令牌表

**用途**: 存储刷新令牌（一次性使用，哈希存储）。

**表结构**:
```sql
CREATE TABLE sys_refresh_tokens (
    id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),  -- 令牌 ID
    tenant_id   VARCHAR(36) DEFAULT 'default-tenant',        -- 租户 ID
    session_id  UUID NOT NULL REFERENCES sys_user_sessions(id) ON DELETE CASCADE, -- 会话 ID
    token_hash  VARCHAR(128) NOT NULL UNIQUE,                -- 令牌哈希
    created_at  TIMESTAMPTZ NOT NULL,                        -- 创建时间
    expires_at  TIMESTAMPTZ NOT NULL,                        -- 过期时间
    used        BOOLEAN NOT NULL DEFAULT FALSE,              -- 是否已使用
    used_at     TIMESTAMPTZ                                  -- 使用时间
);

CREATE INDEX ix_sys_refresh_tokens_session_id ON sys_refresh_tokens(session_id);
CREATE INDEX ix_sys_refresh_tokens_tenant_id ON sys_refresh_tokens(tenant_id);

COMMENT ON TABLE sys_refresh_tokens IS '刷新令牌表 - 一次性使用，哈希存储';
```

**字段说明**:

| 字段 | 类型 | 约束 | 默认值 | 说明 |
|------|------|------|--------|------|
| `id` | UUID | PRIMARY KEY | gen_random_uuid() | 令牌唯一标识 |
| `tenant_id` | VARCHAR(36) | - | 'default-tenant' | 所属租户 ID |
| `session_id` | UUID | NOT NULL, FK → sys_user_sessions | - | 所属会话 ID |
| `token_hash` | VARCHAR(128) | NOT NULL, UNIQUE | - | 令牌哈希值 |
| `created_at` | TIMESTAMPTZ | NOT NULL | - | 创建时间 |
| `expires_at` | TIMESTAMPTZ | NOT NULL | - | 过期时间 |
| `used` | BOOLEAN | NOT NULL | FALSE | 是否已使用 |
| `used_at` | TIMESTAMPTZ | - | NULL | 使用时间 |

**安全特性**:
- 令牌哈希存储，不存储明文
- 一次性使用，使用后立即失效
- 与会话关联，会话撤销时令牌自动失效

---

### 4.4 工作空间管理

#### 4.4.1 `sys_workspaces` — 工作空间表

**用途**: 管理企业中的工作空间，对应个人版的 `workspaces/` 目录。

**表结构**:
```sql
CREATE TABLE sys_workspaces (
    id            UUID PRIMARY KEY DEFAULT gen_random_uuid(),  -- 工作空间 ID
    tenant_id     VARCHAR(36) DEFAULT 'default-tenant',        -- 租户 ID
    name          VARCHAR(200) NOT NULL,                       -- 工作空间名称
    description   TEXT,                                        -- 描述
    is_default    BOOLEAN NOT NULL DEFAULT FALSE,              -- 是否默认工作空间
    owner_id      UUID REFERENCES sys_users(id) ON DELETE SET NULL, -- 所有者 ID
    created_at    TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at    TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX ix_sys_workspaces_tenant_id ON sys_workspaces(tenant_id);
CREATE INDEX ix_sys_workspaces_owner_id ON sys_workspaces(owner_id);

COMMENT ON TABLE sys_workspaces IS '工作空间表 - 对应个人版的 workspaces/ 目录';
```

**字段说明**:

| 字段 | 类型 | 约束 | 默认值 | 说明 |
|------|------|------|--------|------|
| `id` | UUID | PRIMARY KEY | gen_random_uuid() | 工作空间唯一标识 |
| `tenant_id` | VARCHAR(36) | - | 'default-tenant' | 所属租户 ID |
| `name` | VARCHAR(200) | NOT NULL | - | 工作空间名称 |
| `description` | TEXT | - | NULL | 工作空间描述 |
| `is_default` | BOOLEAN | NOT NULL | FALSE | 是否为默认工作空间 |
| `owner_id` | UUID | FK → sys_users | NULL | 工作空间所有者 |
| `created_at` | TIMESTAMPTZ | NOT NULL | NOW() | 创建时间 |
| `updated_at` | TIMESTAMPTZ | NOT NULL | NOW() | 更新时间 |

**关系**:
- **多对多**: `sys_workspace_members` (工作空间成员)
- **多对多**: `sys_workspace_agents` (工作空间 Agent)
- **多对一**: `sys_users` (所有者)

---

#### 4.4.2 `sys_workspace_members` — 工作空间成员表

**用途**: 实现用户和工作空间的多对多关系。

**表结构**:
```sql
CREATE TABLE sys_workspace_members (
    workspace_id UUID REFERENCES sys_workspaces(id) ON DELETE CASCADE, -- 工作空间 ID
    user_id      UUID REFERENCES sys_users(id) ON DELETE CASCADE,      -- 用户 ID
    role         VARCHAR(50) NOT NULL DEFAULT 'viewer',                -- 成员角色
    created_at   TIMESTAMPTZ NOT NULL DEFAULT NOW(),                   -- 加入时间
    PRIMARY KEY (workspace_id, user_id)
);

COMMENT ON TABLE sys_workspace_members IS '工作空间成员表';
```

**成员角色**:
- `owner`: 所有者
- `admin`: 管理员
- `editor`: 编辑者
- `viewer`: 查看者

---

#### 4.4.3 `sys_workspace_agents` — 工作空间 Agent 关联表

**用途**: 记录工作空间中包含的 Agent。

**表结构**:
```sql
CREATE TABLE sys_workspace_agents (
    workspace_id UUID REFERENCES sys_workspaces(id) ON DELETE CASCADE, -- 工作空间 ID
    agent_id     VARCHAR(100) NOT NULL,                                -- Agent ID
    visibility   VARCHAR(50) NOT NULL DEFAULT 'PRIVATE',               -- 可见性
    PRIMARY KEY (workspace_id, agent_id)
);

COMMENT ON TABLE sys_workspace_agents IS '工作空间 Agent 关联表';
```

**可见性**:
- `PRIVATE`: 私有
- `WORKSPACE`: 工作空间可见
- `TENANT`: 租户可见
- `PUBLIC`: 公开

---

### 4.5 AI 任务与评论

#### 4.5.1 `ai_tasks` — 任务表

**用途**: 企业任务管理，可分配给用户、用户组或部门。

**表结构**:
```sql
CREATE TABLE ai_tasks (
    id                UUID PRIMARY KEY DEFAULT gen_random_uuid(),  -- 任务 ID
    tenant_id         VARCHAR(36) DEFAULT 'default-tenant',        -- 租户 ID
    title             VARCHAR(500) NOT NULL,                       -- 任务标题
    description       TEXT,                                        -- 任务描述
    status            VARCHAR(20) NOT NULL DEFAULT 'pending',      -- 任务状态
    priority          VARCHAR(10) NOT NULL DEFAULT 'medium',       -- 优先级
    creator_id        UUID REFERENCES sys_users(id) ON DELETE SET NULL, -- 创建者 ID
    assignee_id       UUID REFERENCES sys_users(id) ON DELETE SET NULL,   -- 被分配用户 ID
    assignee_group_id UUID REFERENCES sys_user_groups(id) ON DELETE SET NULL, -- 被分配用户组 ID
    department_id     UUID REFERENCES sys_departments(id) ON DELETE SET NULL, -- 所属部门 ID
    due_date          TIMESTAMPTZ,                                 -- 截止日期
    completed_at      TIMESTAMPTZ,                                 -- 完成时间
    parent_task_id    UUID REFERENCES ai_tasks(id) ON DELETE SET NULL, -- 父任务 ID
    workflow_id       UUID REFERENCES ai_workflows(id) ON DELETE SET NULL, -- 关联工作流 ID
    metadata          JSONB,                                       -- 任务元数据
    created_at        TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at        TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX ix_ai_tasks_status ON ai_tasks(status);
CREATE INDEX ix_ai_tasks_tenant_id ON ai_tasks(tenant_id);
CREATE INDEX ix_ai_tasks_assignee_id ON ai_tasks(assignee_id);

COMMENT ON TABLE ai_tasks IS '企业任务表 - 可分配给用户、用户组或部门';
```

**字段说明**:

| 字段 | 类型 | 约束 | 默认值 | 说明 |
|------|------|------|--------|------|
| `id` | UUID | PRIMARY KEY | gen_random_uuid() | 任务唯一标识 |
| `tenant_id` | VARCHAR(36) | - | 'default-tenant' | 所属租户 ID |
| `title` | VARCHAR(500) | NOT NULL | - | 任务标题 |
| `description` | TEXT | - | NULL | 任务详细描述 |
| `status` | VARCHAR(20) | NOT NULL | 'pending' | 状态: pending/in_progress/completed/blocked/cancelled |
| `priority` | VARCHAR(10) | NOT NULL | 'medium' | 优先级: high/medium/low |
| `creator_id` | UUID | FK → sys_users | NULL | 创建者 ID |
| `assignee_id` | UUID | FK → sys_users | NULL | 被分配用户 ID |
| `assignee_group_id` | UUID | FK → sys_user_groups | NULL | 被分配用户组 ID |
| `department_id` | UUID | FK → sys_departments | NULL | 所属部门 ID |
| `due_date` | TIMESTAMPTZ | - | NULL | 截止日期 |
| `completed_at` | TIMESTAMPTZ | - | NULL | 完成时间 |
| `parent_task_id` | UUID | FK → ai_tasks | NULL | 父任务 ID (支持子任务) |
| `workflow_id` | UUID | FK → ai_workflows | NULL | 关联工作流 ID |
| `metadata` | JSONB | - | NULL | 任务元数据 (JSON) |
| `created_at` | TIMESTAMPTZ | NOT NULL | NOW() | 创建时间 |
| `updated_at` | TIMESTAMPTZ | NOT NULL | NOW() | 更新时间 |

**关系**:
- **一对多**: `ai_task_comments` (任务评论)
- **自引用**: `parent_task_id` → `ai_tasks.id` (实现子任务)
- **多对一**: `sys_users` (创建者/被分配者)
- **多对一**: `ai_workflows` (关联工作流)

---

#### 4.5.2 `ai_task_comments` — 任务评论表

**用途**: 存储对任务的评论和讨论。

**表结构**:
```sql
CREATE TABLE ai_task_comments (
    id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),  -- 评论 ID
    tenant_id   VARCHAR(36) DEFAULT 'default-tenant',        -- 租户 ID
    task_id     UUID NOT NULL REFERENCES ai_tasks(id) ON DELETE CASCADE, -- 任务 ID
    author_id   UUID REFERENCES sys_users(id) ON DELETE SET NULL,        -- 作者 ID
    content     TEXT NOT NULL,                                     -- 评论内容
    created_at  TIMESTAMPTZ NOT NULL DEFAULT NOW()                 -- 创建时间
);

CREATE INDEX ix_ai_task_comments_task_id ON ai_task_comments(task_id);
CREATE INDEX ix_ai_task_comments_tenant_id ON ai_task_comments(tenant_id);

COMMENT ON TABLE ai_task_comments IS '任务评论表';
```

---

### 4.6 工作流管理（Dify 集成）

#### 4.6.1 `ai_workflows` — 工作流定义表

**用途**: 存储 DAG 工作流定义，支持 Dify 工作流和 CoPaw 原生工作流。

**表结构**:
```sql
CREATE TABLE ai_workflows (
    id            UUID PRIMARY KEY DEFAULT gen_random_uuid(),  -- 工作流 ID
    tenant_id     VARCHAR(36) DEFAULT 'default-tenant',        -- 租户 ID
    name          VARCHAR(200) NOT NULL,                       -- 工作流名称
    description   TEXT,                                        -- 工作流描述
    category      VARCHAR(100),                                -- 工作流类别
    definition    JSONB NOT NULL DEFAULT '{}',                 -- DAG 定义
    version       INTEGER NOT NULL DEFAULT 1,                  -- 版本号
    status        VARCHAR(20) NOT NULL DEFAULT 'draft',        -- 状态
    creator_id    UUID REFERENCES sys_users(id) ON DELETE SET NULL, -- 创建者 ID
    created_at    TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at    TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX ix_ai_workflows_name ON ai_workflows(name);
CREATE INDEX ix_ai_workflows_category ON ai_workflows(category);
CREATE INDEX ix_ai_workflows_tenant_id ON ai_workflows(tenant_id);

COMMENT ON TABLE ai_workflows IS '工作流定义表 - 支持 Dify 和 CoPaw 原生工作流';
```

**字段说明**:

| 字段 | 类型 | 约束 | 默认值 | 说明 |
|------|------|------|--------|------|
| `id` | UUID | PRIMARY KEY | gen_random_uuid() | 工作流唯一标识 |
| `tenant_id` | VARCHAR(36) | - | 'default-tenant' | 所属租户 ID |
| `name` | VARCHAR(200) | NOT NULL | - | 工作流名称 |
| `description` | TEXT | - | NULL | 工作流描述 |
| `category` | VARCHAR(100) | - | NULL | 类别: dify/dify_chatflow/dify_agent/internal |
| `definition` | JSONB | NOT NULL | '{}' | DAG 定义 (节点和边的 JSON 结构) |
| `version` | INTEGER | NOT NULL | 1 | 版本号 |
| `status` | VARCHAR(20) | NOT NULL | 'draft' | 状态: draft/active/archived |
| `creator_id` | UUID | FK → sys_users | NULL | 创建者 ID |
| `created_at` | TIMESTAMPTZ | NOT NULL | NOW() | 创建时间 |
| `updated_at` | TIMESTAMPTZ | NOT NULL | NOW() | 更新时间 |

**工作流类别**:
- `dify`: Dify 标准工作流
- `dify_chatflow`: Dify 对话工作流
- `dify_agent`: Dify Agent 工作流
- `internal`: CoPaw 原生 DAG 工作流

**关系**:
- **一对多**: `ai_workflow_executions` (工作流执行记录)
- **多对一**: `sys_users` (创建者)

---

#### 4.6.2 `ai_workflow_executions` — 工作流执行表

**用途**: 记录工作流的单次执行实例。

**表结构**:
```sql
CREATE TABLE ai_workflow_executions (
    id            UUID PRIMARY KEY DEFAULT gen_random_uuid(),  -- 执行 ID
    tenant_id     VARCHAR(36) DEFAULT 'default-tenant',        -- 租户 ID
    workflow_id   UUID NOT NULL REFERENCES ai_workflows(id) ON DELETE CASCADE, -- 工作流 ID
    triggered_by  UUID REFERENCES sys_users(id) ON DELETE SET NULL, -- 触发者 ID
    status        VARCHAR(20) NOT NULL DEFAULT 'pending',      -- 执行状态
    started_at    TIMESTAMPTZ,                                 -- 开始时间
    completed_at  TIMESTAMPTZ,                                 -- 完成时间
    created_at    TIMESTAMPTZ NOT NULL DEFAULT NOW(),          -- 创建时间
    input_data    JSONB,                                       -- 输入数据
    output_data   JSONB,                                       -- 输出数据
    error_message TEXT,                                        -- 错误信息
    run_metadata  JSONB                                        -- 运行元数据
);

CREATE INDEX ix_ai_workflow_executions_workflow_id ON ai_workflow_executions(workflow_id);
CREATE INDEX ix_ai_workflow_executions_status ON ai_workflow_executions(status);
CREATE INDEX ix_ai_workflow_executions_tenant_id ON ai_workflow_executions(tenant_id);

COMMENT ON TABLE ai_workflow_executions IS '工作流执行记录表';
```

**执行状态**:
- `pending`: 等待执行
- `running`: 运行中
- `paused`: 已暂停
- `completed`: 已完成
- `failed`: 失败
- `cancelled`: 已取消

---

#### 4.6.3 `ai_dify_connectors` — Dify 连接器表

**用途**: 存储与 Dify AI 平台的连接配置。

**表结构**:
```sql
CREATE TABLE ai_dify_connectors (
    id          VARCHAR(36) PRIMARY KEY,                         -- 连接器 ID
    tenant_id   VARCHAR(36) DEFAULT 'default-tenant',            -- 租户 ID
    name        VARCHAR(100) NOT NULL,                           -- 连接器名称
    description VARCHAR(255),                                    -- 描述
    api_url     VARCHAR(255) NOT NULL,                           -- API 地址
    api_key     VARCHAR(255) NOT NULL,                           -- API 密钥
    is_active   BOOLEAN DEFAULT TRUE,                            -- 是否激活
    created_at  TIMESTAMPTZ DEFAULT NOW(),                       -- 创建时间
    updated_at  TIMESTAMPTZ                                      -- 更新时间
);

COMMENT ON TABLE ai_dify_connectors IS 'Dify AI 平台连接器表';
```

---

### 4.7 审计日志（ISO 27001 合规）

#### 4.7.1 `sys_audit_logs` — 审计日志表

**用途**: 只追加的安全/操作审计日志，符合 ISO 27001 标准。

**表结构**:
```sql
CREATE TABLE sys_audit_logs (
    id            BIGINT PRIMARY KEY GENERATED ALWAYS AS IDENTITY, -- 日志 ID (自增)
    tenant_id     VARCHAR(36) DEFAULT 'default-tenant',            -- 租户 ID
    timestamp     TIMESTAMPTZ NOT NULL DEFAULT NOW(),              -- 时间戳
    user_id       UUID REFERENCES sys_users(id) ON DELETE SET NULL, -- 用户 ID
    user_role     VARCHAR(100),                                    -- 用户角色
    action_type   VARCHAR(100) NOT NULL,                           -- 操作类型
    resource_type VARCHAR(100) NOT NULL,                           -- 资源类型
    resource_id   VARCHAR(200),                                    -- 资源 ID
    action_result VARCHAR(20),                                     -- 操作结果
    client_ip     INET,                                            -- 客户端 IP
    client_device JSONB,                                           -- 客户端设备信息
    context       JSONB,                                           -- 上下文
    data_before   JSONB,                                           -- 变更前数据
    data_after    JSONB,                                           -- 变更后数据
    is_sensitive  BOOLEAN NOT NULL DEFAULT FALSE                   -- 是否敏感操作
);

CREATE INDEX idx_sys_audit_logs_timestamp ON sys_audit_logs(timestamp);
CREATE INDEX idx_sys_audit_logs_user_id ON sys_audit_logs(user_id);
CREATE INDEX idx_sys_audit_logs_action_type ON sys_audit_logs(action_type);
CREATE INDEX idx_sys_audit_logs_resource_type ON sys_audit_logs(resource_type);
CREATE INDEX idx_sys_audit_logs_tenant_id ON sys_audit_logs(tenant_id);

COMMENT ON TABLE sys_audit_logs IS '审计日志表 - 只追加的安全/操作审计日志,符合 ISO 27001 标准';
```

**字段说明**:

| 字段 | 类型 | 约束 | 默认值 | 说明 |
|------|------|------|--------|------|
| `id` | BIGINT | PRIMARY KEY, AUTO | - | 日志 ID (自增) |
| `tenant_id` | VARCHAR(36) | - | 'default-tenant' | 所属租户 ID |
| `timestamp` | TIMESTAMPTZ | NOT NULL | NOW() | 操作时间戳 |
| `user_id` | UUID | FK → sys_users | NULL | 操作用户 ID |
| `user_role` | VARCHAR(100) | - | NULL | 用户角色 |
| `action_type` | VARCHAR(100) | NOT NULL | - | 操作类型 (login/logout/create/update/delete) |
| `resource_type` | VARCHAR(100) | NOT NULL | - | 资源类型 (user/role/agent/workflow) |
| `resource_id` | VARCHAR(200) | - | NULL | 资源 ID |
| `action_result` | VARCHAR(20) | - | NULL | 结果: success/failure |
| `client_ip` | INET | - | NULL | 客户端 IP 地址 |
| `client_device` | JSONB | - | NULL | 客户端设备信息 |
| `context` | JSONB | - | NULL | 上下文 (session_id, task_id, agent_id 等) |
| `data_before` | JSONB | - | NULL | 变更前数据 (敏感操作) |
| `data_after` | JSONB | - | NULL | 变更后数据 (敏感操作) |
| `is_sensitive` | BOOLEAN | NOT NULL | FALSE | 是否敏感操作 |

**ISO 27001 合规要求**:
- **Who**: `user_id`, `user_role` - 谁操作的
- **What**: `action_type`, `resource_type`, `resource_id` - 做了什么
- **When**: `timestamp` - 什么时候
- **Result**: `action_result` - 结果如何
- **Where**: `client_ip`, `client_device` - 从哪里
- **Context**: `context` - 上下文
- **Diff**: `data_before`/`data_after` - 数据变更

**操作类型示例**:
- `auth:login`, `auth:logout`, `auth:password_change`
- `user:create`, `user:update`, `user:delete`
- `role:assign`, `role:revoke`
- `agent:create`, `agent:deploy`, `agent:delete`
- `workflow:execute`, `workflow:update`
- `permission:grant`, `permission:revoke`

---

### 4.8 数据安全与合规（DLP）

#### 4.8.1 `sys_dlp_rules` — DLP 规则表

**用途**: 管理员可配置的数据泄漏防护 (DLP) 检测规则。

**表结构**:
```sql
CREATE TABLE sys_dlp_rules (
    id            UUID PRIMARY KEY DEFAULT gen_random_uuid(),  -- 规则 ID
    tenant_id     VARCHAR(36) DEFAULT 'default-tenant',        -- 租户 ID
    rule_name     VARCHAR(100) NOT NULL UNIQUE,                -- 规则名称
    description   VARCHAR(500),                                -- 描述
    pattern_regex TEXT NOT NULL,                               -- 正则表达式
    action        VARCHAR(20) NOT NULL DEFAULT 'alert',        -- 执行动作
    is_active     BOOLEAN NOT NULL DEFAULT TRUE,               -- 是否激活
    is_builtin    BOOLEAN NOT NULL DEFAULT FALSE,              -- 是否内置规则
    created_at    TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at    TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

COMMENT ON TABLE sys_dlp_rules IS 'DLP 数据泄漏防护规则表';
```

**字段说明**:

| 字段 | 类型 | 约束 | 默认值 | 说明 |
|------|------|------|--------|------|
| `id` | UUID | PRIMARY KEY | gen_random_uuid() | 规则唯一标识 |
| `tenant_id` | VARCHAR(36) | - | 'default-tenant' | 所属租户 ID |
| `rule_name` | VARCHAR(100) | NOT NULL, UNIQUE | - | 规则名称 |
| `description` | VARCHAR(500) | - | NULL | 规则描述 |
| `pattern_regex` | TEXT | NOT NULL | - | 正则表达式模式 |
| `action` | VARCHAR(20) | NOT NULL | 'alert' | 动作: mask/alert/block |
| `is_active` | BOOLEAN | NOT NULL | TRUE | 是否激活 |
| `is_builtin` | BOOLEAN | NOT NULL | FALSE | 是否内置规则 (内置不可删除) |
| `created_at` | TIMESTAMPTZ | NOT NULL | NOW() | 创建时间 |
| `updated_at` | TIMESTAMPTZ | NOT NULL | NOW() | 更新时间 |

**DLP 动作**:
- `mask`: 脱敏 (用 * 替换敏感数据)
- `alert`: 告警 (记录并通知管理员)
- `block`: 阻断 (阻止操作并返回警告)

**内置规则示例**:
- 身份证号: `\b\d{17}[\dXx]\b`
- 手机号: `\b1[3-9]\d{9}\b`
- 银行卡号: `\b\d{16,19}\b`
- 邮箱地址: `\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b`

---

#### 4.8.2 `sys_dlp_events` — DLP 事件表

**用途**: 记录 DLP 策略违规/匹配事件。

**表结构**:
```sql
CREATE TABLE sys_dlp_events (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),  -- 事件 ID
    tenant_id       VARCHAR(36) DEFAULT 'default-tenant',        -- 租户 ID
    rule_name       VARCHAR(100) NOT NULL,                       -- 触发的规则名称
    action_taken    VARCHAR(20) NOT NULL,                        -- 采取的动作
    content_summary TEXT,                                        -- 内容摘要 (截断/编辑)
    user_id         UUID,                                        -- 触发用户 ID
    context_path    VARCHAR(200),                                -- 上下文路径
    triggered_at    TIMESTAMPTZ NOT NULL DEFAULT NOW()           -- 触发时间
);

CREATE INDEX ix_sys_dlp_events_rule_name ON sys_dlp_events(rule_name);
CREATE INDEX ix_sys_dlp_events_user_id ON sys_dlp_events(user_id);
CREATE INDEX ix_sys_dlp_events_triggered_at ON sys_dlp_events(triggered_at);
CREATE INDEX ix_sys_dlp_events_tenant_id ON sys_dlp_events(tenant_id);

COMMENT ON TABLE sys_dlp_events IS 'DLP 数据泄漏防护事件表';
```

**安全特性**:
- `content_summary` 仅存储截断/编辑后的摘要
- **绝不存储完整敏感值**
- 支持按用户、规则、时间查询

---

### 4.9 告警管理

#### 4.9.1 `sys_alert_rules` — 告警规则表

**用途**: 定义告警规则和触发条件。

**表结构**:
```sql
CREATE TABLE sys_alert_rules (
    id            UUID PRIMARY KEY DEFAULT gen_random_uuid(),  -- 规则 ID
    tenant_id     VARCHAR(36) DEFAULT 'default-tenant',        -- 租户 ID
    name          VARCHAR(200) NOT NULL,                       -- 规则名称
    description   TEXT,                                        -- 描述
    condition     JSONB NOT NULL,                              -- 触发条件
    severity      VARCHAR(20) NOT NULL DEFAULT 'medium',       -- 严重程度
    enabled       BOOLEAN NOT NULL DEFAULT TRUE,               -- 是否启用
    notify_users  UUID[],                                      -- 通知用户列表
    notify_channels VARCHAR(100)[],                            -- 通知渠道
    created_by    UUID REFERENCES sys_users(id) ON DELETE SET NULL, -- 创建者
    created_at    TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at    TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

COMMENT ON TABLE sys_alert_rules IS '告警规则表';
```

---

#### 4.9.2 `sys_alert_events` — 告警事件表

**用途**: 记录触发的告警事件。

**表结构**:
```sql
CREATE TABLE sys_alert_events (
    id            UUID PRIMARY KEY DEFAULT gen_random_uuid(),  -- 事件 ID
    tenant_id     VARCHAR(36) DEFAULT 'default-tenant',        -- 租户 ID
    rule_id       UUID REFERENCES sys_alert_rules(id) ON DELETE SET NULL, -- 规则 ID
    severity      VARCHAR(20) NOT NULL,                        -- 严重程度
    message       TEXT NOT NULL,                               -- 告警消息
    context       JSONB,                                       -- 上下文
    acknowledged  BOOLEAN NOT NULL DEFAULT FALSE,              -- 是否已确认
    acknowledged_by UUID REFERENCES sys_users(id) ON DELETE SET NULL, -- 确认人
    acknowledged_at TIMESTAMPTZ,                               -- 确认时间
    triggered_at  TIMESTAMPTZ NOT NULL DEFAULT NOW()           -- 触发时间
);

COMMENT ON TABLE sys_alert_events IS '告警事件表';
```

---

### 4.10 租户管理

租户管理已在 `sys_tenants` 表中定义，所有核心表通过 `tenant_id` 字段实现多租户隔离。

**多租户隔离机制**:

1. **TenantAwareMixin**: 所有模型继承此混入类
   ```python
   class TenantAwareMixin:
       tenant_id: Mapped[str | None] = mapped_column(
           String(36), 
           index=True, 
           nullable=True, 
           default="default-tenant",
           server_default="default-tenant"
       )
   ```

2. **默认租户**: `default-tenant` 用于个人版迁移和单租户部署

3. **租户查询过滤**: 所有查询自动添加 `WHERE tenant_id = :tenant_id`

4. **租户数据隔离**: 不同租户的数据完全隔离，无法跨租户访问

---

## 5. 数据模型关系图

### 5.1 完整 ER 图

```mermaid
erDiagram
    SYS_TENANTS ||--o{ SYS_USERS : "拥有"
    SYS_TENANTS ||--o{ SYS_DEPARTMENTS : "拥有"
    SYS_TENANTS ||--o{ SYS_ROLES : "拥有"
    SYS_TENANTS ||--o{ SYS_WORKSPACES : "拥有"
    SYS_TENANTS ||--o{ AI_TASKS : "拥有"
    SYS_TENANTS ||--o{ AI_WORKFLOWS : "拥有"
    SYS_TENANTS ||--o{ SYS_AUDIT_LOGS : "记录"
    SYS_TENANTS ||--o{ SYS_DLP_RULES : "配置"
    SYS_TENANTS ||--o{ SYS_ALERT_RULES : "配置"

    SYS_USERS ||--o{ SYS_USER_ROLES : "分配"
    SYS_USERS ||--o{ SYS_USER_SESSIONS : "创建"
    SYS_USERS ||--o{ SYS_AUDIT_LOGS : "触发"
    SYS_USERS ||--o{ AI_TASKS : "创建/分配"
    SYS_USERS ||--o{ AI_WORKFLOWS : "创建"
    SYS_USERS }o--o{ SYS_USER_GROUP_MEMBERS : "属于"
    SYS_USERS }o--o{ SYS_WORKSPACE_MEMBERS : "属于"

    SYS_ROLES ||--o{ SYS_ROLE_PERMISSIONS : "包含"
    SYS_PERMISSIONS ||--o{ SYS_ROLE_PERMISSIONS : "定义"

    SYS_DEPARTMENTS ||--o{ SYS_USERS : "包含"
    SYS_DEPARTMENTS ||--o{ SYS_DEPARTMENTS : "父子"

    SYS_USER_GROUPS ||--o{ SYS_USER_GROUP_MEMBERS : "包含"
    SYS_USER_GROUPS ||--o{ AI_TASKS : "分配"

    SYS_WORKSPACES ||--o{ SYS_WORKSPACE_MEMBERS : "包含"
    SYS_WORKSPACES ||--o{ SYS_WORKSPACE_AGENTS : "包含"

    SYS_USER_SESSIONS ||--o{ SYS_REFRESH_TOKENS : "关联"

    AI_TASKS ||--o{ AI_TASK_COMMENTS : "评论"
    AI_TASKS }o--o{ AI_TASKS : "父子"
    AI_TASKS }o--|| AI_WORKFLOWS : "关联"

    AI_WORKFLOWS ||--o{ AI_WORKFLOW_EXECUTIONS : "执行"
    AI_DIFY_CONNECTORS ||--o{ AI_WORKFLOWS : "来源"

    SYS_DLP_RULES ||--o{ SYS_DLP_EVENTS : "触发"
    SYS_ALERT_RULES ||--o{ SYS_ALERT_EVENTS : "触发"
```

### 5.2 模块关系图

```
┌─────────────────────────────────────────────────────────┐
│                    用户与组织模块                         │
│                                                         │
│  sys_tenants ───┬─── sys_users ───┬─── sys_departments  │
│                 │                 │                     │
│                 ├─── sys_user_roles                     │
│                 │                                       │
│                 └─── sys_user_groups                    │
│                              │                          │
│                 sys_user_group_members                  │
└─────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────┐
│                    权限与安全模块                         │
│                                                         │
│  sys_roles ──── sys_role_permissions ─── sys_permissions│
│                                                         │
│  sys_user_sessions ─── sys_refresh_tokens               │
│                                                         │
│  sys_audit_logs (ISO 27001)                             │
│                                                         │
│  sys_dlp_rules ─── sys_dlp_events                       │
│                                                         │
│  sys_alert_rules ─── sys_alert_events                   │
└─────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────┐
│                    工作空间与 AI 模块                     │
│                                                         │
│  sys_workspaces ─── sys_workspace_members               │
│        │                                                │
│        └─── sys_workspace_agents                        │
│                                                         │
│  ai_tasks ─── ai_task_comments                          │
│       │                                                 │
│       └─── ai_workflows ─── ai_workflow_executions      │
│                        │                                │
│                        └─── ai_dify_connectors          │
└─────────────────────────────────────────────────────────┘
```

---

## 6. 个人版与企业版数据模型差异

### 6.1 核心差异对比

| 维度 | 个人版 | 企业版 |
|------|--------|--------|
| **用户管理** | 单用户 (`auth.json`) | 多用户 (`sys_users`) |
| **认证方式** | 加盐 SHA-256 | bcrypt + MFA |
| **权限管理** | 无 (单用户) | RBAC (`sys_roles`, `sys_permissions`) |
| **组织架构** | 无 | 部门树 (`sys_departments`) |
| **多租户** | 不支持 | 支持 (`sys_tenants`) |
| **数据存储** | JSON 文件 | PostgreSQL + Redis |
| **对话历史** | `chats.json` | 可扩展为 `ai_conversations` 表 |
| **定时任务** | `jobs.json` | `ai_tasks` 表 (支持分配和协作) |
| **工作流** | 无 | `ai_workflows` (Dify 集成) |
| **审计日志** | 无 | `sys_audit_logs` (ISO 27001) |
| **数据安全** | 文件权限 (0600) | DLP (`sys_dlp_rules`) |
| **会话管理** | JWT (7天) | 会话 + 刷新令牌 + Redis 缓存 |
| **技能管理** | 文件系统 (`skill.json`) | 文件系统 + 企业内商店 (规划中) |
| **记忆管理** | SQLite (ReMe) | SQLite (ReMe) + 向量数据库 (规划中) |

### 6.2 数据存储位置对比

| 数据类型 | 个人版位置 | 企业版位置 |
|----------|-----------|-----------|
| 用户认证 | `~/.copaw.secret/auth.json` | PostgreSQL: `sys_users` |
| Agent 配置 | `~/.copaw/workspaces/{id}/agent.json` | 文件系统 (保持不变) |
| 技能文件 | `~/.copaw/skill_pool/` | 文件系统 (保持不变) |
| 对话历史 | `~/.copaw/workspaces/{id}/chats.json` | PostgreSQL: `ai_conversations` (规划) |
| 定时任务 | `~/.copaw/workspaces/{id}/jobs.json` | PostgreSQL: `ai_tasks` |
| Token 使用 | `~/.copaw/workspaces/{id}/token_usage.json` | PostgreSQL: 统计表 (规划) |
| 记忆数据 | `~/.copaw/workspaces/{id}/.reme/` (SQLite) | SQLite (ReMe, 保持不变) |
| 会话管理 | JWT (内存) | PostgreSQL: `sys_user_sessions` + Redis |
| 审计日志 | 无 | PostgreSQL: `sys_audit_logs` |
| 工作流 | 无 | PostgreSQL: `ai_workflows` |

### 6.3 兼容性说明

**完全兼容**:
- Agent 配置文件 (`agent.json`)
- 技能文件和配置 (`skill.json`, `SKILL.md`)
- 记忆数据 (ReMe SQLite)
- 媒体文件 (`media/`)

**需要迁移**:
- 用户认证数据 (`auth.json` → `sys_users`)
- 定时任务 (`jobs.json` → `ai_tasks`)
- 工作空间元数据 (JSON → `sys_workspaces`)

**保持不变**:
- 文件系统存储的代码和文档
- SQLite 记忆数据库
- 环境变量配置

---

## 7. 数据迁移策略

### 7.1 迁移工具

CoPaw 提供了专用的迁移脚本：`scripts/migrate_personal_to_enterprise.py`

**使用方法**:
```bash
# 预览迁移 (不执行)
python scripts/migrate_personal_to_enterprise.py \
  --postgres-url "postgresql://user:pass@localhost:5432/copaw" \
  --dry-run

# 执行完整迁移
python scripts/migrate_personal_to_enterprise.py \
  --postgres-url "postgresql://user:pass@localhost:5432/copaw"

# 仅迁移认证数据
python scripts/migrate_personal_to_enterprise.py \
  --postgres-url "postgresql://user:pass@localhost:5432/copaw" \
  --skip-agents

# 跳过认证数据 (已手动创建用户)
python scripts/migrate_personal_to_enterprise.py \
  --postgres-url "postgresql://user:pass@localhost:5432/copaw" \
  --skip-auth
```

### 7.2 迁移流程

```
阶段 1: 核心数据迁移 (P0)
├─ 创建默认租户 (sys_tenants)
├─ 迁移用户认证 (auth.json → sys_users)
├─ 创建 admin 角色 (sys_roles)
├─ 分配角色 (sys_user_roles)
└─ 创建默认工作空间 (sys_workspaces)

阶段 2: Agent 配置迁移 (P1, 可选)
├─ 方案 A: 转换为 ai_workflows (推荐)
│   └─ agent.json → ai_workflows (JSONB 存储完整配置)
└─ 方案 B: 保留文件系统 (当前方案)
    └─ 企业版直接读取 agent.json

阶段 3: 任务数据迁移 (P2, 可选)
└─ jobs.json → ai_tasks

阶段 4: 保持原样 (P3)
├─ 技能文件 (skill_pool/)
├─ 人格文件 (AGENTS.md, SOUL.md)
├─ 记忆数据 (.reme/)
└─ 媒体文件 (media/)
```

### 7.3 迁移映射关系

#### 用户认证迁移

| 个人版字段 | 企业版字段 | 转换规则 |
|-----------|-----------|---------|
| `user.username` | `sys_users.username` | 直接映射 |
| `user.password_hash` | `sys_users.password_hash` | SHA-256 → bcrypt (需重新计算) |
| `user.password_salt` | `sys_users.password_salt` | 直接映射 |
| - | `sys_users.tenant_id` | 设置为 `default-tenant` |
| - | `sys_users.status` | 设置为 `active` |
| - | `sys_users.display_name` | 使用 `username` |

#### 工作空间迁移

| 个人版字段 | 企业版字段 | 转换规则 |
|-----------|-----------|---------|
| 目录名 (`default/`) | `sys_workspaces.id` | 生成 UUID |
| `agent.json.name` | `sys_workspaces.name` | 直接映射 |
| - | `sys_workspaces.is_default` | 设置为 `true` |
| - | `sys_workspaces.tenant_id` | 设置为 `default-tenant` |
| - | `sys_workspaces.owner_id` | 关联迁移后的用户 |

#### Agent 配置迁移 (方案 A)

| 个人版字段 | 企业版字段 | 转换规则 |
|-----------|-----------|---------|
| 目录名 | `ai_workflows.id` | 生成 UUID |
| `agent.json.name` | `ai_workflows.name` | 直接映射 |
| `agent.json.description` | `ai_workflows.description` | 直接映射 |
| `agent.json` (完整) | `ai_workflows.definition` | JSONB 存储 |
| `skill.json` (完整) | `ai_workflows.definition.skills` | JSONB 嵌套 |
| - | `ai_workflows.category` | 设置为 `internal` |
| - | `ai_workflows.status` | 设置为 `active` |

### 7.4 迁移注意事项

1. **密码哈希转换**: 个人版使用 SHA-256，企业版使用 bcrypt。迁移时需要重新计算哈希或保持 SHA-256 并在首次登录时转换。

2. **数据备份**: 迁移前务必备份 `~/.copaw/` 目录和 `auth.json`。

3. **事务性**: 迁移脚本使用数据库事务，失败时自动回滚。

4. **幂等性**: 迁移脚本可重复执行，已迁移的数据会跳过。

5. **Dry Run 模式**: 建议先使用 `--dry-run` 预览迁移计划。

---

## 8. 数据存储最佳实践

### 8.1 混合存储架构

```
PostgreSQL (结构化数据):
├─ 用户管理 (sys_*)
├─ 权限管理 (roles, permissions)
├─ 工作流定义 (ai_workflows)
├─ 任务管理 (ai_tasks)
├─ 审计日志 (sys_audit_logs)
├─ DLP 规则 (sys_dlp_rules)
└─ 租户管理 (sys_tenants)

文件系统 (非结构化数据):
├─ Agent 配置 (agent.json)
├─ 技能文件 (skills/, SKILL.md)
├─ 人格文件 (AGENTS.md, SOUL.md)
└─ 记忆数据 (memory/)

SQLite - ReMe (向量/语义数据):
└─ 记忆嵌入和索引 (.reme/)

Redis (高速缓存):
├─ 会话缓存
├─ 令牌缓存
├─ 权限缓存
└─ 实时消息队列

对象存储 (可选, 大文件):
└─ 媒体文件 (media/)
```

### 8.2 数据选择指南

**选择 PostgreSQL 当**:
- 需要 ACID 事务保证
- 需要复杂查询和关联
- 需要多租户隔离
- 需要审计和合规
- 数据量中等 (< 1TB)

**选择文件系统当**:
- 数据是代码或文档
- 需要版本控制 (Git)
- 需要人类可读/可编辑
- 数据量大或二进制
- 不需要复杂查询

**选择 SQLite 当**:
- 单机本地访问
- 向量/语义搜索
- 嵌入式数据库
- 低并发场景

**选择 Redis 当**:
- 需要亚毫秒级响应
- 会话/令牌管理
- 实时消息队列
- 缓存高频查询

### 8.3 性能优化建议

**PostgreSQL**:
- 为高频查询字段创建索引
- 使用 JSONB 而不是 TEXT 存储 JSON
- 定期执行 `VACUUM ANALYZE`
- 分区大表 (如 `sys_audit_logs` 按月份分区)
- 使用连接池 (`pgbouncer`)

**文件系统**:
- 使用符号链接避免数据冗余
- 定期清理过期文件
- 监控磁盘空间
- 使用增量备份

**SQLite**:
- 限制单个数据库文件大小 (< 1GB)
- 定期压缩和归档
- 避免高并发写入

**Redis**:
- 设置合理的过期时间
- 使用合适的数据结构
- 监控内存使用
- 启用持久化 (RDB/AOF)

---

## 9. 附录：数据库迁移记录

### 9.1 Alembic 迁移版本

#### `001_initial_schema.py`

**创建时间**: 2026-04-11

**包含表**:
- `sys_users`
- `sys_user_groups`
- `sys_user_group_members`
- `sys_departments`
- `sys_roles`
- `sys_role_permissions`
- `sys_permissions`
- `sys_user_roles`
- `sys_user_sessions`
- `sys_refresh_tokens`
- `sys_audit_logs`
- `ai_tasks`
- `ai_task_comments`
- `ai_workflows`
- `ai_workflow_executions`
- `sys_workspaces`
- `sys_workspace_members`
- `sys_workspace_agents`
- `sys_tenants`

---

#### `002_enterprise_phase_b.py`

**创建时间**: 2026-04-11

**新增表**:
- `sys_dlp_rules`
- `sys_dlp_events`
- `sys_alert_rules`
- `sys_alert_events`
- `ai_dify_connectors`

---

#### `003_enterprise_phase_c.py`

**创建时间**: 2026-04-11

**修改**:
- 为所有核心表添加 `tenant_id` 字段
- 添加租户外键约束
- 添加租户索引

**影响的表**:
- `sys_alert_rules`, `sys_alert_events`
- `sys_audit_logs`, `ai_dify_connectors`
- `sys_dlp_rules`, `sys_dlp_events`
- `sys_departments`, `sys_permissions`
- `sys_role_permissions`, `sys_roles`
- `sys_user_sessions`, `sys_refresh_tokens`
- `ai_tasks`, `ai_task_comments`
- `sys_users`, `sys_user_groups`
- `sys_user_group_members`, `sys_user_roles`
- `ai_workflows`, `sys_workspaces`
- `sys_workspace_members`, `sys_workspace_agents`

---

### 9.2 数据库初始化命令

```bash
# 创建数据库
createdb copaw_enterprise

# 运行迁移
cd d:\projects\copaw
alembic upgrade head

# 检查迁移状态
alembic current

# 回滚到上一个版本
alembic downgrade -1
```

---

### 9.3 表统计信息

**总表数**: 24

| 模块 | 表数 | 表名 |
|------|------|------|
| 租户管理 | 1 | `sys_tenants` |
| 用户与组织 | 5 | `sys_users`, `sys_departments`, `sys_user_groups`, `sys_user_group_members`, `sys_user_roles` |
| 权限体系 | 3 | `sys_roles`, `sys_permissions`, `sys_role_permissions` |
| 会话与令牌 | 2 | `sys_user_sessions`, `sys_refresh_tokens` |
| 工作空间 | 3 | `sys_workspaces`, `sys_workspace_members`, `sys_workspace_agents` |
| 任务管理 | 2 | `ai_tasks`, `ai_task_comments` |
| 工作流管理 | 3 | `ai_workflows`, `ai_workflow_executions`, `ai_dify_connectors` |
| 审计日志 | 1 | `sys_audit_logs` |
| 数据安全 | 2 | `sys_dlp_rules`, `sys_dlp_events` |
| 告警管理 | 2 | `sys_alert_rules`, `sys_alert_events` |

---

## 总结

CoPaw 的数据模型架构采用了**混合存储策略**，根据数据特性选择最适合的存储方式：

1. **文件系统** 存储代码、配置和文档（灵活性高，便于版本控制）
2. **PostgreSQL** 存储结构化业务数据（支持事务、关联、多租户）
3. **SQLite** 存储向量记忆和嵌入（轻量级，适合单机语义搜索）
4. **Redis** 提供高速缓存和会话管理（亚毫秒级响应）
5. **对象存储** (可选) 存储大文件和媒体

这种架构既保留了个人版的灵活性和易用性，又提供了企业版所需的安全性、合规性和可扩展性。通过清晰的数据迁移路径，用户可以平滑地从个人版升级到企业版，无需担心数据丢失或兼容性问题。

---

**文档维护**:
- 本文档随代码更新而更新
- 新增表或字段时，请同步更新对应的章节
- 数据迁移脚本变更时，请更新迁移策略章节

**联系方式**:
- GitHub Issues: https://github.com/agentscope-ai/CoPaw/issues
- Discord: https://discord.gg/eYMpfnkG8h
- Email: support@copaw.agentscope.io
