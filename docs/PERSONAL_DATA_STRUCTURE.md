# CoPaw 个人版数据结构与迁移可行性分析

## 📁 个人版数据存储位置

所有个人版数据存储在 `~/.copaw/` 目录下(Windows: `C:\Users\<用户名>\.copaw\`)

### 核心数据结构

```
~/.copaw/
├── workspaces/                      # 工作空间目录
│   ├── default/                     # 默认Agent工作空间
│   │   ├── agent.json               # Agent完整配置 (~12KB)
│   │   ├── skill.json               # 技能配置清单 (~16KB)
│   │   ├── chats.json               # 对话历史
│   │   ├── jobs.json                # 定时任务
│   │   ├── token_usage.json         # Token使用记录
│   │   ├── MEMORY.md                # 长期记忆
│   │   ├── AGENTS.md                # 人格定义
│   │   ├── SOUL.md                  # 灵魂定义
│   │   ├── PROFILE.md               # 配置文件
│   │   ├── BOOTSTRAP.md             # 引导文档
│   │   ├── HEARTBEAT.md             # 心跳配置
│   │   ├── skills/                  # 工作区技能目录
│   │   │   ├── browser_cdp/
│   │   │   ├── cron/
│   │   │   ├── docx/
│   │   │   └── ... (14个技能)
│   │   ├── active_skills/           # 已激活技能
│   │   ├── memory/                  # 每日记忆
│   │   │   └── 2026-04-11.md
│   │   └── ...
│   └── CoPaw_QA_Agent_0.1beta1/     # QA Agent工作空间
│       └── (同上结构)
│
├── skill_pool/                      # 共享技能池
│   ├── skill.json                   # 技能池清单
│   ├── browser_cdp/
│   ├── browser_visible/
│   ├── cron/
│   ├── docx/
│   └── ... (14个内置技能)
│
├── memory/                          # 全局记忆目录
├── media/                           # 媒体文件
├── models/                          # 本地模型
└── .secret/                         # 密钥目录
    └── auth.json                    # 认证信息(如启用)
```

## 📊 数据迁移可行性分析

### ✅ 可以迁移到PostgreSQL的数据

| 数据类型 | 个人版位置 | 企业版表 | 迁移方案 | 优先级 |
|---------|-----------|---------|---------|--------|
| **用户认证** | `auth.json` | `sys_users` | ✅ 已实现 | ⭐⭐⭐ |
| **Agent配置** | `agent.json` | `ai_workflows` | ⚠️ 需转换 | ⭐⭐⭐ |
| **定时任务** | `jobs.json` | `ai_tasks` | ⚠️ 需转换 | ⭐⭐ |
| **Token使用** | `token_usage.json` | 无对应表 | ❌ 保持文件 | ⭐ |

### ⚠️ 需要特殊处理的数据

| 数据类型 | 个人版位置 | 企业版表 | 说明 |
|---------|-----------|---------|------|
| **技能配置** | `skill.json` | 无对应表 | 企业版通过文件系统读取 |
| **技能文件** | `skills/` 目录 | 无对应表 | 保持文件系统存储 |
| **对话历史** | `chats.json` | `ai_conversations` | ⚠️ 表结构不同 |
| **记忆数据** | `MEMORY.md` + `memory/` | 无对应表 | ReMe使用SQLite |

### ❌ 不适合迁移的数据

| 数据类型 | 原因 |
|---------|------|
| **人格文件** (AGENTS.md, SOUL.md等) | Markdown文本,保持文件系统更合适 |
| **技能目录** (SKILL.md, scripts等) | 包含代码和文档,不适合数据库存储 |
| **浏览器数据** (cookies, cache) | 二进制数据,量大且临时 |
| **媒体文件** | 应使用对象存储(OSS/S3) |

## 🔄 推荐迁移策略

### 阶段一: 核心数据迁移 (已实现)

```sql
-- 已迁移
sys_tenants       ← 创建默认租户
sys_users         ← 从 auth.json 迁移用户
sys_roles         ← 创建 admin 角色
sys_user_roles    ← 分配角色
sys_workspaces    ← 创建默认工作空间
```

### 阶段二: Agent配置迁移 (需扩展)

**方案A: 转换为ai_workflows** (推荐)

```python
# agent.json → ai_workflows 映射
{
  "id": "agent_id",
  "workspace_id": "workspace_uuid",
  "name": "Agent Name",
  "category": "internal",  # 标识为CoPaw原生Agent
  "definition": {
    "type": "agent",
    "config": { ... agent.json 完整内容 ... },
    "skills": { ... skill.json 内容 ... }
  },
  "status": "active"
}
```

**方案B: 保留文件系统** (当前方案)

- 优点: 无需修改,企业版直接读取
- 缺点: 无法通过数据库查询和管理
- 适用: 小型部署,Agent数量少

### 阶段三: 技能管理 (保持文件系统)

**原因**:
1. 技能包含代码文件(SKILL.md, scripts/)
2. 技能文件可能被外部工具编辑
3. 版本控制更适合用Git而非数据库

**企业版方案**:
```python
# 企业版从文件系统读取技能
~/.copaw/skill_pool/           # 共享技能池
~/.copaw/workspaces/{id}/skills/  # 工作区技能
```

## 💡 最佳实践建议

### 1. 混合存储架构

```
PostgreSQL:
├─ 用户管理 (sys_*)
├─ 权限管理 (roles, permissions)
├─ 工作流定义 (ai_workflows)
├─ 任务管理 (ai_tasks)
└─ 审计日志 (sys_audit_logs)

文件系统:
├─ Agent配置 (agent.json)
├─ 技能文件 (skills/)
├─ 人格文件 (*.md)
└─ 记忆数据 (memory/)

SQLite (ReMe):
└─ 向量记忆 (embedding_cache/)

对象存储 (可选):
└─ 媒体文件 (media/)
```

### 2. 迁移优先级

```
P0 (必须):
└─ 用户认证数据 → sys_users

P1 (推荐):
├─ Agent配置 → ai_workflows (转换格式)
└─ 定时任务 → ai_tasks

P2 (可选):
├─ 对话历史 → 归档存储
└─ Token使用 → 统计分析

P3 (保持原样):
├─ 技能文件 → 文件系统
├─ 人格文件 → 文件系统
└─ 记忆数据 → SQLite
```

### 3. 企业版启动后

企业版会自动从以下位置读取配置:

```python
# 1. Agent配置
WORKING_DIR / "workspaces" / "{agent_id}" / "agent.json"

# 2. 技能配置
WORKING_DIR / "workspaces" / "{agent_id}" / "skill.json"
WORKING_DIR / "skill_pool" / "skill.json"

# 3. 技能文件
WORKING_DIR / "workspaces" / "{agent_id}" / "skills" / "{skill_name}" /
```

## 🎯 结论

### 当前迁移脚本已完成:
✅ 用户认证迁移 (auth.json → sys_users)  
✅ 租户创建 (sys_tenants)  
✅ 角色分配 (sys_roles, sys_user_roles)  
✅ 工作空间创建 (sys_workspaces)  

### 建议保持文件系统的数据:
📁 Agent配置文件 (agent.json)  
📁 技能文件和配置 (skills/, skill.json)  
📁 人格文件 (AGENTS.md, SOUL.md等)  
📁 记忆数据 (memory/, MEMORY.md)  

### 理由:
1. **兼容性**: 企业版已支持从文件系统读取
2. **灵活性**: 便于版本控制和外部编辑
3. **性能**: 大文件和代码不适合数据库存储
4. **维护性**: 混合架构更符合微服务最佳实践

---

**版本**: 1.0.0  
**更新日期**: 2026-04-12  
**分析基于**: CoPaw v0.1beta1
