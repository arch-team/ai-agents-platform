# Agent Blueprint 全面优化 — 设计规格

> 日期: 2026-04-05
> 分支: feat/blueprint-optimization
> 状态: 已确认

## 1. 目标

对 M17 (Agent Blueprint + Builder V2) 进行全面优化：

1. **V1 吸收**: 消除 V1/V2 双路径，统一为 Blueprint-only 模式
2. **代码审查遗留修复**: ISP 接口拆分、SSE 去重、StrEnum、async I/O
3. **功能完善**: TestSandbox 真实执行集成
4. **前端清理**: 移除 V1 创建表单和 hooks

## 2. 前置条件

- Dev/Prod 环境无真实用户数据，V1 Agent 可直接废弃
- 不需要数据迁移脚本
- `blueprint_id` 可直接改为 NOT NULL

## 3. 方案选择

**逐层吸收 (Incremental Absorption)** — 按依赖顺序逐层处理，每层独立 commit，逐步验证。

```
Layer 1: 领域层 — blueprint_id NOT NULL + Agent 实体简化
Layer 2: 接口层 — IAgentCreator/IAgentLifecycle 拆分
Layer 3: 服务层 — BuilderService/AgentService V1 移除
Layer 4: API 层 — POST /agents 自动创建 Blueprint + V1 端点移除
Layer 5: 执行层 — Mode 3 移除
Layer 6: SSE + Infrastructure — SSE 去重 + async I/O
Layer 7: 前端 — AgentCreateForm 移除 + V1 hooks 清理
Layer 8: 功能完善 — TestSandbox 集成
```

---

## 4. 详细设计

### 4.1 领域层 (Layer 1)

#### Agent 实体变更

```python
# 变更前
class Agent(PydanticEntity):
    system_prompt: str = ""           # V1 字段
    blueprint_id: int | None = None   # nullable

# 变更后
class Agent(PydanticEntity):
    blueprint_id: int                 # NOT NULL，所有 Agent 必有 Blueprint
    # system_prompt 字段移除
```

#### Agent.activate() 简化

```python
# 变更前: DRAFT→ACTIVE (V1, 需 system_prompt) 和 TESTING→ACTIVE (V2)
# 变更后: 仅 TESTING→ACTIVE (所有 Agent 走 Blueprint 路径)

def activate(self) -> None:
    self._require_status(self.status, frozenset({AgentStatus.TESTING}), AgentStatus.ACTIVE.value)
    self.status = AgentStatus.ACTIVE
    self.touch()
```

#### GuardrailSeverity StrEnum

```python
class GuardrailSeverity(StrEnum):
    WARN = "warn"
    BLOCK = "block"

@dataclass(frozen=True)
class GuardrailData:
    rule: str
    severity: GuardrailSeverity = GuardrailSeverity.WARN
```

#### 数据库迁移

- 新增 Alembic migration: `agents.blueprint_id` 改为 NOT NULL
- `agents.system_prompt` 列移除
- 前提: 环境无存量 V1 数据

### 4.2 接口层 (Layer 2)

#### IAgentCreator 拆分

```
变更前 (shared/domain/interfaces/agent_creator.py):
  IAgentCreator
    ├── create_agent()                    # V1 抽象方法
    ├── create_agent_with_blueprint()     # V2 带默认实现
    └── start_testing()                   # 生命周期

变更后 (两个文件):
  agent_creator.py:
    IAgentCreator
      └── create_agent(CreateAgentRequest)  # 统一方法，必须包含 BlueprintData

  agent_lifecycle.py:
    IAgentLifecycle
      ├── start_testing(agent_id, operator_id)
      ├── go_live(agent_id, operator_id)
      └── take_offline(agent_id, operator_id)
```

#### CreateAgentRequest 统一

```python
@dataclass
class CreateAgentRequest:
    name: str
    blueprint: BlueprintData            # 必填
    description: str = ""
    model_id: str = ""
    knowledge_base_ids: list[int] = field(default_factory=list)
    # system_prompt 字段移除
```

移除的类型:
- `CreateAgentWithBlueprintRequest` (合并到 CreateAgentRequest)
- V1 的旧 `CreateAgentRequest` (无 blueprint)

### 4.3 服务层 (Layer 3)

#### BuilderService 去重

提取共享方法:

```python
async def _stream_and_parse_blueprint(self, session: BuilderSession) -> AsyncIterator[str]:
    """共享: LLM 流式生成 + Blueprint 解析 + 持久化。"""
    platform_context = await self._build_platform_context()
    messages = [BuilderMessage(role=m["role"], content=m["content"]) for m in session.messages]
    chunks: list[str] = []
    async for chunk in self._llm_service.generate_blueprint(messages, platform_context):
        chunks.append(chunk)
        yield chunk
    self._try_parse_and_save_blueprint(session, "".join(chunks).strip())
    await self._session_repo.update(session)
```

`generate_blueprint_stream` 和 `refine_session` 分别:
1. 转换 session 状态 (`start_generation` / `start_refinement`)
2. 添加用户消息 (`session.prompt` / `dto.message`)
3. 委托 `_stream_and_parse_blueprint`

#### BuilderService V1 移除

- 删除 `_confirm_v1()` 方法
- 删除 `generate_config_stream()` (V1 单轮生成)
- `confirm_session()` 始终走 V2 路径

#### AgentCreatorImpl 合并

- `create_agent()` 方法直接执行完整的 Blueprint 创建流程:
  1. 创建 Agent 实体 (带 blueprint_id)
  2. 创建 Blueprint DB 记录
  3. 创建 workspace 目录
  4. 更新 workspace_path
- 移除 V1 fallback 逻辑

### 4.4 API 层 (Layer 4)

#### POST /api/v1/agents 变更

端点路由保留，请求体扩展支持 Blueprint 字段:

```python
# 请求体: 保持向后兼容的字段名
class CreateAgentRequestSchema(BaseModel):
    name: str
    description: str = ""
    model_id: str = ""
    # 新增可选 Blueprint 字段
    persona_role: str = ""        # 如未提供，用 name 作为 role
    persona_background: str = ""  # 如未提供，用 description
    persona_tone: str = ""
```

内部自动构造 `BlueprintData`:
```python
blueprint = BlueprintData(
    persona=PersonaData(
        role=request.persona_role or request.name,
        background=request.persona_background or request.description,
        tone=request.persona_tone,
    )
)
```

#### Builder V1 端点移除

- 删除 `POST /sessions/{session_id}/messages` (V1 SSE 配置生成)

### 4.5 执行层 (Layer 5)

#### Mode 3 移除

```python
def _build_agent_request(self, ctx, tools, *, gateway_auth_token="") -> AgentRequest:
    """二模式路由 (移除 V1 兼容模式)。"""
    if ctx.agent_info.runtime_arn:
        # 模式1: 专属 Runtime
        runtime_arn = ctx.agent_info.runtime_arn
        cwd = "/workspace"
    else:
        # 模式2: 本地 cwd (所有非 Runtime Agent)
        cwd = ctx.agent_info.workspace_path

    return AgentRequest(
        prompt=ctx.created_user_msg.content,
        system_prompt="",               # Blueprint Agent 不需要 inline system_prompt
        cwd=cwd,
        runtime_arn=runtime_arn,
        ...
    )
```

`ActiveAgentInfo` 中 `system_prompt` 字段可考虑移除（因 Blueprint 通过 CLAUDE.md 提供指令），但需评估 execution 模块内部其他使用场景（如 RAG 注入）。如 RAG 仍需 system_prompt 通道，保留但标记为内部使用。

### 4.6 SSE + Infrastructure (Layer 6)

#### SSE 生成器统一

新增 `shared/api/sse_helpers.py`:

```python
async def stream_sse_events(
    sse_manager: SSEConnectionManager,
    user_id: int,
    stream: AsyncIterator[str],
    *,
    format_chunk: Callable[[str], dict],
    format_done: Callable[[], dict],
    log_event: str = "sse_stream_error",
    **log_context: Any,
) -> AsyncIterator[ServerSentEvent]:
    """统一 SSE 流式事件生成器 — 连接管理 + 错误处理。"""
    async with sse_manager.connect(user_id):
        try:
            async for chunk in stream:
                yield ServerSentEvent(data=json.dumps(format_chunk(chunk)))
            yield ServerSentEvent(data=json.dumps(format_done()))
        except DomainError as e:
            yield ServerSentEvent(data=json.dumps({"error": e.message, "done": True}))
        except Exception:
            logger.exception(log_event, **log_context)
            yield ServerSentEvent(data=json.dumps({"error": "服务内部错误", "done": True}))
```

影响范围: builder 3 个 endpoint + execution 2 个 endpoint → 每个约从 20 行缩减为 5 行。

#### async I/O 修复

涉及文件:
- `agents/infrastructure/external/workspace_manager.py` — 文件系统操作
- `skills/infrastructure/external/skill_file_manager_impl.py` — SKILL.md 文件操作

```python
# 变更前 (同步阻塞)
workspace.mkdir(parents=True, exist_ok=True)
(workspace / "CLAUDE.md").write_text(content)

# 变更后 (异步委托)
await asyncio.to_thread(workspace.mkdir, parents=True, exist_ok=True)
await asyncio.to_thread(Path.write_text, workspace / "CLAUDE.md", content)
```

对于多步文件操作，封装为同步私有方法后用 `asyncio.to_thread` 包装:

```python
def _write_workspace_sync(self, path: Path, claude_md: str, settings: dict) -> None:
    """同步文件写入 — 由 asyncio.to_thread 调用。"""
    path.mkdir(parents=True, exist_ok=True)
    (path / "CLAUDE.md").write_text(claude_md, encoding="utf-8")
    ...

async def create_workspace(self, dto: BlueprintDTO) -> str:
    await asyncio.to_thread(self._write_workspace_sync, workspace, claude_md, settings)
```

### 4.7 前端 (Layer 7)

#### AgentCreateForm 移除

- 删除 `frontend/src/features/agents/ui/AgentCreateForm.tsx`
- 删除 `frontend/src/features/agents/api/types.ts` 中的 `CreateAgentRequest` V1 类型
- 删除 `frontend/src/features/agents/api/mutations.ts` 中的 `useCreateAgent` V1 mutation
- "创建 Agent" 入口统一指向 Builder 页面

#### Builder V1 hooks 清理

移除的导出:
- `useBuilderStream` (V1 SSE hook)
- `useBuilderGeneratedConfig` (V1 config hook)
- `streamBuilderSSE` (V1 SSE adapter)
- Store V1 字段: `streamContent`, `generatedConfig`, `isGenerating` (V1 专用)

### 4.8 TestSandbox 集成 (Layer 8)

#### 功能描述

TestSandbox 组件在 Agent 处于 TESTING 状态时提供真实对话体验:

1. 用户在 TestSandbox 中输入消息
2. 调用 `POST /api/v1/conversations` 创建对话 (关联 TESTING Agent)
3. 调用 `POST /api/v1/conversations/{id}/messages` 发送消息 (SSE 流式)
4. 展示响应内容，包括工具调用结果和知识库引用

#### 前端变更

```tsx
// TestSandbox.tsx
// 变更前: setTimeout mock 响应
// 变更后: 复用 execution 模块的真实 API

import { useCreateConversation, useSendMessageStream } from '@/features/execution';

// 1. 创建对话 (TESTING Agent)
const { mutateAsync: createConversation } = useCreateConversation();
// 2. 发送消息并流式接收
const { sendMessage, isStreaming } = useSendMessageStream();
```

#### 后端变更

Execution 模块需允许 TESTING 状态的 Agent 执行:
- `IAgentQuerier.get_active_agent()` → 扩展为 `get_executable_agent()` (ACTIVE 或 TESTING)
- 或新增 `get_testing_agent()` 查询方法

---

## 5. 删除清单

### 后端

| 文件/代码 | 原因 |
|-----------|------|
| `IAgentCreator.create_agent_with_blueprint()` | 合并到 `create_agent()` |
| `IAgentCreator.start_testing()` | 移到 `IAgentLifecycle` |
| `CreateAgentWithBlueprintRequest` | 合并到 `CreateAgentRequest` |
| `Agent.system_prompt` 字段 | Blueprint Persona 替代 |
| `BuilderService._confirm_v1()` | V1 移除 |
| `BuilderService.generate_config_stream()` | V1 移除 |
| `ClaudeBuilderAdapter.generate_config()` | V1 移除 |
| `builder/api POST /sessions/{id}/messages` | V1 端点移除 |
| `_build_agent_request` Mode 3 分支 | V1 兼容移除 |
| `agents.system_prompt` DB 列 | Alembic 迁移移除 |
| `migrate_agents_to_blueprint.py` 脚本 | 不再需要迁移 |

### 前端

| 文件/代码 | 原因 |
|-----------|------|
| `AgentCreateForm.tsx` | V1 创建表单 |
| `useCreateAgent` mutation | V1 创建 hook |
| `useBuilderStream` | V1 SSE hook |
| `useBuilderGeneratedConfig` | V1 config hook |
| `streamBuilderSSE` | V1 SSE adapter |
| Store V1 字段 | V1 状态管理 |

---

## 6. 测试策略

- V1-only 测试改写为 V2 模式 (Agent 必有 Blueprint)
- `make_agent()` 工厂函数更新: 默认包含 `blueprint_id`
- SSE helper 新增独立单元测试
- TestSandbox E2E 测试覆盖 TESTING Agent 对话流
- 覆盖率目标: >= 85% (与项目标准一致)

---

## 7. 风险与缓解

| 风险 | 概率 | 缓解 |
|------|------|------|
| 大量测试需要改写 | 高 | 逐层推进，每层确保测试全绿 |
| execution 模块 system_prompt 依赖 | 中 | 评估 RAG/Memory 注入路径，必要时保留内部字段 |
| 前端路由变更影响用户体验 | 低 | "创建 Agent" 按钮直接跳转 Builder 页面 |
| TestSandbox 需要 TESTING Agent 执行权限 | 低 | 扩展 IAgentQuerier 查询方法 |
