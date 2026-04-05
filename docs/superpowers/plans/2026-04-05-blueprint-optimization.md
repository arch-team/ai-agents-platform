# Agent Blueprint 全面优化 — 实施计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 消除 V1/V2 双路径，统一为 Blueprint-only 模式，修复代码审查遗留的 5 项问题，完善 TestSandbox 真实执行集成。

**Architecture:** 逐层吸收 — 按 DDD 分层依赖顺序从 Domain 到 API 逐层移除 V1 代码路径。每层独立 commit，确保测试全绿后再推进下一层。所有 Agent 必须关联 Blueprint，执行路由从三模式简化为二模式。

**Tech Stack:** Python 3.11+ | FastAPI | SQLAlchemy 2.0 (async) | Pydantic v2 | React 19 + TypeScript | Zustand

**Design Spec:** `docs/superpowers/specs/2026-04-05-blueprint-optimization-design.md`

---

## 文件变更总览

### 新建文件
- `backend/src/shared/domain/interfaces/agent_lifecycle.py` — IAgentLifecycle 接口
- `backend/src/shared/api/sse_helpers.py` — SSE 流式事件统一生成器
- `backend/migrations/versions/xxxx_remove_v1_fields.py` — Alembic 迁移
- `backend/tests/shared/api/test_sse_helpers.py` — SSE helper 单元测试

### 主要修改文件
| 文件 | 变更类型 |
|------|---------|
| `backend/src/shared/domain/interfaces/agent_creator.py` | 统一 CreateAgentRequest，移除 V1 类型，添加 GuardrailSeverity |
| `backend/src/shared/domain/interfaces/agent_querier.py` | get_active_agent → get_executable_agent |
| `backend/src/modules/agents/domain/entities/agent.py` | 移除 system_prompt，blueprint_id NOT NULL |
| `backend/src/modules/agents/api/schemas/requests.py` | 移除 system_prompt，添加 persona_* 字段 |
| `backend/src/modules/agents/api/endpoints.py` | 自动创建 Blueprint |
| `backend/src/modules/agents/infrastructure/services/agent_creator_impl.py` | 合并 V1/V2 创建逻辑 |
| `backend/src/modules/agents/infrastructure/services/agent_querier_impl.py` | 查询条件扩展 |
| `backend/src/modules/builder/application/services/builder_service.py` | 提取 _stream_and_parse_blueprint，移除 V1 |
| `backend/src/modules/builder/api/endpoints.py` | 移除 V1 端点，SSE helper |
| `backend/src/modules/builder/infrastructure/external/claude_builder_adapter.py` | 移除 generate_config |
| `backend/src/modules/execution/application/services/execution_service.py` | 移除 Mode 3 |
| `backend/src/modules/execution/api/endpoints.py` | SSE helper |
| `backend/src/modules/execution/api/team_endpoints.py` | SSE helper |
| `backend/src/modules/agents/infrastructure/external/workspace_manager.py` | asyncio.to_thread |
| `backend/src/modules/skills/infrastructure/external/skill_file_manager_impl.py` | asyncio.to_thread |
| `backend/src/presentation/api/providers.py` | 注册 IAgentLifecycle |

### 删除文件
| 文件 | 原因 |
|------|------|
| `backend/scripts/migrate_agents_to_blueprint.py` | 不再需要 V1→V2 迁移 |
| `frontend/src/features/agents/ui/AgentCreateForm.tsx` | V1 创建表单 |
| `frontend/src/features/agents/ui/AgentCreateForm.test.tsx` (如存在) | 对应测试 |

### 前端修改文件
| 文件 | 变更类型 |
|------|---------|
| `frontend/src/features/agents/api/types.ts` | 移除 V1 CreateAgentRequest |
| `frontend/src/features/agents/api/mutations.ts` | 移除 useCreateAgent |
| `frontend/src/features/agents/index.ts` | 移除 V1 导出 |
| `frontend/src/features/builder/index.ts` | 移除 V1 hooks 导出 |
| `frontend/src/features/builder/model/store.ts` | 移除 V1 state 字段 |
| `frontend/src/features/builder/api/stream.ts` | 移除 V1 SSE hook |
| `frontend/src/features/builder/lib/sse.ts` | 移除 V1 SSE adapter |
| `frontend/src/features/builder/ui/TestSandbox.tsx` | 真实执行集成 |

---

## Task 1: GuardrailSeverity StrEnum

**Files:**
- Modify: `backend/src/shared/domain/interfaces/agent_creator.py:57-62`
- Modify: `backend/tests/modules/agents/unit/domain/test_agent_blueprint.py`

- [ ] **Step 1: 写测试 — GuardrailSeverity 枚举行为**

在 `backend/tests/shared/domain/test_agent_creator_types.py` (新建) 中:

```python
"""agent_creator 共享类型测试。"""

import pytest

from src.shared.domain.interfaces.agent_creator import GuardrailData, GuardrailSeverity


class TestGuardrailSeverity:
    def test_values(self) -> None:
        assert GuardrailSeverity.WARN == "warn"
        assert GuardrailSeverity.BLOCK == "block"

    def test_from_string(self) -> None:
        """StrEnum 支持从字符串构造（兼容现有 dict.get 调用）。"""
        assert GuardrailSeverity("warn") == GuardrailSeverity.WARN
        assert GuardrailSeverity("block") == GuardrailSeverity.BLOCK

    def test_invalid_value_raises(self) -> None:
        with pytest.raises(ValueError):
            GuardrailSeverity("invalid")


class TestGuardrailDataWithEnum:
    def test_default_severity(self) -> None:
        g = GuardrailData(rule="不可泄露密码")
        assert g.severity == GuardrailSeverity.WARN

    def test_string_severity_compat(self) -> None:
        """现有代码 GuardrailData(severity=g.get("severity", "warn")) 兼容性。"""
        g = GuardrailData(rule="禁止SQL注入", severity=GuardrailSeverity("warn"))
        assert g.severity == GuardrailSeverity.WARN
```

- [ ] **Step 2: 运行测试确认失败**

```bash
cd backend && uv run pytest tests/shared/domain/test_agent_creator_types.py -v
```

预期: FAIL — `GuardrailSeverity` 不存在

- [ ] **Step 3: 实现 GuardrailSeverity StrEnum**

修改 `backend/src/shared/domain/interfaces/agent_creator.py`:

```python
from enum import StrEnum

class GuardrailSeverity(StrEnum):
    """安全护栏严重级别。"""
    WARN = "warn"
    BLOCK = "block"

@dataclass(frozen=True)
class GuardrailData:
    """Agent 安全护栏 (跨模块值对象)。"""
    rule: str
    severity: GuardrailSeverity = GuardrailSeverity.WARN
```

- [ ] **Step 4: 运行测试确认通过**

```bash
cd backend && uv run pytest tests/shared/domain/test_agent_creator_types.py -v
```

预期: 全部 PASS

- [ ] **Step 5: 运行全量检查确认无回归**

```bash
cd backend && uv run ruff check src/ && uv run mypy src/ && uv run pytest --tb=short -q
```

预期: 全部通过 (StrEnum 是 str 子类，现有调用无需修改)

- [ ] **Step 6: 提交**

```bash
git add -A && git commit -m "refactor(shared): GuardrailSeverity 从 str 改为 StrEnum"
```

---

## Task 2: Agent 实体简化 + DB 迁移

**Files:**
- Modify: `backend/src/modules/agents/domain/entities/agent.py`
- Modify: `backend/src/modules/agents/infrastructure/persistence/models/agent_model.py`
- Create: `backend/migrations/versions/xxxx_remove_v1_fields.py`
- Modify: `backend/tests/modules/agents/conftest.py` — `make_agent()` 更新
- Modify: `backend/tests/modules/agents/unit/domain/test_agent_entity.py`

- [ ] **Step 1: 更新 make_agent 工厂函数**

`backend/tests/modules/agents/conftest.py` — `make_agent()` 必须包含 `blueprint_id`:

```python
def make_agent(
    *,
    agent_id: int = 1,
    name: str = "测试 Agent",
    description: str = "测试用",
    status: AgentStatus = AgentStatus.DRAFT,
    owner_id: int = 1,
    blueprint_id: int = 1,  # 不再 Optional
    # system_prompt 参数移除
    **kwargs: object,
) -> Agent:
    return Agent(
        id=agent_id,
        name=name,
        description=description,
        status=status,
        owner_id=owner_id,
        blueprint_id=blueprint_id,
        **kwargs,
    )
```

- [ ] **Step 2: 写测试 — Agent 实体新行为**

```python
class TestAgentActivateV2Only:
    """activate() 仅允许 TESTING -> ACTIVE (V1 DRAFT->ACTIVE 路径移除)。"""

    def test_activate_from_testing(self) -> None:
        agent = make_agent(status=AgentStatus.TESTING)
        agent.activate()
        assert agent.status == AgentStatus.ACTIVE

    def test_activate_from_draft_raises(self) -> None:
        """DRAFT 不能直接激活，必须先经过 TESTING。"""
        agent = make_agent(status=AgentStatus.DRAFT)
        with pytest.raises(InvalidStateTransitionError):
            agent.activate()

    def test_blueprint_id_required(self) -> None:
        """blueprint_id 是必填字段。"""
        agent = make_agent(blueprint_id=42)
        assert agent.blueprint_id == 42
```

- [ ] **Step 3: 运行测试确认失败**

```bash
cd backend && uv run pytest tests/modules/agents/unit/domain/test_agent_entity.py -v -k "V2Only or blueprint_id_required"
```

预期: FAIL — agent 仍有旧 activate() 逻辑

- [ ] **Step 4: 修改 Agent 实体**

`backend/src/modules/agents/domain/entities/agent.py`:

```python
class Agent(PydanticEntity):
    """Agent 实体。"""

    name: str = Field(min_length=1, max_length=100)
    description: str = Field(max_length=500, default="")
    status: AgentStatus = AgentStatus.DRAFT
    owner_id: int
    config: AgentConfig = Field(default_factory=AgentConfig)
    department_id: int | None = None
    blueprint_id: int  # NOT NULL，所有 Agent 必有 Blueprint
    # system_prompt 字段已移除

    def start_testing(self) -> None:
        """DRAFT -> TESTING。"""
        self._require_status(self.status, AgentStatus.DRAFT, AgentStatus.TESTING.value)
        self.status = AgentStatus.TESTING
        self.touch()

    def activate(self) -> None:
        """TESTING -> ACTIVE (所有 Agent 走 Blueprint 路径)。"""
        self._require_status(self.status, frozenset({AgentStatus.TESTING}), AgentStatus.ACTIVE.value)
        self.status = AgentStatus.ACTIVE
        self.touch()

    def archive(self) -> None:
        """DRAFT/TESTING/ACTIVE -> ARCHIVED，不可逆。"""
        self._require_status(self.status, _ARCHIVABLE, AgentStatus.ARCHIVED.value)
        self.status = AgentStatus.ARCHIVED
        self.touch()
```

- [ ] **Step 5: 更新 ORM Model**

`backend/src/modules/agents/infrastructure/persistence/models/agent_model.py`:
- 移除 `system_prompt` 列
- `blueprint_id` 改为 `Mapped[int]` (NOT NULL)

- [ ] **Step 6: 创建 Alembic 迁移**

```bash
cd backend && uv run alembic revision --autogenerate -m "remove_system_prompt_blueprint_not_null"
```

手动验证迁移内容:
- upgrade: DROP COLUMN `system_prompt`, ALTER `blueprint_id` SET NOT NULL
- downgrade: ADD COLUMN `system_prompt`, ALTER `blueprint_id` DROP NOT NULL

- [ ] **Step 7: 修复所有受影响的测试**

逐步修复:
1. `test_agent_entity.py` — 移除引用 `system_prompt` 的测试，更新 `activate()` 相关测试
2. `test_agent_service.py` — `make_agent()` 调用更新 (已通过 conftest 修改)
3. `test_agent_lifecycle.py` — 确认 TESTING→ACTIVE 流程不受影响
4. 其他引用 `system_prompt` 的测试文件

```bash
cd backend && uv run pytest tests/modules/agents/ -v --tb=short
```

- [ ] **Step 8: 全量质量检查**

```bash
cd backend && uv run ruff check src/ && uv run mypy src/ && uv run pytest --tb=short -q
```

预期: 可能有其他模块引用 `Agent.system_prompt` 导致的 mypy 错误，逐一修复。

- [ ] **Step 9: 提交**

```bash
git add -A && git commit -m "refactor(agents): 移除 system_prompt 字段, blueprint_id 改为 NOT NULL"
```

---

## Task 3: IAgentCreator 统一 + IAgentLifecycle 拆分

**Files:**
- Modify: `backend/src/shared/domain/interfaces/agent_creator.py`
- Create: `backend/src/shared/domain/interfaces/agent_lifecycle.py`
- Modify: `backend/src/shared/domain/interfaces/__init__.py`
- Modify: `backend/src/modules/agents/infrastructure/services/agent_creator_impl.py`
- Modify: `backend/src/presentation/api/providers.py`
- Modify: `backend/tests/modules/agents/unit/infrastructure/test_agent_creator_impl.py`
- Modify: `backend/tests/modules/builder/unit/application/test_builder_service.py`

- [ ] **Step 1: 创建 IAgentLifecycle 接口**

`backend/src/shared/domain/interfaces/agent_lifecycle.py`:

```python
"""跨模块 Agent 生命周期接口。

builder 模块依赖此接口管理 Agent 状态转换，
避免直接导入 agents 模块，遵循模块隔离规则。
"""

from abc import ABC, abstractmethod

from src.shared.domain.interfaces.agent_creator import CreatedAgentInfo


class IAgentLifecycle(ABC):
    """跨模块 Agent 生命周期管理接口。"""

    @abstractmethod
    async def start_testing(self, agent_id: int, operator_id: int) -> CreatedAgentInfo:
        """触发 Agent 进入 TESTING 状态 (创建 Runtime)。"""
        ...

    @abstractmethod
    async def go_live(self, agent_id: int, operator_id: int) -> CreatedAgentInfo:
        """触发 Agent 上线 (TESTING -> ACTIVE)。"""
        ...

    @abstractmethod
    async def take_offline(self, agent_id: int, operator_id: int) -> CreatedAgentInfo:
        """触发 Agent 下线 (ACTIVE -> ARCHIVED, 销毁 Runtime)。"""
        ...
```

- [ ] **Step 2: 统一 IAgentCreator — 移除 V1 方法和类型**

`backend/src/shared/domain/interfaces/agent_creator.py`:
- 删除旧的 `CreateAgentRequest` (V1)
- 删除 `CreateAgentWithBlueprintRequest`
- 统一 `CreateAgentRequest` 包含 `BlueprintData`
- 删除 `start_testing()` 方法 (移到 IAgentLifecycle)
- 删除 `create_agent_with_blueprint()` 默认实现

```python
class IAgentCreator(ABC):
    """跨模块 Agent 创建接口。"""

    @abstractmethod
    async def create_agent(self, request: CreateAgentRequest, owner_id: int) -> CreatedAgentInfo:
        """创建 Agent (必须包含 Blueprint)。"""
        ...
```

- [ ] **Step 3: 更新 AgentCreatorImpl**

`backend/src/modules/agents/infrastructure/services/agent_creator_impl.py`:
- `create_agent()` 执行完整 Blueprint 流程 (原 `create_agent_with_blueprint` 的逻辑)
- 实现 `IAgentLifecycle` 接口
- 移除 V1 fallback

- [ ] **Step 4: 更新 providers.py**

注册 `IAgentLifecycle` 工厂:

```python
from src.shared.domain.interfaces.agent_lifecycle import IAgentLifecycle

async def get_agent_lifecycle(
    session: Annotated[AsyncSession, Depends(get_db)],
) -> IAgentLifecycle:
    """创建 IAgentLifecycle 实例（供 builder 模块使用）。"""
    # 复用 AgentCreatorImpl（同时实现 IAgentCreator + IAgentLifecycle）
    creator = await get_agent_creator(session)
    assert isinstance(creator, IAgentLifecycle)
    return creator
```

- [ ] **Step 5: 更新所有消费方导入**

涉及文件:
- `builder_service.py` — `CreateAgentWithBlueprintRequest` → `CreateAgentRequest`
- `builder_service.py` — `self._agent_creator.start_testing()` → 需要注入 `IAgentLifecycle`
- Builder `dependencies.py` — 注入 `IAgentLifecycle`

- [ ] **Step 6: 修复所有测试**

```bash
cd backend && uv run pytest tests/modules/agents/ tests/modules/builder/ -v --tb=short
```

- [ ] **Step 7: 全量检查**

```bash
cd backend && uv run ruff check src/ && uv run mypy src/ && uv run pytest --tb=short -q
```

- [ ] **Step 8: 提交**

```bash
git add -A && git commit -m "refactor(shared): IAgentCreator 统一 + IAgentLifecycle 拆分 (ISP)"
```

---

## Task 4: BuilderService V1 移除 + generate/refine 去重

**Files:**
- Modify: `backend/src/modules/builder/application/services/builder_service.py`
- Modify: `backend/src/modules/builder/infrastructure/external/claude_builder_adapter.py`
- Modify: `backend/src/modules/builder/application/interfaces/builder_llm_service.py`
- Modify: `backend/tests/modules/builder/unit/application/test_builder_service.py`
- Delete test: `backend/tests/modules/builder/unit/application/test_builder_service_v2.py` (合并到主测试)

- [ ] **Step 1: 写测试 — generate/refine 使用共享 _stream_and_parse_blueprint**

```python
class TestStreamAndParseBlueprint:
    """_stream_and_parse_blueprint 共享逻辑测试。"""

    async def test_generate_and_refine_share_streaming_logic(self, builder_service, mock_llm) -> None:
        """generate_blueprint_stream 和 refine_session 产生相同的流式行为。"""
        mock_llm.generate_blueprint.return_value = async_iter(["[PERSONA]", "role: 测试"])
        # ... 验证两个方法都调用 generate_blueprint 并解析结果
```

- [ ] **Step 2: 提取 _stream_and_parse_blueprint**

```python
async def _stream_and_parse_blueprint(self, session: BuilderSession) -> AsyncIterator[str]:
    """共享: LLM 流式生成 + Blueprint 解析 + 持久化。"""
    platform_context = await self._build_platform_context()
    messages = [BuilderMessage(role=m["role"], content=m["content"]) for m in session.messages]

    chunks: list[str] = []
    async for chunk in self._llm_service.generate_blueprint(messages, platform_context):
        chunks.append(chunk)
        yield chunk

    full_text = "".join(chunks).strip()
    self._try_parse_and_save_blueprint(session, full_text)
    await self._session_repo.update(session)
```

- [ ] **Step 3: 简化 generate_blueprint_stream 和 refine_session**

```python
async def generate_blueprint_stream(self, session_id: int, user_id: int) -> AsyncIterator[str]:
    session = await self._get_owned_session(session_id, user_id)
    session.start_generation()
    session.add_message("user", session.prompt)
    await self._session_repo.update(session)
    async for chunk in self._stream_and_parse_blueprint(session):
        yield chunk

async def refine_session(self, session_id: int, user_id: int, *, dto: RefineBuilderDTO) -> AsyncIterator[str]:
    session = await self._get_owned_session(session_id, user_id)
    session.start_refinement()
    session.add_message("user", dto.message)
    await self._session_repo.update(session)
    async for chunk in self._stream_and_parse_blueprint(session):
        yield chunk
```

- [ ] **Step 4: 移除 V1 方法**

从 `BuilderService` 中删除:
- `generate_config_stream()` 方法
- `_confirm_v1()` 方法
- `confirm_session()` 中的 V1 分支: 移除 `elif session.generated_config` 分支

从 `ClaudeBuilderAdapter` 中删除:
- `generate_config()` 方法
- `IBuilderLLMService` 接口中移除 `generate_config` 抽象方法

- [ ] **Step 5: 更新 confirm_session 为 V2-only**

```python
async def confirm_session(self, session_id: int, user_id: int, *, name_override: str | None = None, auto_start_testing: bool = False) -> BuilderSessionDTO:
    session = await self._get_owned_session(session_id, user_id)
    if session.status != BuilderStatus.CONFIRMED:
        raise InvalidStateTransitionError(...)

    if not session.generated_blueprint:
        raise InvalidStateTransitionError(
            entity_type="BuilderSession",
            current_state=session.status.value,
            target_state="confirm_creation",
        )

    agent_info = await self._confirm_v2(session, user_id, name_override=name_override)
    # ... rest stays the same
```

- [ ] **Step 6: 修复测试 + 全量检查**

```bash
cd backend && uv run ruff check src/ && uv run mypy src/ && uv run pytest --tb=short -q
```

- [ ] **Step 7: 提交**

```bash
git add -A && git commit -m "refactor(builder): 移除 V1 路径 + 提取 _stream_and_parse_blueprint 去重"
```

---

## Task 5: API 层 — POST /agents Blueprint 化 + V1 端点移除

**Files:**
- Modify: `backend/src/modules/agents/api/schemas/requests.py`
- Modify: `backend/src/modules/agents/api/endpoints.py`
- Modify: `backend/src/modules/builder/api/endpoints.py` — 移除 V1 SSE endpoint
- Modify: `backend/tests/modules/agents/integration/test_agents_endpoints.py`
- Modify: `backend/tests/modules/builder/integration/test_builder_endpoints.py`
- Modify: `backend/tests/e2e/test_agents_crud.py`

- [ ] **Step 1: 更新 CreateAgentRequest Schema**

`backend/src/modules/agents/api/schemas/requests.py`:

```python
class CreateAgentRequest(BaseModel):
    """创建 Agent 请求 (自动创建最小 Blueprint)。"""

    name: str = Field(min_length=1, max_length=100)
    description: str = Field(max_length=500, default="")
    model_id: str = Field(default=AGENT_DEFAULT_MODEL_ID, max_length=200)
    temperature: float = Field(default=AGENT_DEFAULT_TEMPERATURE, ge=0.0, le=1.0)
    max_tokens: int = Field(default=AGENT_DEFAULT_MAX_TOKENS, ge=1, le=4096)
    runtime_type: str = Field(default=AGENT_DEFAULT_RUNTIME_TYPE, pattern=r"^(agent|basic)$")
    enable_teams: bool = Field(default=AGENT_DEFAULT_ENABLE_TEAMS)
    enable_memory: bool = Field(default=False)
    tool_ids: list[int] = Field(default_factory=list, max_length=50)
    # V2: 可选 Persona 字段 (快速创建)
    persona_role: str = Field(default="", max_length=200)
    persona_background: str = Field(default="", max_length=2000)
    persona_tone: str = Field(default="", max_length=200)
    # system_prompt 字段已移除


class UpdateAgentRequest(BaseModel):
    """更新 Agent 请求。"""

    name: str | None = Field(default=None, min_length=1, max_length=100)
    description: str | None = Field(default=None, max_length=500)
    # system_prompt 已移除
    model_id: str | None = Field(default=None, max_length=200)
    temperature: float | None = Field(default=None, ge=0.0, le=1.0)
    max_tokens: int | None = Field(default=None, ge=1, le=4096)
    runtime_type: str | None = Field(default=None, pattern=r"^(agent|basic)$")
    enable_teams: bool | None = Field(default=None)
    enable_memory: bool | None = Field(default=None)
    tool_ids: list[int] | None = Field(default=None, max_length=50)
```

- [ ] **Step 2: 更新 agents endpoint 创建逻辑**

`backend/src/modules/agents/api/endpoints.py` — POST /agents 内部自动创建 Blueprint:

```python
from src.shared.domain.interfaces.agent_creator import (
    BlueprintData, CreateAgentRequest as CreateAgentCmd, PersonaData, ToolBindingData,
)

@router.post("", status_code=status.HTTP_201_CREATED)
async def create_agent(request: CreateAgentRequest, ..., agent_creator: AgentCreatorDep) -> AgentResponse:
    blueprint = BlueprintData(
        persona=PersonaData(
            role=request.persona_role or request.name,
            background=request.persona_background or request.description,
        ),
        tool_bindings=tuple(ToolBindingData(tool_id=tid, display_name="") for tid in request.tool_ids),
        memory_enabled=request.enable_memory,
    )
    cmd = CreateAgentCmd(name=request.name, blueprint=blueprint, description=request.description, model_id=request.model_id)
    result = await agent_creator.create_agent(cmd, current_user.id)
    # ... return response
```

- [ ] **Step 3: 移除 Builder V1 endpoint**

`backend/src/modules/builder/api/endpoints.py` — 删除整个 `generate_config_stream` 函数 (lines 56-84)

- [ ] **Step 4: 更新测试**

- `test_agents_endpoints.py` — 移除 `system_prompt` 字段，添加 `persona_role` 测试
- `test_builder_endpoints.py` — 移除 V1 messages endpoint 测试
- `test_agents_crud.py` — 更新 E2E 测试

- [ ] **Step 5: 全量检查 + 提交**

```bash
cd backend && uv run ruff check src/ && uv run mypy src/ && uv run pytest --tb=short -q
git add -A && git commit -m "refactor(api): POST /agents 自动创建 Blueprint + 移除 Builder V1 端点"
```

---

## Task 6: 执行路由 Mode 3 移除 + get_executable_agent

**Files:**
- Modify: `backend/src/shared/domain/interfaces/agent_querier.py`
- Modify: `backend/src/modules/agents/infrastructure/services/agent_querier_impl.py`
- Modify: `backend/src/modules/execution/application/services/execution_service.py`
- Modify: `backend/tests/modules/execution/`

- [ ] **Step 1: 重命名 IAgentQuerier 方法**

`backend/src/shared/domain/interfaces/agent_querier.py`:

```python
class IAgentQuerier(ABC):
    """跨模块 Agent 查询接口。"""

    @abstractmethod
    async def get_executable_agent(self, agent_id: int) -> ActiveAgentInfo | None:
        """查询可执行的 Agent (ACTIVE 或 TESTING 状态)。"""
        ...
```

- [ ] **Step 2: 更新 AgentQuerierImpl**

查询条件从 `status == ACTIVE` 扩展为 `status IN (ACTIVE, TESTING)`:

```python
async def get_executable_agent(self, agent_id: int) -> ActiveAgentInfo | None:
    agent = await self._agent_repository.get_by_id(agent_id)
    if agent is None or agent.status not in (AgentStatus.ACTIVE, AgentStatus.TESTING):
        return None
    # 构建 ActiveAgentInfo (system_prompt 设为空字符串)
    return ActiveAgentInfo(
        id=agent.id,
        name=agent.name,
        system_prompt="",  # Blueprint Agent 不使用 inline system_prompt
        ...
    )
```

- [ ] **Step 3: 更新 execution_service.py — 移除 Mode 3**

1. 所有 `get_active_agent` 调用改为 `get_executable_agent`
2. `_build_agent_request` 移除 Mode 3 (V1 兼容):

```python
def _build_agent_request(self, ctx, tools, *, gateway_auth_token="") -> AgentRequest:
    """二模式路由。"""
    cwd = ""
    runtime_arn = ""

    if ctx.agent_info.runtime_arn:
        # 模式1: 专属 Runtime
        runtime_arn = ctx.agent_info.runtime_arn
        cwd = "/workspace"
    elif ctx.agent_info.workspace_path:
        # 模式2: 本地 cwd
        cwd = ctx.agent_info.workspace_path
    # Mode 3 已移除 — 所有 Agent 都有 workspace_path

    return AgentRequest(
        prompt=ctx.created_user_msg.content,
        system_prompt="",
        cwd=cwd,
        runtime_arn=runtime_arn,
        ...
    )
```

- [ ] **Step 4: 修复测试 + 全量检查 + 提交**

```bash
cd backend && uv run ruff check src/ && uv run mypy src/ && uv run pytest --tb=short -q
git add -A && git commit -m "refactor(execution): 移除 Mode 3 路由 + get_executable_agent 支持 TESTING"
```

---

## Task 7: SSE 生成器统一

**Files:**
- Create: `backend/src/shared/api/sse_helpers.py`
- Create: `backend/tests/shared/api/test_sse_helpers.py`
- Modify: `backend/src/shared/api/__init__.py`
- Modify: `backend/src/modules/builder/api/endpoints.py`
- Modify: `backend/src/modules/execution/api/endpoints.py`
- Modify: `backend/src/modules/execution/api/team_endpoints.py`

- [ ] **Step 1: 写测试 — SSE helper 行为**

`backend/tests/shared/api/test_sse_helpers.py`:

```python
"""SSE 统一生成器测试。"""

import json
from collections.abc import AsyncIterator
from unittest.mock import AsyncMock

import pytest

from src.shared.api.sse_helpers import stream_sse_events
from src.shared.domain.exceptions import DomainError


async def _async_iter(*items: str) -> AsyncIterator[str]:
    for item in items:
        yield item


class TestStreamSseEvents:
    async def test_yields_chunks_and_done(self) -> None:
        """正常流: chunk → chunk → done。"""
        manager = AsyncMock()
        manager.connect.return_value.__aenter__ = AsyncMock()
        manager.connect.return_value.__aexit__ = AsyncMock()

        events = []
        async for event in stream_sse_events(
            manager, user_id=1,
            stream=_async_iter("hello", " world"),
            format_chunk=lambda c: {"content": c, "done": False},
            format_done=lambda: {"content": "", "done": True},
        ):
            events.append(json.loads(event.data))

        assert events == [
            {"content": "hello", "done": False},
            {"content": " world", "done": False},
            {"content": "", "done": True},
        ]

    async def test_domain_error_yields_error_event(self) -> None:
        """DomainError 转为 SSE error 事件。"""
        async def _failing_stream() -> AsyncIterator[str]:
            raise DomainError(message="会话不存在")
            yield  # noqa: RET503 — unreachable but needed for type

        manager = AsyncMock()
        manager.connect.return_value.__aenter__ = AsyncMock()
        manager.connect.return_value.__aexit__ = AsyncMock()

        events = []
        async for event in stream_sse_events(
            manager, user_id=1,
            stream=_failing_stream(),
            format_chunk=lambda c: {"content": c},
            format_done=lambda: {"done": True},
        ):
            events.append(json.loads(event.data))

        assert len(events) == 1
        assert events[0]["error"] == "会话不存在"
```

- [ ] **Step 2: 实现 SSE helper**

`backend/src/shared/api/sse_helpers.py`:

```python
"""SSE 流式事件统一生成器。"""

import json
from collections.abc import AsyncIterator, Callable
from typing import Any

import structlog
from sse_starlette import ServerSentEvent

from src.shared.domain.exceptions import DomainError

logger = structlog.get_logger(__name__)


async def stream_sse_events(
    sse_manager: Any,
    user_id: int,
    stream: AsyncIterator[str],
    *,
    format_chunk: Callable[[str], dict[str, object]],
    format_done: Callable[[], dict[str, object]],
    log_event: str = "sse_stream_error",
    **log_context: object,
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

- [ ] **Step 3: 更新 `shared/api/__init__.py` 导出**

```python
from src.shared.api.sse_helpers import stream_sse_events

__all__ = [..., "stream_sse_events"]
```

- [ ] **Step 4: 重构 builder endpoints (2 个 SSE 端点)**

`builder/api/endpoints.py` — `generate_blueprint_stream` 和 `refine_builder_session`:

```python
from src.shared.api.sse_helpers import stream_sse_events

@router.post("/sessions/{session_id}/generate")
async def generate_blueprint_stream(session_id: int, service: ServiceDep, current_user: CurrentUserDep) -> EventSourceResponse:
    sse_manager = get_sse_manager()

    async def _post_stream() -> AsyncIterator[ServerSentEvent]:
        session_dto = await service.get_session(session_id, current_user.id)
        if session_dto.generated_blueprint:
            yield ServerSentEvent(data=json.dumps({"blueprint": session_dto.generated_blueprint, "done": False}))

    return EventSourceResponse(stream_sse_events(
        sse_manager, current_user.id,
        service.generate_blueprint_stream(session_id, current_user.id),
        format_chunk=lambda c: {"content": c, "done": False},
        format_done=lambda: {"content": "", "done": True},
        log_event="builder_blueprint_stream_error", session_id=session_id,
    ))
```

> **注意**: blueprint/refine 端点在流结束后需发送 blueprint 数据。可用 `post_stream` 回调或将此逻辑移入 service 的 stream 输出。具体实现时选择更简洁的方式。

- [ ] **Step 5: 重构 execution endpoints (2 个 SSE 端点)**

同样使用 `stream_sse_events` 替换 boilerplate。

- [ ] **Step 6: 测试 + 提交**

```bash
cd backend && uv run ruff check src/ && uv run mypy src/ && uv run pytest --tb=short -q
git add -A && git commit -m "refactor(shared): 提取 SSE 生成器统一工具函数 (5 端点去重)"
```

---

## Task 8: async I/O 修复

**Files:**
- Modify: `backend/src/modules/agents/infrastructure/external/workspace_manager.py`
- Modify: `backend/src/modules/skills/infrastructure/external/skill_file_manager_impl.py`
- Modify: `backend/tests/modules/agents/unit/infrastructure/test_workspace_manager.py`
- Modify: `backend/tests/modules/skills/unit/infrastructure/test_skill_file_manager.py`

- [ ] **Step 1: WorkspaceManager — 封装同步操作 + asyncio.to_thread**

将 `create_workspace` 中的文件操作封装为同步私有方法:

```python
import asyncio

def _write_workspace_sync(self, workspace: Path, claude_md: str, settings_json: str) -> None:
    """同步写入 workspace 文件 — 由 asyncio.to_thread 调用。"""
    workspace.mkdir(parents=True, exist_ok=True)
    (workspace / "CLAUDE.md").write_text(claude_md, encoding="utf-8")
    claude_dir = workspace / ".claude"
    claude_dir.mkdir(exist_ok=True)
    (claude_dir / "settings.json").write_text(settings_json, encoding="utf-8")

async def create_workspace(self, dto: BlueprintDTO) -> str:
    # ... render claude_md, settings_json ...
    await asyncio.to_thread(self._write_workspace_sync, workspace, claude_md, settings_json)
    return str(workspace)
```

- [ ] **Step 2: SkillFileManagerImpl — 同样处理**

封装 `save_draft`, `publish`, `delete_draft` 中的文件操作。

- [ ] **Step 3: 更新测试 (async mock 适配)**

```bash
cd backend && uv run pytest tests/modules/agents/unit/infrastructure/test_workspace_manager.py tests/modules/skills/unit/infrastructure/test_skill_file_manager.py -v
```

- [ ] **Step 4: 全量检查 + 提交**

```bash
cd backend && uv run ruff check src/ && uv run mypy src/ && uv run pytest --tb=short -q
git add -A && git commit -m "fix(infrastructure): async 方法内同步 I/O 改为 asyncio.to_thread"
```

---

## Task 9: 前端 V1 清理

**Files:**
- Delete: `frontend/src/features/agents/ui/AgentCreateForm.tsx`
- Modify: `frontend/src/features/agents/api/types.ts`
- Modify: `frontend/src/features/agents/api/mutations.ts`
- Modify: `frontend/src/features/agents/index.ts`
- Modify: `frontend/src/features/builder/index.ts`
- Modify: `frontend/src/features/builder/model/store.ts`
- Modify: `frontend/src/features/builder/api/stream.ts`
- Modify: `frontend/src/features/builder/lib/sse.ts`
- Modify: `frontend/src/features/builder/model/types.ts`
- 更新引用 AgentCreateForm 的页面组件

- [ ] **Step 1: 确认 AgentCreateForm 的引用位置**

```bash
cd frontend && grep -r "AgentCreateForm\|useCreateAgent\|useBuilderStream\|useBuilderGeneratedConfig\|streamBuilderSSE" src/ --include="*.ts" --include="*.tsx" -l
```

- [ ] **Step 2: 删除 AgentCreateForm 组件和 V1 创建相关代码**

1. 删除 `AgentCreateForm.tsx` 文件
2. 从 `features/agents/api/types.ts` 移除 V1 `CreateAgentRequest` 类型
3. 从 `features/agents/api/mutations.ts` 移除 `useCreateAgent`
4. 从 `features/agents/index.ts` 移除相关导出
5. 引用 AgentCreateForm 的页面改为跳转 Builder 页面

- [ ] **Step 3: 清理 Builder V1 hooks 和 state**

1. `features/builder/lib/sse.ts` — 删除 `streamBuilderSSE` (V1)
2. `features/builder/api/stream.ts` — 删除 `useBuilderStream` (V1)
3. `features/builder/model/store.ts` — 删除 V1 字段: `streamContent`, `generatedConfig`, `isGenerating`
4. `features/builder/index.ts` — 移除 V1 导出

- [ ] **Step 4: 运行前端测试**

```bash
cd frontend && npm run test -- --passWithNoTests && npm run type-check
```

- [ ] **Step 5: 提交**

```bash
git add -A && git commit -m "refactor(frontend): 移除 V1 AgentCreateForm + Builder V1 hooks"
```

---

## Task 10: TestSandbox 真实执行集成

**Files:**
- Modify: `frontend/src/features/builder/ui/TestSandbox.tsx`
- Modify: `frontend/src/features/builder/ui/TestSandbox.test.tsx` (如存在)

- [ ] **Step 1: 确认 execution feature 的公开 API**

```bash
cd frontend && grep -r "export" src/features/execution/index.ts
```

确认可用的 hooks: `useCreateConversation`, `useSendMessage` 等。

- [ ] **Step 2: 替换 TestSandbox 的 mock 逻辑**

将 `setTimeout` 占位替换为真实 API 调用:

```tsx
// 复用 execution 模块的 API
import { useCreateConversation, useSendMessageStream } from '@/features/execution';

// 1. 组件 mount 时创建对话
const conversationId = useRef<number | null>(null);
const createConversation = useCreateConversation();

useEffect(() => {
    if (agentId && !conversationId.current) {
        createConversation.mutateAsync({ agentId }).then(res => {
            conversationId.current = res.id;
        });
    }
}, [agentId]);

// 2. 用户发送消息
const handleSend = async (message: string) => {
    if (!conversationId.current) return;
    await sendMessageStream({
        conversationId: conversationId.current,
        content: message,
    });
};
```

- [ ] **Step 3: 运行前端测试**

```bash
cd frontend && npm run test -- --passWithNoTests && npm run type-check
```

- [ ] **Step 4: 提交**

```bash
git add -A && git commit -m "feat(builder): TestSandbox 集成真实执行模块 (替换 mock)"
```

---

## Task 11: 清理 + 最终验证

**Files:**
- Delete: `backend/scripts/migrate_agents_to_blueprint.py`
- 修复残留的 mypy/ruff 错误

- [ ] **Step 1: 删除不再需要的文件**

```bash
rm backend/scripts/migrate_agents_to_blueprint.py
```

- [ ] **Step 2: 后端全量质量检查**

```bash
cd backend && uv run ruff check src/ && uv run ruff format --check src/ && uv run mypy src/ && uv run pytest --cov=src --cov-report=term-missing --tb=short -q
```

预期: ruff ✅ | mypy ✅ | pytest >= 85% 覆盖率 ✅

- [ ] **Step 3: 前端全量检查**

```bash
cd frontend && npm run test -- --passWithNoTests && npm run type-check && npm run lint
```

- [ ] **Step 4: 架构合规测试**

```bash
cd backend && uv run pytest tests/unit/test_architecture_compliance.py -v
```

预期: 15/15 通过

- [ ] **Step 5: 提交**

```bash
git add -A && git commit -m "chore: 清理 V1 迁移脚本 + 最终质量验证"
```

---

## 执行顺序依赖图

```
Task 1 (StrEnum) ──────────────────────────────────┐
Task 2 (Agent 实体) ───┐                           │
                       ├─► Task 3 (接口拆分) ──► Task 4 (BuilderService V1 移除)
                       │                          │
                       │   Task 7 (SSE helper) ◄──┤──► Task 5 (API 层)
                       │                          │
                       └──► Task 6 (执行路由) ◄────┘
                                                  │
Task 8 (async I/O) ──────────────────────────────┤
Task 9 (前端 V1 清理) ──► Task 10 (TestSandbox) ──┤
                                                  │
                                           Task 11 (清理+验证)
```

可并行执行: Task 1 | Task 8 | Task 7 (SSE helper 不依赖 V1 移除)
