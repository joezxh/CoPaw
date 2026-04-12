# 项目结构

本文档详细说明 CoPaw 项目的代码结构和模块划分。

---

## 根目录结构

```
D:\projects\copaw\
├── src/                    # 源代码目录
│   └── copaw/             # 主包
├── console/                # 前端Console界面
├── website/                # 项目文档网站
├── tests/                  # 测试代码
│   ├── unit/              # 单元测试
│   └── integrated/        # 集成测试
├── deploy/                 # 部署配置
│   ├── Dockerfile         # Docker镜像构建
│   └── entrypoint.sh      # 容器入口脚本
├── scripts/                # 构建和安装脚本
│   ├── install.sh         # Linux/macOS安装
│   ├── install.ps1        # Windows PowerShell安装
│   ├── install.bat        # Windows CMD安装
│   ├── wheel_build.sh     # Wheel包构建
│   └── pack/              # 桌面应用打包
├── .github/                # GitHub配置
│   ├── workflows/         # GitHub Actions工作流
│   └── ISSUE_TEMPLATE/    # Issue模板
├── pyproject.toml          # Python项目配置
├── setup.py                # 安装脚本
├── docker-compose.yml      # Docker Compose配置
├── README.md               # 项目说明（英文）
├── README_zh.md            # 项目说明（中文）
├── CONTRIBUTING.md         # 贡献指南
└── LICENSE                 # Apache 2.0许可证
```

---

## src/copaw/ 核心模块

### 目录概览

```
src/copaw/
├── __init__.py             # 包初始化，日志配置
├── __main__.py             # 入口点（支持 python -m copaw）
├── __version__.py          # 版本信息
├── constant.py             # 全局常量定义
├── exceptions.py           # 自定义异常类
├── agents/                 # 智能体核心模块
├── app/                    # FastAPI应用和路由
├── cli/                    # 命令行接口
├── config/                 # 配置管理
├── envs/                   # 环境变量管理
├── local_models/           # 本地模型管理
├── plugins/                # 插件系统
├── providers/              # LLM提供商集成
├── security/               # 安全模块
├── token_usage/            # Token使用统计
├── tokenizer/              # Token分词器
├── tunnel/                 # Cloudflare隧道
└── utils/                  # 工具函数
```

### 核心模块详解

#### 1. agents/ - 智能体核心模块

**功能**: 实现 CoPaw 的核心智能体逻辑，基于 ReActAgent 构建

```
agents/
├── react_agent.py          # CoPawAgent主类（1045行）
├── model_factory.py        # 模型工厂，创建LLM实例
├── prompt.py               # 系统提示词构建
├── schema.py               # 数据模式定义
├── routing_chat_model.py   # 多模型路由
├── command_handler.py      # 命令处理器（/compact, /new等）
├── tool_guard_mixin.py     # 工具守卫混入类
├── skills_manager.py       # 技能管理器（2620行）
├── skills_hub.py           # 技能仓库管理
├── hooks/                  # Agent生命周期钩子
│   ├── bootstrap.py       # 启动引导钩子
│   └── memory_compaction.py # 内存压缩钩子
├── memory/                 # 记忆管理
│   ├── base_memory_manager.py
│   ├── reme_light_memory_manager.py
│   └── agent_md_manager.py
├── tools/                  # 内置工具
│   ├── shell.py           # Shell命令执行
│   ├── file_io.py         # 文件读写
│   ├── file_search.py     # 文件搜索
│   ├── browser_*.py       # 浏览器自动化
│   ├── desktop_screenshot.py # 桌面截图
│   ├── view_media.py      # 媒体查看
│   ├── send_file.py       # 文件发送
│   ├── get_token_usage.py # Token统计
│   └── memory_search.py   # 记忆搜索
├── skills/                 # 内置技能
│   ├── pdf/               # PDF处理技能
│   ├── pptx/              # PPT处理技能
│   ├── docx/              # Word文档技能
│   ├── news/              # 新闻摘要技能
│   ├── cron/              # 定时任务技能
│   ├── multi_agent_collaboration/ # 多智能体协作
│   └── browser_*/         # 浏览器相关技能
└── md_files/               # 系统提示词模板
    ├── zh/                # 中文模板
    ├── en/                # 英文模板
    ├── ja/                # 日文模板
    └── ru/                # 俄文模板
```

**核心类**: `CoPawAgent`
- 继承自 `ReActAgent` 和 `ToolGuardMixin`
- 集成内置工具（shell、文件操作、浏览器等）
- 动态技能加载
- 记忆管理与自动压缩
- 启动引导
- 命令处理
- 工具守卫安全拦截

---

#### 2. app/ - FastAPI应用模块

**功能**: Web服务器、API路由、多智能体管理

```
app/
├── _app.py                 # FastAPI主应用（588行）
├── auth.py                 # Web认证中间件
├── agent_context.py        # Agent上下文管理
├── migration.py            # 配置迁移
├── multi_agent_manager.py  # 多智能体管理器（469行）
├── agent_config_watcher.py # 配置文件监控
├── console_push_store.py   # 推送存储
├── routers/                # API路由
│   ├── agents.py          # 智能体管理API
│   ├── agent.py           # 单智能体API
│   ├── agent_scoped.py    # 智能体作用域路由
│   ├── auth.py            # 认证API
│   ├── channel.py         # 渠道配置API
│   ├── chat.py            # 聊天会话API
│   ├── config.py          # 配置管理API
│   ├── console.py         # Console状态API
│   ├── cronjob.py         # 定时任务API
│   ├── envs.py            # 环境变量API
│   ├── files.py           # 文件操作API
│   ├── heartbeat.py       # 心跳任务API
│   ├── local_models.py    # 本地模型API
│   ├── mcp.py             # MCP客户端API
│   ├── messages.py        # 消息API
│   ├── providers.py       # 模型提供商API
│   ├── security.py        # 安全配置API
│   ├── settings.py        # 设置API
│   ├── skills.py          # 技能管理API
│   ├── skills_stream.py   # 技能流式API
│   ├── token_usage.py     # Token统计API
│   ├── tools.py           # 工具配置API
│   ├── voice.py           # 语音通道API
│   └── workspace.py       # 工作区API
├── channels/               # 渠道实现
│   ├── base.py            # 基类
│   ├── manager.py         # 渠道管理器
│   ├── registry.py        # 渠道注册表
│   ├── command_registry.py # 命令注册表
│   ├── console/           # Console渠道
│   ├── dingtalk/          # 钉钉渠道
│   ├── feishu/            # 飞书渠道
│   ├── discord_/          # Discord渠道
│   ├── telegram/          # Telegram渠道
│   ├── qq/                # QQ渠道
│   ├── onebot/            # OneBot渠道
│   ├── imessage/          # iMessage渠道
│   ├── mattermost/        # Mattermost渠道
│   ├── matrix/            # Matrix渠道
│   ├── mqtt/              # MQTT渠道
│   ├── wecom/             # 企业微信渠道
│   ├── weixin/            # 微信渠道
│   ├── xiaoyi/            # 小艺渠道
│   └── voice/             # 语音渠道
├── approvals/              # 审批服务
├── mcp/                    # MCP集成
├── workspace/              # 工作区管理
│   ├── workspace.py
│   ├── service_manager.py
│   └── service_factories.py
└── runner/                 # 任务运行器
    ├── runner.py
    ├── manager.py
    ├── session.py
    ├── task_tracker.py
    └── control_commands/   # 控制命令处理
```

**核心类**: `DynamicMultiAgentRunner`
- 动态路由到正确的工作区运行器
- 支持多智能体场景

---

#### 3. cli/ - 命令行接口模块

**功能**: 提供完整的CLI命令集

```
cli/
├── main.py                 # CLI入口，LazyGroup实现（166行）
├── app_cmd.py              # copaw app 命令
├── init_cmd.py             # copaw init 命令
├── agents_cmd.py           # copaw agents 命令
├── auth_cmd.py             # copaw auth 命令
├── channels_cmd.py         # copaw channels 命令
├── chats_cmd.py            # copaw chats 命令
├── clean_cmd.py            # copaw clean 命令
├── cron_cmd.py             # copaw cron 命令
├── daemon_cmd.py           # copaw daemon 命令
├── desktop_cmd.py          # copaw desktop 命令
├── env_cmd.py              # copaw env 命令
├── plugin_commands.py      # copaw plugin 命令
├── providers_cmd.py        # copaw models 命令
├── shutdown_cmd.py         # copaw shutdown 命令
├── skills_cmd.py           # copaw skills 命令
├── task_cmd.py             # copaw task 命令
├── uninstall_cmd.py        # copaw uninstall 命令
├── update_cmd.py           # copaw update 命令
├── http.py                 # HTTP服务
└── process_utils.py        # 进程工具
```

**命令列表**:
| 命令 | 功能 |
|------|------|
| `copaw app` | 启动Web应用 |
| `copaw init` | 初始化配置 |
| `copaw agents` | 管理多个智能体 |
| `copaw auth` | 认证管理 |
| `copaw channels` | 渠道管理 |
| `copaw chats` | 聊天管理 |
| `copaw clean` | 清理缓存 |
| `copaw cron` | 定时任务 |
| `copaw daemon` | 后台守护进程 |
| `copaw desktop` | 桌面应用 |
| `copaw env` | 环境变量 |
| `copaw plugin` | 插件管理 |
| `copaw models` | 模型提供商 |
| `copaw skills` | 技能管理 |
| `copaw task` | 任务执行 |
| `copaw uninstall` | 卸载 |
| `copaw update` | 更新 |

---

#### 4. config/ - 配置管理模块

**功能**: 配置加载、保存、验证

```
config/
├── config.py               # 配置模型定义（1429行）
├── context.py              # 配置上下文
├── timezone.py             # 时区检测
└── utils.py                # 配置工具函数
```

**核心类**:
- `Config` - 根配置
- `AgentProfileConfig` - 智能体配置
- `ChannelConfig` - 渠道配置（支持钉钉、飞书、Discord、Telegram、QQ等）
- `MCPConfig` - MCP客户端配置
- `SecurityConfig` - 安全配置
- `ToolsConfig` - 工具配置
- `HeartbeatConfig` - 心跳配置

---

#### 5. providers/ - LLM提供商模块

**功能**: 集成多种LLM提供商

```
providers/
├── provider_manager.py     # 提供商管理器（1507行）
├── provider.py             # 提供商基类
├── models.py               # 模型配置模型
├── openai_provider.py      # OpenAI提供商
├── anthropic_provider.py   # Anthropic提供商
├── gemini_provider.py      # Gemini提供商
├── ollama_provider.py      # Ollama提供商
├── openai_chat_model_compat.py # OpenAI兼容模型
├── retry_chat_model.py     # 重试机制
├── rate_limiter.py         # 速率限制
├── capability_baseline.py  # 能力基线
└── multimodal_prober.py    # 多模态探测
```

**支持的提供商**:
- OpenAI (GPT-4, GPT-3.5)
- Anthropic (Claude)
- Google Gemini
- DashScope (通义千问)
- Ollama (本地模型)
- SiliconFlow
- Kimi
- 本地模型

---

#### 6. security/ - 安全模块

**功能**: 多层安全防护

```
security/
├── secret_store.py         # 敏感凭证加密存储
├── tool_guard/             # 工具守卫
│   ├── engine.py          # 守卫引擎（237行）
│   ├── models.py          # 守卫模型
│   ├── approval.py        # 审批机制
│   ├── guardians/         # 守卫实现
│   │   ├── rule_guardian.py # 规则守卫
│   │   └── file_guardian.py # 文件守卫
│   └── rules/
│       └── dangerous_shell_commands.yaml
└── skill_scanner/          # 技能安全扫描
    ├── scanner.py         # 扫描器
    ├── scan_policy.py     # 扫描策略
    ├── analyzers/
    │   └── pattern_analyzer.py
    └── rules/signatures/  # 安全规则签名
        ├── prompt_injection.yaml
        ├── command_injection.yaml
        ├── data_exfiltration.yaml
        ├── hardcoded_secrets.yaml
        └── obfuscation.yaml
```

**安全特性**:
- 工具守卫：拦截危险Shell命令
- 文件守卫：限制敏感路径访问
- 技能扫描：检测提示注入、命令注入、硬编码密钥等

---

#### 7. local_models/ - 本地模型模块

**功能**: 本地LLM运行支持

```
local_models/
├── manager.py              # 本地模型管理器（228行）
├── model_manager.py        # 模型下载管理
├── llamacpp.py             # llama.cpp后端
├── download_manager.py     # 下载管理
└── tag_parser.py           # 标签解析
```

**支持后端**:
- llama.cpp (跨平台)
- Ollama (需要Ollama服务)
- LM Studio (需要LM Studio服务)
- MLX (macOS专用)

---

#### 8. plugins/ - 插件系统模块

**功能**: 插件发现、加载、管理

```
plugins/
├── architecture.py         # 插件架构定义
├── loader.py               # 插件加载器（240行）
├── registry.py             # 插件注册表
├── runtime.py              # 运行时助手
└── api.py                  # 插件API
```

---

## console/ 前端技术栈

### 技术栈

| 类别 | 技术 |
|------|------|
| 框架 | React 18 |
| 构建 | Vite 6.3.5 |
| UI库 | Ant Design 5.29.1 |
| 样式 | antd-style, Less |
| 路由 | react-router-dom 7.13.0 |
| 状态 | Zustand 5.0.3 |
| 国际化 | i18next 25.8.4, react-i18next |
| 图标 | @ant-design/icons, lucide-react |
| 拖拽 | @dnd-kit/core, @dnd-kit/sortable |
| Markdown | @ant-design/x-markdown, react-markdown |
| 语言 | TypeScript ~5.8.3 |

### 目录结构

```
console/
├── package.json            # 依赖配置
├── vite.config.ts          # Vite配置
├── tsconfig.json           # TypeScript配置
├── index.html              # 入口HTML
├── public/                 # 静态资源
└── src/
    ├── main.tsx           # 入口文件
    ├── App.tsx            # 根组件（195行）
    ├── i18n.ts            # 国际化配置
    ├── api/               # API模块
    ├── components/        # 公共组件
    ├── constants/         # 常量
    ├── contexts/          # React上下文
    ├── hooks/             # 自定义Hooks
    ├── layouts/           # 布局组件
    ├── locales/           # 国际化资源
    ├── pages/             # 页面组件
    ├── stores/            # 状态存储
    ├── styles/            # 全局样式
    └── utils/             # 工具函数
```

### 页面路由

| 路径 | 页面 | 功能 |
|------|------|------|
| `/login` | LoginPage | 登录页面 |
| `/agent/config` | AgentConfig | 智能体配置 |
| `/agent/skills` | AgentSkills | 技能管理 |
| `/agent/tools` | AgentTools | 工具配置 |
| `/agent/workspace` | AgentWorkspace | 工作区文件 |
| `/agent/mcp` | AgentMCP | MCP客户端 |
| `/chat` | Chat | 聊天界面 |
| `/control/channels` | Channels | 渠道配置 |
| `/control/cronjobs` | CronJobs | 定时任务 |
| `/control/heartbeat` | Heartbeat | 心跳任务 |
| `/control/sessions` | Sessions | 会话管理 |
| `/settings/models` | Models | 模型配置 |
| `/settings/environments` | Environments | 环境变量 |
| `/settings/security` | Security | 安全设置 |
| `/settings/skill-pool` | SkillPool | 技能池 |
| `/settings/token-usage` | TokenUsage | Token统计 |

---

## website/ 文档网站结构

### 技术栈

| 类别 | 技术 |
|------|------|
| 框架 | React 18.3.1 |
| 构建 | Vite 6.0.1, TypeScript 5.6.2 |
| 样式 | Tailwind CSS 4.2.2 |
| 图表 | Mermaid 11.12.2 |
| 动画 | Motion 11.11.17 |
| 搜索 | Fuse.js 7.0.0 |
| 3D | OGL 1.0.11 |
| UI | Radix UI, Shadcn |

### 目录结构

```
website/
├── package.json            # 依赖配置
├── vite.config.ts          # Vite配置
├── components.json         # Shadcn配置
├── index.html              # 入口HTML
├── scripts/                # 构建脚本
├── public/
│   ├── site.config.json   # 站点配置
│   ├── release-notes/     # 发布说明
│   └── docs/              # 文档内容
└── src/
    ├── main.tsx           # 入口文件
    ├── App.tsx            # 根组件（149行）
    ├── pages/             # 页面组件
    ├── components/        # 公共组件
    └── lib/               # 工具库
```

### 文档页面路由

| 路径 | 页面 | 功能 |
|------|------|------|
| `/` | Home | 首页 |
| `/downloads` | Downloads | 下载页 |
| `/docs` | 重定向到 `/docs/intro` | 文档首页 |
| `/docs/:slug` | Docs | 具体文档页 |
| `/release-notes` | ReleaseNotes | 发布说明 |

---

## tests/ 测试结构

### 目录结构

```
tests/
├── integrated/             # 集成测试
│   ├── test_app_startup.py
│   └── test_version.py
└── unit/                   # 单元测试
    ├── agents/
    ├── app/
    ├── channels/
    ├── cli/
    ├── local_models/
    ├── providers/
    ├── routers/
    ├── security/
    ├── utils/
    └── workspace/
```

### 测试运行

```bash
# 运行所有测试
python scripts/run_tests.py

# 运行单元测试
python scripts/run_tests.py -u

# 运行特定模块测试
python scripts/run_tests.py -u providers

# 运行集成测试
python scripts/run_tests.py -i

# 带覆盖率报告
python scripts/run_tests.py -a -c

# 并行运行
python scripts/run_tests.py -p
```

---

## 关键配置文件

### pyproject.toml

```toml
[project]
name = "copaw"
requires-python = ">=3.10,<3.14"

[project.scripts]
copaw = "copaw.cli.main:cli"

[project.optional-dependencies]
dev = ["pytest>=8.3.5", "pytest-asyncio>=0.23.0", ...]
local = ["huggingface_hub>=0.20.0"]
llamacpp = ["copaw[local]", "llama-cpp-python>=0.3.0"]
mlx = ["copaw[local]", "mlx-lm>=0.10.0"]
ollama = ["ollama>=0.6.1"]
whisper = ["openai-whisper>=20231117"]
full = ["copaw[local,ollama,llamacpp,whisper]", ...]
```

### 核心依赖

| 类别 | 依赖 |
|------|------|
| Agent框架 | agentscope==1.0.18, agentscope-runtime==1.1.3 |
| Web框架 | uvicorn>=0.40.0, fastapi |
| 通信渠道 | discord-py, dingtalk-stream, lark-oapi, python-telegram-bot, matrix-nio, paho-mqtt |
| 模型 | transformers, modelscope, huggingface_hub, google-genai |
| 浏览器 | playwright>=1.49.0 |
| 其他 | APScheduler, python-dotenv, keyring, cryptography, pyyaml |
