# CoPaw 快速开始指南

本指南帮助您在 3 分钟内开始使用 CoPaw。

---

## 选择安装方式

| 方式 | 适用场景 | 时间 |
|------|----------|------|
| **pip 安装** | 个人使用，熟悉 Python | 2 分钟 |
| **企业安装** | 企业部署，多租户支持 | 5 分钟 |
| **Docker** | 快速体验，容器化部署 | 3 分钟 |
| **桌面应用** | 不熟悉命令行 | 1 分钟 |
| **脚本安装** | 自动化安装，无需配置 | 2 分钟 |

---

## 方式一：pip 安装（个人使用）

### 1. 安装 CoPaw

```bash
pip install copaw
```

### 2. 初始化配置

```bash
copaw init --defaults
```

或交互式配置：

```bash
copaw init
```

### 3. 启动服务

```bash
copaw app
```

### 4. 访问控制台

打开浏览器访问：**http://127.0.0.1:8088/**

### 5. 配置模型

在控制台 **设置 → 模型** 中配置 API Key：

- **DashScope（通义千问）**: 从 [阿里云控制台](https://dashscope.console.aliyun.com/) 获取
- **OpenAI**: 从 [OpenAI Platform](https://platform.openai.com/) 获取
- **其他提供商**: 参见 [模型配置文档](https://copaw.agentscope.io/docs/models)

---

## 方式二：企业版安装

### 1. 安装企业版

```bash
pip install copaw[enterprise]
```

### 2. 准备数据库

**PostgreSQL**:
```bash
# 使用 Docker 启动 PostgreSQL
docker run -d \
  --name copaw-postgres \
  -e POSTGRES_PASSWORD=copaw123 \
  -e POSTGRES_DB=copaw \
  -p 5432:5432 \
  postgres:15
```

**Redis**:
```bash
# 使用 Docker 启动 Redis
docker run -d \
  --name copaw-redis \
  -p 6379:6379 \
  redis:7
```

### 3. 初始化企业配置

```bash
copaw init --enterprise
```

按提示配置：
- PostgreSQL 连接信息
- Redis 连接信息
- 管理员账号
- 企业信息

### 4. 运行数据库迁移

```bash
copaw db migrate
```

### 5. 启动服务

```bash
copaw app
```

### 6. 访问企业管理界面

打开浏览器：**http://127.0.0.1:8088/**

使用管理员账号登录后，可以在控制台访问：
- 用户管理
- 角色权限
- 部门管理
- 审计日志
- 工作流管理

---

## 方式三：Docker 部署

### 个人使用

```bash
docker run -p 127.0.0.1:8088:8088 \
  -v copaw-data:/app/working \
  -v copaw-secrets:/app/working.secret \
  agentscope/copaw:latest
```

### 企业部署

使用 docker-compose：

```bash
# 克隆仓库
git clone https://github.com/agentscope-ai/CoPaw.git
cd CoPaw

# 启动企业级服务
docker-compose -f docker-compose.enterprise.yml up -d
```

`docker-compose.enterprise.yml` 包含：
- CoPaw 应用
- PostgreSQL 数据库
- Redis 缓存
- Prometheus 监控
- Grafana 仪表盘

---

## 方式四：桌面应用（Beta）

### 下载

从 [GitHub Releases](https://github.com/agentscope-ai/CoPaw/releases) 下载：

- **Windows**: `CoPaw-Setup-<version>.exe`
- **macOS**: `CoPaw-<version>-macOS.zip`

### 安装

1. 运行下载的安装程序
2. 按提示完成安装
3. 启动 CoPaw 应用

### macOS 安全设置

如果 macOS 提示无法打开：

1. 右键点击应用 → **打开** → 再次点击 **打开**
2. 或在终端运行：`xattr -cr /Applications/CoPaw.app`

---

## 方式五：脚本安装

### macOS / Linux

```bash
curl -fsSL https://copaw.agentscope.io/install.sh | bash
```

**安装选项**：

```bash
# 带 Ollama 支持
curl -fsSL https://copaw.agentscope.io/install.sh | bash -s -- --extras ollama

# 指定版本
curl -fsSL https://copaw.agentscope.io/install.sh | bash -s -- --version 1.0.2

# 从源码安装
curl -fsSL https://copaw.agentscope.io/install.sh | bash -s -- --from-source
```

### Windows

**CMD**:
```cmd
curl -fsSL https://copaw.agentscope.io/install.bat -o install.bat && install.bat
```

**PowerShell**:
```powershell
irm https://copaw.agentscope.io/install.ps1 | iex
```

安装完成后：

```bash
copaw init --defaults
copaw app
```

---

## 配置模型

### 云端模型

在控制台 **设置 → 模型** 配置：

| 提供商 | 获取方式 |
|--------|----------|
| DashScope | [阿里云控制台](https://dashscope.console.aliyun.com/) |
| OpenAI | [OpenAI Platform](https://platform.openai.com/) |
| SiliconFlow | [SiliconFlow 控制台](https://cloud.siliconflow.cn/) |
| Anthropic | [Anthropic Console](https://console.anthropic.com/) |
| Google Gemini | [Google AI Studio](https://makersuite.google.com/) |

### 本地模型

无需 API Key，支持：

| 后端 | 说明 |
|------|------|
| **llama.cpp** | 控制台点击"下载 Llama.cpp" |
| **Ollama** | 安装 Ollama 应用 |
| **LM Studio** | 安装 LM Studio 应用 |

---

## 开始使用

### 在控制台对话

1. 打开 http://127.0.0.1:8088/
2. 在聊天框输入问题
3. AI 会根据启用的 Skills 执行任务

### 常用命令

在对话中使用：

| 命令 | 功能 |
|------|------|
| `/new` | 开始新对话 |
| `/compact` | 压缩对话历史 |
| `/skills` | 列出所有技能 |
| `/<skill_name>` | 指定技能执行 |
| `/model` | 切换模型 |

### 连接到聊天软件

配置渠道后，可在钉钉、飞书、微信等中使用：

1. 完成快速开始
2. 配置模型
3. 参考 [频道配置文档](https://copaw.agentscope.io/docs/channels)

---

## 企业功能快速开始

### 创建第一个团队

1. 以管理员登录
2. 进入 **企业管理 → 部门管理**
3. 创建部门结构
4. 邀请成员加入

### 配置权限

1. 进入 **角色权限**
2. 创建角色（如：HR、财务、IT）
3. 分配权限
4. 将用户添加到角色

### 创建共享智能体

1. 进入 **智能体管理**
2. 创建团队共享的智能体
3. 分配给相应部门
4. 配置共享技能

### 设置审批流程

1. 进入 **工作流管理**
2. 选择模板（费用审批、请假审批等）
3. 配置审批节点
4. 启用工作流

---

## 故障排查

### 端口被占用

```bash
# 使用其他端口
copaw app --port 8089
```

### 无法连接数据库

```bash
# 检查 PostgreSQL 是否运行
docker ps | grep copaw-postgres

# 检查连接
psql -h localhost -U copaw -d copaw
```

### Redis 连接失败

```bash
# 检查 Redis 是否运行
docker ps | grep copaw-redis

# 测试连接
redis-cli ping
```

---

## 下一步

- 📖 阅读 [完整文档](https://copaw.agentscope.io/docs)
- 🏢 配置 [企业功能](docs/ent-copaw.md)
- 🛠️ 探索 [内置技能](https://copaw.agentscope.io/docs/skills)
- 💬 连接 [聊天渠道](https://copaw.agentscope.io/docs/channels)
- 🔒 配置 [安全设置](https://copaw.agentscope.io/docs/security)

---

## 获取帮助

- 📚 [官方文档](https://copaw.agentscope.io/)
- 💬 [GitHub Discussions](https://github.com/agentscope-ai/CoPaw/discussions)
- 🐛 [提交 Issue](https://github.com/agentscope-ai/CoPaw/issues)
- 💬 [Discord 社区](https://discord.gg/eYMpfnkG8h)
- 📱 [钉钉群](https://qr.dingtalk.com/action/joingroup?code=v1,k1,OmDlBXpjW+I2vWjKDsjvI9dhcXjGZi3bQiojOq3dlDw=&_dt_no_comment=1&origin=11)
