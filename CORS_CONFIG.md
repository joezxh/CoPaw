# CoPaw CORS 配置指南

## 问题描述
当前端(`http://localhost:8088` 或 `http://localhost:5173`)调用后端 API(`http://localhost:8088/api/agents`)时,出现跨域请求错误。

## 解决方案

### 方案 1: 配置后端 CORS(已自动配置)

已创建 `.env` 文件,配置了允许的跨域源:

```env
COPAW_CORS_ORIGINS=http://localhost:5173,http://127.0.0.1:5173,http://localhost:8088,http://127.0.0.1:8088
```

**使用步骤:**
1. 重启后端服务,使配置生效
2. 后端会自动读取 `.env` 文件并应用 CORS 中间件

### 方案 2: 使用 Vite 开发代理(推荐开发时使用)

已配置 Vite 代理,在开发模式下自动将 `/api` 请求转发到后端。

**使用步骤:**
1. 在前端开发时,编辑 `console/.env.development`:
   ```env
   VITE_API_BASE_URL=http://localhost:8088
   ```
2. 启动前端开发服务器:
   ```bash
   cd console
   npm run dev
   ```
3. Vite 会自动将所有 `/api/*` 请求代理到 `http://localhost:8088`

### 方案 3: 生产环境部署

在生产环境中,前端和后端通常部署在同一域名下,不存在跨域问题:

1. 构建前端:
   ```bash
   cd console
   npm run build
   ```
2. 构建产物会自动输出到 `src/copaw/console/` 目录
3. 后端会自动提供前端静态文件服务

## 验证配置

### 检查 CORS 是否生效

1. 启动后端服务
2. 打开浏览器开发者工具 → Network 面板
3. 查看请求头中是否包含:
   ```
   Access-Control-Allow-Origin: http://localhost:5173
   Access-Control-Allow-Credentials: true
   ```

### 检查代理是否生效

1. 启动前端开发服务器
2. 查看控制台输出,应该能看到代理配置
3. 所有 `/api/*` 请求应该被转发到后端

## 常见问题

### Q: 修改 `.env` 后不生效?
A: 需要重启后端服务,`.env` 文件在服务启动时加载。

### Q: 仍然出现 CORS 错误?
A: 检查以下几点:
1. `.env` 文件是否在正确的目录(`D:\projects\copaw\.env`)
2. `COPAW_CORS_ORIGINS` 是否包含当前前端URL
3. 后端服务是否已重启

### Q: 前端应该使用哪个端口?
A: 
- 开发模式: `http://localhost:5173` (Vite 默认端口)
- 生产模式: `http://localhost:8088` (后端服务端口,同时提供前端)

## 相关文件

- `.env` - 环境变量配置(已创建,不会被提交到 Git)
- `.env.example` - 环境变量模板(可供参考)
- `src/copaw/constant.py` - CORS_ORIGINS 常量定义(第 185 行)
- `src/copaw/app/_app.py` - CORS 中间件配置(第 527-536 行)
- `console/vite.config.ts` - Vite 代理配置(已更新)
- `console/.env.development` - 前端开发环境配置(已创建)
