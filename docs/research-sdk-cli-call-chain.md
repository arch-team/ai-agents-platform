# Claude Agent SDK -> Claude Code CLI 调用链深度技术分析

> 调研日期: 2026-02-12
> SDK 版本: claude-agent-sdk 0.1.34 (bundled CLI 2.1.38)
> 置信度: 高 (基于 SDK 源码逆向分析 + PyPI 元数据验证 + 项目实际代码审查)

---

## 目录

1. [SDK 如何查找和启动 CLI](#1-sdk-如何查找和启动-cli)
2. [CLI 运行环境需求](#2-cli-运行环境需求)
3. [ECS Fargate 兼容性分析](#3-ecs-fargate-兼容性分析)
4. [项目适配器实现分析](#4-项目适配器实现分析)
5. [替代方案评估](#5-替代方案评估)
6. [结论与建议](#6-结论与建议)

---

## 1. SDK 如何查找和启动 CLI

### 1.1 整体架构

调用链路:

```
Python 用户代码
  -> claude_agent_sdk.query() / ClaudeSDKClient
    -> InternalClient.process_query()
      -> SubprocessCLITransport (创建)
        -> _find_cli() (查找 CLI 二进制)
        -> _build_command() (构建命令行参数)
        -> connect() (spawn 子进程)
      -> Query (控制协议层)
        -> initialize() (发送初始化握手)
        -> stream_input() / receive_messages() (双向 JSON 流通信)
```

核心源文件: `.venv/lib/python3.13/site-packages/claude_agent_sdk/_internal/transport/subprocess_cli.py`

### 1.2 CLI 查找逻辑 (`_find_cli()`)

SDK 通过以下优先级查找 Claude Code CLI 二进制:

```python
def _find_cli(self) -> str:
    # 优先级 1: bundled CLI (SDK 自带的二进制)
    bundled_cli = self._find_bundled_cli()
    if bundled_cli:
        return bundled_cli

    # 优先级 2: PATH 环境变量中的 claude 命令
    if cli := shutil.which("claude"):
        return cli

    # 优先级 3: 已知安装位置遍历
    locations = [
        Path.home() / ".npm-global/bin/claude",
        Path("/usr/local/bin/claude"),
        Path.home() / ".local/bin/claude",
        Path.home() / "node_modules/.bin/claude",
        Path.home() / ".yarn/bin/claude",
        Path.home() / ".claude/local/claude",
    ]
    for path in locations:
        if path.exists() and path.is_file():
            return str(path)

    raise CLINotFoundError(...)
```

**`_find_bundled_cli()` 的完整逻辑:**

```python
def _find_bundled_cli(self) -> str | None:
    cli_name = "claude.exe" if platform.system() == "Windows" else "claude"
    bundled_path = Path(__file__).parent.parent.parent / "_bundled" / cli_name
    # 即: claude_agent_sdk/_bundled/claude
    if bundled_path.exists() and bundled_path.is_file():
        return str(bundled_path)
    return None
```

**用户覆盖**: 通过 `ClaudeAgentOptions(cli_path='/path/to/claude')` 可跳过所有查找逻辑。

### 1.3 命令构建 (`_build_command()`)

SDK 构建的完整 CLI 命令模板:

```bash
/path/to/claude \
  --output-format stream-json \
  --verbose \
  --system-prompt "..." \
  --tools "tool1,tool2" \
  --allowedTools "mcp__gateway__tool1,mcp__gateway__tool2" \
  --max-turns 200 \
  --model "claude-sonnet-4-20250514" \
  --permission-mode bypassPermissions \
  --setting-sources "" \
  --mcp-config '{"mcpServers": {...}}' \
  --input-format stream-json
```

关键参数说明:

| 参数 | 说明 |
|------|------|
| `--output-format stream-json` | 输出格式为流式 JSON |
| `--input-format stream-json` | 启用 stdin 流式输入 (双向通信) |
| `--verbose` | 开启详细日志 |
| `--permission-mode` | 权限模式 (bypassPermissions 跳过所有工具权限检查) |
| `--setting-sources ""` | 空字符串 = 不加载任何用户/项目设置文件 |
| `--mcp-config` | MCP 服务器配置 (JSON 字符串) |
| `--tools` | 工具集配置 |
| `--allowedTools` | 工具白名单 |

### 1.4 子进程启动 (`connect()`)

```python
async def connect(self) -> None:
    # 版本检查 (可通过 CLAUDE_AGENT_SDK_SKIP_VERSION_CHECK 跳过)
    await self._check_claude_version()

    # 构建命令
    cmd = self._build_command()

    # 合并环境变量
    process_env = {
        **os.environ,                           # 系统环境变量
        **self._options.env,                     # 用户自定义环境变量
        "CLAUDE_CODE_ENTRYPOINT": "sdk-py",      # SDK 标识
        "CLAUDE_AGENT_SDK_VERSION": __version__,  # SDK 版本号
    }

    # 启动子进程
    self._process = await anyio.open_process(
        cmd,
        stdin=PIPE,   # 通过 stdin 发送 JSON 消息
        stdout=PIPE,  # 通过 stdout 接收 JSON 消息
        stderr=PIPE,  # stderr 用于调试日志
        cwd=self._cwd,
        env=process_env,
        user=self._options.user,  # 可选: 指定运行用户
    )
```

### 1.5 通信协议

SDK 和 CLI 之间通过 **stdin/stdout 上的换行分隔 JSON (NDJSON)** 进行双向通信:

**SDK -> CLI (stdin):**

```json
// 控制请求 (初始化)
{"type": "control_request", "request_id": "req_1_abc123", "request": {"subtype": "initialize", "hooks": null, "agents": {...}}}

// 用户消息
{"type": "user", "session_id": "", "message": {"role": "user", "content": "Hello"}, "parent_tool_use_id": null}

// 控制响应 (权限决策)
{"type": "control_response", "response": {"subtype": "success", "request_id": "req_2", "response": {"behavior": "allow"}}}
```

**CLI -> SDK (stdout):**

```json
// 控制响应 (初始化成功)
{"type": "control_response", "response": {"subtype": "success", "request_id": "req_1_abc123", "response": {...}}}

// 助手消息
{"type": "assistant", "message": {"role": "assistant", "content": [{"type": "text", "text": "Hello!"}]}, ...}

// 工具使用
{"type": "assistant", "message": {"role": "assistant", "content": [{"type": "tool_use", "id": "toolu_123", "name": "Read", "input": {...}}]}}

// 结果消息
{"type": "result", "subtype": "success", "duration_ms": 5000, "session_id": "sess_xxx", "total_cost_usd": 0.05, ...}

// 控制请求 (权限询问 / MCP 消息 / Hook 回调)
{"type": "control_request", "request_id": "req_2", "request": {"subtype": "can_use_tool", "tool_name": "Bash", "input": {...}}}
```

**缓冲区**: 默认最大 1MB (`_DEFAULT_MAX_BUFFER_SIZE = 1024 * 1024`)，超出抛 `CLIJSONDecodeError`。

### 1.6 初始化握手 (Initialize)

连接建立后，SDK 发送 `initialize` 控制请求:

```json
{
  "type": "control_request",
  "request_id": "req_1_xxx",
  "request": {
    "subtype": "initialize",
    "hooks": null,
    "agents": {
      "researcher": {
        "description": "Research agent",
        "prompt": "You are a research specialist...",
        "tools": ["Read", "Glob", "Grep"],
        "model": "haiku"
      }
    }
  }
}
```

**超时**: 默认 60 秒 (`initialize_timeout`)，可通过 `CLAUDE_CODE_STREAM_CLOSE_TIMEOUT` 环境变量调整。

---

## 2. CLI 运行环境需求

### 2.1 Bundled CLI 的本质

**关键发现: Bundled CLI 是一个平台特定的原生可执行文件 (不依赖 Node.js)。**

验证数据:

| 平台 | 文件类型 | 大小 (wheel) | 解压后大小 |
|------|---------|-------------|-----------|
| macOS arm64 | Mach-O 64-bit executable arm64 | ~52 MB | ~177 MB |
| Linux x86_64 | ELF 64-bit executable | ~67 MB | ~200 MB (估算) |
| Linux aarch64 | ELF 64-bit executable | ~66 MB | ~200 MB (估算) |
| Windows amd64 | PE32+ executable | ~69 MB | ~200 MB (估算) |

```bash
# 本地验证 (macOS arm64)
$ file .venv/.../claude_agent_sdk/_bundled/claude
Mach-O 64-bit executable arm64

$ du -h .venv/.../claude_agent_sdk/_bundled/claude
177M

$ .venv/.../claude_agent_sdk/_bundled/claude -v
2.1.38 (Claude Code)
```

**技术推断**: Claude Code CLI 原本是 Node.js 应用 (`@anthropic-ai/claude-code` npm 包)，通过 Node.js SEA (Single Executable Application) 技术编译为原生二进制。这是一个包含 Node.js 运行时 + JavaScript 代码的自包含可执行文件。因此 **bundled CLI 不需要系统安装 Node.js**。

### 2.2 PyPI 平台特定 Wheel 分发

PyPI 上的 `claude-agent-sdk` 从 0.1.8+ 版本开始，使用**平台特定 wheel** 分发:

```
claude_agent_sdk-0.1.34-py3-none-macosx_11_0_arm64.whl       (52 MB)
claude_agent_sdk-0.1.34-py3-none-manylinux_2_17_aarch64.whl  (66 MB)
claude_agent_sdk-0.1.34-py3-none-manylinux_2_17_x86_64.whl   (67 MB)
claude_agent_sdk-0.1.34-py3-none-win_amd64.whl               (69 MB)
claude_agent_sdk-0.1.34.tar.gz                                (60 KB - 不含二进制)
```

**对 ECS Fargate 的含义**: `pip install claude-agent-sdk` 在 Linux x86_64 容器中会自动下载包含 Linux ELF 二进制的 wheel，**无需额外安装 Node.js 或 npm**。

### 2.3 环境变量需求

| 环境变量 | 必需 | 说明 |
|---------|:----:|------|
| `CLAUDE_CODE_USE_BEDROCK` | 是 | 设为 `1` 启用 Bedrock 认证路径 |
| `AWS_REGION` | 是 | AWS 区域 (如 `us-east-1`) |
| `AWS_ACCESS_KEY_ID` | 条件 | 无 IAM Role 时需要 |
| `AWS_SECRET_ACCESS_KEY` | 条件 | 无 IAM Role 时需要 |
| `AWS_SESSION_TOKEN` | 条件 | 使用临时凭证时需要 |
| `CLAUDE_CODE_ENTRYPOINT` | 自动 | SDK 自动设置为 `sdk-py` |
| `CLAUDE_AGENT_SDK_VERSION` | 自动 | SDK 自动设置版本号 |
| `CLAUDE_AGENT_SDK_SKIP_VERSION_CHECK` | 可选 | 设为任意值跳过版本检查 |
| `CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS` | 可选 | 设为 `1` 启用 Agent Teams |

### 2.4 文件系统需求

CLI 运行时需要写入以下位置:

| 目录 | 用途 | 是否必需 |
|------|------|:--------:|
| `~/.claude/` | 配置目录 (settings, statsig 缓存) | 是 |
| `~/.claude/.claude/` | 内部配置 (settings.local.json) | 是 |
| `~/.claude/statsig/` | 特性开关缓存 | 是 |
| `~/.claude/teams/` | Agent Teams 文件 (仅启用 Teams 时) | 条件 |
| `~/.claude/tasks/` | Agent Teams 任务 (仅启用 Teams 时) | 条件 |
| 工作目录 (cwd) | Agent 的工作区域 | 视场景 |

**重要**: 在 ECS Fargate 中，`~` 取决于运行用户。对于 `appuser` (uid 1000)，`HOME` 通常为 `/home/appuser`。

### 2.5 网络访问需求

CLI 需要访问以下 AWS 端点:

| 端点 | 用途 |
|------|------|
| `bedrock-runtime.{region}.amazonaws.com` | Bedrock Invoke API (LLM 调用) |
| `bedrock.{region}.amazonaws.com` | Bedrock 控制面 (ListInferenceProfiles 等) |
| `statsig.anthropic.com` (推测) | 特性开关 (可能可离线) |

### 2.6 版本要求

```python
MINIMUM_CLAUDE_CODE_VERSION = "2.0.0"  # SDK 要求的最低 CLI 版本
```

SDK 启动时会自动检查 CLI 版本 (`claude -v`)，版本低于 2.0.0 会打印警告 (不会阻止运行)。

---

## 3. ECS Fargate 兼容性分析

### 3.1 核心发现: Bundled CLI 消除了 Node.js 依赖

**这是本次调研最重要的发现。**

之前的 `Dockerfile` 和 `Dockerfile.agent` 都安装了 Node.js，原因是认为 Claude Code CLI 依赖 Node.js 运行时。但源码分析表明:

1. **bundled CLI 是自包含的原生 ELF 二进制** (通过 Node.js SEA 编译)
2. `pip install claude-agent-sdk` 在 Linux x86_64 上会安装包含 ELF 二进制的 wheel
3. SDK 优先使用 bundled CLI (`_find_bundled_cli()` 是第一优先级)
4. **不需要在容器中安装 Node.js 或 npm**

### 3.2 Dockerfile 优化建议

**当前 Dockerfile (主服务)** 中不必要的 Node.js 安装:

```dockerfile
# 当前: 安装了 Node.js 22 + npm + @anthropic-ai/claude-code (不必要)
RUN apt-get update && \
    apt-get install -y --no-install-recommends ca-certificates curl gnupg && \
    curl -fsSL https://deb.nodesource.com/setup_22.x | bash - && \
    apt-get install -y --no-install-recommends nodejs && \
    npm install -g @anthropic-ai/claude-code && \
    ...
```

**优化后: 去掉 Node.js，依赖 SDK bundled CLI**

```dockerfile
# 优化: 不需要 Node.js，SDK bundled CLI 是自包含二进制
# 只需确保 claude-agent-sdk 在依赖列表中
# pyproject.toml: "claude-agent-sdk>=0.1.8" (0.1.8+ 包含 bundled CLI)
```

**预计节省**: 镜像大小减少约 150-200 MB (Node.js 运行时 + npm + @anthropic-ai/claude-code)。

### 3.3 资源需求评估

| 维度 | 最低要求 | 推荐配置 | 说明 |
|------|---------|---------|------|
| **CPU** | 256 (0.25 vCPU) | 512 (0.5 vCPU) | CLI 启动和 JSON 序列化需要 CPU |
| **内存** | 512 MiB | 1024 MiB | CLI 二进制本身 ~200MB，运行时内存需求额外 ~300-500MB |
| **磁盘** | 无 EFS 需求 | 无 EFS 需求 | `/home/appuser/.claude/` 使用容器临时存储 |
| **网络** | VPC + NAT Gateway | VPC + NAT Gateway | 需要出站访问 Bedrock API |

**内存分析**:

- CLI 二进制加载: ~200 MB (Node.js SEA 运行时)
- Python 进程: ~100 MB
- CLI 运行时堆: ~200-500 MB (取决于对话长度和上下文大小)
- **建议**: 512 MiB 仅够最简单场景，**推荐 1024 MiB**

**已知问题**: Claude Code CLI 存在内存泄漏问题 (GitHub Issues #17650, #19223)。长时间运行的 Agent 需要监控内存使用。

### 3.4 非 root 用户兼容性

**结论: 完全兼容。**

1. bundled CLI 二进制嵌入在 Python 包中 (`site-packages/claude_agent_sdk/_bundled/claude`)，不需要全局安装权限
2. CLI 写入的目录 (`~/.claude/`) 在 appuser 的 HOME 下，Dockerfile 中 `useradd --create-home appuser` 已创建
3. SDK 支持 `ClaudeAgentOptions(user=...)` 参数指定运行用户
4. 文件权限: bundled CLI 在 wheel 安装时会保留可执行权限

### 3.5 Agent Teams 在 Fargate 中的限制

| 功能 | Fargate 兼容性 | 说明 |
|------|:-------------:|------|
| 单 Agent (query/ClaudeSDKClient) | 完全兼容 | 标准子进程模式 |
| 子 Agent (AgentDefinition) | 完全兼容 | 通过 initialize 请求传递给 CLI |
| Agent Teams (in-process 模式) | 基本兼容 | CLI 内部 spawn 子进程，需要足够内存 |
| Agent Teams (tmux 模式) | 不兼容 | 容器中无 tmux |
| 文件系统 IPC | 兼容 | `~/.claude/teams/` 写入容器临时存储 |
| 多 Teammate 并行 | 有限兼容 | 受 CPU/内存限制，建议不超过 2-3 个 |

### 3.6 Fargate Task Definition 建议

```json
{
  "family": "agent-runtime",
  "cpu": "512",
  "memory": "1024",
  "networkMode": "awsvpc",
  "containerDefinitions": [{
    "name": "agent",
    "image": "xxx.dkr.ecr.region.amazonaws.com/agent:latest",
    "essential": true,
    "environment": [
      {"name": "CLAUDE_CODE_USE_BEDROCK", "value": "1"},
      {"name": "AWS_REGION", "value": "us-east-1"},
      {"name": "HOME", "value": "/home/appuser"}
    ],
    "user": "1000:1000",
    "linuxParameters": {
      "initProcessEnabled": true
    }
  }],
  "taskRoleArn": "arn:aws:iam::xxx:role/AgentTaskRole"
}
```

**IAM 权限** (Task Role):

```json
{
  "Effect": "Allow",
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

---

## 4. 项目适配器实现分析

### 4.1 ClaudeAgentAdapter

路径: `src/modules/execution/infrastructure/external/claude_agent_adapter.py`

当前实现的调用链:

```
ClaudeAgentAdapter.execute(request)
  -> _build_options(request) -> ClaudeAgentOptions
  -> claude_agent_sdk.query(prompt, options)
    -> SubprocessCLITransport (SDK 内部)
      -> spawn CLI 子进程
      -> stdin/stdout JSON 流通信
    -> 逐条 yield Message
  -> extract_content(message) + extract_usage(message)
  -> 组装 AgentResponseChunk
```

**当前实现的优点:**

1. 符合 SDK-First 原则，薄封装层 (~120 行)
2. 通过 `IAgentRuntime` 接口抽象，支持替换
3. 支持同步和流式两种执行模式
4. MCP 配置构建逻辑清晰
5. Agent Teams 支持已内置 (`enable_teams` 参数)

**需要注意的问题:**

1. `_build_platform_tools_config()` 使用 `stdio` 类型占位 (TODO 标记)，需替换为 `create_sdk_mcp_server`
2. `extract_content()` 和 `extract_usage()` 兼容 dict/object 两种格式，SDK 0.1.x 已统一为对象格式
3. 未利用 `ClaudeAgentOptions(cli_path=...)` 显式指定 CLI 路径

### 4.2 sdk_message_utils.py

路径: `src/modules/execution/infrastructure/external/sdk_message_utils.py`

消息解析工具模块，同时支持 dict 和 object 属性格式。在 SDK 0.1.x 中，消息已统一为 dataclass 对象:

- `AssistantMessage`: 包含 `content: list[ContentBlock]`
- `ResultMessage`: 包含 `usage`, `total_cost_usd`, `duration_ms`
- `TextBlock`: 包含 `text: str`
- `ToolUseBlock`: 包含 `id`, `name`, `input`

建议: 后续可简化为仅处理对象格式。

### 4.3 Dockerfile 现状

当前有两个 Dockerfile:

| 文件 | 用途 | Node.js | 问题 |
|------|------|:-------:|------|
| `Dockerfile` | 主服务 (API + Agent) | 安装 Node.js 22 + npm + claude-code | 不必要 |
| `Dockerfile.agent` | Agent 专用 | 安装 Node.js 20 (无 npm 全局安装) | 不必要 |

**Dockerfile 中的注释 `"SDK bundled CLI 是 macOS arm64 二进制，Linux amd64 需要通过 npm 安装"` 是错误的。** PyPI 上存在 `manylinux_2_17_x86_64` 和 `manylinux_2_17_aarch64` wheel，会自动安装对应平台的 bundled CLI。

---

## 5. 替代方案评估

### 5.1 方案对比矩阵

| 方案 | CLI 依赖 | Agent Loop | MCP 支持 | Agent Teams | 部署复杂度 | 成熟度 |
|------|:--------:|:----------:|:--------:|:-----------:|:----------:|:------:|
| A: SDK + Bundled CLI | 自带 | 内置 | 完整 | 支持 | 低 | 正式 |
| B: 自定义 Transport | 自实现 | 需自建 | 需自建 | 不支持 | 极高 | 实验 |
| C: Bedrock Converse API | 无 | 需自建 | 无 | 不支持 | 中 | 正式 |
| D: Strands Agents SDK | 无 | 内置 | 部分 | 不支持 | 低 | 正式 |

### 5.2 方案 A: SDK + Bundled CLI (推荐 -- 当前方案)

**可行性: 完全可行，是最优方案。**

关键发现:
- bundled CLI 是自包含原生二进制，不依赖 Node.js
- PyPI 提供 Linux x86_64 和 aarch64 的平台特定 wheel
- ECS Fargate 完全兼容 (需适当的内存配置)
- Docker 镜像可大幅精简 (去掉 Node.js 层)

### 5.3 方案 B: 自定义 Transport

SDK 的 `Transport` 是一个抽象类，支持自定义实现:

```python
class Transport(ABC):
    """Abstract transport for Claude communication.
    WARNING: This internal API is exposed for custom transport implementations
    (e.g., remote Claude Code connections). The Claude Code team may change or
    remove this abstract class in any future release."""

    async def connect(self) -> None: ...
    async def write(self, data: str) -> None: ...
    def read_messages(self) -> AsyncIterator[dict[str, Any]]: ...
    async def close(self) -> None: ...
    def is_ready(self) -> bool: ...
    async def end_input(self) -> None: ...
```

`query()` 和 `ClaudeSDKClient` 都接受 `transport` 参数:

```python
async for msg in query(prompt="...", transport=my_custom_transport):
    ...
```

**理论上可以实现不依赖 CLI 的 Transport，但实际不可行:**

1. `Transport` 只是底层 I/O 层，上层的 `Query` 类实现了完整的 **Control Protocol** (初始化握手、权限回调、Hook 回调、MCP 路由等)
2. Control Protocol 是 Claude Code CLI 的私有协议，不是标准 API
3. 如果不运行 CLI，就没有接收 Control Protocol 消息的对端
4. 自定义 Transport 的实际用途是"远程 Claude Code 连接" (如 SSH 到远程机器运行 CLI)
5. **不可能在不运行 CLI 的情况下仅通过 Transport 实现 Agent Loop**

### 5.4 方案 C: Bedrock Converse API 手动构建 Agent Loop

完全绕过 Claude Agent SDK，使用 boto3 `bedrock-runtime` 的 `converse()` / `converse_stream()` API 自建 Agent Loop:

```python
# 伪代码: 手动 Agent Loop
while True:
    response = bedrock.converse(
        modelId="anthropic.claude-sonnet-4-20250514-v1:0",
        messages=messages,
        toolConfig={"tools": mcp_tool_definitions},
    )
    if response["stopReason"] == "tool_use":
        tool_results = await execute_tools(response["output"])
        messages.append(tool_results)
        continue
    elif response["stopReason"] == "end_turn":
        break
```

**评估:**

| 维度 | 可行性 | 说明 |
|------|:------:|------|
| 基本对话 | 可行 | Converse API 原生支持 |
| Tool Use 循环 | 可行但复杂 | 需自行实现 tool_use -> execute -> tool_result 循环 |
| MCP 集成 | 不可行 | Converse API 不支持 MCP，需自行实现 MCP 客户端 |
| 内置工具 (Read/Write/Bash 等) | 不可行 | 这些是 Claude Code CLI 的内置工具，Converse API 不提供 |
| Agent Teams | 不可行 | Agent Teams 是 CLI 功能 |
| 会话管理 | 需自建 | Converse API 无内置会话管理 |
| 结构化输出 | 可行 | Converse API 支持 JSON mode |
| Hooks | 不可行 | Hooks 是 CLI 功能 |

**结论**: 可作为降级路径 (项目中已有 `BedrockLLMClient` 实现)，但无法替代完整的 Agent SDK 能力。

### 5.5 方案 D: Strands Agents SDK (AWS 原生)

ADR-006 已评估并排除此方案，理由:
- 与项目 "Claude Agent SDK + Claude Code CLI" 愿景不一致
- 缺少 Claude Code 级别的内置工具集
- 双框架维护成本

### 5.6 Agent Teams 是否只能通过 CLI 实现？

**是的。** Agent Teams 的核心依赖:

1. **文件系统 IPC**: teams/tasks/inboxes 目录结构，基于文件锁的并发控制
2. **CLI 内部的 Teammate spawn**: CLI 负责创建新的 Claude Code 实例
3. **CLI 内部的消息路由**: 轮询收件箱、投递消息
4. **SDK 侧**: 只是通过 `env={"CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS": "1"}` 传递环境变量给 CLI

Agent Teams 的所有实际逻辑都在 CLI 内部实现。SDK 只是一个启动器。

---

## 6. 结论与建议

### 6.1 核心结论

1. **Claude Agent SDK 通过 spawn CLI 子进程工作**，CLI 是一个自包含的原生二进制 (Node.js SEA)
2. **PyPI 提供 Linux x86_64/aarch64 的平台特定 wheel**，bundled CLI 已包含在内
3. **ECS Fargate 完全兼容**，不需要安装 Node.js
4. **Docker 镜像可大幅精简**，去掉 Node.js 层节省 150-200 MB
5. **自定义 Transport 不能绕过 CLI**，Control Protocol 需要 CLI 对端
6. **Agent Teams 完全依赖 CLI 内部实现**，无法独立实现
7. **Bedrock Converse API 可作为降级路径**，但能力远不及 Agent SDK

### 6.2 行动建议

#### 立即可做 (低风险):

1. **优化 Dockerfile**: 去掉 Node.js 安装层，依赖 SDK bundled CLI
2. **修正 Dockerfile 注释**: 删除 "SDK bundled CLI 是 macOS arm64 二进制" 的错误描述
3. **确认 pyproject.toml**: `claude-agent-sdk>=0.1.8` (确保使用带 bundled CLI 的版本)

#### 短期建议 (中等风险):

4. **ECS Task Definition**: 内存提升到 1024 MiB (CLI 运行时需要较多内存)
5. **添加健康检查**: CLI 子进程监控 (检测 OOM / 僵尸进程)
6. **显式 cli_path**: 在 `ClaudeAgentAdapter` 中添加 `cli_path` 配置，避免查找逻辑的不确定性

#### 中期建议:

7. **platform-tools MCP**: 将 `_build_platform_tools_config()` 的 stdio 占位替换为 `create_sdk_mcp_server`
8. **消息解析简化**: `sdk_message_utils.py` 统一为对象格式，去掉 dict 兼容层
9. **Agent Teams 测试**: 在 Fargate 中测试 in-process 模式的 Agent Teams

### 6.3 优化后的 Dockerfile 示例

```dockerfile
# ============================================================
# 优化后: 不再需要 Node.js (SDK bundled CLI 是自包含二进制)
# ============================================================

# -- Stage 1: Builder --
FROM public.ecr.aws/docker/library/python:3.12-slim AS builder

RUN apt-get update && apt-get install -y --no-install-recommends gcc libc6-dev && rm -rf /var/lib/apt/lists/*

COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

WORKDIR /app
COPY pyproject.toml uv.lock* ./
RUN uv sync --no-dev --frozen --no-install-project

COPY src/ src/
COPY migrations/ migrations/
COPY alembic.ini .
COPY README.md .
RUN uv sync --no-dev --frozen

# -- Stage 2: Runtime --
FROM public.ecr.aws/docker/library/python:3.12-slim AS runtime

# 无需 Node.js -- claude-agent-sdk 包含自包含的 CLI 二进制
# 仅需安装 ca-certificates 用于 TLS 连接
RUN apt-get update && \
    apt-get install -y --no-install-recommends ca-certificates && \
    rm -rf /var/lib/apt/lists/*

RUN groupadd --gid 1000 appuser && \
    useradd --uid 1000 --gid 1000 --create-home appuser

WORKDIR /app

COPY --from=builder /app/.venv /app/.venv
COPY --from=builder /app/src /app/src
COPY --from=builder /app/migrations /app/migrations
COPY --from=builder /app/alembic.ini /app/alembic.ini

# 确保 bundled CLI 有执行权限
RUN chmod +x /app/.venv/lib/python3.12/site-packages/claude_agent_sdk/_bundled/claude 2>/dev/null || true

ENV PATH="/app/.venv/bin:$PATH" \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    CLAUDE_CODE_USE_BEDROCK=1 \
    HOME=/home/appuser

USER appuser

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD python -c "import httpx; r = httpx.get('http://localhost:8000/health'); r.raise_for_status()"

CMD ["sh", "-c", "alembic upgrade head && uvicorn src.presentation.api.main:app --host 0.0.0.0 --port 8000"]
```

---

## 附录 A: 关键源文件路径

| 文件 | 说明 |
|------|------|
| `.venv/.../claude_agent_sdk/_internal/transport/subprocess_cli.py` | CLI 查找、启动、通信核心 |
| `.venv/.../claude_agent_sdk/_internal/transport/__init__.py` | Transport 抽象接口 |
| `.venv/.../claude_agent_sdk/_internal/client.py` | 内部客户端 (Transport + Query 编排) |
| `.venv/.../claude_agent_sdk/_internal/query.py` | Control Protocol 实现 |
| `.venv/.../claude_agent_sdk/client.py` | ClaudeSDKClient 公开接口 |
| `.venv/.../claude_agent_sdk/query.py` | query() 公开函数 |
| `.venv/.../claude_agent_sdk/types.py` | 所有类型定义 |
| `.venv/.../claude_agent_sdk/_bundled/claude` | Bundled CLI 二进制 |
| `.venv/.../claude_agent_sdk/_version.py` | SDK 版本 (0.1.34) |
| `.venv/.../claude_agent_sdk/_cli_version.py` | Bundled CLI 版本 (2.1.38) |
| `src/modules/execution/infrastructure/external/claude_agent_adapter.py` | 项目适配器 |
| `src/modules/execution/infrastructure/external/sdk_message_utils.py` | 消息解析工具 |

## 附录 B: PyPI Wheel 数据 (0.1.35 最新版)

```
claude_agent_sdk-0.1.35-py3-none-macosx_11_0_arm64.whl       54,665,881 bytes
claude_agent_sdk-0.1.35-py3-none-manylinux_2_17_aarch64.whl  69,419,673 bytes
claude_agent_sdk-0.1.35-py3-none-manylinux_2_17_x86_64.whl   70,007,339 bytes
claude_agent_sdk-0.1.35-py3-none-win_amd64.whl               72,528,072 bytes
claude_agent_sdk-0.1.35.tar.gz                                   61,194 bytes
```

## 附录 C: SDK 通信协议消息类型速查

| 消息方向 | 类型 | 子类型 | 说明 |
|---------|------|--------|------|
| SDK->CLI | control_request | initialize | 初始化握手 (传递 hooks, agents) |
| SDK->CLI | user | - | 用户消息 |
| SDK->CLI | control_response | success/error | 响应 CLI 的控制请求 |
| CLI->SDK | control_response | success/error | 响应 SDK 的控制请求 |
| CLI->SDK | control_request | can_use_tool | 请求工具使用权限 |
| CLI->SDK | control_request | hook_callback | 触发 Hook 回调 |
| CLI->SDK | control_request | mcp_message | SDK MCP Server 消息路由 |
| CLI->SDK | assistant | - | 助手消息 (文本/工具调用) |
| CLI->SDK | result | success/error | 执行结果 (含成本/用量) |
