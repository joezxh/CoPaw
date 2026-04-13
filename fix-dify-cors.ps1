# Dify 连接器 CORS + 500 错误快速修复

## 🔴 问题
```
CORS policy: No 'Access-Control-Allow-Origin' header
GET http://localhost:8088/api/enterprise/dify/connectors net::ERR_FAILED 500
```

## ✅ 快速修复（3 步）

### Step 1: 重启后端服务

CORS 配置已经在 `.env` 文件中，但后端可能是在配置添加之前启动的。

```powershell
# 1. 停止当前运行的 copaw serve (按 Ctrl+C)

# 2. 重新启动
cd d:/projects/copaw
copaw serve
```

### Step 2: 验证数据库表存在

```powershell
cd d:/projects/copaw

# 检查表是否存在
python -c "import asyncio; from sqlalchemy import text; from copaw.db.postgresql import async_engine; asyncio.run((async lambda: print('表存在' if (await (await async_engine.connect()).execute(text(\"SELECT EXISTS (SELECT FROM information_schema.tables WHERE table_name = 'ai_dify_connectors')\"))).scalar() else '表不存在'))())"
```

如果表不存在，执行迁移：
```powershell
cd d:/projects/copaw
alembic upgrade head
```

### Step 3: 刷新浏览器

```
按 Ctrl+Shift+R 强制刷新浏览器
```

## 🔍 验证修复

### 1. 检查浏览器 Network 面板

打开开发者工具 (F12) → Network 面板，刷新页面，检查请求：

**请求头应该包含：**
```
Origin: http://localhost:5173
```

**响应头应该包含：**
```
Access-Control-Allow-Origin: http://localhost:5173
```

### 2. 检查控制台

✅ **成功**：没有 CORS 错误，返回 `[]` 或连接器列表  
❌ **失败**：仍然有 CORS 错误或 500 错误

### 3. 测试 API

在浏览器 Console 中执行：
```javascript
fetch('http://localhost:8088/api/enterprise/dify/connectors')
  .then(r => r.json())
  .then(console.log)
  .catch(console.error)
```

## 🐛 仍然失败？

### 检查后端日志

```powershell
# 查看最近的日志
Get-Content d:/projects/copaw/working/copaw.log -Tail 50

# 实时监控日志
Get-Content d:/projects/copaw/working/copaw.log -Tail 20 -Wait
```

查找关键词：
- `ERROR`
- `dify`
- `ai_dify_connectors`
- `correlation_id`

### 常见问题

#### Q: 重启后仍然有 CORS 错误？
**A**: 检查环境变量是否生效
```powershell
# 在运行 copaw serve 的终端中执行
echo $env:COPAW_CORS_ORIGINS
# 应该输出: http://localhost:5173,http://127.0.0.1:5173,http://localhost:8088,http://127.0.0.1:8088
```

#### Q: 500 错误仍然出现？
**A**: 可能是数据库问题
```powershell
# 检查数据库连接
python -c "
import asyncio
from copaw.db.postgresql import async_engine

async def test():
    try:
        async with async_engine.connect() as conn:
            print('✅ 数据库连接成功')
    except Exception as e:
        print(f'❌ 数据库连接失败: {e}')

asyncio.run(test())
"
```

#### Q: 如何查看详细错误堆栈？
**A**: 修改 `.env` 文件，开启 debug 模式
```env
COPAW_LOG_LEVEL=debug
```
然后重启后端。

## 📋 检查清单

- [ ] `.env` 文件包含 `COPAW_CORS_ORIGINS` 配置
- [ ] 后端服务已重启（在配置添加之后）
- [ ] 数据库表 `ai_dify_connectors` 存在
- [ ] 浏览器已强制刷新（Ctrl+Shift+R）
- [ ] Network 面板中响应头包含 `Access-Control-Allow-Origin`
- [ ] 浏览器 Console 无 CORS 错误
- [ ] API 返回 200 状态码

## 📝 相关文件

- CORS 配置: `.env` (第 4 行)
- CORS 常量: `src/copaw/constant.py:183-185`
- CORS 中间件: `src/copaw/app/_app.py:555-565`
- Dify 路由: `src/copaw/app/routers/dify.py`
- Dify 模型: `src/copaw/db/models/dify.py`
- 数据库迁移: `alembic/versions/002_enterprise_phase_a.py`
