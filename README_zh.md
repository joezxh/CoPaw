<div align="center">

# CoPaw

[![GitHub 仓库](https://img.shields.io/badge/GitHub-仓库-black.svg?logo=github)](https://github.com/agentscope-ai/CoPaw)
[![PyPI](https://img.shields.io/pypi/v/copaw?color=3775A9&label=PyPI&logo=pypi)](https://pypi.org/project/copaw/)
[![文档](https://img.shields.io/badge/文档-在线-green.svg?logo=readthedocs&label=Docs)](https://copaw.agentscope.io/)
[![Python 版本](https://img.shields.io/badge/python-3.10%20~%20%3C3.14-blue.svg?logo=python&label=Python)](https://www.python.org/downloads/)
[![许可证](https://img.shields.io/badge/license-Apache%202.0-red.svg?logo=apache&label=许可证)](LICENSE)

[[文档](https://copaw.agentscope.io/)] [[English](README.md)] [[日本語](README_ja.md)] [[Русский](README_ru.md)] [[企业版](docs/ent-copaw.md)]

<p align="center">
<img src="https://img.alicdn.com/imgextra/i2/O1CN014TIqyO1U5wDiSbFfA_!!6000000002467-2-tps-816-192.png" alt="CoPaw Logo" width="120">
</p>

<p align="center"><b>懂你所需，伴你左右。</b></p>

<p align="center"><b>企业级就绪 | 多租户 | 安全协作</b></p>

</div>

---

你的 AI 助理；从个人使用到企业部署。安装极简、本地与云上均可部署；支持多端接入、能力轻松扩展。

> **核心能力：**
>
> **由你掌控** — 记忆与个性化完全由你掌控，支持本地或云端部署。无第三方托管，无数据上传。
>
> **Skills 扩展** — 内置定时任务、PDF/Office 处理、新闻摘要等；自定义技能自动加载，无绑定。通过 Skills 决定 CoPaw 能做什么。
>
> **多智能体协作** — 创建多个独立智能体，各司其职；启用协作技能，智能体间互相通信共同完成复杂任务。
>
> **多层安全防护** — 工具防护、文件访问控制、技能安全扫描，保障运行安全。
>
> **全域触达** — 钉钉、飞书、微信、Discord、Telegram 等频道，一个 CoPaw 按需连接。
>
> **🆕 企业级功能** — 多租户架构、RBAC权限管理、团队协作、审计日志、SSO集成、数据加密等。

> <details>
> <summary><b>你可以用 CoPaw 做什么</b></summary>
>
> <br>
>
> **个人使用：**
> - **社交媒体**：每日热帖摘要（小红书、知乎、Reddit），B 站/YouTube 新视频摘要。
> - **生产力**：邮件与 Newsletter 精华推送到钉钉/飞书/QQ，邮件与日历整理联系人。
> - **创意与构建**：睡前说明目标、自动执行，次日获得雏形；从选题到成片全流程。
> - **研究与学习**：追踪科技与 AI 资讯，个人知识库检索复用。
> - **桌面与文件**：整理与搜索本地文件、阅读与摘要文档，在会话中索要文件。
>
> **企业使用：**
> - **团队协作**：共享智能体、协作工作区、团队任务管理
> - **工作流自动化**：Dify集成、自动审批流程、报告生成
> - **数据安全**：端到端加密、DLP数据防泄露、审计日志
> - **用户管理**：RBAC权限控制、SSO/LDAP集成、部门权限管理
> - **IT运维**：自动工单、密码重置、系统监控
> - **HR与财务**：入职自动化、费用审批、发票OCR识别
>
> </details>

---

## 新闻

[2026-04-11] **🎉 CoPaw 企业版发布！** 我们很高兴地宣布企业级功能，包括多租户架构、RBAC权限管理、团队协作和增强安全！

[2026-04-09] 我们发布了 v1.0.2！完整更新说明见 [v1.0.2 发布说明](https://agentscope-ai.github.io/CoPaw/release-notes)。

[2026-04-04] 我们发布了 v1.0.1！完整更新说明见 [v1.0.1 发布说明](https://agentscope-ai.github.io/CoPaw/release-notes)。

[2026-03-30] 我们发布了 v1.0.0！完整更新说明见 [v1.0.0 发布说明](https://agentscope-ai.github.io/CoPaw/release-notes)。

---

## 目录

> **推荐阅读：**
>
> - **🚀 快速开始**：[安装指南](docs/QUICK-START.zh.md) → 3分钟上手
> - **🏢 企业部署**：[企业版指南](docs/ent-copaw.md) → 多租户配置与部署
> - **💬 在钉钉/飞书/微信里用**：完成快速开始 → [配置模型](#api-key) → [频道配置](https://copaw.agentscope.io/docs/channels)
> - **💻 用本地模型（无需 API Key）**：[本地模型](#本地模型)
> - **🛠️ 贡献代码**：[从源码安装](#从源码安装) → [参与贡献](#参与贡献)

- [新闻](#新闻)
- [快速开始](#快速开始)
- [企业级功能](#企业级功能)
- [API Key](#api-key)
- [本地模型](#本地模型)
- [文档](#文档)
- [安全特性](#安全特性)
- [常见问题](#常见问题)
- [路线图](#路线图)
- [从源码安装](#从源码安装)
- [参与贡献](#参与贡献)
- [许可证](#许可证)

---

## 快速开始

### 方式一：pip 安装（个人使用）

如果你习惯自行管理 Python 环境：

```bash
pip install copaw
copaw init --defaults
copaw app
```

然后在浏览器中打开控制台：**http://127.0.0.1:8088/**，配置模型后即可开始对话。

### 方式二：企业版安装

支持 PostgreSQL、Redis 和多租户的企业部署：

```bash
pip install copaw[enterprise]
copaw init --enterprise
copaw app
```

详见 [企业版指南](docs/ent-copaw.md)。

### 方式三：Docker 部署

**个人使用：**
```bash
docker run -p 127.0.0.1:8088:8088 \
  -v copaw-data:/app/working \
  -v copaw-secrets:/app/working.secret \
  agentscope/copaw:latest
```

**企业部署：**
```bash
docker-compose -f docker-compose.enterprise.yml up -d
```

详见 [部署指南](wiki/Deployment.md)。

### 方式四：桌面应用（Beta）

从 [GitHub Releases](https://github.com/agentscope-ai/CoPaw/releases) 下载：
- **Windows**: `CoPaw-Setup-<version>.exe`
- **macOS**: `CoPaw-<version>-macOS.zip`

### 方式五：脚本安装

**macOS / Linux：**
```bash
curl -fsSL https://copaw.agentscope.io/install.sh | bash
```

**Windows (PowerShell)：**
```powershell
irm https://copaw.agentscope.io/install.ps1 | iex
```

---

## 企业级功能

CoPaw 企业版在个人助理基础上扩展了企业级能力：

### 🏢 多租户架构

- **租户隔离**：部门/公司间完整数据隔离
- **组织架构管理**：层级化部门结构
- **资源配额**：按租户的用量限制和监控

### 👥 用户与权限管理

- **RBAC系统**：基于角色的细粒度权限控制
- **SSO集成**：支持 LDAP/Active Directory/OAuth2/SAML
- **部门权限**：可继承的权限结构
- **用户组**：基于团队的权限分配

### 🤝 团队协作

- **共享智能体**：团队拥有的智能助手
- **协作工作区**：共享知识库和对话历史
- **任务分配**：分配任务给团队成员并追踪
- **实时协作**：多用户编辑和评论

### 🔒 企业安全

- **端到端加密**：AES-256 加密（静态和传输中）
- **数据防泄露 (DLP)**：自动敏感数据检测和脱敏
- **审计日志**：全量操作审计追踪
- **合规性**：GDPR、ISO 27001、等保2.0 就绪

### 🔄 工作流自动化

- **Dify 集成**：可视化工作流设计器，50+ 模板
- **审批流程**：多级审批自动化
- **定时报告**：自动生成和分发报告
- **跨系统集成**：通过 API 连接企业系统

### 📊 监控与分析

- **Prometheus 指标**：实时性能监控
- **使用分析**：团队和个人使用洞察
- **告警系统**：可定制的告警规则和通知
- **仪表盘**：高管仪表盘展示关键指标

### 🛠️ 企业技能

预置常见企业场景的技能：

| 类别 | 技能 |
|------|------|
| **HR** | `hr_onboarding`（入职）、`expense_approval`（费用审批）、`password_reset_helper`（密码重置） |
| **财务** | `invoice_ocr`（发票识别）、`expense_approval`（费用审批）、`report_generator`（报告生成） |
| **IT** | `it_support_ticketing`（IT工单）、`password_reset_helper`（密码重置）、`crm_sync`（CRM同步） |
| **生产力** | `meeting_assistant`（会议助手）、`report_generator`（报告生成）、`dify_workflow`（工作流） |

### 🗄️ 基础设施

- **PostgreSQL**：主数据库，存储用户、角色、任务、审计日志
- **Redis**：会话管理、缓存、实时消息
- **Alembic**：数据库迁移管理
- **Prometheus**：指标采集和告警

### 📋 企业 API 端点

| 端点 | 描述 |
|------|------|
| `/api/enterprise/users` | 用户管理 |
| `/api/enterprise/roles` | 角色权限管理 |
| `/api/enterprise/groups` | 用户组管理 |
| `/api/enterprise/tasks` | 团队任务管理 |
| `/api/enterprise/workflows` | 工作流管理 |
| `/api/enterprise/audit` | 审计日志查询 |
| `/api/enterprise/dlp` | 数据防泄露规则 |
| `/api/enterprise/alerts` | 告警管理 |
| `/api/enterprise/dify` | Dify 集成 |

---

## API Key

若使用**云端大模型 API**（如通义千问、Gemini、OpenAI），在开始对话前必须配置 API Key。

**配置方式：**

1. **控制台（推荐）** — 打开 **http://127.0.0.1:8088/** → **设置** → **模型**
2. **`copaw init`** — 按提示配置
3. **环境变量** — 在终端或 `.env` 文件中设置 `DASHSCOPE_API_KEY`

> **仅用本地模型？** 若使用 [本地模型](#本地模型)，则无需任何 API Key。

---

## 本地模型

CoPaw 可在本机完全本地运行大模型，无需 API Key。

| 后端 | 适用场景 | 安装 |
| --- | --- | --- |
| **llama.cpp** | 跨平台 | 无需额外安装 |
| **Ollama** | 跨平台 | 提前安装 Ollama 应用并启动 |
| **LM Studio** | 跨平台 | 提前安装 LM Studio 应用并启动 |

---

## 文档

| 主题 | 说明 |
| --- | --- |
| [项目介绍](https://copaw.agentscope.io/docs/intro) | CoPaw 是什么、怎么用 |
| [快速开始](https://copaw.agentscope.io/docs/quickstart) | 安装与运行 |
| [企业版指南](docs/ent-copaw.md) | 企业部署与配置 |
| [模型](https://copaw.agentscope.io/docs/models) | 配置云/本地/自定义提供商 |
| [频道配置](https://copaw.agentscope.io/docs/channels) | 钉钉、飞书、微信、Discord、Telegram 等 |
| [Skills](https://copaw.agentscope.io/docs/skills) | 扩展与自定义能力 |
| [安全](https://copaw.agentscope.io/docs/security) | 工具防护、文件防护、技能安全扫描 |

完整文档见本仓库 [website/public/docs/](website/public/docs/)。

---

## 安全特性

CoPaw 内置多层安全防护机制：

### 个人版
- **工具防护** — 自动拦截危险 Shell 命令
- **文件访问守卫** — 限制智能体访问敏感路径
- **技能安全扫描** — 安装技能前自动扫描
- **本地部署** — 所有数据存储在本地

### 企业版
包含所有个人版功能，以及：
- **端到端加密** — AES-256 加密（静态和传输中）
- **RBAC** — 细粒度基于角色的访问控制
- **审计日志** — 全量操作审计追踪
- **DLP** — 自动敏感数据检测和脱敏
- **SSO** — 企业身份提供商集成

---

## 常见问题

访问 **[FAQ 页面](https://copaw.agentscope.io/docs/faq)** 了解常见问题和故障排查。

---

## 路线图

| 方向 | 事项 | 状态 |
| --- | --- | --- |
| **企业核心** | 多租户架构 | ✅ 已完成 |
| | RBAC权限系统 | ✅ 已完成 |
| | 团队协作 | ✅ 已完成 |
| | 审计日志 | ✅ 已完成 |
| | SSO集成 | ✅ 已完成 |
| **安全** | 端到端加密 | ✅ 已完成 |
| | DLP系统 | ✅ 已完成 |
| **集成** | Dify工作流集成 | ✅ 已完成 |
| **监控** | Prometheus指标 | ✅ 已完成 |
| **横向拓展** | 更多频道、模型、技能 | 征集中 |

---

## 从源码安装

```bash
git clone https://github.com/agentscope-ai/CoPaw.git
cd CoPaw

# 构建前端控制台
cd console && npm ci && npm run build
cd ..

# 复制控制台构建产物
mkdir -p src/copaw/console
cp -R console/dist/. src/copaw/console/

# 安装 Python 包
pip install -e .

# 企业版功能
pip install -e ".[enterprise]"
```

---

## 参与贡献

CoPaw 在开放协作中持续演进，欢迎各种形式的参与！请参考 [路线图](#路线图) 选择你感兴趣的方向。

欢迎在 [GitHub Discussions](https://github.com/agentscope-ai/CoPaw/discussions) 参与讨论。

---

## 为什么叫 CoPaw？

CoPaw 既是「你的搭档小爪子」（co-paw），也寓意 **Co Personal Agent Workstation**（协同个人智能体工作台）。我们希望它不是冰冷的工具，而是一只随时准备帮忙的温暖「小爪子」，是你数字生活中最默契的伙伴。

**企业级就绪**：从个人助理到企业平台，CoPaw 随需求扩展。

---

## 许可证

CoPaw 采用 [Apache License 2.0](LICENSE) 开源协议。

---

## 贡献者

感谢所有为 CoPaw 做出贡献的朋友们：

<a href="https://github.com/agentscope-ai/CoPaw/graphs/contributors">
<img src="https://contrib.rocks/image?repo=agentscope-ai/CoPaw" alt="贡献者" />
</a>
