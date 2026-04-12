# 常见问题 (FAQ)

本文档汇总了 CoPaw 使用中的常见问题和解决方案。

---

## 安装问题

### 1. Python 版本不兼容

**问题**: 提示 Python 版本不满足要求。

**解决**:
```bash
# 检查 Python 版本
python --version

# CoPaw 要求 Python 3.10 - 3.13
# 使用 pyenv 切换版本
pyenv install 3.12
pyenv local 3.12

# 或使用 conda
conda create -n copaw python=3.12
conda activate copaw
```

### 2. pip 安装失败

**问题**: pip 安装时报错。

**解决**:
```bash
# 升级 pip
pip install --upgrade pip setuptools wheel

# 使用国内镜像
pip install copaw -i https://pypi.tuna.tsinghua.edu.cn/simple

# 或使用阿里云镜像
pip install copaw -i https://mirrors.aliyun.com/pypi/simple/
```

### 3. Windows 安装脚本失败

**问题**: Windows PowerShell 运行安装脚本失败。

**解决**:
```powershell
# 以管理员身份运行
# 允许脚本执行
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser

# 重新运行安装脚本
irm https://copaw.agentscope.io/install.ps1 | iex
```

### 4. Windows LTSC 环境变量问题

**问题**: Windows LTSC 版本环境变量无法自动设置。

**解决**:
参见 [README](../README_zh.md#windows-企业版-ltsc-用户特别提示) 中的手动配置步骤。

---

## 启动问题

### 1. 端口被占用

**问题**: 提示端口 8088 已被占用。

**解决**:
```bash
# 方式1: 使用其他端口
copaw app --port 8089

# 方式2: 查找并关闭占用端口的进程
# Linux/macOS
lsof -i :8088
kill -9 <PID>

# Windows
netstat -ano | findstr :8088
taskkill /PID <PID> /F
```

### 2. 无法访问控制台

**问题**: 启动后浏览器无法打开 http://127.0.0.1:8088/

**解决**:
```bash
# 检查服务是否启动
curl http://127.0.0.1:8088/api/health

# 检查日志
copaw app --log-level debug

# 确认防火墙设置
# Linux
sudo ufw status
sudo ufw allow 8088

# Windows: 检查防火墙规则
```

### 3. Docker 容器启动失败

**问题**: Docker 容器无法正常启动。

**解决**:
```bash
# 查看容器日志
docker logs <container_id>

# 进入容器调试
docker exec -it <container_id> bash

# 检查挂载卷权限
ls -la ~/.copaw
```

---

## 模型配置问题

### 1. API Key 无效

**问题**: 配置 API Key 后仍无法使用。

**解决**:
- 检查 API Key 格式是否正确（无多余空格）
- 确认 API Key 是否有配额
- 检查 API Key 是否过期
- 测试连接:
  ```bash
  copaw models test --provider dashscope
  ```

### 2. 通义千问 API 错误

**问题**: 使用通义千问时报错。

**解决**:
- 确认在 DashScope 控制台开通了相应模型
- 检查账户余额是否充足
- 确认 API Key 权限设置

### 3. OpenAI API 不可用

**问题**: 无法连接 OpenAI API。

**解决**:
- 检查网络连接
- 如在中国大陆，需要配置代理:
  ```bash
  export HTTP_PROXY=http://127.0.0.1:7890
  export HTTPS_PROXY=http://127.0.0.1:7890
  copaw app
  ```

### 4. 本地模型下载慢

**问题**: 本地模型下载速度慢或失败。

**解决**:
```bash
# 使用 ModelScope 镜像
export HF_ENDPOINT=https://hf-mirror.com

# 手动下载模型文件
# 然后在控制台指定本地路径
```

---

## 渠道配置问题

### 1. 钉钉机器人无法接收消息

**问题**: 配置钉钉后无法接收消息。

**解决**:
- 确认机器人已添加到群
- 检查 Stream 模式是否开启
- 验证 Client ID 和 Client Secret
- 查看 [钉钉配置文档](https://copaw.agentscope.io/docs/channels)

### 2. 飞书机器人连接失败

**问题**: 飞书机器人无法连接。

**解决**:
- 确认应用已发布
- 检查事件订阅配置
- 验证 App ID 和 App Secret
- 查看 [飞书配置文档](https://copaw.agentscope.io/docs/channels)

### 3. Discord Bot 无响应

**问题**: Discord Bot 不回复消息。

**解决**:
- 确认 Bot 有消息读取权限
- 检查 Bot Token 是否正确
- 验证 Bot 是否已加入服务器
- 查看 [Discord 配置文档](https://copaw.agentscope.io/docs/channels)

### 4. 微信消息发送失败

**问题**: 微信渠道消息发送失败。

**解决**:
- 检查企业微信配置
- 确认应用权限设置
- 验证 Corp ID 和 Secret

---

## 技能相关问题

### 1. 技能加载失败

**问题**: 技能无法正常加载。

**解决**:
```bash
# 检查技能文件结构
ls ~/.copaw/workspaces/default/skills/<skill_name>/

# 确认 SKILL.md 存在
cat ~/.copaw/workspaces/default/skills/<skill_name>/SKILL.md

# 查看日志
copaw app --log-level debug
```

### 2. 技能冲突

**问题**: 技能名称冲突。

**解决**:
- 重命名冲突技能
- 使用不同的技能别名

### 3. 技能安全扫描报错

**问题**: 安装技能时安全扫描失败。

**解决**:
- 查看扫描报告了解具体风险
- 确认技能来源可信
- 临时禁用扫描（不推荐）:
  ```json
  {
    "security": {
      "skill_scanner_enabled": false
    }
  }
  ```

### 4. PDF 处理失败

**问题**: PDF 文件处理报错。

**解决**:
- 确认 PDF 文件未加密
- 检查 PDF 文件是否损坏
- 尝试使用 OCR 功能处理扫描 PDF

---

## 记忆相关问题

### 1. 记忆丢失

**问题**: 对话历史或记忆丢失。

**解决**:
```bash
# 检查工作目录
ls ~/.copaw/workspaces/default/

# 确认记忆文件存在
ls ~/.copaw/workspaces/default/memory/

# 备份后重启服务
cp -r ~/.copaw ~/.copaw-backup
copaw app
```

### 2. 记忆占用过大

**问题**: 记忆文件占用过多磁盘空间。

**解决**:
```bash
# 手动压缩记忆
curl -X POST http://127.0.0.1:8088/api/memory/compact

# 或在对话中使用
/compact
```

### 3. 记忆搜索无结果

**问题**: 搜索记忆时无结果。

**解决**:
- 确认搜索关键词正确
- 检查记忆是否已压缩
- 查看日志确认索引状态

---

## 性能问题

### 1. 响应速度慢

**问题**: AI 响应速度很慢。

**解决**:
- 检查网络延迟
- 尝试使用更快的模型
- 对于本地模型，考虑使用 GPU 加速
- 减少上下文长度:
  ```bash
  /compact
  ```

### 2. 内存占用高

**问题**: CoPaw 占用过多内存。

**解决**:
- 减少并发对话数
- 定期清理历史记录
- 使用更小的模型
- 重启服务释放内存

### 3. CPU 使用率高

**问题**: CPU 使用率异常高。

**解决**:
- 检查是否有后台任务运行
- 查看定时任务配置
- 确认 MCP 客户端连接状态

---

## 安全问题

### 1. 工具执行被拦截

**问题**: 正常命令被工具守卫拦截。

**解决**:
- 检查命令是否在黑名单
- 确认命令参数安全性
- 临时调整守卫规则（谨慎操作）

### 2. 文件访问被拒绝

**问题**: 无法访问某些文件。

**解决**:
- 检查文件路径是否在保护列表
- 确认文件权限
- 查看 [安全文档](https://copaw.agentscope.io/docs/security)

### 3. API Key 泄露

**问题**: API Key 可能泄露。

**解决**:
- 立即重新生成 API Key
- 更新 CoPaw 配置
- 检查日志和监控
- 查看 [安全最佳实践](https://copaw.agentscope.io/docs/security)

---

## 其他问题

### 1. 升级后配置不兼容

**问题**: 升级版本后配置失效。

**解决**:
```bash
# 清除浏览器缓存
Ctrl+Shift+R (Windows/Linux)
Cmd+Shift+R (macOS)

# 重新初始化配置
copaw init

# 或手动迁移配置
# 参见 Migration 文档
```

### 2. 如何备份数据

**解决**:
```bash
# 备份工作目录
tar -czf copaw-backup-$(date +%Y%m%d).tar.gz ~/.copaw/

# 仅备份配置
cp ~/.copaw/config.json ~/copaw-config-backup.json
```

### 3. 如何完全重置

**问题**: 想要完全重置 CoPaw。

**解决**:
```bash
# 停止服务
copaw shutdown

# 卸载并删除所有数据
copaw uninstall --purge

# 重新安装
pip install copaw
copaw init --defaults
```

### 4. 如何获取帮助

**解决**:
- 查看官方文档: https://copaw.agentscope.io/docs
- 提交 Issue: https://github.com/agentscope-ai/CoPaw/issues
- 加入社区讨论: https://github.com/agentscope-ai/CoPaw/discussions
- Discord: https://discord.gg/eYMpfnkG8h

---

## 错误代码参考

| 错误代码 | 说明 | 解决方案 |
|----------|------|----------|
| `E001` | API Key 无效 | 检查并重新配置 API Key |
| `E002` | 网络连接失败 | 检查网络和代理设置 |
| `E003` | 模型不可用 | 检查模型是否已启用 |
| `E004` | 配额不足 | 充值或等待配额恢复 |
| `E005` | 权限不足 | 检查文件和系统权限 |
| `E006` | 技能加载失败 | 检查技能文件完整性 |
| `E007` | 渠道连接失败 | 检查渠道配置 |
| `E008` | 记忆操作失败 | 检查磁盘空间和权限 |
| `E009` | 任务超时 | 增加超时时间或简化任务 |
| `E010` | 资源冲突 | 重试或检查并发操作 |
