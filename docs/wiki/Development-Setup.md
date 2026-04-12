# 开发环境搭建

本文档说明如何搭建 CoPaw 的开发环境。

---

## 系统要求

### 基础要求

| 项目 | 要求 |
|------|------|
| **操作系统** | macOS / Linux / Windows 10+ |
| **Python** | 3.10 - 3.13 |
| **Node.js** | 18+ (用于前端构建) |
| **内存** | 建议 8GB+ |
| **磁盘** | 建议 10GB+ 可用空间 |

### 可选要求

- **Docker**: 用于容器化开发
- **Ollama**: 用于本地模型测试
- **GPU**: 用于本地模型加速

---

## 后端开发环境

### 1. 克隆仓库

```bash
git clone https://github.com/agentscope-ai/CoPaw.git
cd CoPaw
```

### 2. 创建虚拟环境

**使用 venv**:
```bash
python -m venv venv
source venv/bin/activate  # Linux/macOS
# 或
venv\Scripts\activate     # Windows
```

**使用 conda**:
```bash
conda create -n copaw python=3.12
conda activate copaw
```

**使用 uv** (推荐):
```bash
# 安装 uv
curl -LsSf https://astral.sh/uv/install.sh | sh

# 创建虚拟环境
uv venv
source .venv/bin/activate
```

### 3. 安装依赖

**基础安装**:
```bash
pip install -e .
```

**开发依赖**:
```bash
pip install -e ".[dev,full]"
```

**可选依赖**:
```bash
# 本地模型支持
pip install -e ".[local]"

# llama.cpp 支持
pip install -e ".[llamacpp]"

# Ollama 支持
pip install -e ".[ollama]"

# Whisper 支持
pip install -e ".[whisper]"

# 完整安装
pip install -e ".[full]"
```

### 4. 构建前端

```bash
cd console
npm ci
npm run build
cd ..

# 复制构建产物
mkdir -p src/copaw/console
cp -R console/dist/. src/copaw/console/
```

### 5. 初始化配置

```bash
copaw init --defaults
```

### 6. 启动服务

```bash
copaw app
```

访问 http://127.0.0.1:8088/ 查看控制台。

---

## 前端开发环境

### Console 前端

#### 1. 安装依赖

```bash
cd console
npm ci
```

#### 2. 开发模式

```bash
npm run dev
```

访问 http://localhost:5173/（Vite 默认端口）

#### 3. 构建生产版本

```bash
npm run build
```

#### 4. 代码检查

```bash
npm run lint
npm run format:check
```

### Website 前端

#### 1. 安装依赖

```bash
cd website
npm ci  # 或 pnpm install
```

#### 2. 开发模式

```bash
npm run dev
```

#### 3. 构建

```bash
npm run build
```

---

## IDE 配置

### VS Code

推荐安装以下扩展：

- **Python** (ms-python.python)
- **Pylance** (ms-python.vscode-pylance)
- **ES7+ React/Redux/React-Native snippets**
- **TypeScript Importer**
- **Ant Design snippets**
- **Tailwind CSS IntelliSense** (用于 Website)

**推荐 settings.json**:
```json
{
  "python.defaultInterpreterPath": "${workspaceFolder}/.venv/bin/python",
  "python.linting.enabled": true,
  "python.linting.pylintEnabled": false,
  "python.linting.flake8Enabled": true,
  "python.formatting.provider": "black",
  "editor.formatOnSave": true,
  "editor.codeActionsOnSave": {
    "source.organizeImports": true
  },
  "typescript.preferences.importModuleSpecifier": "relative"
}
```

### PyCharm

1. 打开项目，选择 `src/copaw` 作为源根目录
2. 配置 Python 解释器为虚拟环境
3. 启用 Flake8 代码检查
4. 配置 Black 格式化器

---

## 测试环境

### 运行测试

```bash
# 运行所有测试
python scripts/run_tests.py

# 运行单元测试
python scripts/run_tests.py -u

# 运行集成测试
python scripts/run_tests.py -i

# 带覆盖率报告
python scripts/run_tests.py -a -c

# 运行特定模块
python scripts/run_tests.py -u providers

# 并行运行
python scripts/run_tests.py -p
```

### 测试覆盖率

```bash
# 生成覆盖率报告
pytest --cov=copaw --cov-report=html tests/

# 查看 HTML 报告
open htmlcov/index.html
```

---

## Docker 开发环境

### 构建镜像

```bash
# 从源码构建
docker build -t copaw:dev -f deploy/Dockerfile .

# 使用脚本构建
./scripts/docker_build.sh
```

### 运行容器

```bash
docker run -p 127.0.0.1:8088:8088 \
  -v $(pwd)/src:/app/src \
  -v copaw-data:/app/working \
  -v copaw-secrets:/app/working.secret \
  -e LOG_LEVEL=debug \
  copaw:dev
```

### 开发调试

```bash
# 进入容器
docker exec -it <container_id> bash

# 查看日志
docker logs <container_id> -f
```

---

## 配置文件说明

### pyproject.toml

项目主配置文件，定义：
- 项目元数据
- 依赖关系
- 可选依赖组
- 测试配置

### .env 文件

环境变量配置文件（可选）：

```bash
# 日志级别
COPAW_LOG_LEVEL=debug

# 工作目录
COPAW_WORKING_DIR=~/.copaw

# 端口
COPAW_PORT=8088

# API Keys (敏感信息，建议使用控制台配置)
# DASHSCOPE_API_KEY=xxx
# OPENAI_API_KEY=xxx
```

### 配置文件位置

```
~/.copaw/                    # 默认工作目录
├── config.json             # 主配置文件
├── .env                    # 环境变量
├── skill_pool/             # 技能池
│   └── skill.json
└── workspaces/             # 工作区
    └── default/
        ├── config.json
        ├── skill.json
        └── skills/
```

---

## 常见问题

### 1. Python 版本不兼容

```bash
# 检查 Python 版本
python --version

# CoPaw 要求 Python 3.10 - 3.13
# 使用 pyenv 切换版本
pyenv install 3.12
pyenv local 3.12
```

### 2. 前端构建失败

```bash
# 清理 node_modules
cd console
rm -rf node_modules package-lock.json
npm install

# 或使用 yarn
yarn install
```

### 3. 依赖冲突

```bash
# 使用 pip-compile 锁定依赖
pip install pip-tools
pip-compile pyproject.toml

# 或使用 uv 锁定
uv pip compile pyproject.toml
```

### 4. 端口占用

```bash
# 检查端口占用
lsof -i :8088  # macOS/Linux
netstat -ano | findstr :8088  # Windows

# 使用其他端口
copaw app --port 8089
```

### 5. 权限问题

```bash
# macOS/Linux
chmod +x scripts/*.sh

# Windows: 以管理员身份运行
```

---

## 开发工作流

### 1. 功能开发流程

```bash
# 1. 创建功能分支
git checkout -b feature/new-feature

# 2. 开发和测试
# ... 编写代码 ...

# 3. 运行测试
python scripts/run_tests.py

# 4. 代码格式化
black src/
isort src/

# 5. 提交代码
git add .
git commit -m "feat: add new feature"

# 6. 推送分支
git push origin feature/new-feature

# 7. 创建 Pull Request
```

### 2. Pre-commit 钩子

```bash
# 安装 pre-commit
pip install pre-commit

# 安装钩子
pre-commit install

# 手动运行
pre-commit run --all-files
```

### 3. 调试技巧

**后端调试**:
```python
import logging
logging.basicConfig(level=logging.DEBUG)

# 或使用环境变量
export COPAW_LOG_LEVEL=debug
```

**前端调试**:
```javascript
// 在浏览器控制台
localStorage.setItem('debug', 'true');
```

**API 调试**:
```bash
# 使用 httpie
pip install httpie
http GET http://127.0.0.1:8088/api/agents

# 或使用 curl
curl -X GET http://127.0.0.1:8088/api/agents
```
