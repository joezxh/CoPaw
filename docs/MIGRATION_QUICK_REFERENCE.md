# CoPaw 个人版 → 企业版 迁移快速参考

## 🚀 快速开始

### 1️⃣ 预览迁移 (推荐先执行)
```powershell
.\scripts\migrate-to-enterprise.ps1 -DryRun
```

### 2️⃣ 执行迁移
```powershell
.\scripts\migrate-to-enterprise.ps1 `
  -PostgresUrl "postgresql://用户名:密码@localhost:5432/数据库名"
```

### 3️⃣ 验证登录
```powershell
# 使用原用户名密码登录企业版
# 访问: http://localhost:8088
```

---

## 📊 迁移内容

| 项目 | 来源 | 目标 | 状态 |
|------|------|------|------|
| 用户认证 | `auth.json` | `sys_users` | ✅ 自动 |
| 租户信息 | - | `sys_tenants` | ✅ 创建默认 |
| 角色权限 | - | `sys_roles` | ✅ 创建admin |
| 工作空间 | - | `sys_workspaces` | ✅ 创建默认 |
| Agent配置 | `working/workspaces/` | `ai_agents` | ✅ 自动 |
| 记忆数据 | SQLite | SQLite | ⏭️ 保持不变 |

---

## ⚙️ 常用参数

```powershell
# 仅迁移认证数据
.\scripts\migrate-to-enterprise.ps1 `
  -PostgresUrl "postgresql://..." `
  -SkipAgents

# 跳过认证 (已手动创建用户)
.\scripts\migrate-to-enterprise.ps1 `
  -PostgresUrl "postgresql://..." `
  -SkipAuth

# 预览模式 (不执行)
.\scripts\migrate-to-enterprise.ps1 -DryRun
```

---

## 🔍 验证查询

```sql
-- 检查用户
SELECT username, status, created_at FROM sys_users;

-- 检查角色分配
SELECT u.username, r.name as role
FROM sys_users u
JOIN sys_user_roles ur ON u.id = ur.user_id
JOIN sys_roles r ON ur.role_id = r.id;

-- 检查工作空间
SELECT name, is_default FROM sys_workspaces;

-- 检查Agent
SELECT name, status FROM ai_agents;
```

---

## ⚠️ 注意事项

1. **备份优先**: 迁移前备份 `working.secret/auth.json`
2. **密码保留**: 原密码可直接使用,无需重置
3. **幂等安全**: 可重复执行,不会创建重复数据
4. **事务保护**: 失败自动回滚,数据不损坏

---

## 🆘 常见问题

**Q: 提示数据库连接失败?**  
A: 检查PostgreSQL服务是否启动,连接字符串是否正确

**Q: 提示表不存在?**  
A: 先运行企业版初始化: `.\scripts\start-enterprise.ps1`

**Q: 用户已存在?**  
A: 正常,脚本会自动跳过,可安全重试

**Q: YAML格式的Agent配置?**  
A: 当前仅支持JSON,需手动转换为JSON格式

---

## 📞 获取帮助

- 完整文档: `docs/MIGRATION_GUIDE.md`
- 测试脚本: `tests/unit/test_migration_personal_to_enterprise.py`
- 迁移工具: `scripts/migrate_personal_to_enterprise.py`

---

**版本**: 1.0.0 | **更新**: 2026-04-12
