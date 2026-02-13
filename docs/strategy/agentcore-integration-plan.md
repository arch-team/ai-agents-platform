# AgentCore 集成行动计划

> **来源**: 技术选型全面审查 + ADR-006 (Agent 框架选型: Claude Agent SDK + Claude Code CLI)
> **审查日期**: 2026-02-10
> **状态**: 已批准
> **关联**: ADR-003, ADR-005, ADR-006

---

## 0. 概述

### 审查结论

项目架构"骨架"（DDD 分层 + Anti-Corruption Layer 适配器模式 + 接口抽象 + 模块隔离）与目标架构高度一致，但当前代码**未引入 Claude Agent SDK 和任何 AgentCore 服务**。全部 LLM 交互通过 boto3 `bedrock-runtime` 的 `converse()` / `converse_stream()` API 实现单轮问答。

### 差距总览

| 能力 | 当前实现 | 目标技术 | 差距 |
|------|---------|---------|:----:|
| LLM 调用 | boto3 Converse API (直接) | Claude Agent SDK → Claude Code CLI → Bedrock Invoke API | 🔴 高 |
| Agent 循环 | 单轮问答 | Agentic Loop (tool_use → 执行 → 继续推理，CLI 自动处理) | 🔴 高 |
| Agent 运行时 | uvicorn / Docker | AgentCore Runtime (Firecracker microVM) | 🔴 高 |
| MCP 工具入口 | 仅元数据管理 | AgentCore Gateway (MCP 协议原生) | 🔴 高 |
| 可观测性 | 基本 Health Check | AgentCore Observability (OpenTelemetry + CloudWatch) | 🔴 高 |
| 知识库 | boto3 KB API (部分占位) | Bedrock Knowledge Base (完整集成) | 🟡 中 |
| 记忆管理 | MySQL 自建 | AgentCore Memory (通过 MCP 桥接) | 🟡 中 |
| SDK 封装层 | 各模块独立 boto3 薄封装 | Agent 路径: Claude Agent SDK → CLI → Invoke API; Platform 路径: boto3 → AgentCore SDK | 🟡 中 |

### 目标架构

```
┌──────────────────────────────────────────────────────────────────┐
│                   AI Agents Platform                              │
│                                                                  │
│  Platform API Layer (FastAPI + MySQL)         [boto3 路径]        │
│  ├── auth, agents, tool_catalog, knowledge, templates            │
│  ├── boto3 → AgentCore Control API (管理 Runtime/Gateway/Memory) │
│  ├── boto3 → Bedrock KB API (管理知识库)                          │
│  ├── boto3 → Converse API (BedrockLLMClient 降级路径)             │
│  └── 部署: ECS Fargate                                           │
│       │                                                          │
│       ▼  invoke_agent_runtime()                                  │
│  Agent Execution Layer (AgentCore Runtime)    [SDK→CLI 路径]      │
│  ├── Claude Agent SDK (Python)                                   │
│  │   └── Claude Code CLI (Node.js 子进程)                        │
│  │       └── Bedrock Invoke API (非 Converse)                    │
│  │           • 认证: AWS 凭证链 (IAM Role, 非 API Key)           │
│  │           • 环境变量: CLAUDE_CODE_USE_BEDROCK=1 + AWS_REGION   │
│  ├── 内置工具 (Read/Write/Edit/Bash/Glob/Grep/WebSearch...)      │
│  ├── MCP 原生支持 → AgentCore Gateway                            │
│  ├── Hooks (PreToolUse/PostToolUse 审计拦截)                      │
│  ├── 子 Agent (AgentDefinition + Task 工具)                       │
│  ├── AgentCore Gateway (MCP 统一工具入口)                         │
│  ├── AgentCore Memory (通过自定义 MCP Server 桥接)                │
│  ├── AgentCore Observability (独立 ADOT SDK + CloudWatch)         │
│  └── Bedrock Knowledge Base (RAG, 通过 MCP 或 Gateway)           │
└──────────────────────────────────────────────────────────────────┘
```

---

## 1. 行动分级

| 优先级 | 定义 | 时间窗口 | 前置条件 |
|--------|------|---------|---------|
| **P0 — 基础就绪** | 依赖引入、接口定义、基础落实 | Phase 2 M6 之前 | improvement-plan S0 全部完成 |
| **P1 — 核心集成** | Claude Agent SDK 适配器、AgentCore Runtime 部署 | Phase 2 M6 期间 | P0 完成 |
| **P2 — 平台能力** | Gateway、Memory、Observability 集成 | Phase 3 之前 | P1 完成 |
| **P3 — 深度集成** | 长期记忆、多 Agent 编排、Identity | Phase 3-4 | P2 完成 |

---

## 2. P0 — 基础就绪

### P0-1: 引入 Claude Agent SDK + 升级 boto3

**问题**: 项目无 Agent 框架依赖。当前 `boto3>=1.34.0` 不支持 AgentCore 控制面 API。

**关键理解 — 两条独立的依赖路径**:

```
Agent 执行路径:
  Python → claude-agent-sdk → Claude Code CLI (Node.js 子进程) → Bedrock Invoke API
  • SDK 不使用 boto3，不直接调用 Bedrock API
  • CLI 使用 AWS 标准凭证链认证 (环境变量 / IAM Role)
  • 需要: Node.js 18+ + CLAUDE_CODE_USE_BEDROCK=1 + AWS_REGION

Platform API 路径:
  Python → boto3 → AgentCore Control API / Bedrock KB API / Converse API (降级)
  • 管理 AgentCore 资源 (Runtime, Gateway, Memory) 和 Bedrock KB
  • BedrockLLMClient 降级路径仍走 Converse API
```

**行动项**:

```toml
# pyproject.toml [project] dependencies 变更

# Agent 执行路径
"claude-agent-sdk>=0.1.0",          # 新增: Claude Agent SDK (自动捆绑 Claude Code CLI)

# Platform API 路径
"boto3>=1.36.0",                     # 升级: 支持 AgentCore 控制面 API
"bedrock-agentcore>=0.1.0",         # 新增: AgentCore SDK (Runtime 部署封装)
```

**运行时要求**: Node.js 18+（`claude-agent-sdk` 安装时自动捆绑 Claude Code CLI）。开发环境需安装 Node.js；Docker 镜像需包含 Node.js 运行时。

**影响文件**:
- `backend/pyproject.toml`
- `backend/.claude/rules/tech-stack.md`（更新版本矩阵，新增 Claude Agent SDK + Node.js 18+ 要求）

**验证标准**:
- `uv sync` 成功
- `python -c "from claude_agent_sdk import query"` 无 ImportError
- `python -c "import boto3; c = boto3.client('bedrock-agentcore-control', region_name='us-east-1')"` 无 ImportError
- `node --version` 输出 >= 18

---

### P0-2: 定义 `IAgentRuntime` 接口

**问题**: 当前 `ILLMClient` 仅支持单轮问答，不支持工具列表传递和 Agent 循环。

**行动项**: 在 `execution/application/interfaces/` 新增 `agent_runtime.py`：

```python
@dataclass
class AgentTool:
    """Agent 可用工具定义（MCP 工具）。"""
    name: str
    description: str
    input_schema: dict[str, Any]
    tool_type: str  # "mcp_server" | "api" | "function"
    config: dict[str, Any] = field(default_factory=dict)

@dataclass
class AgentRequest:
    """Agent 执行请求。"""
    prompt: str
    system_prompt: str = ""
    model_id: str = ""
    tools: list[AgentTool] = field(default_factory=list)
    history: list[LLMMessage] = field(default_factory=list)
    temperature: float = 0.7
    max_tokens: int = 2048
    gateway_url: str = ""  # AgentCore Gateway MCP 端点

@dataclass
class AgentResponseChunk:
    """Agent 流式响应片段。"""
    content: str = ""
    tool_use: dict[str, Any] | None = None
    tool_result: str | None = None
    done: bool = False
    input_tokens: int = 0
    output_tokens: int = 0

class IAgentRuntime(ABC):
    """Agent 运行时抽象接口。支持 Agent Loop。"""

    @abstractmethod
    async def execute(self, request: AgentRequest) -> AgentResponseChunk:
        """同步执行 Agent。"""

    @abstractmethod
    async def execute_stream(
        self, request: AgentRequest,
    ) -> AsyncIterator[AgentResponseChunk]:
        """流式执行 Agent。"""
```

**设计决策**: `ILLMClient` **保留**作为降级路径。`IAgentRuntime` 为新接口，由 `runtime_type` 决定使用哪个。即使当前只有一个 `ClaudeAgentAdapter` 实现，保留接口抽象符合 Clean Architecture。

**影响文件**:
- 新增: `backend/src/modules/execution/application/interfaces/agent_runtime.py`
- 修改: `backend/src/modules/execution/application/interfaces/__init__.py`

**验证标准**: 接口定义通过 mypy strict 检查；架构合规测试通过。

---

### P0-3: 定义 `IToolQuerier` 跨模块接口

**问题**: execution 模块无法获取 Agent 绑定的已审批工具列表。

**行动项**: 在 `shared/domain/interfaces/` 新增 `tool_querier.py`：

```python
@dataclass(frozen=True)
class ApprovedToolInfo:
    """已审批工具的最小信息集。"""
    id: int
    name: str
    description: str
    tool_type: str  # "mcp_server" | "api" | "function"
    server_url: str = ""
    endpoint_url: str = ""
    method: str = ""
    runtime: str = ""
    handler: str = ""

class IToolQuerier(ABC):
    @abstractmethod
    async def list_tools_for_agent(
        self, agent_id: int,
    ) -> list[ApprovedToolInfo]:
        """获取 Agent 可用的已审批工具列表。"""
```

同步新增 `ToolQuerierImpl` 实现。

**影响文件**:
- 新增: `backend/src/shared/domain/interfaces/tool_querier.py`
- 修改: `backend/src/shared/domain/interfaces/__init__.py`
- 新增: `backend/src/modules/tool_catalog/infrastructure/services/tool_querier_impl.py`

**验证标准**: `IToolQuerier` 可通过 DI 注入到 `ExecutionService`；架构合规测试通过。

---

### P0-4: `AgentConfig` 新增 `runtime_type` 字段

**问题**: 需要区分 Agent 使用 Claude Agent SDK 执行还是简单对话。

**行动项**:

```python
@dataclass(frozen=True)
class AgentConfig:
    model_id: str = "us.anthropic.claude-sonnet-4-20250514-v1:0"
    temperature: float = 0.7
    max_tokens: int = 2048
    top_p: float = 1.0
    stop_sequences: tuple[str, ...] = ()
    runtime_type: str = "agent"  # 新增: "agent" (Claude Agent SDK) | "basic" (BedrockLLMClient)
```

| runtime_type | 使用方式 | 适用场景 |
|-------------|---------|---------|
| `agent` (默认) | Claude Agent SDK（ClaudeAgentAdapter） | 工具调用、Agent Loop、MCP、代码操作 |
| `basic` | BedrockLLMClient（现有） | 简单对话（无工具调用），降级路径 |

**影响文件**:
- 修改: `backend/src/modules/agents/domain/` (AgentConfig)
- 修改: `backend/src/modules/agents/infrastructure/persistence/models/` (ORM 新列)
- 新增: Alembic migration
- 修改: `backend/src/shared/domain/interfaces/agent_querier.py` (ActiveAgentInfo 新增 runtime_type)

**验证标准**: 创建 Agent 时可指定 `runtime_type`；`ActiveAgentInfo` 正确传递该字段。

---

### P0-5: 落实可观测性基础

**问题**: 规范完整但实际代码不足：无 structlog 配置、无 Correlation ID 中间件、readiness 空实现。

**行动项**:
1. 实现 `src/shared/infrastructure/logging.py` — structlog 配置（dev 彩色/prod JSON）
2. 实现 `src/presentation/api/middleware/correlation.py` — Correlation ID 中间件
3. 完善 `/health/ready` 端点 — 添加数据库连接检查（`SELECT 1` 超时 3s）
4. 将 `bedrock_llm_client.py` 中的 `logging.getLogger` 替换为 `structlog.get_logger`

**影响文件**:
- 新增: `backend/src/shared/infrastructure/logging.py`
- 新增: `backend/src/presentation/api/middleware/correlation.py`
- 修改: `backend/src/presentation/api/routes/health.py`
- 修改: `backend/src/modules/execution/infrastructure/external/bedrock_llm_client.py`
- 修改: `backend/src/presentation/api/main.py`（注册中间件）

**验证标准**: 所有日志输出包含 `correlation_id`；`/health/ready` 数据库不可达时返回 503；prod 模式日志为 JSON 格式。

---

### P0-6: 完善 Bedrock Knowledge Base 创建参数

**问题**: `BedrockKnowledgeAdapter.create_knowledge_base()` 中关键参数为空字符串占位。

**行动项**:
1. 在 `Settings` 中新增 KB 相关配置（IAM Role ARN、Embedding Model ARN、S3 Bucket 名称）
2. 完善 `create_knowledge_base` 方法参数
3. RAG 注入优化：从伪造 user 消息 → system prompt 级上下文注入

**影响文件**:
- 修改: `backend/src/modules/knowledge/infrastructure/external/bedrock_knowledge_adapter.py`
- 修改: `backend/src/shared/infrastructure/settings.py`
- 修改: `backend/src/modules/execution/application/services/execution_service.py`（RAG 注入方式）

**验证标准**: 配置完整参数后调用 Bedrock API 成功；RAG 检索结果注入到 system prompt 而非 user 消息。

---

## 3. P1 — 核心集成

### P1-1: 实现 `ClaudeAgentAdapter`

**前置**: P0-1, P0-2, P0-3

**行动项**: 在 `execution/infrastructure/external/` 新增 Claude Agent SDK 适配器。

```python
# execution/infrastructure/external/claude_agent_adapter.py

from claude_agent_sdk import ClaudeSDKClient, ClaudeAgentOptions, query

class ClaudeAgentAdapter(IAgentRuntime):
    """基于 Claude Agent SDK 的 Agent 运行时实现。"""

    async def execute(self, request: AgentRequest) -> AgentResponseChunk:
        mcp_servers = self._build_mcp_config(request)
        options = ClaudeAgentOptions(
            system_prompt=request.system_prompt,
            allowed_tools=self._build_allowed_tools(request.tools),
            mcp_servers=mcp_servers,
            permission_mode="bypassPermissions",
            max_turns=20,
        )

        collected = ""
        total_input = 0
        total_output = 0

        async for msg in query(prompt=request.prompt, options=options):
            if hasattr(msg, 'content'):
                collected += msg.content
            if hasattr(msg, 'usage'):
                total_input = msg.usage.get("input_tokens", 0)
                total_output = msg.usage.get("output_tokens", 0)

        return AgentResponseChunk(
            content=collected,
            done=True,
            input_tokens=total_input,
            output_tokens=total_output,
        )

    async def execute_stream(
        self, request: AgentRequest,
    ) -> AsyncIterator[AgentResponseChunk]:
        mcp_servers = self._build_mcp_config(request)
        options = ClaudeAgentOptions(
            system_prompt=request.system_prompt,
            allowed_tools=self._build_allowed_tools(request.tools),
            mcp_servers=mcp_servers,
            permission_mode="bypassPermissions",
        )

        async for msg in query(prompt=request.prompt, options=options):
            if hasattr(msg, 'content'):
                yield AgentResponseChunk(content=msg.content)
            # ResultMessage 表示完成
            if hasattr(msg, 'session_id'):
                yield AgentResponseChunk(
                    done=True,
                    input_tokens=msg.usage.get("input_tokens", 0) if msg.usage else 0,
                    output_tokens=msg.usage.get("output_tokens", 0) if msg.usage else 0,
                )

    def _build_mcp_config(self, request: AgentRequest) -> dict:
        """构建 Claude Agent SDK 的 MCP Server 配置。"""
        config = {}
        if request.gateway_url:
            config["gateway"] = {
                "type": "sse",
                "url": request.gateway_url,
            }
        # 将 API/FUNCTION 类型工具封装为进程内 MCP Server
        non_mcp_tools = [t for t in request.tools if t.tool_type != "mcp_server"]
        if non_mcp_tools:
            config["platform-tools"] = self._create_sdk_mcp_server(non_mcp_tools)
        return config

    def _build_allowed_tools(self, tools: list[AgentTool]) -> list[str]:
        """构建 allowed_tools 列表。"""
        allowed = []
        if any(t.tool_type == "mcp_server" for t in tools):
            allowed.append("mcp__gateway__*")
        if any(t.tool_type != "mcp_server" for t in tools):
            allowed.append("mcp__platform-tools__*")
        return allowed

    def _create_sdk_mcp_server(self, tools: list[AgentTool]):
        """将 API/FUNCTION 类型工具封装为 SDK MCP Server。"""
        from claude_agent_sdk import tool, create_sdk_mcp_server
        # 动态生成 MCP 工具定义...
        ...
```

**关键设计**:
- `MCP_SERVER` 类型工具 → 通过 AgentCore Gateway URL 连接（`mcp_servers.gateway`）
- `API` / `FUNCTION` 类型工具 → 封装为进程内 SDK MCP Server（`create_sdk_mcp_server`）
- Claude Agent SDK 内置的 Agent Loop 自动处理 tool_use → 执行 → tool_result 循环

**影响文件**:
- 新增: `backend/src/modules/execution/infrastructure/external/claude_agent_adapter.py`

**验证标准**: 单元测试（Mock Claude Agent SDK）通过；集成测试（调用 Bedrock Claude + 简单 MCP 工具）通过。

---

### P1-2: 扩展 `ExecutionService` 支持 `IAgentRuntime`

**前置**: P0-2, P0-3, P0-4, P1-1

**行动项**: 修改 `ExecutionService` 根据 `runtime_type` 选择运行时。

```python
class ExecutionService:
    def __init__(
        self,
        # ...现有参数...
        agent_runtime: IAgentRuntime | None = None,  # 新增
        tool_querier: IToolQuerier | None = None,     # 新增
    ) -> None: ...

    async def send_message(self, conversation_id, dto, user_id):
        ctx = await self._prepare_for_send(conversation_id, dto.content, user_id)

        if ctx.agent_info.runtime_type == "agent" and self._agent_runtime:
            # Agent 模式: Claude Agent SDK (支持工具调用 + Agent Loop)
            tools = await self._tool_querier.list_tools_for_agent(ctx.agent_info.id) if self._tool_querier else []
            request = AgentRequest(
                prompt=dto.content,
                system_prompt=ctx.agent_info.system_prompt,
                model_id=ctx.agent_info.model_id,
                tools=[self._to_agent_tool(t) for t in tools],
                history=ctx.llm_messages,
                gateway_url=self._settings.agentcore_gateway_url,
            )
            response = await self._agent_runtime.execute(request)
            ...
        else:
            # Basic 模式: BedrockLLMClient (现有逻辑, 降级路径)
            response = await self._llm_client.invoke(...)
            ...
```

**影响文件**:
- 修改: `backend/src/modules/execution/application/services/execution_service.py`
- 修改: `backend/src/modules/execution/api/dependencies.py`（DI 注入）
- 修改: `backend/src/presentation/api/providers.py`（组装新依赖）

**验证标准**: `runtime_type=agent` 使用 ClaudeAgentAdapter；`runtime_type=basic` 使用 BedrockLLMClient；所有现有测试继续通过。

---

### P1-3: AgentCore Runtime CDK 资源

**前置**: P1-1

**行动项**: 在 `infra/` 新增 AgentCore Runtime + Gateway CDK 资源。

```typescript
import * as agentcore from '@aws-cdk/aws-bedrock-agentcore-alpha';

export class AgentCoreStack extends cdk.Stack {
    constructor(scope: Construct, id: string, props: AgentCoreStackProps) {
        super(scope, id, props);

        // Agent Runtime (Claude Agent SDK 容器)
        const runtime = new agentcore.Runtime(this, 'AgentRuntime', {
            runtimeName: `${props.projectName}-agent-runtime`,
            agentRuntimeArtifact: agentcore.AgentRuntimeArtifact.fromEcrImage(
                props.ecrRepository, 'latest'
            ),
            networkConfiguration: { networkMode: 'VPC', vpc: props.vpc },
        });

        // Agent Gateway (MCP 统一入口)
        const gateway = new agentcore.Gateway(this, 'AgentGateway', {
            name: `${props.projectName}-gateway`,
            protocolType: 'MCP',
        });
    }
}
```

**影响文件**:
- 新增: `infra/lib/stacks/agentcore-stack.ts`
- 修改: `infra/bin/app.ts`（Stack 依赖链）
- 新增: `backend/Dockerfile.agent`（Python + Node.js 双运行时镜像）

**验证标准**: `cdk synth` 成功生成 CloudFormation 模板；`cdk deploy` 到 Dev 环境成功。

---

### P1-4: Agent 应用入口点

**前置**: P1-1, P1-3

**行动项**: 创建可部署到 AgentCore Runtime 的 Agent 入口应用。

```python
# backend/src/agent_entrypoint.py

from bedrock_agentcore.runtime import BedrockAgentCoreApp
from claude_agent_sdk import query, ClaudeAgentOptions

app = BedrockAgentCoreApp()

@app.entrypoint
async def invoke(payload: dict) -> dict:
    """AgentCore Runtime 入口函数。"""
    prompt = payload.get("prompt", "")
    system_prompt = payload.get("system_prompt", "")
    gateway_url = payload.get("gateway_url", "")
    allowed_tools = payload.get("allowed_tools", [])

    options = ClaudeAgentOptions(
        system_prompt=system_prompt,
        allowed_tools=allowed_tools,
        mcp_servers={"gateway": {"type": "sse", "url": gateway_url}} if gateway_url else {},
        permission_mode="bypassPermissions",
    )

    collected = ""
    usage = {}
    async for msg in query(prompt=prompt, options=options):
        if hasattr(msg, 'content'):
            collected += msg.content
        if hasattr(msg, 'usage'):
            usage = msg.usage or {}

    return {
        "content": collected,
        "input_tokens": usage.get("input_tokens", 0),
        "output_tokens": usage.get("output_tokens", 0),
    }

if __name__ == "__main__":
    app.run()
```

**Docker 镜像**:

```dockerfile
# backend/Dockerfile.agent
FROM python:3.12-slim AS base

# Node.js 18+ — Claude Code CLI 运行时依赖
RUN apt-get update && apt-get install -y nodejs npm && rm -rf /var/lib/apt/lists/*

COPY pyproject.toml uv.lock ./
RUN pip install uv && uv sync
# claude-agent-sdk 安装时自动捆绑 Claude Code CLI，无需单独安装

COPY src/ ./src/

# Bedrock 认证: 通过 AWS 标准凭证链 (ECS Task Role / AgentCore Runtime IAM Role)
# 不需要 ANTHROPIC_API_KEY
ENV CLAUDE_CODE_USE_BEDROCK=1
# AWS_REGION 由部署时注入

CMD ["python", "src/agent_entrypoint.py"]
```

**认证说明**:
- Agent 容器通过 AgentCore Runtime 的 IAM Role 获取 AWS 凭证，无需硬编码
- `CLAUDE_CODE_USE_BEDROCK=1` 告诉 Claude Code CLI 使用 Bedrock 而非 Anthropic API
- `AWS_REGION` 由 AgentCore Runtime / ECS Task Definition 注入
- **不需要** `ANTHROPIC_API_KEY` 环境变量

**IAM 权限** (Agent 执行路径需要 Invoke API，非 Converse API):
```json
{
  "Action": [
    "bedrock:InvokeModel",
    "bedrock:InvokeModelWithResponseStream",
    "bedrock:ListInferenceProfiles"
  ]
}
```

**影响文件**:
- 新增: `backend/src/agent_entrypoint.py`
- 新增: `backend/Dockerfile.agent`

**验证标准**: 本地 `CLAUDE_CODE_USE_BEDROCK=1 AWS_REGION=us-east-1 python src/agent_entrypoint.py` 启动成功；容器化后可通过 AgentCore Runtime 调用。

---

## 4. P2 — 平台能力

### P2-1: AgentCore Gateway 集成

**前置**: P1-1, ADR-007（待创建）

**行动项**:
1. CDK 中配置 Gateway Target（将 tool-catalog 已审批 MCP_SERVER 工具注册为 Target）
2. Claude Agent SDK `mcp_servers` 配置中连接 Gateway MCP 端点
3. 实现工具同步机制（tool_catalog 审批通过 → 自动注册到 Gateway）
4. API/FUNCTION 类型工具通过 SDK MCP Server 或 Lambda Target 接入

**影响文件**:
- 修改: `infra/lib/stacks/agentcore-stack.ts`（Gateway Target）
- 新增: `backend/src/modules/tool_catalog/infrastructure/external/gateway_sync_adapter.py`

**验证标准**: MCP_SERVER 类型工具通过 Gateway 可被 Claude Agent SDK 调用。

---

### P2-2: AgentCore Memory 集成（通过 MCP 桥接）

**前置**: P1-2

Claude Agent SDK 无原生 AgentCore Memory 集成。通过自定义 MCP Server 桥接：

**行动项**:
1. 创建 AgentCore Memory 资源（CDK 或 boto3）
2. 实现 `memory-mcp-server` — 封装 AgentCore Memory API 为 MCP 工具（`save_memory`、`recall_memory`）
3. 在 ClaudeAgentAdapter 的 `mcp_servers` 中配置该 MCP Server
4. Agent 可通过 MCP 工具调用 Memory 读写

```python
# memory_mcp_server.py — AgentCore Memory 的 MCP Server 封装

from claude_agent_sdk import tool, create_sdk_mcp_server

@tool("save_memory", "保存信息到长期记忆", {"content": str, "topic": str})
async def save_memory(args):
    # 调用 AgentCore Memory API 写入
    ...

@tool("recall_memory", "从记忆中检索相关信息", {"query": str})
async def recall_memory(args):
    # 调用 AgentCore Memory API 检索
    ...

memory_server = create_sdk_mcp_server(
    name="memory", version="1.0.0",
    tools=[save_memory, recall_memory]
)
```

5. 保留 MySQL Conversation/Message 作为平台管理数据

**验证标准**: Agent 执行时可通过 MCP 工具写入/检索 AgentCore Memory。

---

### P2-3: OpenTelemetry / AgentCore Observability 集成

**前置**: P0-5

Claude Agent SDK 无内置 OpenTelemetry。独立集成 ADOT SDK：

**行动项**:
1. 引入 OpenTelemetry SDK (`opentelemetry-api`, `opentelemetry-sdk`, `opentelemetry-instrumentation-fastapi`)
2. 配置 ADOT 导出到 CloudWatch
3. 关键操作添加 Span（Agent 执行、工具调用、RAG 检索、数据库查询）
4. Claude Agent SDK 的 Hooks（PostToolUse）可用于记录工具调用 Span

**影响文件**:
- 新增: `backend/src/shared/infrastructure/tracing.py`
- 修改: `backend/pyproject.toml`（新增 OpenTelemetry 依赖）
- 修改: `backend/src/presentation/api/main.py`（TracerProvider 初始化）

**验证标准**: CloudWatch 中可看到 Agent 执行 trace；关键 Span 可见。

---

## 5. P3 — 深度集成

### P3-1: AgentCore Memory 长期记忆策略

**前置**: P2-2

1. 启用 Memory Strategy（Summary、User Preference、Semantic）
2. 配置异步提取任务
3. Agent 执行时自动检索长期记忆作为上下文补充

---

### P3-2: 多 Agent 编排 (orchestration 模块)

**前置**: P1-1, P1-2

1. 基于 Claude Agent SDK 子 Agent（AgentDefinition + Task 工具）实现 Agent 间协作
2. 通过 AgentCore Runtime A2A 协议支持跨会话 Agent 通信
3. DAG 定义和执行引擎

---

### P3-3: AgentCore Identity 集成

**前置**: P2-1

1. 配置 AgentCore Identity OAuth 2.0 凭证提供者
2. Gateway 入站认证对接平台 auth 模块
3. Token Vault 管理第三方 API 密钥

---

### P3-4: Agent 容器镜像构建 + ECR 推送 + AgentCore Runtime 部署验证

**前置**: P1-3 (AgentCore Runtime CDK), P1-4 (agent_entrypoint.py)

**背景**: P1-3 和 P1-4 完成了代码产物（AgentCoreStack CDK 资源、agent_entrypoint.py、Dockerfile.agent），但从未实际构建镜像推送到 ECR 并在 AgentCore Runtime 上运行验证。当前 AgentCore Runtime 处于"CDK 已部署但无容器运行"状态。

**行动项**:
1. 构建 `Dockerfile.agent` 镜像并推送到 AgentCoreStack 创建的 ECR Repository
2. 触发 AgentCore Runtime 拉取镜像并启动容器
3. 通过 `invoke_agent_runtime()` API 验证 agent_entrypoint.py 正常运行（健康检查 + 基础对话测试）
4. 建立 CI/CD Pipeline 自动化 Agent 镜像构建和推送流程

**影响文件**:
- 新增/修改: `.github/workflows/agent-deploy.yml`（CI/CD Pipeline）
- 修改: `infra/` CDK（可能需要调整 Runtime 配置参数）
- 验证: `backend/src/agent_entrypoint.py`（Runtime 上运行正确性）

**验证标准**: AgentCore Runtime 健康检查通过；通过 `invoke_agent_runtime()` API 发送测试 prompt 获得正确响应。

---

### P3-5: Platform API → AgentCore Runtime 调用路径切换

**前置**: P3-4

**背景**: 当前 Platform API 的 `ClaudeAgentAdapter` 在 ECS Fargate 进程内直接调用 `claude_agent_sdk.query()`，Agent Loop 运行在 Platform API 进程中。目标架构是 Platform API 通过 `invoke_agent_runtime()` 将 Agent 执行委托给 AgentCore Runtime，实现 Platform API 与 Agent 执行层的部署分离。

**行动项**:
1. 实现 `AgentCoreRuntimeAdapter`（新的 `IAgentRuntime` 实现），内部调用 `invoke_agent_runtime()` API
2. 在 `dependencies.py` 中根据配置选择适配器：`ClaudeAgentAdapter`（进程内，降级路径）或 `AgentCoreRuntimeAdapter`（远程 Runtime）
3. 处理 `invoke_agent_runtime()` 的流式响应映射到 `AgentResponseChunk`
4. 性能对比测试：进程内执行 vs AgentCore Runtime 远程调用的延迟和吞吐量差异
5. 更新 ExecutionService 的 OpenTelemetry Span，区分两种执行路径

**影响文件**:
- 新增: `backend/src/modules/execution/infrastructure/external/agentcore_runtime_adapter.py`
- 修改: `backend/src/modules/execution/api/dependencies.py`（适配器选择逻辑）
- 修改: `backend/src/shared/infrastructure/settings.py`（新增 `AGENT_RUNTIME_MODE` 配置）
- 修改: `backend/src/modules/execution/application/services/execution_service.py`（Span 属性）

**验证标准**: Platform API 通过 AgentCore Runtime 执行对话成功；流式 SSE 响应正常；两种路径可通过配置切换；进程内路径作为降级保留。

---

## 6. 与 improvement-plan.md 的关系

### 依赖关系

```
improvement-plan S0 (已完成 ✅)
       ↓
本计划 P0 (基础就绪)
├── P0-1: 依赖升级
├── P0-2: IAgentRuntime 接口
├── P0-3: IToolQuerier 接口
├── P0-4: runtime_type 字段
├── P0-5: 可观测性基础
└── P0-6: KB 参数完善
       ↓
本计划 P1 (核心集成)
├── P1-1: ClaudeAgentAdapter (进程内调用 claude_agent_sdk.query())
├── P1-2: ExecutionService 扩展
├── P1-3: AgentCore Runtime CDK (资源已部署，无容器运行)
└── P1-4: Agent 入口点 (代码已就绪，未构建部署)
       ↓
本计划 P2 (平台能力)
       ↓
本计划 P3 (深度集成)
├── P3-1~3: Memory / 多 Agent / Identity
├── P3-4: Agent 容器构建 + ECR 推送 + Runtime 部署验证 (依赖 P1-3, P1-4)
└── P3-5: Platform API → AgentCore Runtime 调用路径切换 (依赖 P3-4)
```

### 互补关系

| improvement-plan 项 | 本计划关联项 | 关系 |
|---------------------|-------------|------|
| S2-2 对话历史滑动窗口 | P2-2 AgentCore Memory | Memory 可替代自建滑动窗口 |
| S4-4 基础监控告警 | P2-3 Observability | OpenTelemetry + CloudWatch 统一实现 |
| S3-2 端到端集成验证 | P1-4 Agent 入口点 | Agent 入口点是端到端验证的前提 |

---

## 7. 进度跟踪

### 检查清单

#### P0 — 基础就绪

- [ ] P0-1: 升级 boto3 + 引入 Claude Agent SDK 依赖
- [ ] P0-2: 定义 IAgentRuntime 接口
- [ ] P0-3: 定义 IToolQuerier 跨模块接口
- [ ] P0-4: AgentConfig 新增 runtime_type 字段
- [ ] P0-5: 落实可观测性基础 (structlog + Correlation ID + readiness check)
- [ ] P0-6: 完善 Bedrock KB 创建参数

#### P1 — 核心集成

- [ ] P1-1: 实现 ClaudeAgentAdapter
- [ ] P1-2: 扩展 ExecutionService 支持 IAgentRuntime
- [ ] P1-3: AgentCore Runtime + Gateway CDK 资源
- [ ] P1-4: Agent 应用入口点 (BedrockAgentCoreApp + Claude Agent SDK)

#### P2 — 平台能力

- [ ] P2-1: AgentCore Gateway 集成
- [ ] P2-2: AgentCore Memory 集成（MCP 桥接）
- [ ] P2-3: OpenTelemetry / AgentCore Observability 集成

#### P3 — 深度集成

- [ ] P3-1: AgentCore Memory 长期记忆策略
- [ ] P3-2: 多 Agent 编排 (orchestration 模块)
- [ ] P3-3: AgentCore Identity 集成
- [ ] P3-4: Agent 容器镜像构建 + ECR 推送 + AgentCore Runtime 部署验证
- [ ] P3-5: Platform API → AgentCore Runtime 调用路径切换

### 后续 ADR

| ADR | 标题 | 触发时机 |
|-----|------|---------|
| ADR-007 | AgentCore Gateway 集成策略 | P2-1 开始前 |
| ADR-008 | 架构拆分 — Platform API 与 Agent Runtime 部署分离 | Phase 2 完成后评估 |

---

## 8. 风险管理

| 风险 | 影响 | 概率 | 缓解策略 |
|------|------|:----:|---------|
| AgentCore API 区域可用性 | 部署区域受限（当前 9 个区域） | 中 | 确认部署区域；保留 Converse API 降级路径 |
| Claude Agent SDK 稳定性 | SDK 或 Claude Code CLI 版本更新可能有 breaking changes | 中 | IAgentRuntime 接口隔离；锁定 SDK 版本 + 定期升级；降级到 BedrockLLMClient |
| Node.js 依赖 | Docker 镜像需 Python + Node.js 18+ 双运行时，体积增大约 100MB | 低 | 独立 Dockerfile.agent；Node.js 仅 Agent 执行层需要，Platform API 层不需要 |
| CLI 子进程通信 | SDK 通过子进程调用 CLI，可能有 IPC 延迟和进程管理复杂度 | 低 | AgentCore Runtime Firecracker microVM 提供进程隔离；监控 CLI 进程健康状态 |
| CDK L2 Construct 成熟度 | `@aws-cdk/aws-bedrock-agentcore-alpha` 为 alpha | 中 | 必要时降级到 L1 CfnResource |
| AgentCore Memory MCP 桥接 | 非原生集成，额外延迟和复杂度 | 低 | 短期保留 MySQL 会话管理；桥接层保持薄封装 |
| 仅 Claude 模型 | 无法使用其他 Bedrock 模型 | 低 | Claude 系列覆盖成本梯度（Haiku/Sonnet/Opus）；basic 模式保留 Converse API |
| AgentCore 成本超预期 | 各服务独立计费 | 中 | Dev 环境最小化使用；保留降级路径 |
