# 核心模块详解

本文档详细介绍 CoPaw 的核心模块及其实现原理。

---

## 1. CoPawAgent - 智能体核心

### 类定义

```python
class CoPawAgent(ToolGuardMixin, ReActAgent):
    """CoPaw Agent with integrated tools, skills, and memory management.

    This agent extends ReActAgent with:
    - Built-in tools (shell, file operations, browser, etc.)
    - Dynamic skill loading from working directory
    - Memory management with auto-compaction
    - Bootstrap guidance for first-time setup
    - System command handling (/compact, /new, etc.)
    - Tool-guard security interception (via ToolGuardMixin)
    """
```

### 核心特性

#### 1.1 内置工具集成

CoPawAgent 内置以下工具：

| 工具 | 文件 | 功能 |
|------|------|------|
| `execute_shell_command` | `tools/shell.py` | 执行Shell命令 |
| `read_file` | `tools/file_io.py` | 读取文件 |
| `write_file` | `tools/file_io.py` | 写入文件 |
| `edit_file` | `tools/file_io.py` | 编辑文件 |
| `glob_search` | `tools/file_search.py` | 文件模式匹配搜索 |
| `grep_search` | `tools/file_search.py` | 文件内容搜索 |
| `browser_use` | `tools/browser_*.py` | 浏览器自动化 |
| `desktop_screenshot` | `tools/desktop_screenshot.py` | 桌面截图 |
| `view_image` | `tools/view_media.py` | 查看图片 |
| `view_video` | `tools/view_media.py` | 查看视频 |
| `send_file_to_user` | `tools/send_file.py` | 发送文件给用户 |
| `get_token_usage` | `tools/get_token_usage.py` | 获取Token使用量 |
| `get_current_time` | `tools/*.py` | 获取当前时间 |
| `set_user_timezone` | `tools/*.py` | 设置用户时区 |

#### 1.2 动态技能加载

```python
# 技能加载流程
1. 从工作目录加载技能配置 (skill.json)
2. 解析技能依赖和环境变量
3. 动态注册工具到 Toolkit
4. 处理技能冲突（同名策略）
```

**技能结构**:
```
skill_name/
├── SKILL.md          # 技能定义文件
├── config.json       # 技能配置（可选）
└── requirements.txt  # Python依赖（可选）
```

#### 1.3 记忆管理

CoPaw 支持多种记忆管理器：

| 管理器 | 实现 | 特点 |
|--------|------|------|
| `BaseMemoryManager` | `memory/base_memory_manager.py` | 基础接口 |
| `RemeLightMemoryManager` | `memory/reme_light_memory_manager.py` | 基于 ReMe 的轻量记忆 |
| `AgentMdManager` | `memory/agent_md_manager.py` | Markdown 格式记忆 |

**记忆压缩钩子**:
```python
class MemoryCompactionHook:
    """自动压缩长期记忆，防止上下文过长"""
    
    def should_compact(self, memory) -> bool:
        """检查是否需要压缩"""
        
    def compact(self, memory) -> None:
        """执行压缩操作"""
```

#### 1.4 启动引导

```python
class BootstrapHook:
    """首次使用时的引导钩子"""
    
    def get_bootstrap_message(self) -> str:
        """生成引导消息，帮助用户快速上手"""
```

#### 1.5 命令处理

支持的系统命令：

| 命令 | 功能 |
|------|------|
| `/compact` | 压缩对话历史 |
| `/new` | 开始新对话 |
| `/clear` | 清空对话历史 |
| `/stop` | 停止当前任务 |
| `/restart` | 重启服务 |
| `/model` | 切换模型 |
| `/skills` | 列出所有技能 |
| `/<skill_name>` | 指定技能执行 |

---

## 2. FastAPI 应用架构

### 2.1 应用结构

```python
# src/copaw/app/_app.py

class DynamicMultiAgentRunner:
    """动态多智能体运行器
    
    根据请求中的 X-Agent-Id header 动态路由到正确的工作区运行器
    """
    
    async def _get_workspace_runner(self, request):
        """获取正确的工作区运行器"""
        agent_id = get_current_agent_id()
        workspace = await self._multi_agent_manager.get_agent(agent_id)
        return workspace.runner
```

### 2.2 中间件

| 中间件 | 功能 |
|--------|------|
| `AuthMiddleware` | Web认证保护 |
| `AgentContextMiddleware` | 设置当前智能体上下文 |
| `CORSMiddleware` | 跨域资源共享 |

### 2.3 API 路由结构

```
/api/
├── /agents              # 多智能体管理
│   ├── GET /           # 列出所有智能体
│   ├── POST /          # 创建新智能体
│   └── /{agent_id}/    # 单个智能体操作
├── /agent              # 单智能体API
│   ├── /config        # 配置管理
│   ├── /skills        # 技能管理
│   ├── /tools         # 工具配置
│   ├── /workspace     # 工作区文件
│   └── /mcp           # MCP客户端
├── /chat               # 聊天会话
│   ├── POST /message  # 发送消息
│   └── GET /history   # 获取历史
├── /channel            # 渠道配置
├── /cronjob            # 定时任务
├── /heartbeat          # 心跳任务
├── /providers          # 模型提供商
├── /local-models       # 本地模型
├── /skills             # 技能池
├── /envs               # 环境变量
├── /security           # 安全配置
├── /token-usage        # Token统计
└── /files              # 文件操作
```

---

## 3. 多智能体管理

### 3.1 MultiAgentManager

```python
class MultiAgentManager:
    """多智能体管理器
    
    负责：
    - 创建、删除、切换智能体
    - 管理智能体生命周期
    - 协调智能体间通信
    """
    
    async def create_agent(self, config: AgentProfileConfig) -> AgentWorkspace:
        """创建新智能体"""
        
    async def get_agent(self, agent_id: str) -> AgentWorkspace:
        """获取智能体实例"""
        
    async def list_agents(self) -> List[AgentInfo]:
        """列出所有智能体"""
```

### 3.2 AgentWorkspace

```python
class AgentWorkspace:
    """智能体工作区
    
    包含：
    - 智能体配置
    - 工作目录
    - 技能副本
    - 对话历史
    - 记忆存储
    """
    
    agent_id: str
    config: AgentProfileConfig
    runner: Runner
    workspace_dir: Path
```

---

## 4. 渠道系统

### 4.1 渠道基类

```python
class BaseChannel(ABC):
    """渠道基类"""
    
    @abstractmethod
    async def start(self):
        """启动渠道"""
        
    @abstractmethod
    async def stop(self):
        """停止渠道"""
        
    @abstractmethod
    async def send_message(self, message: str, **kwargs):
        """发送消息"""
        
    @abstractmethod
    async def receive_message(self) -> Message:
        """接收消息"""
```

### 4.2 支持的渠道

| 渠道 | 实现目录 | 协议 |
|------|----------|------|
| Console | `channels/console/` | HTTP/WebSocket |
| DingTalk | `channels/dingtalk/` | Stream |
| Feishu | `channels/feishu/` | WebSocket |
| Discord | `channels/discord_/` | Bot API |
| Telegram | `channels/telegram/` | Bot API |
| QQ | `channels/qq/` | OneBot |
| WeChat | `channels/weixin/` | HTTP API |
| Enterprise WeChat | `channels/wecom/` | WebSocket |
| iMessage | `channels/imessage/` | AppleScript |
| Matrix | `channels/matrix/` | Client API |
| Mattermost | `channels/mattermost/` | WebSocket |
| MQTT | `channels/mqtt/` | MQTT Protocol |

### 4.3 渠道注册表

```python
class ChannelRegistry:
    """渠道注册表"""
    
    _channels: Dict[str, Type[BaseChannel]] = {}
    
    @classmethod
    def register(cls, name: str, channel_class: Type[BaseChannel]):
        """注册新渠道"""
        
    @classmethod
    def create(cls, name: str, config: ChannelConfig) -> BaseChannel:
        """创建渠道实例"""
```

---

## 5. LLM 提供商管理

### 5.1 ProviderManager

```python
class ProviderManager:
    """提供商管理器
    
    负责：
    - 管理多个LLM提供商配置
    - 创建模型实例
    - 处理API密钥
    - 实现速率限制和重试
    """
    
    def __init__(self, config: Config):
        self.providers: Dict[str, Provider] = {}
        self.rate_limiter = RateLimiter()
        
    def create_model(self, provider_name: str, model_name: str):
        """创建模型实例"""
        
    def get_available_models(self) -> List[ModelInfo]:
        """获取可用模型列表"""
```

### 5.2 提供商实现

```python
class Provider(ABC):
    """提供商基类"""
    
    @abstractmethod
    def create_chat_model(self, model_name: str, **kwargs):
        """创建聊天模型"""
        
    @abstractmethod
    def test_connection(self) -> bool:
        """测试连接"""
```

### 5.3 速率限制

```python
class RateLimiter:
    """基于滑动窗口的速率限制器
    
    支持 QPM (Queries Per Minute) 限制
    """
    
    def __init__(self, max_qpm: int = 60):
        self.max_qpm = max_qpm
        self.requests = deque()
        
    async def acquire(self):
        """获取请求许可"""
```

---

## 6. 安全机制

### 6.1 工具守卫

```python
class ToolGuardMixin:
    """工具守卫混入类
    
    在工具执行前进行安全检查：
    - 拦截危险Shell命令
    - 验证参数安全性
    - 记录审计日志
    """
    
    def _acting(self, *args, **kwargs):
        """工具执行前的守卫拦截"""
        # 检查命令是否在黑名单
        # 验证参数安全性
        # 记录执行日志
        return super()._acting(*args, **kwargs)
```

**危险命令规则** (`dangerous_shell_commands.yaml`):
- `rm -rf /` - 删除根目录
- `mkfs` - 格式化磁盘
- `dd if=/dev/zero` - 磁盘覆写
- `fork bombs` - 炸弹命令
- `reverse shells` - 反向Shell

### 6.2 文件守卫

```python
class FileGuardian:
    """文件访问守卫
    
    限制对敏感路径的访问
    """
    
    PROTECTED_PATHS = [
        "~/.ssh",
        "~/.gnupg",
        "/etc/passwd",
        "/etc/shadow",
        "*.pem",
        "*.key",
    ]
    
    def check_path_access(self, path: Path, operation: str) -> bool:
        """检查路径访问权限"""
```

### 6.3 技能安全扫描

```python
class SkillScanner:
    """技能安全扫描器
    
    在安装技能前扫描：
    - 提示词注入
    - 命令注入
    - 硬编码密钥
    - 数据外泄
    - 代码混淆
    """
    
    def scan_skill(self, skill_dir: Path) -> ScanResult:
        """扫描技能目录"""
        
    def check_prompt_injection(self, content: str) -> List[Finding]:
        """检测提示词注入"""
        
    def check_hardcoded_secrets(self, content: str) -> List[Finding]:
        """检测硬编码密钥"""
```

---

## 7. 本地模型管理

### 7.1 LocalModelManager

```python
class LocalModelManager:
    """本地模型管理器
    
    支持：
    - llama.cpp
    - Ollama
    - LM Studio
    - MLX (macOS)
    """
    
    def __init__(self, config: Config):
        self.backends: Dict[str, Backend] = {}
        
    async def download_model(self, model_id: str, backend: str):
        """下载模型"""
        
    def create_backend(self, backend_type: str, config: dict):
        """创建后端实例"""
```

### 7.2 llama.cpp 集成

```python
class LlamaCppBackend:
    """llama.cpp 后端
    
    无需额外安装，内置支持
    """
    
    def __init__(self, model_path: Path):
        self.model_path = model_path
        
    def load_model(self):
        """加载模型"""
        
    def generate(self, prompt: str, **kwargs) -> str:
        """生成文本"""
```

---

## 8. 技能系统

### 8.1 SkillsManager

```python
class SkillsManager:
    """技能管理器（2620行）
    
    负责：
    - 技能池管理
    - 工作区技能副本管理
    - 技能加载和注册
    - 技能冲突处理
    """
    
    def load_skill(self, skill_dir: Path) -> Skill:
        """加载技能"""
        
    def broadcast_skill(self, skill_name: str, agent_ids: List[str]):
        """广播技能到工作区"""
        
    def resolve_skill_conflict(self, skill_name: str) -> str:
        """解决技能冲突"""
```

### 8.2 内置技能

| 技能 | 功能 |
|------|------|
| `pdf` | PDF处理（读取、合并、拆分、OCR等） |
| `pptx` | PPT创建和编辑 |
| `docx` | Word文档处理 |
| `xlsx` | Excel表格处理 |
| `news` | 新闻摘要 |
| `cron` | 定时任务管理 |
| `browser_cdp` | Chrome CDP自动化 |
| `browser_visible` | 可见浏览器控制 |
| `multi_agent_collaboration` | 多智能体协作 |
| `channel_message` | 跨渠道消息发送 |

---

## 9. 记忆系统

### 9.1 记忆管理器接口

```python
class BaseMemoryManager(ABC):
    """记忆管理器基类"""
    
    @abstractmethod
    async def save_memory(self, key: str, value: Any):
        """保存记忆"""
        
    @abstractmethod
    async def load_memory(self, key: str) -> Any:
        """加载记忆"""
        
    @abstractmethod
    async def search_memory(self, query: str) -> List[MemoryItem]:
        """搜索记忆"""
        
    @abstractmethod
    async def compress_memory(self):
        """压缩记忆"""
```

### 9.2 ReMe 集成

```python
class RemeLightMemoryManager(BaseMemoryManager):
    """基于 ReMe 的轻量记忆管理器
    
    特点：
    - 长期记忆存储
    - 语义搜索
    - 自动压缩
    """
    
    def __init__(self, working_dir: Path):
        self.reme_client = RemeClient(working_dir)
```

---

## 10. 插件系统

### 10.1 插件架构

```python
class PluginLoader:
    """插件加载器
    
    支持：
    - 从目录加载插件
    - 从 pip 包加载插件
    - 插件依赖管理
    """
    
    def discover_plugins(self) -> List[PluginInfo]:
        """发现可用插件"""
        
    def load_plugin(self, plugin_id: str) -> Plugin:
        """加载插件"""
```

### 10.2 插件 API

```python
class PluginAPI:
    """插件开发 API
    
    提供给插件开发者的接口
    """
    
    def register_tool(self, tool: Tool):
        """注册工具"""
        
    def register_skill(self, skill: Skill):
        """注册技能"""
        
    def register_channel(self, channel: BaseChannel):
        """注册渠道"""
```
