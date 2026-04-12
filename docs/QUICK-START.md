# CoPaw Quick Start Guide

Get started with CoPaw in 3 minutes.

---

## Choose Installation Method

| Method | Use Case | Time |
|--------|----------|------|
| **pip install** | Personal use, familiar with Python | 2 min |
| **Enterprise** | Enterprise deployment, multi-tenant | 5 min |
| **Docker** | Quick try, containerized deployment | 3 min |
| **Desktop App** | Not familiar with command line | 1 min |
| **Script Install** | Automated installation, no config | 2 min |

---

## Option 1: pip Install (Personal Use)

### 1. Install CoPaw

```bash
pip install copaw
```

### 2. Initialize Configuration

```bash
copaw init --defaults
```

Or interactive configuration:

```bash
copaw init
```

### 3. Start Service

```bash
copaw app
```

### 4. Access Console

Open browser: **http://127.0.0.1:8088/**

### 5. Configure Model

Configure API Key in **Settings → Models**:

- **DashScope (Qianwen)**: Get from [Alibaba Cloud Console](https://dashscope.console.aliyun.com/)
- **OpenAI**: Get from [OpenAI Platform](https://platform.openai.com/)
- **Other providers**: See [Model Configuration Docs](https://copaw.agentscope.io/docs/models)

---

## Option 2: Enterprise Installation

### 1. Install Enterprise Edition

```bash
pip install copaw[enterprise]
```

### 2. Prepare Databases

**PostgreSQL**:
```bash
docker run -d \
  --name copaw-postgres \
  -e POSTGRES_PASSWORD=copaw123 \
  -e POSTGRES_DB=copaw \
  -p 5432:5432 \
  postgres:15
```

**Redis**:
```bash
docker run -d \
  --name copaw-redis \
  -p 6379:6379 \
  redis:7
```

### 3. Initialize Enterprise Configuration

```bash
copaw init --enterprise
```

Follow prompts to configure:
- PostgreSQL connection
- Redis connection
- Admin account
- Company information

### 4. Run Database Migrations

```bash
copaw db migrate
```

### 5. Start Service

```bash
copaw app
```

### 6. Access Enterprise Console

Open browser: **http://127.0.0.1:8088/**

After logging in with admin account, access:
- User Management
- Role Permissions
- Department Management
- Audit Logs
- Workflow Management

---

## Option 3: Docker Deployment

### Personal Use

```bash
docker run -p 127.0.0.1:8088:8088 \
  -v copaw-data:/app/working \
  -v copaw-secrets:/app/working.secret \
  agentscope/copaw:latest
```

### Enterprise Deployment

Using docker-compose:

```bash
git clone https://github.com/agentscope-ai/CoPaw.git
cd CoPaw

docker-compose -f docker-compose.enterprise.yml up -d
```

`docker-compose.enterprise.yml` includes:
- CoPaw application
- PostgreSQL database
- Redis cache
- Prometheus monitoring
- Grafana dashboard

---

## Option 4: Desktop App (Beta)

### Download

From [GitHub Releases](https://github.com/agentscope-ai/CoPaw/releases):

- **Windows**: `CoPaw-Setup-<version>.exe`
- **macOS**: `CoPaw-<version>-macOS.zip`

### Install

1. Run downloaded installer
2. Follow installation prompts
3. Launch CoPaw application

### macOS Security Settings

If macOS shows security warning:

1. Right-click app → **Open** → Click **Open** again
2. Or run in terminal: `xattr -cr /Applications/CoPaw.app`

---

## Option 5: Script Install

### macOS / Linux

```bash
curl -fsSL https://copaw.agentscope.io/install.sh | bash
```

**Installation options**:

```bash
# With Ollama support
curl -fsSL https://copaw.agentscope.io/install.sh | bash -s -- --extras ollama

# Specific version
curl -fsSL https://copaw.agentscope.io/install.sh | bash -s -- --version 1.0.2

# From source
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

After installation:

```bash
copaw init --defaults
copaw app
```

---

## Configure Model

### Cloud Models

Configure in **Settings → Models**:

| Provider | How to Get |
|----------|------------|
| DashScope | [Alibaba Cloud Console](https://dashscope.console.aliyun.com/) |
| OpenAI | [OpenAI Platform](https://platform.openai.com/) |
| SiliconFlow | [SiliconFlow Console](https://cloud.siliconflow.cn/) |
| Anthropic | [Anthropic Console](https://console.anthropic.com/) |
| Google Gemini | [Google AI Studio](https://makersuite.google.com/) |

### Local Models

No API key needed, supports:

| Backend | Description |
|---------|-------------|
| **llama.cpp** | Click "Download Llama.cpp" in console |
| **Ollama** | Install Ollama application |
| **LM Studio** | Install LM Studio application |

---

## Start Using

### Chat in Console

1. Open http://127.0.0.1:8088/
2. Type message in chat box
3. AI executes tasks based on enabled Skills

### Common Commands

Use in conversation:

| Command | Function |
|---------|----------|
| `/new` | Start new conversation |
| `/compact` | Compress conversation history |
| `/skills` | List all skills |
| `/<skill_name>` | Execute specific skill |
| `/model` | Switch model |

### Connect to Chat Apps

After configuration, use in DingTalk, Feishu, WeChat, etc.:

1. Complete Quick Start
2. Configure model
3. See [Channel Configuration Docs](https://copaw.agentscope.io/docs/channels)

---

## Enterprise Quick Start

### Create First Team

1. Login as admin
2. Go to **Enterprise Management → Departments**
3. Create department structure
4. Invite members

### Configure Permissions

1. Go to **Role Permissions**
2. Create roles (e.g., HR, Finance, IT)
3. Assign permissions
4. Add users to roles

### Create Shared Agent

1. Go to **Agent Management**
2. Create team-shared agent
3. Assign to department
4. Configure shared skills

### Setup Approval Workflow

1. Go to **Workflow Management**
2. Select template (expense approval, leave approval, etc.)
3. Configure approval nodes
4. Enable workflow

---

## Troubleshooting

### Port in Use

```bash
# Use different port
copaw app --port 8089
```

### Cannot Connect to Database

```bash
# Check if PostgreSQL is running
docker ps | grep copaw-postgres

# Test connection
psql -h localhost -U copaw -d copaw
```

### Redis Connection Failed

```bash
# Check if Redis is running
docker ps | grep copaw-redis

# Test connection
redis-cli ping
```

---

## Next Steps

- 📖 Read [Full Documentation](https://copaw.agentscope.io/docs)
- 🏢 Configure [Enterprise Features](docs/ent-copaw.md)
- 🛠️ Explore [Built-in Skills](https://copaw.agentscope.io/docs/skills)
- 💬 Connect [Chat Channels](https://copaw.agentscope.io/docs/channels)
- 🔒 Configure [Security Settings](https://copaw.agentscope.io/docs/security)

---

## Get Help

- 📚 [Official Docs](https://copaw.agentscope.io/)
- 💬 [GitHub Discussions](https://github.com/agentscope-ai/CoPaw/discussions)
- 🐛 [Submit Issue](https://github.com/agentscope-ai/CoPaw/issues)
- 💬 [Discord Community](https://discord.gg/eYMpfnkG8h)
