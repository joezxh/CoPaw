# API 参考

本文档提供 CoPaw HTTP API 的完整参考。

---

## 基础信息

- **基础 URL**: `http://127.0.0.1:8088/api`
- **认证**: 可选的 Bearer Token 认证
- **内容类型**: `application/json`
- **API 版本**: v1

---

## 认证

### 启用认证

```bash
export COPAW_AUTH_ENABLED=true
copaw app
```

### 认证请求

```bash
curl -H "Authorization: Bearer YOUR_TOKEN" \
  http://127.0.0.1:8088/api/agents
```

---

## 智能体管理

### 列出所有智能体

```http
GET /api/agents
```

**响应示例**:
```json
[
  {
    "id": "default",
    "name": "Default Agent",
    "description": "Main agent",
    "created_at": "2024-01-01T00:00:00Z",
    "status": "active"
  }
]
```

### 创建智能体

```http
POST /api/agents
Content-Type: application/json

{
  "name": "New Agent",
  "description": "Agent description",
  "config": {
    "model": "qwen-plus",
    "provider": "dashscope"
  }
}
```

**响应示例**:
```json
{
  "id": "agent_123",
  "name": "New Agent",
  "status": "created"
}
```

### 获取智能体详情

```http
GET /api/agents/{agent_id}
```

### 更新智能体

```http
PUT /api/agents/{agent_id}
Content-Type: application/json

{
  "name": "Updated Name",
  "description": "Updated description"
}
```

### 删除智能体

```http
DELETE /api/agents/{agent_id}
```

### 启用/禁用智能体

```http
PATCH /api/agents/{agent_id}/status
Content-Type: application/json

{
  "enabled": true
}
```

---

## 聊天 API

### 发送消息

```http
POST /api/chat/message
Content-Type: application/json
X-Agent-Id: default

{
  "content": "Hello, CoPaw!",
  "conversation_id": "conv_123"
}
```

**响应示例** (流式):
```json
{
  "type": "stream",
  "content": "Hello! How can I help you today?",
  "role": "assistant"
}
```

### 获取对话历史

```http
GET /api/chat/history?conversation_id={conversation_id}&limit=100
X-Agent-Id: default
```

### 清空对话历史

```http
DELETE /api/chat/history?conversation_id={conversation_id}
X-Agent-Id: default
```

### 创建新对话

```http
POST /api/chat/conversation
X-Agent-Id: default
```

---

## 技能管理

### 列出技能池技能

```http
GET /api/skills/pool
```

**响应示例**:
```json
{
  "skills": [
    {
      "id": "pdf",
      "name": "PDF Processing",
      "version": "1.0.0",
      "description": "PDF相关操作",
      "builtin": true
    }
  ]
}
```

### 列出工作区技能

```http
GET /api/skills/workspace
X-Agent-Id: default
```

### 广播技能到工作区

```http
POST /api/skills/broadcast
Content-Type: application/json

{
  "skill_ids": ["pdf", "docx"],
  "agent_ids": ["default", "agent_2"]
}
```

### 导入技能

```http
POST /api/skills/import
Content-Type: application/json

{
  "source": "url",
  "url": "https://github.com/user/skill-repo"
}
```

### 删除技能

```http
DELETE /api/skills/pool/{skill_id}
```

### 更新内置技能

```http
POST /api/skills/update-builtin
```

---

## 模型提供商

### 列出提供商

```http
GET /api/providers
```

**响应示例**:
```json
{
  "providers": [
    {
      "name": "dashscope",
      "display_name": "DashScope (通义千问)",
      "enabled": true,
      "models": ["qwen-plus", "qwen-turbo"]
    }
  ]
}
```

### 配置提供商

```http
POST /api/providers/{provider_name}/config
Content-Type: application/json

{
  "api_key": "sk-xxx",
  "enabled": true,
  "models": ["qwen-plus"]
}
```

### 测试提供商连接

```http
POST /api/providers/{provider_name}/test
```

### 获取可用模型列表

```http
GET /api/providers/{provider_name}/models
```

---

## 本地模型

### 列出本地模型

```http
GET /api/local-models
```

### 下载模型

```http
POST /api/local-models/download
Content-Type: application/json

{
  "model_id": "Qwen/Qwen2.5-7B-Instruct",
  "backend": "llamacpp"
}
```

### 删除本地模型

```http
DELETE /api/local-models/{model_id}
```

### 启动本地模型服务

```http
POST /api/local-models/{model_id}/start
```

### 停止本地模型服务

```http
POST /api/local-models/{model_id}/stop
```

---

## 渠道配置

### 列出渠道

```http
GET /api/channel
```

**响应示例**:
```json
{
  "channels": [
    {
      "name": "dingtalk",
      "enabled": true,
      "config": {
        "client_id": "xxx",
        "client_secret": "***"
      }
    }
  ]
}
```

### 配置渠道

```http
POST /api/channel/{channel_name}/config
Content-Type: application/json

{
  "enabled": true,
  "config": {
    "client_id": "xxx",
    "client_secret": "xxx"
  }
}
```

### 测试渠道连接

```http
POST /api/channel/{channel_name}/test
```

---

## 定时任务

### 列出定时任务

```http
GET /api/cronjob
```

**响应示例**:
```json
{
  "jobs": [
    {
      "id": "job_123",
      "name": "Daily Summary",
      "cron": "0 9 * * *",
      "enabled": true,
      "next_run": "2024-01-02T09:00:00Z"
    }
  ]
}
```

### 创建定时任务

```http
POST /api/cronjob
Content-Type: application/json

{
  "name": "Daily Report",
  "cron": "0 9 * * *",
  "type": "agent",
  "agent_id": "default",
  "message": "Generate daily report",
  "channel": "dingtalk"
}
```

### 更新定时任务

```http
PUT /api/cronjob/{job_id}
Content-Type: application/json

{
  "enabled": false
}
```

### 删除定时任务

```http
DELETE /api/cronjob/{job_id}
```

### 手动触发任务

```http
POST /api/cronjob/{job_id}/trigger
```

---

## 心跳任务

### 获取心跳配置

```http
GET /api/heartbeat
X-Agent-Id: default
```

### 更新心跳配置

```http
PUT /api/heartbeat
Content-Type: application/json
X-Agent-Id: default

{
  "enabled": true,
  "interval_minutes": 60,
  "questions": ["What's the weather today?"],
  "publish_result": true
}
```

---

## 环境变量

### 列出环境变量

```http
GET /api/envs
```

**响应示例**:
```json
{
  "envs": {
    "TAVILY_API_KEY": "tvly-xxx",
    "CUSTOM_VAR": "value"
  }
}
```

### 设置环境变量

```http
POST /api/envs
Content-Type: application/json

{
  "key": "TAVILY_API_KEY",
  "value": "tvly-xxx"
}
```

### 删除环境变量

```http
DELETE /api/envs/{key}
```

---

## 工作区文件

### 列出文件

```http
GET /api/workspace/files?path=/
X-Agent-Id: default
```

### 读取文件

```http
GET /api/workspace/files/content?path=/document.pdf
X-Agent-Id: default
```

### 上传文件

```http
POST /api/workspace/files/upload
Content-Type: multipart/form-data
X-Agent-Id: default

file: <binary>
path: /uploads/filename.pdf
```

### 删除文件

```http
DELETE /api/workspace/files?path=/old_file.pdf
X-Agent-Id: default
```

---

## MCP 管理

### 列出 MCP 客户端

```http
GET /api/mcp
X-Agent-Id: default
```

### 添加 MCP 客户端

```http
POST /api/mcp
Content-Type: application/json
X-Agent-Id: default

{
  "name": "my-mcp-server",
  "transport": "stdio",
  "command": "node",
  "args": ["server.js"]
}
```

### 删除 MCP 客户端

```http
DELETE /api/mcp/{client_id}
X-Agent-Id: default
```

### 列出 MCP 工具

```http
GET /api/mcp/{client_id}/tools
X-Agent-Id: default
```

---

## 安全配置

### 获取安全配置

```http
GET /api/security
```

### 更新安全配置

```http
PUT /api/security
Content-Type: application/json

{
  "tool_guard_enabled": true,
  "file_guard_enabled": true,
  "skill_scanner_enabled": true
}
```

### 获取工具守卫规则

```http
GET /api/security/tool-guard/rules
```

### 添加工具守卫规则

```http
POST /api/security/tool-guard/rules
Content-Type: application/json

{
  "name": "block-dangerous-command",
  "pattern": "rm -rf /",
  "action": "block"
}
```

---

## Token 使用统计

### 获取统计摘要

```http
GET /api/token-usage/summary?days=7
```

**响应示例**:
```json
{
  "total_tokens": 100000,
  "total_cost": 1.50,
  "by_model": {
    "qwen-plus": 50000,
    "qwen-turbo": 50000
  },
  "daily_usage": [
    {
      "date": "2024-01-01",
      "tokens": 15000,
      "cost": 0.22
    }
  ]
}
```

### 获取详细记录

```http
GET /api/token-usage/details?start_date=2024-01-01&end_date=2024-01-31
```

---

## 控制台状态

### 获取控制台状态

```http
GET /api/console/status
```

**响应示例**:
```json
{
  "version": "1.0.2",
  "uptime": 3600,
  "agents": 2,
  "active_conversations": 3,
  "channels": {
    "dingtalk": "connected",
    "feishu": "disconnected"
  }
}
```

### 获取系统信息

```http
GET /api/console/system
```

---

## 错误处理

### 错误响应格式

```json
{
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Invalid parameter",
    "details": {
      "field": "agent_id",
      "value": "invalid_id"
    }
  }
}
```

### 常见错误码

| 错误码 | HTTP 状态 | 说明 |
|--------|-----------|------|
| `UNAUTHORIZED` | 401 | 未认证 |
| `FORBIDDEN` | 403 | 无权限 |
| `NOT_FOUND` | 404 | 资源不存在 |
| `VALIDATION_ERROR` | 400 | 参数验证失败 |
| `CONFLICT` | 409 | 资源冲突 |
| `RATE_LIMIT` | 429 | 请求过于频繁 |
| `INTERNAL_ERROR` | 500 | 服务器内部错误 |

---

## WebSocket API

### 连接 WebSocket

```javascript
const ws = new WebSocket('ws://127.0.0.1:8088/ws');

ws.onopen = () => {
  ws.send(JSON.stringify({
    type: 'subscribe',
    agent_id: 'default'
  }));
};

ws.onmessage = (event) => {
  const data = JSON.parse(event.data);
  console.log('Received:', data);
};
```

### 消息类型

| 类型 | 方向 | 说明 |
|------|------|------|
| `subscribe` | 客户端→服务器 | 订阅智能体消息 |
| `unsubscribe` | 客户端→服务器 | 取消订阅 |
| `message` | 服务器→客户端 | 新消息 |
| `typing` | 服务器→客户端 | AI 正在输入 |
| `error` | 服务器→客户端 | 错误通知 |

---

## SDK 使用示例

### Python

```python
import requests

BASE_URL = 'http://127.0.0.1:8088/api'

# 获取智能体列表
response = requests.get(f'{BASE_URL}/agents')
agents = response.json()

# 发送消息
response = requests.post(
    f'{BASE_URL}/chat/message',
    headers={'X-Agent-Id': 'default'},
    json={'content': 'Hello!'}
)
```

### JavaScript

```javascript
const BASE_URL = 'http://127.0.0.1:8088/api';

// 获取智能体列表
const response = await fetch(`${BASE_URL}/agents`);
const agents = await response.json();

// 发送消息
const messageResponse = await fetch(`${BASE_URL}/chat/message`, {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
    'X-Agent-Id': 'default'
  },
  body: JSON.stringify({ content: 'Hello!' })
});
```

### cURL

```bash
# 获取智能体列表
curl http://127.0.0.1:8088/api/agents

# 发送消息
curl -X POST http://127.0.0.1:8088/api/chat/message \
  -H "Content-Type: application/json" \
  -H "X-Agent-Id: default" \
  -d '{"content": "Hello!"}'
```
