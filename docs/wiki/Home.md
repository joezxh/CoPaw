# CoPaw 项目 Wiki

<div align="center">

![CoPaw Logo](https://img.alicdn.com/imgextra/i2/O1CN014TIqyO1U5wDiSbFfA_!!6000000002467-2-tps-816-192.png)

**懂你所需，伴你左右**

[![GitHub Repo](https://img.shields.io/badge/GitHub-Repo-black.svg?logo=github)](https://github.com/agentscope-ai/CoPaw)
[![PyPI](https://img.shields.io/pypi/v/copaw?color=3775A9&label=PyPI&logo=pypi)](https://pypi.org/project/copaw/)
[![Documentation](https://img.shields.io/badge/Docs-Website-green.svg?logo=readthedocs&label=Docs)](https://copaw.agentscope.io/)
[![Python Version](https://img.shields.io/badge/python-3.10%20~%20%3C3.14-blue.svg?logo=python&label=Python)](https://www.python.org/downloads/)
[![License](https://img.shields.io/badge/license-Apache%202.0-red.svg?logo=apache&label=License)](LICENSE)

</div>

---

## 项目概述

**CoPaw** 是一个个人AI助手框架，支持多渠道（钉钉、飞书、QQ、Discord、Telegram等）接入，具备技能扩展、多智能体协作、安全防护等功能。项目基于 AgentScope 框架构建，使用 Python 后端 + React 前端架构。

### 核心特性

- **由你掌控** — 记忆与个性化完全由你掌控，支持本地或云端部署，无第三方托管，无数据上传
- **Skills 扩展** — 内置定时任务、PDF/Office 处理、新闻摘要等；自定义技能自动加载，无绑定
- **多智能体协作** — 创建多个独立智能体，各司其职；启用协作技能，智能体间互相通信共同完成复杂任务
- **多层安全防护** — 工具防护、文件访问控制、技能安全扫描，保障运行安全
- **全域触达** — 钉钉、飞书、微信、Discord、Telegram 等频道，一个 CoPaw 按需连接

---

## Wiki 目录

### 📚 架构与设计

| 文档 | 说明 |
|------|------|
| [项目结构](Project-Structure) | 详细的代码目录结构和模块划分 |
| [技术架构](Architecture) | 系统架构设计和技术选型 |
| [核心模块](Core-Modules) | agents、app、cli等核心模块详解 |

### 🚀 开发指南

| 文档 | 说明 |
|------|------|
| [环境搭建](Development-Setup) | 开发环境配置和本地运行 |
| [前端开发](Frontend-Development) | Console和Website前端开发指南 |
| [后端开发](Backend-Development) | Python后端开发指南 |
| [测试指南](Testing) | 单元测试和集成测试 |

### 🔧 运维部署

| 文档 | 说明 |
|------|------|
| [部署指南](Deployment) | Docker、云平台等部署方式 |
| [配置说明](Configuration) | 配置文件和环境变量 |
| [安全配置](Security) | 安全机制配置 |

### 📖 参考资料

| 文档 | 说明 |
|------|------|
| [API 参考](API-Reference) | HTTP API 接口文档 |
| [CLI 命令](CLI-Commands) | 命令行工具使用指南 |
| [常见问题](FAQ) | 常见问题解答 |

---

## 快速链接

- **官方网站**: https://copaw.agentscope.io/
- **GitHub 仓库**: https://github.com/agentscope-ai/CoPaw
- **文档网站**: https://copaw.agentscope.io/docs/intro
- **问题反馈**: https://github.com/agentscope-ai/CoPaw/issues
- **社区讨论**: https://github.com/agentscope-ai/CoPaw/discussions

---

## 技术栈

### 后端
- **Python**: 3.10 - 3.13
- **框架**: AgentScope, FastAPI, uvicorn
- **AI**: transformers, huggingface_hub, google-genai
- **通信**: discord-py, dingtalk-stream, lark-oapi, python-telegram-bot

### 前端
- **Console**: React 18, TypeScript 5.8, Ant Design 5.29, Vite 6.3
- **Website**: React 18, TypeScript 5.6, Tailwind CSS 4.2, Vite 6.0

### 部署
- **Docker**: 多阶段构建，支持 amd64/arm64
- **桌面应用**: Electron/Tauri 包装

---

## 贡献者

感谢所有为 CoPaw 做出贡献的朋友们！

<a href="https://github.com/agentscope-ai/CoPaw/graphs/contributors">
<img src="https://contrib.rocks/image?repo=agentscope-ai/CoPaw" alt="Contributors" />
</a>

---

## 许可证

CoPaw 采用 [Apache License 2.0](../LICENSE) 开源协议。
