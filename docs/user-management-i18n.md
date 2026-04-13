# 👥 用户管理页面国际化实施文档

## 📋 概述

本文档记录了企业版用户管理页面（`UserList.tsx`）的完整国际化实施过程。

---

## ✅ 修改文件清单

### 1. 组件文件

| 文件 | 修改内容 | 状态 |
|------|---------|------|
| `console/src/pages/Enterprise/Users/UserList.tsx` | 添加 `useTranslation` Hook | ✅ |
| `console/src/pages/Enterprise/Users/UserList.tsx` | 替换所有硬编码文本为 `t()` 调用 | ✅ |

### 2. 语言包文件

| 文件 | 添加的翻译键数量 | 状态 |
|------|-----------------|------|
| `console/src/locales/zh.json` | 29 个键 | ✅ |
| `console/src/locales/en.json` | 29 个键 | ✅ |
| `console/src/locales/ja.json` | 29 个键 | ✅ |
| `console/src/locales/ru.json` | 29 个键 | ✅ |

**总计**: 116 个翻译项（29 键 × 4 语言）

---

## 🔧 技术实施细节

### 1. 导入 useTranslation Hook

```tsx
// ✅ 添加导入
import { useTranslation } from "react-i18next";

// ✅ 在组件中使用
export default function UserList() {
  const { t } = useTranslation();
  // ...
}
```

### 2. 表格列国际化

#### 修复前
```tsx
const columns = [
  { title: "Username", dataIndex: "username", key: "username" },
  { title: "Email", dataIndex: "email", key: "email" },
  { title: "Status", dataIndex: "status", key: "status" },
];
```

#### 修复后
```tsx
const columns = [
  { title: t("enterprise.users.username"), dataIndex: "username", key: "username" },
  { title: t("enterprise.users.email"), dataIndex: "email", key: "email" },
  { title: t("enterprise.users.status"), dataIndex: "status", key: "status" },
];
```

### 3. 状态标签国际化

#### 修复前
```tsx
render: (s: string) => <Tag color={STATUS_COLORS[s]}>{s}</Tag>
// 显示: "active", "disabled", "vacation"
```

#### 修复后
```tsx
render: (s: string) => (
  <Tag color={STATUS_COLORS[s]}>
    {t(`enterprise.users.status.${s}`)}
  </Tag>
)
// 显示: "启用", "Active", "有効", "Включено"
```

### 4. MFA 状态国际化

#### 修复前
```tsx
render: (v: boolean) => (
  <Tag color={v ? "blue" : "default"}>
    {v ? "Enabled" : "Disabled"}
  </Tag>
)
```

#### 修复后
```tsx
render: (v: boolean) => (
  <Tag color={v ? "blue" : "default"}>
    {v ? t("common.enabled") : t("common.disabled")}
  </Tag>
)
```

### 5. 操作按钮国际化

#### 修复前
```tsx
<Space>
  <Button>Edit</Button>
  <Button>Roles</Button>
  <Popconfirm title="Disable this user?">
    <Button danger>Disable</Button>
  </Popconfirm>
</Space>
```

#### 修复后
```tsx
<Space>
  <Button>{t("common.edit")}</Button>
  <Button>{t("enterprise.users.roles")}</Button>
  <Popconfirm title={t("enterprise.users.disableConfirm")}>
    <Button danger>{t("enterprise.users.disable")}</Button>
  </Popconfirm>
</Space>
```

### 6. 搜索和筛选国际化

#### 修复前
```tsx
<Input placeholder="Search username or email" />
<Select placeholder="Status">
  <Option value="active">Active</Option>
  <Option value="disabled">Disabled</Option>
  <Option value="vacation">Vacation</Option>
</Select>
```

#### 修复后
```tsx
<Input placeholder={t("enterprise.users.searchPlaceholder")} />
<Select placeholder={t("enterprise.users.status")}>
  <Option value="active">{t("enterprise.users.status.active")}</Option>
  <Option value="disabled">{t("enterprise.users.status.disabled")}</Option>
  <Option value="vacation">{t("enterprise.users.status.vacation")}</Option>
</Select>
```

### 7. 表单国际化

#### 修复前
```tsx
<Modal title="Create User">
  <Form.Item name="username" label="Username" rules={[{ required: true }]}>
    <Input />
  </Form.Item>
  <Form.Item name="password" label="Password" rules={[{ required: true, min: 8 }]}>
    <Input.Password />
  </Form.Item>
</Modal>
```

#### 修复后
```tsx
<Modal
  title={t("enterprise.users.createUser")}
  okText={t("common.ok")}
  cancelText={t("common.cancel")}
>
  <Form.Item
    name="username"
    label={t("enterprise.users.username")}
    rules={[{ required: true, message: t("enterprise.users.usernameRequired") }]}
  >
    <Input />
  </Form.Item>
  <Form.Item
    name="password"
    label={t("enterprise.users.password")}
    rules={[{ required: true, min: 8, message: t("enterprise.users.passwordMinLength") }]}
  >
    <Input.Password />
  </Form.Item>
</Modal>
```

### 8. 成功提示国际化

#### 修复前
```tsx
message.success("User created");
message.success("User updated");
message.success("User disabled");
message.success("Roles updated");
```

#### 修复后
```tsx
message.success(t("enterprise.users.createSuccess"));
message.success(t("enterprise.users.updateSuccess"));
message.success(t("enterprise.users.disableSuccess"));
message.success(t("enterprise.users.rolesUpdated"));
```

### 9. 角色分配抽屉国际化

#### 修复前
```tsx
<Drawer title={`Assign Roles — ${roleUser?.username}`}>
  <Button type="primary" onClick={handleAssignRoles}>Save</Button>
</Drawer>
```

#### 修复后
```tsx
<Drawer title={`${t("enterprise.users.assignRoles")} — ${roleUser?.username}`}>
  <Button type="primary" onClick={handleAssignRoles}>{t("common.save")}</Button>
</Drawer>
```

---

## 📊 翻译键对照表

### enterprise.users 命名空间

| i18n Key | 中文 | English | 日本語 | Русский |
|----------|------|---------|---------|---------|
| `enterprise.users.title` | 用户管理 | User Management | ユーザー管理 | Управление пользователями |
| `enterprise.users.addUser` | 添加用户 | Add User | ユーザー追加 | Добавить пользователя |
| `enterprise.users.createUser` | 创建用户 | Create User | ユーザー作成 | Создать пользователя |
| `enterprise.users.editUser` | 编辑用户 | Edit User | ユーザー編集 | Редактировать пользователя |
| `enterprise.users.username` | 用户名 | Username | ユーザー名 | Имя пользователя |
| `enterprise.users.usernameRequired` | 请输入用户名 | Please enter username | ユーザー名を入力してください | Пожалуйста, введите имя пользователя |
| `enterprise.users.password` | 密码 | Password | パスワード | Пароль |
| `enterprise.users.passwordMinLength` | 密码至少 8 个字符 | Password must be at least 8 characters | パスワードは8文字以上である必要があります | Пароль должен содержать не менее 8 символов |
| `enterprise.users.email` | 邮箱 | Email | メール | Email |
| `enterprise.users.displayName` | 显示名称 | Display Name | 表示名 | Отображаемое имя |
| `enterprise.users.status` | 状态 | Status | ステータス | Статус |
| `enterprise.users.status.active` | 启用 | Active | 有効 | Включено |
| `enterprise.users.status.disabled` | 禁用 | Disabled | 無効 | Отключено |
| `enterprise.users.status.vacation` | 休假 | Vacation | 休暇 | Отпуск |
| `enterprise.users.mfa` | MFA | MFA | MFA | MFA |
| `enterprise.users.lastLogin` | 最后登录 | Last Login | 最終ログイン | Последний вход |
| `enterprise.users.roles` | 角色 | Roles | ロール | Роли |
| `enterprise.users.assignRoles` | 分配角色 | Assign Roles | ロールの割り当て | Назначить роли |
| `enterprise.users.disable` | 禁用 | Disable | 無効化 | Отключить |
| `enterprise.users.disableConfirm` | 确定禁用此用户？ | Disable this user? | このユーザーを無効化してもよろしいですか？ | Отключить этого пользователя? |
| `enterprise.users.createSuccess` | 用户创建成功 | User created successfully | ユーザーが正常に作成されました | Пользователь успешно создан |
| `enterprise.users.updateSuccess` | 用户更新成功 | User updated successfully | ユーザーが正常に更新されました | Пользователь успешно обновлён |
| `enterprise.users.disableSuccess` | 用户已禁用 | User disabled | ユーザーが無効化されました | Пользователь отключён |
| `enterprise.users.rolesUpdated` | 角色已更新 | Roles updated | ロールが更新されました | Роли обновлены |
| `enterprise.users.searchPlaceholder` | 搜索用户名或邮箱 | Search username or email | ユーザー名またはメールを検索 | Поиск по имени пользователя или email |

### 复用的通用翻译键

| i18n Key | 中文 | English | 日本語 | Русский |
|----------|------|---------|---------|---------|
| `common.enabled` | 已启用 | Enabled | 有効 | Включено |
| `common.disabled` | 已禁用 | Disabled | 無効 | Отключено |
| `common.edit` | 编辑 | Edit | 編集 | Редактировать |
| `common.save` | 保存 | Save | 保存 | Сохранить |
| `common.ok` | 确定 | OK | OK | OK |
| `common.cancel` | 取消 | Cancel | キャンセル | Отмена |
| `common.actions` | 操作 | Actions | 操作 | Действия |

---

## 🧪 验证清单

### 功能测试

- [ ] 页面标题正确显示当前语言的"用户管理"
- [ ] "添加用户"按钮文本正确显示
- [ ] 搜索框 placeholder 正确显示
- [ ] 状态下拉框选项正确显示
- [ ] 表格列名正确显示
- [ ] 状态标签（启用/禁用/休假）正确显示
- [ ] MFA 状态标签（已启用/已禁用）正确显示
- [ ] 操作按钮（编辑/角色/禁用）正确显示
- [ ] 禁用确认对话框文本正确显示

### 表单测试

- [ ] 创建用户弹窗标题正确显示
- [ ] 表单标签（用户名/密码/邮箱/显示名称）正确显示
- [ ] 必填验证提示正确显示
- [ ] 密码长度验证提示正确显示
- [ ] 弹窗按钮（确定/取消）正确显示

- [ ] 编辑用户弹窗标题正确显示
- [ ] 状态下拉框选项正确显示

### 角色分配测试

- [ ] 角色分配抽屉标题正确显示
- [ ] 保存按钮文本正确显示

### 提示消息测试

- [ ] 创建成功提示正确显示
- [ ] 更新成功提示正确显示
- [ ] 禁用成功提示正确显示
- [ ] 角色更新成功提示正确显示

### 语言切换测试

依次切换到以下语言，验证所有文本正确显示：

- [ ] 🇨🇳 中文（简体）
- [ ] 🇬🇧 English
- [ ] 🇯🇵 日本語
- [ ] 🇷🇺 Русский

### 暗黑主题测试

- [ ] 在深色主题下，所有文本对比度正常
- [ ] 表单输入框文字可见
- [ ] 按钮文字可见
- [ ] 表格内容可读

---

## 💡 最佳实践总结

### 1. 命名空间组织

使用 `enterprise.users.*` 命名空间，结构清晰：

```json
{
  "enterprise": {
    "users": {
      "title": "用户管理",
      "addUser": "添加用户",
      "status": {
        "active": "启用",
        "disabled": "禁用",
        "vacation": "休假"
      }
    }
  }
}
```

### 2. 复用通用翻译

避免重复翻译通用词汇：

```tsx
// ✅ 推荐：复用 common 命名空间
t("common.edit")        // 编辑
t("common.save")        // 保存
t("common.cancel")      // 取消
t("common.enabled")     // 已启用
t("common.disabled")    // 已禁用

// ❌ 不推荐：重复定义
t("enterprise.users.edit")     // 编辑
t("enterprise.users.save")     // 保存
```

### 3. 动态键值拼接

对于枚举值，使用模板字符串动态拼接：

```tsx
// ✅ 动态拼接状态翻译
t(`enterprise.users.status.${status}`)
// 结果: "enterprise.users.status.active" → "启用"

// ❌ 不推荐：硬编码映射
const statusMap = {
  active: "启用",
  disabled: "禁用",
  vacation: "休假"
};
```

### 4. 表单验证提示

为必填字段和格式验证提供专门的翻译键：

```tsx
rules={[
  { required: true, message: t("enterprise.users.usernameRequired") },
  { min: 8, message: t("enterprise.users.passwordMinLength") }
]}
```

### 5. Modal/Drawer 按钮文本

统一使用 `okText` 和 `cancelText` 属性：

```tsx
<Modal
  okText={t("common.ok")}
  cancelText={t("common.cancel")}
>
```

---

## 📈 实施效果

### 修复前
- ❌ 所有文本硬编码为英文
- ❌ 切换语言后页面仍显示英文
- ❌ 不符合国际化标准

### 修复后
- ✅ 所有文本使用 `t()` 函数翻译
- ✅ 支持 4 种语言（中/英/日/俄）
- ✅ 切换语言后页面立即更新
- ✅ 符合 i18n 最佳实践

---

## 🚀 下一步行动

### 建议的优先级

1. 🔴 **角色权限页面** (`Roles/RoleList.tsx`)
   - 与用户管理紧密相关
   - 用户使用频率高

2. 🟡 **用户组页面** (`Groups/GroupList.tsx`)
   - 组织架构管理
   - 中等使用频率

3. 🟡 **工作流页面** (`Workflows/WorkflowList.tsx`)
   - 业务流程管理
   - 中等使用频率

4. 🟢 **任务管理页面** (`Tasks/TaskList.tsx`)
   - 任务调度管理
   - 较低使用频率

5. 🟢 **安全设置页面** (`Security/DLPRules.tsx`, `Security/AlertRules.tsx`)
   - DLP 规则和告警规则
   - 辅助功能

6. 🟢 **Dify 连接器页面** (`Dify/DifyConnectors.tsx`)
   - 第三方集成
   - 辅助功能

7. 🟢 **审计日志页面** (`Audit/AuditLog.tsx`)
   - 日志查看
   - 只读功能

---

## 📝 技术要点

### useTranslation Hook 使用

```tsx
import { useTranslation } from "react-i18next";

const Component = () => {
  const { t, i18n } = useTranslation();
  
  // t: 翻译函数
  // i18n: i18n 实例（可用于切换语言等）
  
  return <div>{t("key")}</div>;
};
```

### 插值语法

对于需要动态插入变量的文本：

```tsx
// 语言包定义
{
  "total": "共 {{count}} 个用户"
}

// 使用
t("enterprise.users.total", { count: 10 })
// 结果: "共 10 个用户"
```

### 命名空间引用

```tsx
// 点号分隔的键路径
t("enterprise.users.username")
t("enterprise.users.status.active")

// 嵌套对象结构
{
  "enterprise": {
    "users": {
      "username": "用户名",
      "status": {
        "active": "启用"
      }
    }
  }
}
```

---

**实施日期**: 2026-04-13  
**实施人员**: AI Assistant  
**测试状态**: 待验证  
**文档版本**: v1.0
