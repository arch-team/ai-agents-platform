# ADR-006: Agent 框架选型 — Claude Agent SDK + Claude Code CLI

- **日期**: 2026-02-10
- **状态**: 已采纳
- **关联**: ADR-001 (架构模式), ADR-003 (AgentCore 基础设施), ADR-005 (数据库引擎选型)

## 背景

### 当前状态

项目已完成 Phase 1-2 的 5 个业务模块（auth, agents, execution, knowledge, tool-catalog），1023 个测试，95%+ 覆盖率。`execution` 模块通过 `BedrockLLMClient` 直接调用 boto3 `bedrock-runtime` 的 `converse()` / `converse_stream()` API，实现单轮请求-响应式对话。

**当前 `ILLMClient` 接口**:

```python
class ILLMClient(ABC):
    async def invoke(self, model_id, messages, *, system_prompt, temperature, max_tokens, top_p, stop_sequences) -> LLMResponse
    async def invoke_stream(self, model_id, messages, *, ...) -> AsyncIterator[LLMStreamChunk]
```

**当前依赖**: `boto3>=1.34.0`，未引入任何 Agent 框架依赖。

### 需要解决的问题

| 问题 | 说明 |
|------|------|
| **无 Agent 循环** | 当前是单轮问答，LLM 无法自主决定是否调用工具并继续推理 |
| **无 Tool Use** | `ILLMClient` 不接收 `tools` 参数，tool-catalog 中注册的工具无法在对话中使用 |
| **无 MCP 集成** | tool-catalog 定义了 `MCP_SERVER` 类型但无实际 MCP 客户端 |
| **未对接 AgentCore** | ADR-003 已决策采纳 AgentCore，但代码中未使用任何 AgentCore 服务 |
| **未使用 Agent SDK** | 项目愿景为"基于 Claude Agent SDK + AgentCore"，但尚未引入 SDK |

### 决策驱动

项目目标架构要求：
1. 使用 **Claude Agent SDK** + Claude Code CLI 构建 Agent 应用
2. 通过 **AWS AgentCore Runtime** 解决 Agent 运行时
3. 使用 **AWS AgentCore Gateway** 对接外部 MCP 统一入口
4. 基于 **AWS AgentCore + Bedrock KB** 的 Python SDK 封装

## 备选方案

### 方案 A: Claude Agent SDK（单一框架）

将 `execution` 模块的 Agent 执行层替换为 Claude Agent SDK，所有 Agent 统一使用 Claude Agent SDK 运行。

```python
from claude_agent_sdk import query, ClaudeAgentOptions

async for msg in query(
    prompt=user_message,
    options=ClaudeAgentOptions(
        system_prompt=agent.system_prompt,
        allowed_tools=["mcp__gateway__*"],
        mcp_servers={"gateway": {"type": "sse", "url": agentcore_gateway_url}},
        permission_mode="bypassPermissions",
    )
):
    yield msg
```

| 优势 | 劣势 |
|------|------|
| Claude Code 全部能力（文件读写、代码编辑、Web 搜索等 13 种内置工具） | 仅支持 Claude 模型 |
| 内置 Agent Loop — 自动处理 tool_use → 执行 → tool_result 循环 | 依赖 Node.js（SDK 底层运行 Claude Code CLI） |
| 原生 MCP 支持（stdio/HTTP/SSE 三种传输协议） | 自定义工具必须包装为 MCP Server |
| 已有 AgentCore Runtime 生产部署案例（BGL 金融合规） | 无内置 AgentCore Memory 集成（需 MCP 桥接） |
| Hooks 系统（PreToolUse/PostToolUse 等 6 种事件） | 无内置 OpenTelemetry（需独立集成） |
| 子 Agent 支持（AgentDefinition + Task 工具） | - |
| 会话管理（resume/fork） | - |
| 结构化输出（JSON Schema / Pydantic 验证） | - |
| 与项目愿景完全一致（Claude Agent SDK + Claude Code CLI） | - |
| 单一框架降低项目复杂度 | - |

### 方案 B: Strands Agents SDK（AWS 原生）

使用 AWS 官方 Strands Agents SDK，获得 AgentCore 原生集成。

| 优势 | 劣势 |
|------|------|
| AgentCore 一等公民（Memory/Observability 原生集成） | 无 Claude Code 级别内置工具 |
| 模型无关（Bedrock 全模型支持） | 与项目"Claude Agent SDK"愿景不一致 |
| 纯 Python，无 Node.js 依赖 | Agent 能力不如 Claude Agent SDK 丰富 |
| Apache 2.0 开源 | - |

### 方案 C: 混合方案（Strands 默认 + Claude Agent SDK 补充）

两套框架并存，增加复杂度。

| 优势 | 劣势 |
|------|------|
| 两者兼备 | 双框架维护成本 |
| 灵活 | 接口设计需兼容两种 SDK 差异 |
| - | runtime_type 三种模式增加认知负担 |

## 决策

**选择方案 A: Claude Agent SDK 作为唯一 Agent 框架**，配合 `BedrockLLMClient` 作为降级路径。

## 理由

### 1. 与项目愿景完全一致

项目的核心定位是"基于 Claude Agent SDK + Claude Code CLI + AWS AgentCore 构建 AI Agents 平台"。选择 Claude Agent SDK 作为唯一框架，使项目目标、技术选型和实现代码三者对齐，降低认知成本和决策负担。

### 2. 单一框架降低项目复杂度

| 维度 | 混合方案 | 纯 Claude Agent SDK |
|------|---------|-------------------|
| Agent 框架 | 2 套 SDK + 2 个适配器 | 1 套 SDK + 1 个适配器 |
| runtime_type | 3 种 (standard/code/basic) | 2 种 (agent/basic) |
| 工具定义 | `@tool` 装饰器 + MCP Server 两种 | 统一 MCP Server 一种 |
| 依赖管理 | strands + claude-agent-sdk + bedrock-agentcore | claude-agent-sdk + bedrock-agentcore |
| IAgentRuntime 适配器 | 需兼容两种 SDK 差异 | 只对接一种 SDK |
| 文档/维护 | 两套用法说明 | 一套 |

### 3. Claude Agent SDK 能力足够覆盖全部场景

Claude Agent SDK 内置 13 种工具（Read/Write/Edit/Bash/Glob/Grep/WebSearch/WebFetch/Task/AskUserQuestion/NotebookEdit 等），这些能力覆盖了：
- **通用对话**: system_prompt + MCP 工具调用
- **RAG 检索**: 通过 MCP 连接 AgentCore Gateway → Bedrock Knowledge Base
- **代码操作**: 内置 Read/Write/Edit/Bash
- **多 Agent 协作**: 内置 Task 工具 + AgentDefinition 子 Agent

### 4. MCP 统一工具协议

Claude Agent SDK 强制所有自定义工具通过 MCP 实现。这与 AgentCore Gateway（MCP 统一入口）的设计理念一致——所有工具通过 MCP 协议标准化。tool-catalog 中注册的三种工具类型均可通过 MCP 方式接入：

| ToolType | 接入方式 |
|----------|---------|
| `MCP_SERVER` | 直接通过 AgentCore Gateway 连接 |
| `API` | 封装为 MCP Server（API → MCP 适配器） |
| `FUNCTION` | 封装为 SDK MCP Server（`create_sdk_mcp_server`） |

### 5. AgentCore Runtime 已验证

AWS 官方博客和 BGL（金融合规场景）案例已验证 Claude Agent SDK + AgentCore Runtime 的组合在生产环境运行。部署模式：Docker 容器 → ECR → AgentCore Runtime。

### 6. 已知约束可接受

| 约束 | 评估 |
|------|------|
| **仅 Claude 模型** | Claude 系列已覆盖成本梯度（Haiku 低成本/Sonnet 通用/Opus 高质量），企业内部平台不需要多厂商模型 |
| **Node.js 依赖** | Docker 多阶段构建，镜像增大约 100MB，可接受 |
| **AgentCore Memory 无原生集成** | 短期保留 MySQL 会话管理；中期通过自定义 MCP Server 桥接 AgentCore Memory |
| **无内置 OpenTelemetry** | 独立集成 ADOT SDK（与框架无关），observability.md 已有规范 |

### 方案 B/C 不选的理由

**方案 B (纯 Strands)**: 与项目"Claude Agent SDK + Claude Code CLI"愿景不一致；缺少 Claude Code 级别的内置工具集。

**方案 C (混合方案)**: 双框架维护成本高；runtime_type 三种模式增加认知负担；对当前项目规模而言过度设计。

## 影响

### 1. 新增依赖

项目存在**两条依赖路径**，需分别管理：

**Agent 执行路径**（Claude Agent SDK → Claude Code CLI → Bedrock Invoke API）:
```toml
# pyproject.toml [project] dependencies
"claude-agent-sdk>=0.1.0",          # 新增: Claude Agent SDK (内部捆绑 Claude Code CLI)
```
- Claude Agent SDK **不使用 boto3**，不直接调用 Bedrock API
- SDK 通过子进程调用 Claude Code CLI（Node.js），CLI 负责所有 LLM 通信
- CLI 使用 Bedrock **Invoke API**（非 Converse API），通过 AWS 标准凭证链认证
- 运行时需要: Node.js 18+（SDK 安装时自动捆绑 CLI）+ 环境变量 `CLAUDE_CODE_USE_BEDROCK=1` + `AWS_REGION`

**Platform API 路径**（FastAPI → boto3 → AgentCore/KB 管理 API）:
```toml
# pyproject.toml [project] dependencies
"boto3>=1.36.0",                     # 升级: 支持 AgentCore 控制面 API
"bedrock-agentcore>=0.1.0",         # 新增: AgentCore SDK (Runtime 部署封装)
```
- Platform API 层仍需 boto3 管理 AgentCore 资源（Runtime、Gateway、Memory）和 Bedrock KB
- `BedrockLLMClient`（降级路径）仍使用 boto3 `bedrock-runtime` Converse API

**依赖链对比**:
```
Agent 路径:  Python → claude-agent-sdk → Claude Code CLI (Node.js) → Bedrock Invoke API
Platform 路径: Python → boto3 → Bedrock Converse API / AgentCore Control API / KB API
```

### 2. 新增接口: `IAgentRuntime`

在 `execution/application/interfaces/` 新增 Agent 运行时抽象：

```python
# execution/application/interfaces/agent_runtime.py

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

**设计决策**: 即使当前只有一个 `ClaudeAgentAdapter` 实现，保留 `IAgentRuntime` 接口抽象，符合 Clean Architecture 依赖倒置原则，未来扩展零成本。

### 3. 新增适配器

| 适配器 | 位置 | 实现的接口 | 用途 |
|--------|------|-----------|------|
| `ClaudeAgentAdapter` | `execution/infrastructure/external/claude_agent_adapter.py` | `IAgentRuntime` | Agent 模式（工具调用 + Agent Loop） |
| `BedrockLLMClient` | (现有，保留) | `ILLMClient` | Basic 模式（简单对话，降级路径） |

### 4. 新增跨模块接口: `IToolQuerier`

在 `shared/domain/interfaces/` 新增工具查询接口，连通 tool-catalog → execution：

```python
@dataclass(frozen=True)
class ApprovedToolInfo:
    """已审批工具的最小信息集。"""
    id: int
    name: str
    description: str
    tool_type: str  # "mcp_server" | "api" | "function"
    config: dict[str, Any]

class IToolQuerier(ABC):
    @abstractmethod
    async def list_tools_for_agent(self, agent_id: int) -> list[ApprovedToolInfo]:
        """获取 Agent 可用的已审批工具列表。"""
```

### 5. Agent 类型

在 `agents` 模块的 `AgentConfig` 中新增 `runtime_type` 字段：

| runtime_type | 使用方式 | 适用场景 |
|-------------|---------|---------|
| `agent` (默认) | Claude Agent SDK（`ClaudeAgentAdapter`） | 工具调用、Agent Loop、MCP 集成、代码操作 |
| `basic` | BedrockLLMClient（现有） | 简单对话（无工具调用），降级路径 |

### 6. AgentCore 服务集成计划

| AgentCore 服务 | 集成阶段 | 实现方式 |
|----------------|---------|---------|
| **Runtime** | Phase 2 M6 | CDK `@aws-cdk/aws-bedrock-agentcore-alpha` + `BedrockAgentCoreApp` 部署 |
| **Gateway** | Phase 2 M6 | Claude Agent SDK `mcp_servers` 配置连接 Gateway MCP 端点 |
| **Memory** | Phase 3 | 自定义 MCP Server 封装 AgentCore Memory API → Claude Agent SDK 作为 MCP 工具使用 |
| **Observability** | Phase 2 M6 | 独立集成 OpenTelemetry ADOT SDK + CloudWatch |
| **Identity** | Phase 3 | AgentCore Gateway 入站认证配置 |

### 7. CDK 基础设施新增

```typescript
import * as agentcore from '@aws-cdk/aws-bedrock-agentcore-alpha';

const runtime = new agentcore.Runtime(this, 'AgentRuntime', {
    runtimeName: 'ai-agents-platform',
    agentRuntimeArtifact: agentcore.AgentRuntimeArtifact.fromEcrImage(repo, 'latest'),
    networkConfiguration: { networkMode: 'VPC' },
});

const gateway = new agentcore.Gateway(this, 'AgentGateway', {
    name: 'tool-gateway',
    protocolType: 'MCP',
});
```

**IAM 权限**: Agent 执行路径需要 Bedrock **Invoke API** 权限（非 Converse API）：

```json
{
  "Action": [
    "bedrock:InvokeModel",
    "bedrock:InvokeModelWithResponseStream",
    "bedrock:ListInferenceProfiles"
  ],
  "Resource": [
    "arn:aws:bedrock:*:*:inference-profile/*",
    "arn:aws:bedrock:*:*:application-inference-profile/*",
    "arn:aws:bedrock:*:*:foundation-model/*"
  ]
}
```

**注意**: 这与现有 `BedrockLLMClient` 使用的 Converse API 权限不同，CDK SecurityStack 需同时包含两组权限。

### 8. 对现有代码的影响

| 模块 | 影响程度 | 说明 |
|------|:--------:|------|
| `execution` | **中** | 新增 `IAgentRuntime` + `ClaudeAgentAdapter`；`ExecutionService` 扩展支持新接口；`ILLMClient` 保留 |
| `tool_catalog` | **低** | 新增 `ToolQuerierImpl`；现有代码无修改 |
| `agents` | **低** | `AgentConfig` 新增 `runtime_type`；Alembic migration |
| `shared` | **低** | 新增 `IToolQuerier` + `ApprovedToolInfo` |
| `knowledge` | **无** | 继续使用 Bedrock KB（ADR-005） |
| `auth` | **无** | 无变更 |
| `infra` | **中** | 新增 AgentCore Runtime + Gateway CDK 资源 |

### 9. 降级路径

```
ClaudeAgentAdapter 失败
  → 重试 (指数退避)
  → 降级到 BedrockLLMClient (无工具调用的纯对话模式)
  → 返回错误
```

### 10. Docker 镜像构建

Agent 应用需要 Python + Node.js 18+ 双运行时（Claude Agent SDK 捆绑的 Claude Code CLI 依赖 Node.js）：

```dockerfile
# Dockerfile.agent
FROM python:3.12-slim AS base

# 安装 Node.js 18+ (Claude Code CLI 运行时依赖)
RUN apt-get update && apt-get install -y nodejs npm && rm -rf /var/lib/apt/lists/*

# 安装 Python 依赖
COPY pyproject.toml uv.lock ./
RUN pip install uv && uv sync
# claude-agent-sdk 安装时自动捆绑 Claude Code CLI，无需单独安装

COPY src/ ./src/

# Bedrock 认证: 通过 AWS 标准凭证链 (环境变量 / IAM Role / SSO)
# 不需要 ANTHROPIC_API_KEY
ENV CLAUDE_CODE_USE_BEDROCK=1
# AWS_REGION 由部署时注入 (ECS Task Definition / AgentCore Runtime 配置)

CMD ["python", "src/agent_entrypoint.py"]
```

**认证方式**: Agent 容器通过 ECS Task Role 或 AgentCore Runtime IAM Role 获取 AWS 凭证，无需硬编码密钥。环境变量 `CLAUDE_CODE_USE_BEDROCK=1` + `AWS_REGION` 由部署配置注入。

### 11. 后续 ADR

| ADR | 标题 | 时机 |
|-----|------|------|
| ADR-007 | AgentCore Gateway 集成策略 — tool_catalog 与 MCP 工具对接 | Phase 2 M6 |
| ADR-008 | 架构拆分 — Platform API 与 Agent Runtime 部署分离 | Phase 2 完成后评估 |
