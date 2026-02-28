# ADR-014: Agent 运行时 × MCP × Memory 技术架构

- **日期**: 2026-02-28
- **状态**: 已采纳
- **关联**: ADR-006 (Agent 框架选型), ADR-003 (AgentCore 基础设施), ADR-008 (Agent Teams)

## 背景

ADR-006 确定了 Claude Agent SDK 作为唯一 Agent 框架，但未深入定义 Agent 运行时的两种部署模式、MCP 工具注入机制和 Memory 集成方案的技术细节。经过 Dev 环境 E2E 调试（2026-02-27/28），这些细节的设计缺陷暴露为生产问题，需要正式记录和规范化。

### 需要解决的问题

| 问题 | 说明 |
|------|------|
| **两种运行时模式的架构差异** | `in_process` 和 `agentcore_runtime` 的执行链路、进程模型、容错策略完全不同 |
| **MCP 工具注入粒度** | 工具应按 Agent 绑定还是全平台注入 |
| **MCP Server 类型对 CLI 进程的影响** | SSE 远程 MCP vs SDK 进程内 MCP 的时序约束 |
| **Memory 集成方式** | AgentCore Memory 如何通过 MCP 桥接到 Agent SDK |

---

## 1. 双模式运行时架构

### 1.1 进程模型对比

```
┌─ in_process 模式 ─────────────────────────────────────────────────┐
│                                                                    │
│  ECS Task (单容器)                                                  │
│  ┌──────────────────────────────────────────────────────────────┐  │
│  │  Python FastAPI 进程 (PID 1)                                  │  │
│  │  ├── ExecutionService                                        │  │
│  │  ├── ClaudeAgentAdapter                                      │  │
│  │  │   └── claude_agent_sdk.query()                            │  │
│  │  │       └── fork CLI 子进程 ──────────────────┐             │  │
│  │  │                                              │             │  │
│  │  │  ┌───────────────────────────────────────────┤             │  │
│  │  │  │  Claude Code CLI (Node.js SEA)            │             │  │
│  │  │  │  ├── stdio pipe ⇄ Python SDK 进程         │             │  │
│  │  │  │  ├── Bedrock Invoke API (HTTPS)           │             │  │
│  │  │  │  └── MCP Server 连接                      │             │  │
│  │  │  └───────────────────────────────────────────┘             │  │
│  │  └── platform-tools MCP (进程内)                               │  │
│  └──────────────────────────────────────────────────────────────┘  │
└────────────────────────────────────────────────────────────────────┘

┌─ agentcore_runtime 模式 ──────────────────────────────────────────┐
│                                                                    │
│  ECS Task (单容器)              AgentCore Runtime (托管容器)        │
│  ┌─────────────────────┐       ┌──────────────────────────────┐   │
│  │  Python FastAPI 进程  │       │  Agent 容器 (ECR 镜像)        │   │
│  │  ├── ExecutionService │  ──►  │  ├── agent_entrypoint.py     │   │
│  │  ├── AgentCoreRuntime │ HTTP  │  ├── claude_agent_sdk.query()│   │
│  │  │   Adapter          │ API   │  │   └── CLI 子进程           │   │
│  │  │   (boto3 invoke)   │       │  └── Bedrock Invoke API      │   │
│  └─────────────────────┘       └──────────────────────────────┘   │
│                                                                    │
│  Python 进程不运行 CLI                                              │
│  Agent 运行在独立 AgentCore 托管容器中                                │
└────────────────────────────────────────────────────────────────────┘
```

### 1.2 模式选择矩阵

| 维度 | in_process | agentcore_runtime |
|------|-----------|-------------------|
| **执行位置** | ECS 容器内 (CLI 子进程) | AgentCore 托管容器 (独立) |
| **进程隔离** | 无 — CLI 与 API 共享资源 | 完全隔离 — 独立容器/内存/CPU |
| **MCP 支持** | SDK 进程内 MCP + 远程 SSE | Agent 容器内独立配置 |
| **启动延迟** | ~2s (CLI fork) | ~5-10s (容器冷启动) |
| **资源上限** | 受 ECS Task 内存/CPU 限制 | AgentCore 独立资源配额 |
| **适用场景** | 开发调试、轻量 Agent | 生产负载、长时间执行、Teams |
| **CDK Context** | `--context agentRuntimeMode=in_process` | 默认值 |

### 1.3 配置化切换

```typescript
// infra/bin/app.ts — 入口文件默认值 (实际生效)
const agentRuntimeMode = app.node.tryGetContext('agentRuntimeMode') ?? 'agentcore_runtime';

// infra/lib/stacks/compute-stack.ts — Props 默认值 (被入口覆盖)
AGENT_RUNTIME_MODE: props.agentRuntimeMode ?? 'in_process',
```

> **注意**: `bin/app.ts` 的默认值 (`agentcore_runtime`) 覆盖 `compute-stack.ts` 的 Props 默认值 (`in_process`)。实际生效的是入口文件的默认值。

```python
# backend/src/modules/execution/api/dependencies.py
@lru_cache
def get_agent_runtime() -> IAgentRuntime:
    settings = get_settings()
    if settings.AGENT_RUNTIME_MODE == "agentcore_runtime" and settings.AGENTCORE_RUNTIME_ARN:
        return AgentCoreRuntimeAdapter(client=..., runtime_arn=...)
    return ClaudeAgentAdapter()  # in_process 降级
```

---

## 2. MCP 工具集成架构

### 2.1 三种工具类型的 MCP 映射

Agent SDK 要求所有工具通过 MCP 协议暴露。平台 tool_catalog 中的三种工具类型分别映射为不同的 MCP Server：

```
tool_catalog 工具类型          MCP Server 类型              传输协议
─────────────────────────────────────────────────────────────────────
mcp_server                 →  gateway (远程)             →  SSE over HTTPS
  └─ 连接到 AgentCore Gateway 统一入口
  └─ Gateway 背后可挂载多个 MCP Target

api                        →  platform-tools (进程内)    →  stdio pipe
  └─ SDK create_sdk_mcp_server() 创建进程内 MCP
  └─ handler: httpx.AsyncClient 调用远程 REST API

function                   →  platform-tools (进程内)    →  stdio pipe
  └─ SDK create_sdk_mcp_server() 同上
  └─ handler: 本地函数执行
```

### 2.2 MCP Server 配置构建流程

```python
# ClaudeAgentAdapter._build_mcp_config()
def _build_mcp_config(self, request: AgentRequest) -> dict[str, Any]:
    mcp_servers = {}

    # 1. 远程 MCP: mcp_server 类型工具 → gateway SSE
    has_mcp_tools = any(t.tool_type == "mcp_server" for t in request.tools)
    if has_mcp_tools and request.gateway_url:
        mcp_servers["gateway"] = {"type": "sse", "url": request.gateway_url}

    # 2. 进程内 MCP: api/function 类型工具 → SDK MCP Server
    non_mcp_tools = [t for t in request.tools if t.tool_type in ("api", "function")]
    if non_mcp_tools:
        mcp_servers["platform-tools"] = self._build_platform_tools_config(non_mcp_tools)

    # 3. Memory MCP (可选)
    if self._memory_id:
        mcp_servers["memory"] = build_memory_mcp_server_config(...)

    return mcp_servers
```

最终传递给 CLI 的 `ClaudeAgentOptions.mcp_servers` 结构:

```json
{
  "gateway": {"type": "sse", "url": "https://...gateway.bedrock-agentcore.../mcp"},
  "platform-tools": "<McpSdkServerConfig object>",
  "memory": {"type": "sse", "url": "https://...memory-endpoint..."}
}
```

### 2.3 CLI 进程与 MCP 的交互时序

```
SDK Python 进程                    CLI Node.js 子进程
     │                                   │
     ├── fork CLI ──────────────────────►│ 启动
     │                                   │
     │   ◄── stdout ────────────────────│ handshake
     │                                   │
     │                                   ├── 初始化 MCP 连接
     │                                   │   ├── gateway: HTTPS 连接 AgentCore
     │                                   │   └── platform-tools: stdio 控制请求
     │                                   │
     │   ◄── control_request ───────────│ "list tools for platform-tools"
     │                                   │
     ├── _handle_control_request         │
     ├── 调用进程内 MCP handler           │
     ├── transport.write(response) ────►│ 收到 tool list
     │                                   │
     │                                   ├── Bedrock Invoke API (LLM 调用)
     │                                   │
     │   ◄── message (assistant) ───────│ 返回响应
     │                                   │
     ├── extract_content()               │
     ├── extract_usage()                 │
     │                                   │
     │   ◄── done ──────────────────────│ 退出
```

### 2.4 已知约束: CLI 启动时序竞态

**问题**: 当 `mcp_servers` 包含远程 SSE 类型 (gateway) 时，CLI 进程启动后立即尝试建立 SSE 连接。如果连接失败（网络/认证），CLI 进程崩溃，导致 `ProcessTransport is not ready for writing`。

**触发条件**:
1. `request.tools` 中存在 `tool_type == "mcp_server"` 的工具
2. `request.gateway_url` 非空
3. Gateway SSE 端点不可达或认证失败

**影响链路**:
```
mcp_server 工具存在 → gateway SSE MCP 注入 → CLI 连接 Gateway
→ 连接失败 → CLI exit → stdio pipe 断裂 → Read task cancelled
→ SDK write response → ProcessTransport not ready → CLIConnectionError
→ 重试 3 次 → 最终 AGENT_SDK_ERROR
```

**规避方案**:
- 不注入 `mcp_server` 类型工具时无此问题（纯 `api`/`function` 工具走进程内 MCP，无远程连接）
- 确保 Gateway SSE 端点可达且认证正确

### 2.5 工具注入粒度规范

**问题** (待修复): `execution_service._get_agent_tools()` 调用 `list_approved_tools()` 返回全平台所有已审批工具，而非当前 Agent 绑定的工具。

**正确设计**:

```
_get_agent_tools(agent_id)
  └── tool_querier.list_tools_for_agent(agent_id)  # 按 Agent 绑定关系过滤
      └── 只返回该 Agent 配置的工具
```

**理由**:
- Agent A 只绑定了 2 个 api 工具 → 只注入 2 个 → CLI 启动快速稳定
- 全平台 39 个工具全部注入 → 37 个 api handler + 2 个 mcp_server gateway → 不必要的负担和竞态风险

---

## 3. Memory 集成架构

### 3.1 AgentCore Memory × MCP 桥接

AgentCore Memory 没有原生 Claude Agent SDK 集成。通过自定义 MCP Server 桥接:

```
Claude Agent SDK
  └── mcp_servers: {"memory": <MCP 配置>}
      └── Memory MCP Server (SDK 进程内)
          └── boto3 → AgentCore Memory API
              ├── save_memory(content, metadata)
              └── recall_memory(query, top_k)
```

### 3.2 Memory MCP 配置构建

```python
# memory_mcp_server.py
@dataclass
class MemoryMcpConfig:
    memory_id: str     # AgentCore Memory 资源 ID
    region: str = "us-east-1"

def build_memory_mcp_server_config(config: MemoryMcpConfig) -> McpSdkServerConfig | None:
    if not config.memory_id:
        return None
    return create_sdk_mcp_server(
        name="memory",
        tools=[
            SdkMcpTool(name="save_memory", ...),
            SdkMcpTool(name="recall_memory", ...),
        ],
    )
```

### 3.3 Memory 注入条件

| 条件 | 说明 |
|------|------|
| `agent_info.enable_memory == True` | Agent 配置启用 Memory |
| `settings.AGENTCORE_MEMORY_ID != ""` | 环境配置了 Memory 资源 ID |
| 两者同时满足 | 才注入 Memory MCP Server |

> **注意**: 当前 `ClaudeAgentAdapter` 使用 `self._memory_id`（构造函数参数），而非 `request.memory_id`。Memory 配置在 adapter 层面是全局的，不按请求动态切换。

---

## 4. in_process 模式运行前置条件

| 条件 | 说明 | 验证方式 |
|------|------|---------|
| `HOME` 环境变量 | CLI 需写入 `~/.claude/` | `ENV HOME=/home/appuser` |
| `.claude` 目录可写 | CLI 启动时创建配置文件 | `mkdir -p $HOME/.claude && chown appuser` |
| `libstdc++6` | Node.js SEA 二进制运行时依赖 | `apt-get install libstdc++6` |
| `CLAUDE_CODE_USE_BEDROCK=1` | 启用 Bedrock 认证路径 | Dockerfile ENV |
| AWS IAM 凭证 | ECS Task Role → Bedrock Invoke API | Task Definition IAM Role |
| MCP Server 数量可控 | 避免大量远程 MCP 触发时序竞态 | 工具按 Agent 绑定过滤 |

---

## 5. agentcore_runtime 模式架构细节

### 5.1 调用链路

```python
# AgentCoreRuntimeAdapter.execute()
response = self._client.invoke_agent_runtime(
    runtimeIdentifier=self._runtime_arn,
    payload=json.dumps({"prompt": request.prompt, ...}).encode(),
    sessionId=session_id,
)
```

### 5.2 ECR 镜像要求

AgentCore Runtime 从 ECR 拉取 Agent 容器镜像:

```typescript
// agentcore-stack.ts
agentRuntimeArtifact: AgentRuntimeArtifact.fromEcrRepository(this.ecrRepository, 'latest')
```

| 要求 | 说明 |
|------|------|
| ECR `latest` 标签必须存在 | Runtime 按标签拉取，无标签则失败 |
| 镜像架构与 Runtime 匹配 | `linux/arm64` (ARM64 实例) |
| 镜像包含 `agent_entrypoint.py` | Runtime 启动入口 |
| 镜像包含 claude-agent-sdk | Agent 运行时依赖 |

### 5.3 响应解析

AgentCore Runtime 返回的响应通过 HTTP API（非 stdio pipe）。`AgentCoreRuntimeAdapter` 需要解析 invoke 响应体中的 Agent 输出内容。

> **已知问题**: 当前响应解析返回空内容，需要对齐 `agent_entrypoint.py` 的输出格式与 adapter 的解析逻辑。

---

## 6. 错误处理与降级策略

### 6.1 in_process 错误处理

```
CLINotFoundError        → 不可重试, 立即 AGENT_SDK_ERROR
CLIConnectionError      → 重试 3 次 (指数退避 0.5s/1s/2s)
CLIJSONDecodeError      → 重试 3 次
MessageParseError       → 重试 3 次
ProcessError (exit=1)   → 有内容则忽略, 无内容则 AGENT_SDK_ERROR
ProcessError (stderr)   → 记录 stderr[:500] 辅助诊断
```

### 6.2 agentcore_runtime 错误处理

```
invoke 超时 (read_timeout=600s) → AGENT_SDK_ERROR
invoke 4xx/5xx                  → AGENT_SDK_ERROR
Runtime 无 latest 镜像           → invoke 失败
```

### 6.3 全局降级路径

```
IAgentRuntime (in_process 或 agentcore_runtime) 失败
  → ExecutionService 根据 runtime_type 判断
  → runtime_type == "basic" → BedrockLLMClient (Converse API, 无工具)
  → runtime_type == "agent" → 直接返回 AGENT_SDK_ERROR
```

---

## 7. OTel 可观测性集成

### 7.1 Span 导出策略

| 环境 | Exporter | 理由 |
|------|----------|------|
| Dev (无 OTLP) | `_NoOpSpanExporter` | 避免 Console JSON 输出淹没 structlog |
| Dev (有 OTLP) | `OTLPSpanExporter` | 导出到本地 Jaeger/Tempo |
| Prod | `OTLPSpanExporter` | 导出到 ADOT Collector → CloudWatch |

> **历史教训**: `ConsoleSpanExporter` 会将每个 Span 的完整 JSON 输出到 stdout，与 structlog 的业务日志混杂，导致 CloudWatch 中业务日志不可见。Dev 环境必须使用 `_NoOpSpanExporter`。

### 7.2 关键 structlog 事件

| 事件 | 日志键 | 级别 |
|------|--------|------|
| CLI 启动 | `Using bundled Claude Code CLI` | info (SDK 内部) |
| CLI 重试 | `cli_connection_retry` | info |
| CLI stderr | `claude_agent_sdk_cli_stderr` | warning |
| CLI 崩溃 (有内容) | `claude_agent_sdk_process_exit1_ignored` | warning |
| CLI 崩溃 (无内容) | `claude_agent_sdk_failed_no_content` | error |
| 重试用尽 | `Claude Agent SDK 调用失败` | exception |
| Teams 完成 | `团队执行完成` | info |

---

## 8. E2E 验证结果 (2026-02-28)

| 模式 | 对话 | Teams | 根因 |
|------|------|-------|------|
| in_process | HTTP 400 | 5s 完成, 结果正确 | 对话注入 39 个全平台工具 → gateway SSE 连接失败 |
| agentcore_runtime | HTTP 201, 内容为空 | 15s 完成, 内容为空 | 响应解析未提取 content |

### 修复效果

| 修复项 | 效果 |
|-------|------|
| ECR `latest` 标签推送 | agentcore_runtime Teams: FAILED 95s → completed 15s |
| Dockerfile `HOME=/home/appuser` | in_process Teams: PENDING 卡死 → completed 5s |
| `_NoOpSpanExporter` 替换 Console | CloudWatch 日志可读，诊断信息清晰 |
| ProcessError stderr 日志增强 | 错误链路完整可追溯 |

### 待修复

| 问题 | 影响 | 修复方向 |
|------|------|---------|
| `_get_agent_tools()` 返回全平台工具 | in_process 对话失败 | 改为按 Agent 绑定过滤 |
| `AgentCoreRuntimeAdapter` 响应解析空内容 | agentcore_runtime 无回复 | 对齐 entrypoint 输出格式 |
