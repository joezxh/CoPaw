# CoPaw 个人版 → 企业版 数据迁移指南

## 📋 概述

本指南说明如何将CoPaw个人版的数据迁移到企业版PostgreSQL数据库,实现从单用户模式到多租户企业架构的升级。

## 🗂️ 数据架构对比

### 个人版 (OSS)
```
个人版数据存储:
├─ auth.json                 # 用户认证信息 (用户名、密码哈希、JWT密钥)
├─ config.json               # 系统配置
├─ working/
│  ├─ workspaces/            # 工作空间目录
│  │  └─ <workspace>/
│  │     ├─ agent.yaml       # Agent配置
│  │     └─ agent.json       # Agent配置(备选)
│  └─ skill_pool/            # 技能池
└─ *.db                      # SQLite数据库 (ReMe记忆系统)
```

### 企业版 (Enterprise)
```
企业版数据存储 (PostgreSQL):
├─ sys_tenants               # 租户表
├─ sys_users                 # 用户表 (多租户)
├─ sys_roles                 # 角色表
├─ sys_permissions           # 权限表
├─ sys_user_roles            # 用户-角色关联
├─ sys_workspaces            # 工作空间表
├─ sys_user_groups           # 用户组表
├─ ai_agents                 # Agent配置表
├─ ai_workflows              # 工作流表
└─ ...                       # 其他企业表
```

## 🔄 迁移数据映射

| 个人版数据 | 企业版表 | 说明 |
|-----------|---------|------|
| `auth.json` 中的 `user` | `sys_users` | 用户认证信息,保留密码哈希 |
| - | `sys_tenants` | 创建默认租户 `domain='default'` |
| - | `sys_roles` | 创建 `admin` 系统角色 |
| - | `sys_user_roles` | 为用户分配admin角色 |
| - | `sys_workspaces` | 创建默认工作空间 |
| `workspaces/*/agent.json` | `ai_agents` | Agent配置JSON |
| SQLite记忆数据库 | 保持不变 | ReMe继续使用SQLite,不迁移 |

## 🚀 迁移步骤

### 前置条件

1. **安装PostgreSQL** (如果尚未安装)
   ```bash
   # Windows (使用Chocolatey)
   choco install postgresql

   # 或从官网下载: https://www.postgresql.org/download/
   ```

2. **创建企业版数据库**
   ```sql
   CREATE DATABASE copaw_enterprise;
   CREATE USER copaw WITH PASSWORD 'your_password';
   GRANT ALL PRIVILEGES ON DATABASE copaw_enterprise TO copaw;
   ```

3. **执行数据库初始化**
   ```powershell
   # 运行企业版初始化脚本
   .\scripts\start-enterprise.ps1
   ```

### 方式一: 使用PowerShell脚本 (推荐)

#### 1. 预览迁移 (不执行)
```powershell
.\scripts\migrate-to-enterprise.ps1 -DryRun
```

#### 2. 执行完整迁移
```powershell
.\scripts\migrate-to-enterprise.ps1 `
  -PostgresUrl "postgresql://copaw:your_password@localhost:5432/copaw_enterprise"
```

#### 3. 仅迁移认证数据
```powershell
.\scripts\migrate-to-enterprise.ps1 `
  -PostgresUrl "postgresql://copaw:your_password@localhost:5432/copaw_enterprise" `
  -SkipAgents
```

### 方式二: 直接使用Python脚本

```bash
# 预览模式
python scripts/migrate_personal_to_enterprise.py \
  --postgres-url "postgresql://copaw:password@localhost:5432/copaw_enterprise" \
  --dry-run

# 执行迁移
python scripts/migrate_personal_to_enterprise.py \
  --postgres-url "postgresql://copaw:password@localhost:5432/copaw_enterprise"

# 仅迁移认证数据
python scripts/migrate_personal_to_enterprise.py \
  --postgres-url "postgresql://copaw:password@localhost:5432/copaw_enterprise" \
  --skip-agents
```

## 📊 迁移过程说明

### 步骤 1: 验证数据库连接
- 测试PostgreSQL连接
- 确认数据库版本和权限

### 步骤 2: 迁移用户认证数据
1. 读取 `auth.json` 文件
2. 创建默认租户 (`domain='default'`)
3. 创建用户记录 (`sys_users`),保留原密码哈希
4. 创建 `admin` 角色 (如果不存在)
5. 为用户分配 `admin` 角色

### 步骤 3: 迁移工作空间
1. 创建默认工作空间 (`is_default=true`)
2. 关联到迁移的用户

### 步骤 4: 迁移Agent配置
1. 扫描 `working/workspaces/` 目录
2. 读取 `agent.json` 或 `agent.yaml` 配置文件
3. 将配置存储到 `ai_agents` 表
4. 保留原始配置JSON

## ⚠️ 注意事项

### 密码兼容性
- ✅ **保留原密码**: 迁移时直接使用个人版的密码哈希,用户可以使用原密码登录
- ✅ **算法一致**: 个人版和企业版都使用 salted SHA-256
- ⚠️ **安全性**: 建议迁移后启用 bcrypt 加密 (企业版默认)

### 记忆数据
- 📌 **SQLite保持不变**: ReMe记忆系统继续使用SQLite存储
- 📌 **无需迁移**: 记忆数据与用户ID无关,存储在独立数据库中
- 📌 **多用户支持**: 企业版可以为每个用户配置独立的记忆数据库

### 配置文件
- ⚠️ **YAML配置**: 当前仅支持JSON格式的Agent配置迁移
- ⚠️ **手动迁移**: YAML配置需要手动转换为JSON格式

### 数据完整性
- ✅ **事务保护**: 所有数据库操作使用事务,失败时自动回滚
- ✅ **幂等性**: 可以重复执行,不会创建重复数据
- ✅ **预览模式**: 使用 `--dry-run` 预览迁移计划

## 🔍 验证迁移结果

### 1. 检查用户数据
```sql
SELECT id, username, email, status, created_at 
FROM sys_users 
WHERE username = 'your_username';
```

### 2. 检查角色分配
```sql
SELECT u.username, r.name as role_name, ur.assigned_at
FROM sys_users u
JOIN sys_user_roles ur ON u.id = ur.user_id
JOIN sys_roles r ON ur.role_id = r.id
WHERE u.username = 'your_username';
```

### 3. 检查工作空间
```sql
SELECT id, name, is_default, owner_id 
FROM sys_workspaces 
WHERE is_default = true;
```

### 4. 检查Agent数据
```sql
SELECT id, name, workspace_id, status, created_at
FROM ai_agents;
```

### 5. 登录测试
```bash
# 使用原用户名密码登录
curl -X POST http://localhost:8088/api/enterprise/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"your_username","password":"your_password"}'
```

## 🛠️ 故障排除

### 问题1: 数据库连接失败
```
错误: could not connect to server
```
**解决方案**:
- 确认PostgreSQL服务已启动
- 检查连接字符串格式是否正确
- 验证用户名密码和网络连通性

### 问题2: 权限不足
```
错误: permission denied for table sys_users
```
**解决方案**:
```sql
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO copaw;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO copaw;
```

### 问题3: 表不存在
```
错误: relation "sys_users" does not exist
```
**解决方案**:
- 先运行企业版初始化脚本: `.\scripts\start-enterprise.ps1`
- 或手动运行Alembic迁移: `alembic upgrade head`

### 问题4: 用户已存在
```
信息: 用户已存在,跳过创建
```
**说明**: 这是正常行为,迁移脚本具有幂等性,可以安全重试。

## 📝 迁移后操作

### 1. 启用企业版服务
```powershell
.\scripts\start-enterprise.ps1
```

### 2. 访问企业版控制台
```
http://localhost:8088
```

### 3. 验证功能
- ✅ 使用原用户名密码登录
- ✅ 检查用户管理页面
- ✅ 检查Agent列表
- ✅ 测试Agent功能

### 4. 可选优化
- [ ] 启用MFA多因素认证
- [ ] 配置DLP数据防泄漏规则
- [ ] 设置安全告警规则
- [ ] 创建更多用户和角色
- [ ] 配置用户组

## 🔒 安全建议

1. **备份数据**: 迁移前备份 `auth.json` 和工作目录
2. **修改密码**: 迁移后建议修改密码,使用企业版bcrypt加密
3. **启用MFA**: 为管理员账户启用多因素认证
4. **定期审计**: 启用审计日志,监控用户活动
5. **最小权限**: 为不同用户分配最小必需权限

## 📞 技术支持

如遇问题,请提供:
- 迁移日志输出
- PostgreSQL版本
- 个人版和企业版版本号
- 错误堆栈信息

---

**版本**: 1.0.0  
**更新日期**: 2026-04-12  
**维护者**: CoPaw Team
