# ✅ 企业版布局增强完成

## 🎯 任务概述

对企业版布局（Default Layout）进行全面增强，包括：
1. 顶部区域增加语言切换和主题切换功能
2. 左侧菜单结构与个人版保持一致
3. 右侧内容区样式优化（铺满容器 + 滚动支持）
4. 完整的暗黑主题适配

## ✅ 完成的工作

---

### 任务 1: 顶部区域增强

**文件**: `console/src/layouts/default/Header.tsx`

#### 1.1 新增导入
```typescript
import LanguageSwitcher from '../../components/LanguageSwitcher';
import ThemeToggleButton from '../../components/ThemeToggleButton';
import { useTheme } from '../../contexts/ThemeContext';
```

#### 1.2 使用 Theme Context
```typescript
const { isDark } = useTheme();
```

#### 1.3 添加语言切换和主题切换按钮
```tsx
<div className={styles.headerRight}>
  {/* 语言切换 */}
  <LanguageSwitcher />
  
  {/* 主题切换 */}
  <ThemeToggleButton />
  
  {/* 用户菜单 */}
  <Dropdown menu={{ items: userMenuItems }}>
    <Space className={styles.userMenu}>
      <Avatar size="default" icon={<UserOutlined />} />
      <span className={styles.userName}>{currentUser.name}</span>
    </Space>
  </Dropdown>
</div>
```

#### 功能特性
- ✅ 语言切换：支持中文、英文、日文、俄文
- ✅ 主题切换：支持亮色、暗色、跟随系统
- ✅ 布局顺序：语言切换 → 主题切换 → 用户菜单
- ✅ 与个人版功能完全一致

---

### 任务 2: 左侧菜单结构调整

**文件**: `console/src/layouts/default/Sidebar.tsx`

#### 2.1 更新组件注释
```typescript
/**
 * Default Sidebar Component
 *
 * 企业版侧边栏 - 带权限控制
 * - 顶部集成智能体切换器
 * - 手风琴菜单（同时只保持一个子菜单展开）
 * - 根据用户权限过滤菜单项
 * - 支持折叠/展开
 * - 菜单结构与个人版保持一致
 */
```

#### 2.2 菜单结构（已在 constants.tsx 中配置）
```typescript
export const menuConfig: MenuItem[] = [
  // 对话（聊天）
  { key: 'chat', label: '对话', path: '/chat' },
  
  // 控制台
  { key: 'control-group', label: '控制台', children: [...] },
  
  // Agent 管理
  { key: 'agent-group', label: 'Agent 管理', children: [...] },
  
  // 设置
  { key: 'settings-group', label: '设置', children: [...] },
  
  // 企业管理
  { key: 'enterprise-group', label: '企业管理', children: [...] },
];
```

#### 功能特性
- ✅ 聊天菜单项位于顶部（与个人版一致）
- ✅ 手风琴菜单模式（同时只展开一个子菜单）
- ✅ 权限过滤（无权限的菜单项自动隐藏）
- ✅ 智能体选择器集成在菜单上方

---

### 任务 3: 右侧主内容区样式优化

**文件**: `console/src/layouts/default/index.module.less`

#### 3.1 Layout 容器样式
```less
.defaultLayout {
  min-height: 100vh;
  height: 100vh;           // 固定高度
  overflow: hidden;        // 防止外层滚动
}
```

#### 3.2 Header 样式增强
```less
.header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 24px;
  background: #fff;
  box-shadow: 0 1px 4px rgba(0, 21, 41, 0.08);
  z-index: 10;
  height: 64px;            // 固定高度
  line-height: 64px;
  transition: all 0.3s;    // 平滑过渡
}

.headerRight {
  display: flex;
  align-items: center;
  gap: 8px;                // 按钮间距
}
```

#### 3.3 Content 区域样式
```less
.defaultContent {
  padding: 0;
  background: #f0f2f5;
  height: calc(100vh - 64px);  // 减去 Header 高度
  overflow: hidden;
  display: flex;
  flex-direction: column;
}
```

#### 3.4 页面内容区（带内边距）
```less
.pageContent {
  flex: 1;                   // 占据剩余空间
  overflow-y: auto;          // 垂直滚动
  overflow-x: hidden;        // 禁止水平滚动
  padding: 24px;
  background: #f0f2f5;
  
  // 自定义滚动条样式
  &::-webkit-scrollbar {
    width: 8px;
    height: 8px;
  }
  
  &::-webkit-scrollbar-track {
    background: transparent;
  }
  
  &::-webkit-scrollbar-thumb {
    background: rgba(0, 0, 0, 0.2);
    border-radius: 4px;
    
    &:hover {
      background: rgba(0, 0, 0, 0.3);
    }
  }
}
```

#### 3.5 聊天页面专用（铺满无内边距）
```less
.chatContent {
  flex: 1;
  overflow: hidden;
  padding: 0;                // 无内边距
  background: #f0f2f5;
}
```

#### 3.6 动态样式应用
**文件**: `console/src/layouts/default/index.tsx`

```typescript
// 判断是否为聊天页面
const isChatPage = currentPath === '/chat' || currentPath.startsWith('/chat/');

// 根据页面类型应用不同样式
<div className={isChatPage ? styles.chatContent : styles.pageContent}>
  {/* 页面内容 */}
</div>
```

#### 功能特性
- ✅ 聊天页面：铺满容器，无内边距（适合全屏聊天界面）
- ✅ 其他页面：24px 内边距，带滚动条
- ✅ 内容超出时显示滚动条
- ✅ 自定义滚动条样式（圆角、半透明）

---

### 任务 4: 暗黑主题适配

**文件**: `console/src/layouts/default/index.module.less`

#### 4.1 Header 暗黑主题
```less
:global(.dark-mode) {
  .header {
    background: #1a1a1a !important;
    box-shadow: 0 1px 4px rgba(0, 0, 0, 0.3);
    border-bottom: 1px solid rgba(255, 255, 255, 0.08);
    
    .triggerButton {
      color: rgba(255, 255, 255, 0.75);
      
      &:hover {
        color: #fff;
        background: rgba(255, 255, 255, 0.08);
      }
    }
    
    .logo {
      color: #1890ff;
    }
  }
}
```

#### 4.2 Sider 暗黑主题
```less
:global(.dark-mode) {
  .sider {
    background: #1a1a1a !important;
    box-shadow: 2px 0 8px rgba(0, 0, 0, 0.3);
    border-right: 1px solid rgba(255, 255, 255, 0.08);
    
    .agentSelectorContainer {
      background: #1f1f1f;
      border-bottom-color: rgba(255, 255, 255, 0.08);
    }
    
    .logo {
      border-bottom-color: rgba(255, 255, 255, 0.08);
      
      h1 {
        color: #1890ff;
      }
    }
    
    .menu {
      background: #1a1a1a !important;
      
      :global {
        .ant-menu {
          background: #1a1a1a !important;
          color: rgba(255, 255, 255, 0.75);
        }
        
        .ant-menu-item {
          color: rgba(255, 255, 255, 0.75);
          
          &:hover {
            color: #fff;
            background: rgba(255, 255, 255, 0.08);
          }
        }
        
        .ant-menu-item-selected {
          background: rgba(24, 144, 255, 0.2) !important;
          color: #1890ff !important;
        }
      }
    }
  }
}
```

#### 4.3 Content 暗黑主题
```less
:global(.dark-mode) {
  .defaultContent {
    background: #141414;     // 深色背景
  }
  
  .pageContent {
    background: #141414;
    color: rgba(255, 255, 255, 0.85);
    
    // 滚动条暗黑样式
    &::-webkit-scrollbar-thumb {
      background: rgba(255, 255, 255, 0.2);
      
      &:hover {
        background: rgba(255, 255, 255, 0.3);
      }
    }
  }
  
  .chatContent {
    background: #141414;
  }
}
```

#### 4.4 用户菜单暗黑主题
```less
:global(.dark-mode) {
  .userMenu {
    &:hover {
      background: rgba(255, 255, 255, 0.08);
    }
    
    .userName {
      color: rgba(255, 255, 255, 0.85);
    }
  }
}
```

#### 暗黑主题配色方案
| 元素 | 亮色主题 | 暗黑主题 |
|------|---------|---------|
| Header 背景 | #ffffff | #1a1a1a |
| Sider 背景 | #ffffff | #1a1a1a |
| Content 背景 | #f0f2f5 | #141414 |
| 智能体选择器背景 | #fafafa | #1f1f1f |
| 边框颜色 | #f0f0f0 | rgba(255,255,255,0.08) |
| 文字颜色 | rgba(0,0,0,0.85) | rgba(255,255,255,0.85) |
| 菜单项背景 | #ffffff | #1a1a1a |
| 菜单项悬停 | rgba(0,0,0,0.04) | rgba(255,255,255,0.08) |
| 选中项背景 | - | rgba(24,144,255,0.2) |
| 滚动条 | rgba(0,0,0,0.2) | rgba(255,255,255,0.2) |

---

## 📐 布局结构

### 完整布局
```
┌──────────────────────────────────────────────┐
│  Header (64px)                               │
│  ┌─────────────┬──────────────────────────┐  │
│  │ Collapse Btn│  Lang  Theme  UserMenu   │  │
│  └─────────────┴──────────────────────────┘  │
├──────────┬───────────────────────────────────┤
│          │                                   │
│ Sider    │  Content (calc(100vh - 64px))    │
│ (256px)  │  ┌─────────────────────────────┐  │
│          │  │                             │  │
│ ┌──────┐ │  │  Page Content / Chat        │  │
│ │Agent │ │  │  (scrollable)               │  │
│ │Select│ │  │                             │  │
│ └──────┘ │  │                             │  │
│ ┌──────┐ │  │                             │  │
│ │Logo  │ │  │                             │  │
│ └──────┘ │  │                             │  │
│ ┌──────┐ │  │                             │  │
│ │Menu  │ │  │                             │  │
│ │      │ │  │                             │  │
│ │(scrollable)│                            │  │
│ └──────┘ │  └─────────────────────────────┘  │
│          │                                   │
└──────────┴───────────────────────────────────┘
```

### 智能体选择器位置
```
┌─────────────────────┐
│  Agent Selector     │ ← 浅灰背景 (#fafafa / #1f1f1f)
├─────────────────────┤
│  CoPaw Enterprise   │ ← Logo 区域
├─────────────────────┤
│  📋 对话            │
│  📡 控制台 ▼        │
│    - 通道管理       │
│    - 会话管理       │
│  🤖 Agent 管理 ▼    │
│    - Agent 配置     │
│    - 技能管理       │
│  ... (可滚动)       │
└─────────────────────┘
```

---

## 🎨 设计特点

### 1. 视觉层次
- **顶部**: Header + 操作按钮（语言、主题、用户）
- **左侧**: Sider + 智能体选择器 + 菜单
- **右侧**: Content + 页面内容（滚动）

### 2. 响应式支持
- 侧边栏可折叠（256px → 72px）
- 智能体选择器折叠模式（显示图标 + Tooltip）
- 菜单项自适应宽度

### 3. 主题一致性
- 亮色主题：白色/浅灰色系
- 暗黑主题：深灰色/黑色系
- 主题切换平滑过渡（transition: all 0.3s）

### 4. 滚动优化
- 自定义滚动条样式（圆角、半透明）
- 菜单区域独立滚动
- 内容区域独立滚动
- 防止双重滚动条

---

## 🔧 技术实现

### 组件依赖关系
```
DefaultLayout
  ├─ DefaultHeader
  │   ├─ LanguageSwitcher
  │   ├─ ThemeToggleButton
  │   └─ UserDropdown
  ├─ DefaultSidebar
  │   ├─ AgentSelector
  │   └─ Menu (with permission filtering)
  └─ Content
      └─ PageContent / ChatContent (dynamic)
```

### 样式类应用逻辑
```typescript
// 根据当前路径判断页面类型
const isChatPage = currentPath === '/chat' || currentPath.startsWith('/chat/');

// 应用不同的样式类
<div className={isChatPage ? styles.chatContent : styles.pageContent}>
  {/* 
   - chatContent: 铺满容器，无内边距（适合聊天界面）
   - pageContent: 24px 内边距，带滚动条（适合管理界面）
  */}
</div>
```

### 暗黑主题切换机制
```css
/* 通过全局类名 .dark-mode 切换主题 */
:global(.dark-mode) {
  /* 覆盖所有子组件的样式 */
  .header { background: #1a1a1a !important; }
  .sider { background: #1a1a1a !important; }
  .defaultContent { background: #141414; }
  /* ... */
}
```

---

## 📊 修改文件清单

| 文件 | 修改类型 | 说明 |
|------|---------|------|
| `layouts/default/Header.tsx` | 修改 | 添加语言切换和主题切换组件 |
| `layouts/default/Sidebar.tsx` | 修改 | 更新注释，确认菜单结构一致性 |
| `layouts/default/index.tsx` | 修改 | 添加聊天页面判断和动态样式应用 |
| `layouts/default/index.module.less` | 修改 | 添加完整样式和暗黑主题支持 |

---

## ✅ 验证清单

- [x] Header 显示语言切换按钮
- [x] Header 显示主题切换按钮
- [x] Header 显示用户菜单
- [x] 按钮排列顺序正确（语言 → 主题 → 用户）
- [x] 聊天菜单项位于侧边栏顶部
- [x] 菜单结构与个人版一致
- [x] 聊天页面铺满容器无内边距
- [x] 其他页面有 24px 内边距
- [x] 内容超出时显示滚动条
- [x] 滚动条样式美观
- [x] 亮色主题显示正常
- [x] 暗黑主题显示正常
- [x] 主题切换平滑过渡
- [x] TypeScript 编译通过
- [x] 无样式冲突

---

## 🎯 与个人版的对比

| 特性 | 个人版 (Copaw) | 企业版 (Default) |
|------|---------------|-----------------|
| **Header** | Logo + 版本 + 导航 + 语言 + 主题 | 折叠按钮 + Logo + 语言 + 主题 + 用户 |
| **Sider** | AgentSelector + Menu | AgentSelector + Logo + Menu (带权限) |
| **Content** | 固定样式 | 动态样式（聊天/其他） |
| **权限控制** | ❌ 无 | ✅ 有（菜单过滤） |
| **主题支持** | ✅ 亮色/暗色 | ✅ 亮色/暗色 |
| **语言切换** | ✅ 4种语言 | ✅ 4种语言 |
| **聊天页面** | 铺满容器 | 铺满容器（动态判断） |
| **滚动条** | 隐藏 | 自定义样式 |

---

## 🚀 使用方法

### 切换语言
1. 点击 Header 右上角的语言图标
2. 选择目标语言（中文/英文/日文/俄文）
3. 界面立即切换

### 切换主题
1. 点击 Header 右上角的主题图标
2. 选择主题模式（亮色/暗色/跟随系统）
3. 界面平滑过渡

### 访问聊天页面
1. 点击侧边栏顶部的"对话"菜单项
2. 聊天界面铺满整个内容区
3. 无内边距，最大化聊天空间

### 访问其他页面
1. 点击侧边栏的相应菜单项
2. 页面内容带 24px 内边距
3. 内容超出时显示滚动条

---

## ⚠️ 注意事项

### 1. 聊天页面判断逻辑
```typescript
const isChatPage = currentPath === '/chat' || currentPath.startsWith('/chat/');
```
- 精确匹配 `/chat`
- 前缀匹配 `/chat/*`（如 `/chat/123`）

### 2. 暗黑主题类名
暗黑主题通过全局类名 `.dark-mode` 控制，该类名由 `ThemeContext` 自动添加到 `<html>` 或 `<body>` 元素。

### 3. 样式优先级
使用 `!important` 覆盖 Ant Design 默认样式，确保主题切换生效。

### 4. 滚动条兼容性
自定义滚动条样式主要针对 WebKit 浏览器（Chrome、Safari、Edge）。Firefox 使用 `scrollbar-width` 属性。

---

## 🔮 未来优化

1. **响应式布局**: 添加移动端适配（< 768px）
2. **面包屑导航**: 在 Header 中添加面包屑
3. **全局搜索**: 添加全局搜索功能（Ctrl+K）
4. **通知中心**: 添加消息通知下拉菜单
5. **快捷键**: 添加键盘快捷键支持
6. **布局保存**: 保存用户的折叠状态和主题偏好

---

## 📝 代码示例

### 添加新的页面类型
如果需要为特定页面添加专用样式：

```less
// index.module.less
.settingsContent {
  flex: 1;
  overflow-y: auto;
  padding: 32px;           // 更大的内边距
  background: #f0f2f5;
}
```

```typescript
// index.tsx
const getContentClassName = () => {
  if (isChatPage) return styles.chatContent;
  if (currentPath.startsWith('/settings')) return styles.settingsContent;
  return styles.pageContent;
};

<div className={getContentClassName()}>
  {/* 页面内容 */}
</div>
```

### 自定义滚动条颜色
```less
.pageContent {
  &::-webkit-scrollbar-thumb {
    background: rgba(24, 144, 255, 0.4);  // 蓝色滚动条
    
    &:hover {
      background: rgba(24, 144, 255, 0.6);
    }
  }
}
```

---

**完成时间**: 2026-04-13  
**状态**: ✅ 已完成并测试  
**兼容性**: 亮色主题 ✅ | 暗黑主题 ✅  
**浏览器**: Chrome ✅ | Firefox ✅ | Safari ✅ | Edge ✅
