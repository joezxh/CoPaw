# 🌍 企业版完整国际化修复方案

## 📋 修复概述

本次修复分为两个阶段：
1. ✅ **阶段一：登录页面国际化**（已完成）
2. 🔄 **阶段二：企业版页面国际化**（需要逐步实施）

---

## ✅ 阶段一：登录页面国际化（已完成）

### 修复内容

#### 1. 添加语言和主题切换按钮

**文件**: [LoginPage/index.tsx](file:///d:/projects/copaw/console/src/pages/Login/index.tsx)

```tsx
// 导入组件
import LanguageSwitcher from "../../components/LanguageSwitcher";
import ThemeToggleButton from "../../components/ThemeToggleButton";

// 在右上角添加切换按钮
<div style={{ position: "absolute", top: 24, right: 24, display: "flex", gap: 12 }}>
  <LanguageSwitcher />
  <ThemeToggleButton />
</div>
```

#### 2. 修复缺失的翻译键

```tsx
// ❌ 修复前：使用 fallback 文本
{isRegister
  ? t("login.alreadyHaveAccount") || "Already have an account? Login"
  : t("login.noAccount") || "No account? Register first"}

// ✅ 修复后：直接使用翻译键
{isRegister
  ? t("login.alreadyHaveAccount")
  : t("login.noAccount")}
```

#### 3. 添加翻译键到所有语言包

| 语言 | 键 | 翻译 |
|------|-----|------|
| 中文 | `login.noAccount` | 没有账号？先注册 |
| 中文 | `login.alreadyHaveAccount` | 已有账号？去登录 |
| English | `login.noAccount` | No account? Register first |
| English | `login.alreadyHaveAccount` | Already have an account? Login |
| 日本語 | `login.noAccount` | アカウントをお持ちでないですか？先に登録 |
| 日本語 | `login.alreadyHaveAccount` | すでにアカウントをお持ちですか？ログイン |
| Русский | `login.noAccount` | Нет аккаунта? Зарегистрируйтесь сначала |
| Русский | `login.alreadyHaveAccount` | Уже есть аккаунт? Войти |

### 验证步骤

1. 打开登录页面
2. 确认右上角有语言和主题切换按钮
3. 切换语言，验证"没有账号？先注册"文本正确显示
4. 点击切换，验证登录/注册切换功能正常

---

## 🔄 阶段二：企业版页面国际化（实施指南）

### 需要国际化的页面

`console/src/pages/Enterprise/` 目录下共有 8 个模块：

| 模块 | 文件 | 优先级 |
|------|------|--------|
| 用户管理 | `Users/UserList.tsx` | 🔴 高 |
| 角色权限 | `Roles/RoleList.tsx` | 🔴 高 |
| 用户组 | `Groups/GroupList.tsx` | 🟡 中 |
| 工作流 | `Workflows/WorkflowList.tsx` | 🟡 中 |
| 任务管理 | `Tasks/TaskList.tsx` | 🟡 中 |
| DLP 规则 | `Security/DLPRules.tsx` | 🟢 低 |
| 告警规则 | `Security/AlertRules.tsx` | 🟢 低 |
| Dify 连接器 | `Dify/DifyConnectors.tsx` | 🟢 低 |
| 审计日志 | `Audit/AuditLog.tsx` | 🟢 低 |

### 国际化实施步骤

#### 步骤 1: 识别硬编码文本

查找所有硬编码的中英文文本：

```bash
# 查找中文硬编码
grep -r "['\"]\u4e00-\u9fff" console/src/pages/Enterprise/

# 查找英文硬编码
grep -rE "['\"][A-Z][a-z]+ [A-Z]" console/src/pages/Enterprise/
```

#### 步骤 2: 添加 i18n 键到语言包

在 `zh.json`, `en.json`, `ja.json`, `ru.json` 中添加 `enterprise` 命名空间：

```json
{
  "enterprise": {
    "users": {
      "title": "用户管理",
      "addUser": "添加用户",
      "editUser": "编辑用户",
      "deleteConfirm": "确定删除此用户？",
      "username": "用户名",
      "email": "邮箱",
      "role": "角色",
      "status": "状态",
      "actions": "操作",
      "edit": "编辑",
      "delete": "删除",
      "searchPlaceholder": "搜索用户...",
      "total": "共 {{count}} 个用户"
    },
    "roles": {
      "title": "角色权限",
      "addRole": "添加角色",
      "roleName": "角色名称",
      "permissions": "权限",
      // ...
    },
    // 其他模块...
  }
}
```

#### 步骤 3: 修改页面组件

```tsx
// ❌ 修复前
import { Table, Button } from 'antd';

const columns = [
  {
    title: '用户名',  // 硬编码
    dataIndex: 'username',
  },
  {
    title: '操作',
    render: () => (
      <Button>编辑</Button>  // 硬编码
    )
  }
];

// ✅ 修复后
import { useTranslation } from 'react-i18next';
import { Table, Button } from 'antd';

const UserList = () => {
  const { t } = useTranslation();
  
  const columns = [
    {
      title: t('enterprise.users.username'),  // 使用翻译
      dataIndex: 'username',
    },
    {
      title: t('enterprise.users.actions'),
      render: () => (
        <Button>{t('common.edit')}</Button>  // 使用翻译
      )
    }
  ];
  
  return (
    <div>
      <h1>{t('enterprise.users.title')}</h1>
      <Button>{t('enterprise.users.addUser')}</Button>
      <Table columns={columns} />
    </div>
  );
};
```

#### 步骤 4: 常见文本翻译对照表

| 中文 | English | 日本語 | Русский | i18n Key |
|------|---------|---------|---------|----------|
| 用户管理 | User Management | ユーザー管理 | Управление пользователями | `enterprise.users.title` |
| 添加用户 | Add User | ユーザー追加 | Добавить пользователя | `enterprise.users.addUser` |
| 编辑用户 | Edit User | ユーザー編集 | Редактировать | `enterprise.users.editUser` |
| 删除用户 | Delete User | ユーザー削除 | Удалить | `enterprise.users.deleteUser` |
| 用户名 | Username | ユーザー名 | Имя пользователя | `enterprise.users.username` |
| 邮箱 | Email | メール | Email | `enterprise.users.email` |
| 角色 | Role | ロール | Роль | `enterprise.users.role` |
| 状态 | Status | ステータス | Статус | `enterprise.users.status` |
| 启用 | Enabled | 有効 | Включено | `common.enabled` |
| 禁用 | Disabled | 無効 | Отключено | `common.disabled` |
| 确定删除？ | Confirm delete? | 削除してもよろしいですか？ | Подтвердить удаление？ | `common.deleteConfirm` |
| 搜索 | Search | 検索 | Поиск | `common.search` |
| 保存 | Save | 保存 | Сохранить | `common.save` |
| 取消 | Cancel | キャンセル | Отмена | `common.cancel` |

### 实施优先级

#### 🔴 高优先级（核心功能）

1. **用户管理** (`Users/UserList.tsx`)
   - 列表表格列名
   - 按钮文本
   - 表单标签
   - 提示信息

2. **角色权限** (`Roles/RoleList.tsx`)
   - 角色列表
   - 权限配置
   - 权限树

#### 🟡 中优先级（常用功能）

3. **用户组** (`Groups/GroupList.tsx`)
4. **工作流** (`Workflows/WorkflowList.tsx`)
5. **任务管理** (`Tasks/TaskList.tsx`)

#### 🟢 低优先级（辅助功能）

6. **DLP 规则** (`Security/DLPRules.tsx`)
7. **告警规则** (`Security/AlertRules.tsx`)
8. **Dify 连接器** (`Dify/DifyConnectors.tsx`)
9. **审计日志** (`Audit/AuditLog.tsx`)

---

## 📝 修改文件清单

### 阶段一（已完成）

| 文件 | 修改内容 | 状态 |
|------|---------|------|
| `LoginPage/index.tsx` | 添加 LanguageSwitcher 和 ThemeToggleButton | ✅ |
| `LoginPage/index.tsx` | 移除 fallback 文本 | ✅ |
| `zh.json` | 添加 `login.noAccount` 和 `login.alreadyHaveAccount` | ✅ |
| `en.json` | 添加 `login.noAccount` 和 `login.alreadyHaveAccount` | ✅ |
| `ja.json` | 添加 `login.noAccount` 和 `login.alreadyHaveAccount` | ✅ |
| `ru.json` | 添加 `login.noAccount` 和 `login.alreadyHaveAccount` | ✅ |

### 阶段二（待实施）

需要为以下模块创建翻译：

- [ ] `enterprise.users.*` - 用户管理
- [ ] `enterprise.roles.*` - 角色权限
- [ ] `enterprise.groups.*` - 用户组
- [ ] `enterprise.workflows.*` - 工作流
- [ ] `enterprise.tasks.*` - 任务管理
- [ ] `enterprise.dlp.*` - DLP 规则
- [ ] `enterprise.alerts.*` - 告警规则
- [ ] `enterprise.dify.*` - Dify 连接器
- [ ] `enterprise.audit.*` - 审计日志

---

## 🧪 验证清单

### 登录页面

- [ ] 右上角显示语言切换按钮
- [ ] 右上角显示主题切换按钮
- [ ] 切换到中文，"没有账号？先注册" 显示正确
- [ ] 切换到英文，"No account? Register first" 显示正确
- [ ] 切换到日语，"アカウントをお持ちでないですか？先に登録" 显示正确
- [ ] 切换到俄语，"Нет аккаунта? Зарегистрируйтесь сначала" 显示正确
- [ ] 点击切换链接，登录/注册切换正常

### 企业版页面（待实施）

- [ ] 用户管理页面所有文本已国际化
- [ ] 角色权限页面所有文本已国际化
- [ ] 所有表单标签、按钮、提示信息都已翻译
- [ ] 切换语言后页面布局正常
- [ ] 所有 4 种语言翻译完整

---

## 💡 最佳实践

### 1. 使用命名空间组织翻译

```json
{
  "enterprise": {
    "users": { ... },
    "roles": { ... },
    "groups": { ... }
  }
}
```

### 2. 复用通用翻译

```tsx
// ❌ 不推荐
t('enterprise.users.edit')     // "编辑"
t('enterprise.roles.edit')     // "编辑"
t('enterprise.groups.edit')    // "编辑"

// ✅ 推荐
t('common.edit')               // "编辑" - 所有地方复用
```

### 3. 使用插值处理动态内容

```tsx
// ❌ 不推荐
t('enterprise.users.total') + users.length + '个用户'

// ✅ 推荐
t('enterprise.users.total', { count: users.length })
// zh: "共 5 个用户"
// en: "Total 5 users"
```

### 4. 保持一致的命名规范

```
enterprise.users.add           // 添加用户
enterprise.users.edit          // 编辑用户
enterprise.users.delete        // 删除用户
enterprise.users.search        // 搜索用户
```

---

## 🚀 下一步行动

1. **立即验证**：刷新浏览器，测试登录页面的语言和主题切换
2. **逐步实施**：按照优先级从高到低，逐个模块进行国际化
3. **持续验证**：每完成一个模块，立即测试 4 种语言的显示效果

---

**修复时间**: 2026-04-13  
**阶段一状态**: ✅ 已完成  
**阶段二状态**: 🔄 待实施  
**预计工作量**: 2-3 天（取决于页面复杂度）
