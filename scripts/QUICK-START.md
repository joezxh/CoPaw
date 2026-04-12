# CoPaw Enterprise 快速参考

## 🚀 快速开始

### Windows
```powershell
# 首次运行
.\start-enterprise.ps1 init
.\start-enterprise.ps1 start

# 日常使用
.\start-enterprise.ps1 start    # 启动
.\start-enterprise.ps1 status   # 状态
.\start-enterprise.ps1 stop     # 停止
```

### Linux/macOS
```bash
# 首次运行
chmod +x start-enterprise.sh
./start-enterprise.sh init
./start-enterprise.sh start

# 日常使用
./start-enterprise.sh start     # 启动
./start-enterprise.sh status    # 状态
./start-enterprise.sh stop      # 停止
```

## 📋 可用命令

| 命令 | 说明 |
|------|------|
| `init` | 初始化数据库、运行迁移、创建管理员 |
| `start` | 启动服务 |
| `stop` | 停止服务 |
| `restart` | 重启服务 |
| `status` | 查看服务状态 |

## 🔧 默认配置

| 参数 | 默认值 |
|------|--------|
| 数据库主机 | localhost |
| 数据库端口 | 5432 |
| 数据库名称 | copaw_enterprise |
| 数据库用户 | copaw |
| 数据库密码 | copaw123! |
| Redis 主机 | localhost |
| Redis 端口 | 6379 |
| Web 端口 | 8088 |

## 📁 重要文件

| 文件 | 说明 |
|------|------|
| `.copaw-enterprise.pid` | 进程 ID 文件 |
| `logs/copaw-enterprise.log` | 服务日志 |
| `.env` | 环境变量配置 |

## 🌐 访问地址

- **控制台**: http://localhost:8088
- **API 文档**: http://localhost:8088/docs

## ⚠️ 注意事项

1. 首次运行必须先执行 `init` 命令
2. 确保 PostgreSQL 和 Redis 已启动
3. 管理员密码至少 8 个字符
4. 生产环境请修改默认密码和密钥

## 🔍 故障排查

```bash
# 查看服务状态
./start-enterprise.sh status

# 查看日志
tail -f logs/copaw-enterprise.log

# 检查端口占用
netstat -tlnp | grep 8088
```
