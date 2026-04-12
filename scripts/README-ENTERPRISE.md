# CoPaw Enterprise 启动脚本使用说明

## 概述

企业版启动脚本提供了完整的 CoPaw Enterprise 服务管理功能,包括:
- ✅ 数据库连接测试
- ✅ Redis 连接测试  
- ✅ 数据库初始化(自动跳过已初始化的数据库)
- ✅ 管理员用户创建
- ✅ 服务启动/停止/重启
- ✅ 状态检查

## 文件说明

| 文件 | 平台 | 说明 |
|------|------|------|
| `start-enterprise.ps1` | Windows | PowerShell 脚本 |
| `start-enterprise.sh` | Linux/macOS | Bash Shell 脚本 |

## 环境变量配置

可以通过环境变量或编辑脚本来配置以下参数:

```bash
# 数据库配置
COPAW_DB_HOST=localhost          # 数据库主机
COPAW_DB_PORT=5432               # 数据库端口
COPAW_DB_DATABASE=copaw_enterprise  # 数据库名称
COPAW_DB_USERNAME=copaw          # 数据库用户
COPAW_DB_PASSWORD=copaw123!      # 数据库密码

# Redis 配置
COPAW_REDIS_HOST=localhost       # Redis 主机
COPAW_REDIS_PORT=6379            # Redis 端口

# 安全配置
COPAW_JWT_SECRET=your-secret-key           # JWT 密钥
COPAW_FIELD_ENCRYPT_KEY=your-encrypt-key   # 字段加密密钥(64位十六进制)
```

### 设置环境变量

**Windows PowerShell:**
```powershell
$env:COPAW_DB_HOST = "localhost"
$env:COPAW_DB_PASSWORD = "your_password"
# 然后运行脚本
.\start-enterprise.ps1 start
```

**Linux/macOS:**
```bash
export COPAW_DB_HOST="localhost"
export COPAW_DB_PASSWORD="your_password"
# 然后运行脚本
./start-enterprise.sh start
```

## 使用方式

### Windows (PowerShell)

```powershell
# 1. 初始化数据库和创建管理员用户
.\start-enterprise.ps1 init

# 2. 启动服务
.\start-enterprise.ps1 start

# 3. 查看状态
.\start-enterprise.ps1 status

# 4. 重启服务
.\start-enterprise.ps1 restart

# 5. 停止服务
.\start-enterprise.ps1 stop
```

### Linux/macOS (Bash)

```bash
# 添加执行权限(首次使用)
chmod +x start-enterprise.sh

# 1. 初始化数据库和创建管理员用户
./start-enterprise.sh init

# 2. 启动服务
./start-enterprise.sh start

# 3. 查看状态
./start-enterprise.sh status

# 4. 重启服务
./start-enterprise.sh restart

# 5. 停止服务
./start-enterprise.sh stop
```

## 完整工作流程

### 首次部署

```bash
# 1. 确保 PostgreSQL 和 Redis 已启动并运行

# 2. 初始化(会测试连接、运行迁移、创建管理员)
./start-enterprise.sh init
# 或 Windows: .\start-enterprise.ps1 init

# 3. 启动服务
./start-enterprise.sh start
# 或 Windows: .\start-enterprise.ps1 start

# 4. 访问控制台
# 浏览器打开: http://localhost:8088
```

### 日常使用

```bash
# 启动服务
./start-enterprise.sh start

# 查看状态
./start-enterprise.sh status

# 重启服务(修改配置后)
./start-enterprise.sh restart

# 停止服务
./start-enterprise.sh stop
```

## 脚本功能详解

### 1. 数据库连接测试

自动测试 PostgreSQL 连接:
- 优先使用 `psql` 命令行工具
- 回退到 Python SQLAlchemy 测试
- 显示连接成功/失败状态

### 2. Redis 连接测试

自动测试 Redis 连接:
- 优先使用 `redis-cli` 命令行工具
- 回退到 Python redis 库测试
- 发送 PING 命令验证连接

### 3. 数据库初始化检测

智能检测数据库状态:
- 检查 `alembic_version` 表是否存在
- 读取当前数据库迁移版本
- 如果已初始化,自动跳过迁移步骤

### 4. 管理员用户创建

交互式创建管理员账户:
- 检查用户是否已存在
- 提示输入密码(至少8个字符)
- 密码安全输入(不显示在终端)
- 显示创建结果

### 5. 服务管理

完整的服务生命周期管理:
- **启动**: 后台运行,保存 PID 文件
- **停止**: 优雅关闭(SIGTERM),超时强制终止(SIGKILL)
- **重启**: 先停止再启动
- **状态**: 显示服务、数据库、Redis 状态

## 输出示例

### 初始化
```
CoPaw Enterprise Management
==================================================
ℹ Initializing CoPaw Enterprise...
ℹ Testing PostgreSQL connection...
✓ PostgreSQL connection successful
ℹ Testing Redis connection...
✓ Redis connection successful
ℹ Checking if database is initialized...
ℹ Database not initialized
ℹ Initializing database...
✓ Database migration completed
ℹ Checking for admin user...
Enter admin password (min 8 characters): ********
✓ Admin user created successfully (ID: 123e4567-e89b-12d3-a456-426614174000)
ℹ Username: admin
ℹ Password: ********
✓ Initialization completed
```

### 启动
```
CoPaw Enterprise Management
==================================================
ℹ Testing PostgreSQL connection...
✓ PostgreSQL connection successful
ℹ Testing Redis connection...
✓ Redis connection successful
ℹ Checking if database is initialized...
✓ Database already initialized (version: 003)
ℹ Starting CoPaw Enterprise...
✓ CoPaw Enterprise started (PID: 12345)
ℹ Access the console at: http://localhost:8088
```

### 状态
```
CoPaw Enterprise Management
==================================================
CoPaw Enterprise Status
==================================================
✓ Service: Running (PID: 12345)
✓ Database: Connected & Initialized
✓ Redis: Connected
==================================================
```

## 日志文件

服务日志保存在:
- **路径**: `logs/copaw-enterprise.log`
- **查看日志**: 
  - Linux: `tail -f logs/copaw-enterprise.log`
  - Windows: `Get-Content logs/copaw-enterprise.log -Wait`

## PID 文件

进程 ID 保存在:
- **路径**: `.copaw-enterprise.pid`
- **用途**: 跟踪服务进程,用于停止和状态检查

## 故障排除

### 数据库连接失败

```bash
# 检查 PostgreSQL 是否运行
# Linux
systemctl status postgresql

# Windows
Get-Service postgresql*
```

### Redis 连接失败

```bash
# 检查 Redis 是否运行
# Linux
systemctl status redis

# Windows
Get-Service Redis
```

### 服务启动失败

1. 检查日志文件: `logs/copaw-enterprise.log`
2. 确认端口 8088 未被占用:
   ```bash
   # Linux
   netstat -tlnp | grep 8088
   
   # Windows
   netstat -ano | findstr 8088
   ```
3. 检查 Python 虚拟环境是否激活

### 端口被占用

```bash
# 查找占用端口的进程
# Linux
lsof -i :8088

# Windows
netstat -ano | findstr 8088

# 终止进程
# Linux
kill -9 <PID>

# Windows
taskkill /PID <PID> /F
```

## 安全建议

1. **修改默认密码**: 生产环境必须修改数据库密码和 JWT 密钥
2. **使用强密码**: 管理员密码至少 8 个字符,建议 12+ 字符
3. **保护密钥**: 不要将 `.env` 文件提交到版本控制
4. **HTTPS**: 生产环境使用反向代理(Nginx)配置 HTTPS
5. **防火墙**: 仅开放必要的端口(8088)

## 高级配置

### 使用不同的端口

编辑脚本,修改启动命令:
```python
uvicorn.run(app, host='127.0.0.1', port=9000, log_level='info')
```

### 生产环境部署

建议使用 systemd(Linux)或 NSSM(Windows)管理服务:

**systemd 示例:**
```ini
[Unit]
Description=CoPaw Enterprise
After=network.target postgresql.service redis.service

[Service]
Type=forking
User=copaw
WorkingDirectory=/opt/copaw
ExecStart=/opt/copaw/scripts/start-enterprise.sh start
ExecStop=/opt/copaw/scripts/start-enterprise.sh stop
Restart=on-failure

[Install]
WantedBy=multi-user.target
```

## 技术支持

如遇到问题,请:
1. 检查日志文件
2. 查看 [GitHub Issues](https://github.com/your-org/copaw/issues)
3. 提交问题报告,包含:
   - 操作系统版本
   - Python 版本
   - 错误日志
   - 复现步骤
