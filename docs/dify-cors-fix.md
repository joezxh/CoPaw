# Dify 连接器 CORS 和 500 错误修复指南

## 问题描述

访问 `http://localhost:8088/api/enterprise/dify/connectors` 时出现：
1. CORS 跨域错误
2. 500 Internal Server Error

## 根因分析

### 1. CORS 错误
- **原因**: 后端未配置 `COPAW_CORS_ORIGINS` 环境变量
- **影响**: 前端 `http://localhost:5173` 无法访问后端 `http://localhost:8088`

### 2. 500 错误  
- **可能原因**: 
  - 数据库表 `ai_dify_connectors` 不存在（未执行迁移）
  - Dify 连接器验证逻辑异常
  - 认证中间件问题

## 解决方案

### 方案 1: 配置环境变量（推荐）

#### Windows PowerShell
```powershell
$env:COPAW_CORS_ORIGINS="http://localhost:5173,http://127.0.0.1:5173"
```

#### Windows CMD
```cmd
set COPAW_CORS_ORIGINS=http://localhost:5173,http://127.0.0.1:5173
```

#### Linux/Mac
```bash
export COPAW_CORS_ORIGINS="http://localhost:5173,http://127.0.0.1:5173"
```

#### 永久配置（.env 文件）
在 `d:/projects/copaw/.env` 文件中添加：
```env
COPAW_CORS_ORIGINS=http://localhost:5173,http://127.0.0.1:5173
```

### 方案 2: 验证数据库表存在

```powershell
# 启动后端后检查表是否存在
cd d:/projects/copaw
python -c "
import asyncio
from sqlalchemy import text
from copaw.db.postgresql import async_engine

async def check():
    async with async_engine.connect() as conn:
        result = await conn.execute(text(
            \"SELECT EXISTS (SELECT FROM information_schema.tables WHERE table_name = 'ai_dify_connectors')\"
        ))
        exists = result.scalar()
        print(f'ai_dify_connectors 表存在: {exists}')

asyncio.run(check())
"
```

如果表不存在，执行数据库迁移：
```powershell
cd d:/projects/copaw
alembic upgrade head
```

### 方案 3: 检查后端日志

启动后端后查看详细错误：
```powershell
cd d:/projects/copaw
# 启动服务
copaw serve

# 或在另一个终端查看日志
Get-Content working/copaw.log -Tail 100 -Wait
```

## 完整修复步骤

### Step 1: 配置 CORS 环境变量

编辑 `.env` 文件：
```env
# 企业版配置
COPAW_ENTERPRISE_MODE=true

# CORS 配置（允许前端开发服务器）
COPAW_CORS_ORIGINS=http://localhost:5173,http://127.0.0.1:5173
```

### Step 2: 重启后端服务

```powershell
# 停止当前服务（Ctrl+C）
# 重新启动
cd d:/projects/copaw
copaw serve
```

### Step 3: 验证 CORS 配置

在浏览器开发者工具 Console 中执行：
```javascript
fetch('http://localhost:8088/api/enterprise/dify/connectors', {
  headers: {
    'Authorization': 'Bearer YOUR_TOKEN'
  }
})
.then(r => r.json())
.then(console.log)
.catch(console.error)
```

### Step 4: 检查数据库表

```sql
-- 连接到 PostgreSQL 数据库
\c copaw_enterprise

-- 检查表是否存在
SELECT table_name 
FROM information_schema.tables 
WHERE table_name = 'ai_dify_connectors';

-- 如果不存在，执行迁移
-- alembic upgrade head
```

### Step 5: 测试 API 端点

使用 curl 或 Postman：
```bash
curl -X GET http://localhost:8088/api/enterprise/dify/connectors \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json"
```

## 常见问题

### Q1: 配置了 CORS 但仍然报错？
**A**: 确保：
1. 环境变量在**启动后端前**设置
2. 后端已完全重启
3. 浏览器已刷新（Ctrl+Shift+R）

### Q2: 500 错误仍然出现？
**A**: 检查：
1. 数据库连接是否正常
2. 表 `ai_dify_connectors` 是否存在
3. 后端日志中的详细错误信息
4. 认证 token 是否有效

### Q3: 如何在开发环境永久配置 CORS？
**A**: 有三种方式：
1. 在 `.env` 文件中配置（推荐）
2. 在 PowerShell profile 中添加环境变量
3. 修改 `src/copaw/constant.py` 中的默认值

### Q4: 生产环境如何配置？
**A**: 修改实际的前端域名：
```env
COPAW_CORS_ORIGINS=https://your-domain.com
```

## 验证成功

配置成功后，你应该看到：
1. ✅ 浏览器 Network 面板中请求状态为 200
2. ✅ Response Headers 包含 `Access-Control-Allow-Origin: http://localhost:5173`
3. ✅ 返回空数组 `[]` 或连接器列表
4. ✅ 无 CORS 错误信息

## 代码位置参考

- CORS 配置: `src/copaw/constant.py:183-185`
- CORS 中间件: `src/copaw/app/_app.py:555-565`
- Dify 路由: `src/copaw/app/routers/dify.py`
- Dify 模型: `src/copaw/db/models/dify.py`
- 迁移脚本: `alembic/versions/002_enterprise_phase_a.py`
