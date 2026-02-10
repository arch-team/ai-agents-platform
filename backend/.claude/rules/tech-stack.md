# 技术栈规范 (Tech Stack Standards)

> **职责**: 技术栈版本要求的**单一真实源**，包括 Python、FastAPI、Claude Agent SDK 等核心依赖版本。

---

## §0 速查卡片

### 版本要求矩阵

#### 核心框架

| 类别 | 技术 | 最低版本 | 推荐版本 |
|------|------|---------|---------|
| **语言** | Python | >=3.11 | 3.12+ |
| **运行时** | Node.js | >=18.0 | 20 LTS |
| **Web 框架** | FastAPI | >=0.110.0 | 0.115+ |
| **ASGI 服务器** | Uvicorn | >=0.27.0 | 0.30+ |
| **数据验证** | Pydantic | >=2.6.0 | 2.x |
| **ORM** | SQLAlchemy (async) | >=2.0.25 | 2.0+ |
| **数据库迁移** | Alembic | >=1.13.0 | 1.13+ |
| **数据库** | MySQL | 8.0+ | Aurora MySQL 3.x |

#### Agent 框架 (ADR-006)

| 类别 | 技术 | 最低版本 | 说明 |
|------|------|---------|------|
| **Agent SDK** | claude-agent-sdk | >=0.1.0 | Agent 执行路径: SDK → Claude Code CLI → Bedrock Invoke API |
| **AgentCore SDK** | bedrock-agentcore | >=0.1.0 | Platform API 路径: Runtime 部署封装 |
| **AWS SDK** | boto3 | >=1.36.0 | Platform API 路径: AgentCore 控制面 + KB + 降级 Converse API |

#### 工具链

| 类别 | 技术 | 最低版本 | 推荐版本 |
|------|------|---------|---------|
| **认证** | python-jose, passlib | - | - |
| **日志** | structlog | >=24.1.0 | 24.x |
| **包管理** | uv | - | 最新 |
| **代码检查** | Ruff | - | 最新 |
| **类型检查** | MyPy | - | 最新 |
| **测试** | pytest | >=8.0.0 | 8.x |

### 依赖路径说明

```
Agent 执行路径 (LLM 对话 + 工具调用):
  Python → claude-agent-sdk → Claude Code CLI (Node.js) → Bedrock Invoke API
  • 不使用 boto3
  • 认证: AWS 标准凭证链 (IAM Role / 环境变量)
  • 环境变量: CLAUDE_CODE_USE_BEDROCK=1 + AWS_REGION

Platform API 路径 (资源管理 + 降级):
  Python → boto3 → AgentCore Control API / Bedrock KB API / Converse API
  • BedrockLLMClient (降级路径) 使用 Converse API
  • AgentCore 资源管理使用 bedrock-agentcore-control 客户端
```

### 关键约束

- **包管理器**: 仅使用 uv，禁止 pip/poetry
- **代码检查**: 仅使用 Ruff，禁止 flake8/black/isort
- **类型检查**: MyPy `strict` 模式
- **Node.js**: Claude Agent SDK 依赖 Claude Code CLI (Node.js 18+)，开发环境和 Docker 镜像需安装

### 快速验证命令

```bash
# 检查核心版本
python --version && node --version && uv --version

# 检查 Agent SDK
uv run python -c "from claude_agent_sdk import query; print('claude-agent-sdk OK')"

# 检查 Platform SDK
uv run python -c "import boto3; print(boto3.__version__)"
uv run python -c "import bedrock_agentcore; print('bedrock-agentcore OK')"

# 检查 Web 框架
uv run python -c "import fastapi; print(fastapi.__version__)"
uv run python -c "import sqlalchemy; print(sqlalchemy.__version__)"
```

---

## 相关文档

| 文档 | 说明 |
|------|------|
| [CLAUDE.md](../CLAUDE.md) | 技术栈概述和开发命令 |
| [testing.md](testing.md) | 测试规范 |
| [code-style.md](code-style.md) | 代码风格规范 |
| `docs/adr/006-agent-framework-selection.md` | Agent 框架选型决策 |
