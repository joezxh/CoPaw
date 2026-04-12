# 部署指南

本文档说明 CoPaw 的各种部署方式。

---

## 部署方式概览

| 方式 | 适用场景 | 复杂度 |
|------|----------|--------|
| **pip 安装** | 本地开发、快速试用 | ⭐ |
| **脚本安装** | 无需 Python 配置的环境 | ⭐ |
| **Docker** | 生产环境、云部署 | ⭐⭐ |
| **桌面应用** | 非技术用户 | ⭐ |
| **云平台** | 阿里云 ECS 等云服务 | ⭐⭐⭐ |

---

## 1. pip 安装部署

### 安装

```bash
pip install copaw
copaw init --defaults
copaw app
```

### 配置模型

访问 http://127.0.0.1:8088/ → **设置** → **模型**，配置 API Key。

### 后台运行

**使用 systemd (Linux)**:

```bash
# 创建服务文件
sudo nano /etc/systemd/system/copaw.service

[Unit]
Description=CoPaw AI Assistant
After=network.target

[Service]
Type=simple
User=your_username
WorkingDirectory=/home/your_username
ExecStart=/usr/bin/copaw app
Restart=on-failure
RestartSec=10

[Install]
WantedBy=multi-user.target

# 启用服务
sudo systemctl daemon-reload
sudo systemctl enable copaw
sudo systemctl start copaw
```

**使用 supervisor (Linux)**:

```ini
[program:copaw]
command=copaw app
directory=/home/user
user=user
autostart=true
autorestart=true
redirect_stderr=true
stdout_logfile=/var/log/copaw.log
```

---

## 2. 脚本安装部署

### macOS / Linux

```bash
curl -fsSL https://copaw.agentscope.io/install.sh | bash
```

**安装选项**:

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

### 启动服务

```bash
copaw init --defaults
copaw app
```

---

## 3. Docker 部署

### 快速启动

```bash
docker pull agentscope/copaw:latest

docker run -p 127.0.0.1:8088:8088 \
  -v copaw-data:/app/working \
  -v copaw-secrets:/app/working.secret \
  agentscope/copaw:latest
```

### 国内镜像

```bash
docker pull agentscope-registry.ap-southeast-1.cr.aliyuncs.com/agentscope/copaw:latest
```

### 环境变量配置

```bash
docker run -p 127.0.0.1:8088:8088 \
  -v copaw-data:/app/working \
  -v copaw-secrets:/app/working.secret \
  -e DASHSCOPE_API_KEY=your_key \
  -e OPENAI_API_KEY=your_key \
  -e LOG_LEVEL=info \
  agentscope/copaw:latest
```

### 使用 .env 文件

```bash
# 创建 .env 文件
cat > .env << EOF
DASHSCOPE_API_KEY=your_dashscope_key
OPENAI_API_KEY=your_openai_key
LOG_LEVEL=info
EOF

# 运行容器
docker run -p 127.0.0.1:8088:8088 \
  -v copaw-data:/app/working \
  -v copaw-secrets:/app/working.secret \
  --env-file .env \
  agentscope/copaw:latest
```

### 连接宿主机服务

**方式 A: host.docker.internal (推荐)**

```bash
docker run -p 127.0.0.1:8088:8088 \
  --add-host=host.docker.internal:host-gateway \
  -v copaw-data:/app/working \
  -v copaw-secrets:/app/working.secret \
  agentscope/copaw:latest
```

然后在 CoPaw 控制台配置：
- Ollama: `http://host.docker.internal:11434`
- LM Studio: `http://host.docker.internal:1234/v1`

**方式 B: Host 网络 (仅 Linux)**

```bash
docker run --network=host \
  -v copaw-data:/app/working \
  -v copaw-secrets:/app/working.secret \
  agentscope/copaw:latest
```

### Docker Compose

```yaml
version: '3.8'

services:
  copaw:
    image: agentscope/copaw:latest
    container_name: copaw
    ports:
      - "127.0.0.1:8088:8088"
    volumes:
      - copaw-data:/app/working
      - copaw-secrets:/app/working.secret
    environment:
      - LOG_LEVEL=info
      - DASHSCOPE_API_KEY=${DASHSCOPE_API_KEY}
    restart: unless-stopped

  ollama:
    image: ollama/ollama:latest
    container_name: ollama
    ports:
      - "11434:11434"
    volumes:
      - ollama-data:/root/.ollama
    restart: unless-stopped

volumes:
  copaw-data:
  copaw-secrets:
  ollama-data:
```

```bash
docker-compose up -d
```

### 自定义镜像构建

```bash
# 克隆仓库
git clone https://github.com/agentscope-ai/CoPaw.git
cd CoPaw

# 构建镜像
./scripts/docker_build.sh

# 或手动构建
docker build -t copaw:custom -f deploy/Dockerfile .
```

---

## 4. 云平台部署

### 阿里云 ECS

使用一键部署链接：

https://computenest.console.aliyun.com/service/instance/create/cn-hangzhou?type=user&ServiceId=service-1ed84201799f40879884

详细步骤参见：[阿里云开发者：CoPaw 3 分钟部署你的 AI 助理](https://developer.aliyun.com/article/1713682)

### 阿里云部署配置

**安全组规则**:
- 入站规则: 允许 8088 端口访问
- 出站规则: 允许所有流量

**ECS 实例规格推荐**:
- 最低配置: 2 vCPU, 4GB 内存
- 推荐配置: 4 vCPU, 8GB 内存
- 本地模型: 8 vCPU, 16GB 内存 + GPU

---

## 5. 桌面应用部署

### 下载

从 [GitHub Releases](https://github.com/agentscope-ai/CoPaw/releases) 下载：

- **Windows**: `CoPaw-Setup-<version>.exe`
- **macOS**: `CoPaw-<version>-macOS.zip`

### macOS 安全绕过

1. 右键点击应用 → **打开** → 再次点击 **打开**
2. 或在终端运行: `xattr -cr /Applications/CoPaw.app`

---

## 6. 反向代理配置

### Nginx

```nginx
server {
    listen 80;
    server_name copaw.yourdomain.com;

    location / {
        proxy_pass http://127.0.0.1:8088;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

### Caddy

```
copaw.yourdomain.com {
    reverse_proxy localhost:8088
}
```

### Apache

```apache
<VirtualHost *:80>
    ServerName copaw.yourdomain.com
    
    ProxyPreserveHost On
    ProxyPass / http://127.0.0.1:8088/
    ProxyPassReverse / http://127.0.0.1:8088/
    
    RewriteEngine on
    RewriteCond %{HTTP:Upgrade} websocket [NC]
    RewriteCond %{HTTP:Connection} upgrade [NC]
    RewriteRule ^/?(.*) "ws://127.0.0.1:8088/$1" [P,L]
</VirtualHost>
```

---

## 7. 安全配置

### Web 认证

```bash
# 启用 Web 认证
export COPAW_AUTH_ENABLED=true
copaw app

# 或在配置文件中
# config.json:
{
  "security": {
    "auth_enabled": true
  }
}
```

### HTTPS 配置

**使用 Let's Encrypt**:

```bash
# 安装 certbot
sudo apt install certbot python3-certbot-nginx

# 获取证书
sudo certbot --nginx -d copaw.yourdomain.com

# 自动续期
sudo certbot renew --dry-run
```

### 防火墙配置

```bash
# UFW (Ubuntu)
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
sudo ufw allow 8088/tcp  # 如需直接访问

# firewalld (CentOS/RHEL)
sudo firewall-cmd --permanent --add-port=8088/tcp
sudo firewall-cmd --reload
```

---

## 8. 监控和日志

### 日志位置

```
~/.copaw/logs/          # 应用日志
/var/log/copaw.log      # supervisor 日志
/var/log/syslog         # 系统日志
```

### 日志级别

```bash
# 设置日志级别
export COPAW_LOG_LEVEL=debug
copaw app
```

**日志级别**:
- `debug`: 详细调试信息
- `info`: 一般信息（默认）
- `warning`: 警告信息
- `error`: 错误信息

### 健康检查

```bash
# 检查服务状态
curl http://127.0.0.1:8088/api/health

# 或使用 CLI
copaw status
```

---

## 9. 备份和恢复

### 备份

```bash
# 备份工作目录
tar -czf copaw-backup-$(date +%Y%m%d).tar.gz ~/.copaw/

# 或使用 rsync
rsync -avz ~/.copaw/ backup/copaw/
```

### 恢复

```bash
# 解压备份
tar -xzf copaw-backup-20240101.tar.gz -C ~/

# 重启服务
copaw app
```

---

## 10. 故障排查

### 常见问题

**端口被占用**:
```bash
# 查找占用端口的进程
lsof -i :8088
# 或
netstat -tlnp | grep 8088

# 使用其他端口
copaw app --port 8089
```

**内存不足**:
```bash
# 检查内存使用
free -h

# 增加 swap
sudo fallocate -l 2G /swapfile
sudo chmod 600 /swapfile
sudo mkswap /swapfile
sudo swapon /swapfile
```

**Docker 容器无法启动**:
```bash
# 查看容器日志
docker logs <container_id>

# 进入容器调试
docker exec -it <container_id> bash
```

**API Key 无效**:
- 检查 Key 格式是否正确
- 确认 Key 是否有配额
- 检查网络连接

---

## 11. 性能优化

### 本地模型优化

```bash
# 使用 GPU 加速
# 安装 CUDA 版本的 llama.cpp
CMAKE_ARGS="-DGGML_CUDA=on" pip install llama-cpp-python

# 或使用 Metal (macOS)
CMAKE_ARGS="-DGGML_METAL=on" pip install llama-cpp-python
```

### 速率限制配置

在 `config.json` 中配置：

```json
{
  "providers": {
    "dashscope": {
      "rate_limit": {
        "qpm": 60,
        "tokens_per_minute": 100000
      }
    }
  }
}
```

### 内存优化

```json
{
  "memory": {
    "max_messages": 100,
    "compression_threshold": 50,
    "enable_auto_compaction": true
  }
}
```
