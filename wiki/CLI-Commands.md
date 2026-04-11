# CLI 命令参考

本文档提供 CoPaw 命令行工具的完整参考。

---

## 基础命令

### 查看帮助

```bash
copaw --help
copaw <command> --help
```

### 查看版本

```bash
copaw --version
```

---

## 应用管理

### copaw app

启动 Web 应用服务。

```bash
copaw app [OPTIONS]
```

**选项**:
| 选项 | 说明 | 默认值 |
|------|------|--------|
| `--port` | 监听端口 | 8088 |
| `--host` | 监听地址 | 127.0.0.1 |
| `--log-level` | 日志级别 | info |
| `--reload` | 开发模式（自动重载） | false |

**示例**:
```bash
# 默认启动
copaw app

# 指定端口
copaw app --port 9000

# 开发模式
copaw app --reload --log-level debug

# 外部访问
copaw app --host 0.0.0.0
```

### copaw init

初始化配置。

```bash
copaw init [OPTIONS]
```

**选项**:
| 选项 | 说明 |
|------|------|
| `--defaults` | 使用默认配置 |
| `--working-dir` | 指定工作目录 |
| `--no-telemetry` | 禁用遥测 |

**示例**:
```bash
# 交互式初始化
copaw init

# 使用默认配置
copaw init --defaults

# 指定工作目录
copaw init --working-dir /path/to/workdir
```

---

## 智能体管理

### copaw agents

管理多个智能体。

```bash
copaw agents [COMMAND] [OPTIONS]
```

**子命令**:

#### list

列出所有智能体。

```bash
copaw agents list
```

#### create

创建新智能体。

```bash
copaw agents create --name "Agent Name" [OPTIONS]
```

**选项**:
| 选项 | 说明 | 必需 |
|------|------|------|
| `--name` | 智能体名称 | 是 |
| `--description` | 描述 | 否 |
| `--model` | 默认模型 | 否 |
| `--provider` | 默认提供商 | 否 |

#### delete

删除智能体。

```bash
copaw agents delete --agent-id <id>
```

#### enable

启用智能体。

```bash
copaw agents enable --agent-id <id>
```

#### disable

禁用智能体。

```bash
copaw agents disable --agent-id <id>
```

---

## 渠道管理

### copaw channels

管理通信渠道。

```bash
copaw channels [COMMAND] [OPTIONS]
```

**子命令**:

#### list

列出所有渠道。

```bash
copaw channels list
```

#### enable

启用渠道。

```bash
copaw channels enable --name <channel_name>
```

**示例**:
```bash
copaw channels enable --name dingtalk
copaw channels enable --name feishu
```

#### disable

禁用渠道。

```bash
copaw channels disable --name <channel_name>
```

#### test

测试渠道连接。

```bash
copaw channels test --name <channel_name>
```

---

## 聊天管理

### copaw chats

管理聊天会话。

```bash
copaw chats [COMMAND] [OPTIONS]
```

**子命令**:

#### list

列出聊天会话。

```bash
copaw chats list --agent-id <id>
```

#### clear

清空对话历史。

```bash
copaw chats clear --agent-id <id> --conversation-id <conv_id>
```

#### delete

删除会话。

```bash
copaw chats delete --agent-id <id> --conversation-id <conv_id>
```

---

## 定时任务

### copaw cron

管理定时任务。

```bash
copaw cron [COMMAND] [OPTIONS]
```

**子命令**:

#### list

列出所有定时任务。

```bash
copaw cron list
```

#### create

创建定时任务。

```bash
copaw cron create [OPTIONS]
```

**选项**:
| 选项 | 说明 | 必需 |
|------|------|------|
| `--name` | 任务名称 | 是 |
| `--cron` | Cron 表达式 | 是 |
| `--type` | 任务类型 (agent/message) | 是 |
| `--agent-id` | 智能体ID (type=agent时) | 条件 |
| `--message` | 消息内容 (type=agent时) | 条件 |
| `--channel` | 发送渠道 | 否 |
| `--enabled` | 是否启用 | 否 |

**示例**:
```bash
# 每天9点发送消息
copaw cron create \
  --name "daily-summary" \
  --cron "0 9 * * *" \
  --type agent \
  --agent-id default \
  --message "Generate daily summary" \
  --channel dingtalk

# 每小时检查
copaw cron create \
  --name "hourly-check" \
  --cron "0 * * * *" \
  --type agent \
  --agent-id default \
  --message "Check for updates"
```

#### delete

删除定时任务。

```bash
copaw cron delete --job-id <id>
```

#### enable

启用任务。

```bash
copaw cron enable --job-id <id>
```

#### disable

禁用任务。

```bash
copaw cron disable --job-id <id>
```

#### trigger

手动触发任务。

```bash
copaw cron trigger --job-id <id>
```

#### state

查看任务状态。

```bash
copaw cron state --job-id <id>
```

---

## 技能管理

### copaw skills

管理技能。

```bash
copaw skills [COMMAND] [OPTIONS]
```

**子命令**:

#### list

列出技能。

```bash
copaw skills list [OPTIONS]
```

**选项**:
| 选项 | 说明 |
|------|------|
| `--pool` | 列出技能池技能 |
| `--workspace` | 列出工作区技能 |

#### broadcast

广播技能到工作区。

```bash
copaw skills broadcast --skill <skill_name> --agent-id <id>
```

**示例**:
```bash
# 广播单个技能
copaw skills broadcast --skill pdf --agent-id default

# 广播多个技能
copaw skills broadcast --skill pdf,docx --agent-id default
```

#### import

导入技能。

```bash
copaw skills import --source <url_or_path>
```

**示例**:
```bash
# 从 URL 导入
copaw skills import --source https://github.com/user/skill-repo

# 从本地路径导入
copaw skills import --source /path/to/skill
```

#### remove

删除技能。

```bash
copaw skills remove --skill <skill_name>
```

#### update

更新内置技能。

```bash
copaw skills update-builtin
```

---

## 模型管理

### copaw models

管理模型提供商。

```bash
copaw models [COMMAND] [OPTIONS]
```

**子命令**:

#### list

列出提供商。

```bash
copaw models list
```

#### configure

配置提供商。

```bash
copaw models configure --provider <name> --api-key <key>
```

**示例**:
```bash
copaw models configure --provider dashscope --api-key sk-xxx
copaw models configure --provider openai --api-key sk-xxx
```

#### enable

启用提供商。

```bash
copaw models enable --provider <name>
```

#### disable

禁用提供商。

```bash
copaw models disable --provider <name>
```

#### test

测试提供商连接。

```bash
copaw models test --provider <name>
```

---

## 本地模型管理

### copaw local-models

管理本地模型。

```bash
copaw local-models [COMMAND] [OPTIONS]
```

**子命令**:

#### list

列出本地模型。

```bash
copaw local-models list
```

#### download

下载模型。

```bash
copaw local-models download --model <model_id> --backend <backend>
```

**示例**:
```bash
copaw local-models download --model Qwen/Qwen2.5-7B-Instruct --backend llamacpp
copaw local-models download --model llama3 --backend ollama
```

#### delete

删除模型。

```bash
copaw local-models delete --model <model_id>
```

---

## 任务执行

### copaw task

执行一次性任务。

```bash
copaw task [OPTIONS]
```

**选项**:
| 选项 | 说明 | 必需 |
|------|------|------|
| `--agent-id` | 智能体ID | 否 |
| `--message` | 任务消息 | 是 |
| `--background` | 后台执行 | 否 |
| `--output` | 输出文件 | 否 |

**示例**:
```bash
# 执行任务并等待结果
copaw task --message "Summarize the document"

# 后台执行
copaw task --message "Process files" --background

# 指定智能体
copaw task --agent-id research --message "Search for papers"
```

---

## 环境变量

### copaw env

管理环境变量。

```bash
copaw env [COMMAND] [OPTIONS]
```

**子命令**:

#### list

列出环境变量。

```bash
copaw env list
```

#### set

设置环境变量。

```bash
copaw env set --key <name> --value <value>
```

**示例**:
```bash
copaw env set --key TAVILY_API_KEY --value tvly-xxx
```

#### unset

删除环境变量。

```bash
copaw env unset --key <name>
```

---

## 系统命令

### copaw daemon

管理后台守护进程。

```bash
copaw daemon [COMMAND]
```

**子命令**:

#### start

启动守护进程。

```bash
copaw daemon start
```

#### stop

停止守护进程。

```bash
copaw daemon stop
```

#### status

查看守护进程状态。

```bash
copaw daemon status
```

### copaw shutdown

优雅关闭服务。

```bash
copaw shutdown [OPTIONS]
```

**选项**:
| 选项 | 说明 |
|------|------|
| `--force` | 强制关闭 |
| `--timeout` | 超时时间（秒） |

### copaw update

更新 CoPaw。

```bash
copaw update [OPTIONS]
```

**选项**:
| 选项 | 说明 |
|------|------|
| `--version` | 指定版本 |
| `--prerelease` | 安装预发布版本 |

**示例**:
```bash
# 更新到最新版本
copaw update

# 更新到指定版本
copaw update --version 1.0.2

# 安装预发布版本
copaw update --prerelease
```

### copaw uninstall

卸载 CoPaw。

```bash
copaw uninstall [OPTIONS]
```

**选项**:
| 选项 | 说明 |
|------|------|
| `--purge` | 删除所有配置和数据 |

**示例**:
```bash
# 卸载但保留配置和数据
copaw uninstall

# 完全卸载
copaw uninstall --purge
```

### copaw clean

清理缓存和临时文件。

```bash
copaw clean [OPTIONS]
```

**选项**:
| 选项 | 说明 |
|------|------|
| `--all` | 清理所有缓存 |
| `--cache` | 仅清理缓存 |
| `--logs` | 仅清理日志 |
| `--temp` | 仅清理临时文件 |

---

## 插件管理

### copaw plugin

管理插件。

```bash
copaw plugin [COMMAND] [OPTIONS]
```

**子命令**:

#### list

列出已安装插件。

```bash
copaw plugin list
```

#### install

安装插件。

```bash
copaw plugin install --name <plugin_name>
```

#### uninstall

卸载插件。

```bash
copaw plugin uninstall --name <plugin_name>
```

#### enable

启用插件。

```bash
copaw plugin enable --name <plugin_name>
```

#### disable

禁用插件。

```bash
copaw plugin disable --name <plugin_name>
```

---

## 认证管理

### copaw auth

管理认证。

```bash
copaw auth [COMMAND] [OPTIONS]
```

**子命令**:

#### login

登录。

```bash
copaw auth login --username <user>
```

#### logout

登出。

```bash
copaw auth logout
```

#### token

生成 API Token。

```bash
copaw auth token [OPTIONS]
```

**选项**:
| 选项 | 说明 |
|------|------|
| `--expire` | 过期时间（小时） |
| `--name` | Token 名称 |

---

## 桌面应用

### copaw desktop

启动桌面应用。

```bash
copaw desktop [OPTIONS]
```

**选项**:
| 选项 | 说明 |
|------|------|
| `--no-browser` | 不自动打开浏览器 |

---

## 全局选项

所有命令都支持以下全局选项：

| 选项 | 说明 |
|------|------|
| `--help, -h` | 显示帮助信息 |
| `--version` | 显示版本号 |
| `--verbose, -v` | 详细输出 |
| `--quiet, -q` | 静默模式 |
| `--config` | 指定配置文件 |
| `--log-level` | 设置日志级别 |

**示例**:
```bash
# 详细输出
copaw -v app

# 静默模式
copaw -q init --defaults

# 指定配置文件
copaw --config /path/to/config.json app
```

---

## 环境变量

CLI 支持以下环境变量：

| 变量 | 说明 | 默认值 |
|------|------|--------|
| `COPAW_PORT` | 默认端口 | 8088 |
| `COPAW_HOST` | 默认主机 | 127.0.0.1 |
| `COPAW_WORKING_DIR` | 工作目录 | ~/.copaw |
| `COPAW_LOG_LEVEL` | 日志级别 | info |
| `COPAW_CONFIG` | 配置文件路径 | - |
| `COPAW_NO_TELEMETRY` | 禁用遥测 | false |

---

## 配置文件

CLI 从以下位置读取配置：

1. 命令行参数
2. 环境变量
3. `.env` 文件（工作目录）
4. `config.json`（工作目录）
5. 默认值

---

## 完整示例

### 快速开始

```bash
# 安装
pip install copaw

# 初始化
copaw init --defaults

# 启动服务
copaw app

# 在浏览器打开
# http://127.0.0.1:8088/
```

### 配置模型

```bash
# 配置 DashScope
copaw models configure --provider dashscope --api-key sk-xxx

# 启用模型
copaw models enable --provider dashscope

# 测试连接
copaw models test --provider dashscope
```

### 创建定时任务

```bash
# 创建每日摘要任务
copaw cron create \
  --name "daily-summary" \
  --cron "0 9 * * *" \
  --type agent \
  --agent-id default \
  --message "Generate daily news summary" \
  --channel dingtalk \
  --enabled

# 查看任务状态
copaw cron list
copaw cron state --job-id daily-summary
```

### 执行一次性任务

```bash
# 前台执行
copaw task --message "Summarize the meeting notes"

# 后台执行
copaw task --message "Process uploaded files" --background

# 指定智能体
copaw task --agent-id research --message "Find papers about AI"
```
