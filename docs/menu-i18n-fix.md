# 🌍 企业版布局国际化完整修复

## 📋 修复概述

本次修复全面解决了企业版布局的多语言国际化问题，确保所有菜单项和UI元素都能根据用户选择的语言正确显示。

---

## ✅ 修复内容

### 1. 菜单国际化

#### 问题
- 菜单项使用硬编码的中文文本
- 切换语言时菜单不会更新
- 英文/日语/俄语用户看到的是中文菜单

#### 修复方案

**文件 1: `constants.tsx`**

将硬编码文本改为 i18n key：

```typescript
// ❌ 修复前
{
  key: 'chat',
  label: '聊天',  // 硬编码中文
}

// ✅ 修复后
{
  key: 'chat',
  label: 'menu.chat',  // i18n key
}
```

**完整菜单 i18n key 映射**：

| 菜单项 | i18n Key |
|--------|----------|
| 聊天 | `menu.chat` |
| 控制台 | `menu.control` |
| 通道管理 | `menu.channels` |
| 会话管理 | `menu.sessions` |
| 定时任务 | `menu.cronJobs` |
| 心跳检测 | `menu.heartbeat` |
| Agent 管理 | `menu.agentManagement` |
| Agent 配置 | `menu.agentConfig` |
| 技能管理 | `menu.skills` |
| 工具管理 | `menu.tools` |
| MCP 服务 | `menu.mcp` |
| 工作空间 | `menu.workspace` |
| 设置 | `menu.settings` |
| 技能池 | `menu.skillPool` |
| 模型管理 | `menu.models` |
| 环境配置 | `menu.environments` |
| Agents | `menu.agents` |
| 安全设置 | `menu.security` |
| Token 使用 | `menu.tokenUsage` |
| 语音转写 | `menu.voiceTranscription` |
| 企业管理 | `menu.enterprise` |
| 用户管理 | `menu.enterpriseUsers` |
| 角色权限 | `menu.enterprisePermissions` |
| 用户组 | `menu.userGroups` |
| 工作流 | `menu.enterpriseWorkflows` |
| 任务管理 | `menu.enterpriseTasks` |
| DLP 规则 | `menu.dlpRules` |
| 告警规则 | `menu.alertRules` |
| Dify 连接器 | `menu.difyConnectors` |
| 审计日志 | `menu.enterpriseAudit` |

---

**文件 2: `Sidebar.tsx`**

修改 `convertToMenuItems` 函数使用 `t()` 翻译：

```typescript
// ❌ 修复前
function convertToMenuItems(menu: MenuItem[], t: (key: string) => string): any[] {
  return menu.map((item) => {
    const menuItem: any = {
      key: item.key,
      icon: item.icon,
      label: item.label,  // 直接使用硬编码文本
    };
    // ...
  });
}

// ✅ 修复后
function convertToMenuItems(menu: MenuItem[], t: (key: string) => string): any[] {
  return menu.map((item) => {
    const menuItem: any = {
      key: item.key,
      icon: item.icon,
      label: t(item.label),  // 使用 t() 翻译
    };
    // ...
  });
}
```

同时修复加载状态的文本：

```typescript
// ❌ 修复前
<div className={styles.loadingMenu}>加载中...</div>

// ✅ 修复后
<div className={styles.loadingMenu}>{t('common.loading')}</div>
```

---

### 2. 语言包翻译

为所有 4 种语言添加了完整的菜单翻译：

#### 中文 (zh.json)
```json
"menu": {
  "chat": "聊天",
  "control": "控制台",
  "channels": "通道管理",
  // ... 共 30 个菜单项
}
```

#### 英文 (en.json)
```json
"menu": {
  "chat": "Chat",
  "control": "Control",
  "channels": "Channels",
  // ... 共 30 个菜单项
}
```

#### 日语 (ja.json)
```json
"menu": {
  "chat": "チャット",
  "control": "コントロール",
  "channels": "チャンネル",
  // ... 共 30 个菜单项
}
```

#### 俄语 (ru.json)
```json
"menu": {
  "chat": "Чат",
  "control": "Управление",
  "channels": "Каналы",
  // ... 共 30 个菜单项
}
```

---

## 📊 翻译对照表

### 主菜单项

| 中文 | English | 日本語 | Русский |
|------|---------|---------|---------|
| 聊天 | Chat | チャット | Чат |
| 控制台 | Control | コントロール | Управление |
| Agent 管理 | Agent Management | エージェント管理 | Управление агентами |
| 设置 | Settings | 設定 | Настройки |
| 企业管理 | Enterprise | 企業管理 | Предприятие |

### 控制台子菜单

| 中文 | English | 日本語 | Русский |
|------|---------|---------|---------|
| 通道管理 | Channels | チャンネル | Каналы |
| 会话管理 | Sessions | セッション | Сессии |
| 定时任务 | Cron Jobs | 定期実行 | Задачи по расписанию |
| 心跳检测 | Heartbeat | ハートビート | Пульс |

### Agent 管理子菜单

| 中文 | English | 日本語 | Русский |
|------|---------|---------|---------|
| Agent 配置 | Agent Config | エージェント設定 | Конфигурация агента |
| 技能管理 | Skills | スキル | Навыки |
| 工具管理 | Tools | ツール | Инструменты |
| MCP 服务 | MCP Services | MCPサービス | MCP сервисы |
| 工作空间 | Workspace | ワークスペース | Рабочее пространство |

### 设置子菜单

| 中文 | English | 日本語 | Русский |
|------|---------|---------|---------|
| 技能池 | Skill Pool | スキルプール | Пул навыков |
| 模型管理 | Models | モデル | Модели |
| 环境配置 | Environments | 環境変数 | Переменные окружения |
| Agents | Agents | エージェント | Агенты |
| 安全设置 | Security | セキュリティ | Безопасность |
| Token 使用 | Token Usage | トークン使用量 | Использование токенов |
| 语音转写 | Voice Transcription | 音声文字起こし | Расшифровка голоса |

### 企业管理子菜单

| 中文 | English | 日本語 | Русский |
|------|---------|---------|---------|
| 用户管理 | User Management | ユーザー管理 | Управление пользователями |
| 角色权限 | Roles & Permissions | ロールと権限 | Роли и права |
| 用户组 | User Groups | ユーザーグループ | Группы пользователей |
| 工作流 | Workflows | ワークフロー | Рабочие процессы |
| 任务管理 | Tasks | タスク管理 | Задачи |
| DLP 规则 | DLP Rules | DLPルール | Правила DLP |
| 告警规则 | Alert Rules | アラートルール | Правила оповещений |
| Dify 连接器 | Dify Connectors | Difyコネクタ | Dify коннекторы |
| 审计日志 | Audit Logs | 監査ログ | Журнал аудита |

---

## 🧪 验证步骤

### 1. 测试菜单切换

1. 启动应用并登录
2. 点击 Header 右上角的语言切换按钮
3. 依次切换到：
   - ✅ 简体中文 → 菜单显示中文
   - ✅ English → 菜单显示英文
   - ✅ 日本語 → 菜单显示日语
   - ✅ Русский → 菜单显示俄语

### 2. 检查菜单项

对于每种语言，检查以下菜单项：

#### 主菜单（5 个）
- 聊天 / Chat / チャット / Чат
- 控制台 / Control / コントロール / Управление
- Agent 管理 / Agent Management / エージェント管理 / Управление агентами
- 设置 / Settings / 設定 / Настройки
- 企业管理 / Enterprise / 企業管理 / Предприятие

#### 子菜单（共 25 个）
确保所有子菜单项都正确显示对应语言的文本。

### 3. 检查加载状态

1. 清除浏览器缓存
2. 刷新页面
3. 查看侧边栏加载时的文本：
   - 中文：`加载中...`
   - 英文：`Loading...`
   - 日语：`読み込み中...`
   - 俄语：`Загрузка...`

### 4. 检查权限过滤

1. 使用不同权限的用户登录
2. 检查菜单是否根据权限正确过滤
3. 验证过滤后的菜单项翻译正确

---

## 📝 修改文件清单

| 文件 | 修改内容 | 状态 |
|------|---------|------|
| `constants.tsx` | 所有菜单 label 改为 i18n key | ✅ |
| `Sidebar.tsx` | `convertToMenuItems` 使用 `t()` | ✅ |
| `Sidebar.tsx` | 加载状态使用 `t('common.loading')` | ✅ |
| `zh.json` | 添加 `menu` 对象（30 个键） | ✅ |
| `en.json` | 添加 `menu` 对象（30 个键） | ✅ |
| `ja.json` | 添加 `menu` 对象（30 个键） | ✅ |
| `ru.json` | 添加 `menu` 对象（30 个键） | ✅ |

---

## 🎯 技术实现

### i18n 工作原理

```typescript
// 1. 菜单配置使用 i18n key
{
  key: 'chat',
  label: 'menu.chat',  // i18n key
}

// 2. Sidebar 使用 t() 函数翻译
const { t } = useTranslation();
const menuItems = convertToMenuItems(filteredMenu, t);

// 3. convertToMenuItems 调用 t()
function convertToMenuItems(menu: MenuItem[], t: (key: string) => string) {
  return menu.map((item) => ({
    key: item.key,
    icon: item.icon,
    label: t(item.label),  // t('menu.chat') → "聊天" / "Chat" / etc.
  }));
}

// 4. i18n 根据当前语言返回对应翻译
// zh: t('menu.chat') → "聊天"
// en: t('menu.chat') → "Chat"
// ja: t('menu.chat') → "チャット"
// ru: t('menu.chat') → "Чат"
```

### 语言切换流程

```
用户点击语言切换按钮
  ↓
i18n.changeLanguage('en')
  ↓
localStorage.setItem('language', 'en')
  ↓
useTranslation() hook 重新渲染
  ↓
t() 函数返回英文翻译
  ↓
菜单重新渲染，显示英文
```

---

## ⚠️ 注意事项

### 1. i18n Key 命名规范

使用嵌套结构：`namespace.key`

```typescript
// ✅ 推荐
'menu.chat'
'menu.control'
'menu.agentManagement'

// ❌ 不推荐
'chat'          // 可能冲突
'menuChat'       // 不符合嵌套规范
```

### 2. 翻译文件结构

保持所有语言文件的结构一致：

```json
{
  "menu": {
    "chat": "...",
    "control": "...",
    // 所有语言都有相同的键
  }
}
```

### 3. 新增菜单项

添加新菜单项时，需要：

1. 在 `constants.tsx` 中添加配置
2. 在所有 4 个语言文件中添加翻译
3. 验证所有语言显示正确

---

## 🚀 下一步

### 待完成的工作

1. **企业版功能页面国际化**
   - 用户管理页面
   - 角色权限页面
   - 工作流页面
   - 任务管理页面
   - DLP 规则页面
   - 告警规则页面
   - Dify 连接器页面
   - 审计日志页面

2. **Header 组件国际化**
   - 用户菜单文本
   - 折叠按钮 tooltip

3. **AgentSelector 组件国际化**
   - 智能体选择器文本
   - 加载状态文本

---

**修复时间**: 2026-04-13  
**状态**: ✅ 菜单国际化已完成  
**影响范围**: 企业版布局左侧菜单  
**测试语言**: 中文、英文、日语、俄语
