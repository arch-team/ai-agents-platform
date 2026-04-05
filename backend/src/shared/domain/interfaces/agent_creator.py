"""跨模块 Agent 创建接口。

builder 模块依赖此接口创建 Agent，
避免直接导入 agents 模块，遵循模块隔离规则。
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field


# ── V1: 简单 Agent 创建 ──


@dataclass
class CreateAgentRequest:
    """V1: 创建 Agent 的跨模块传输对象（最小知识原则）。"""

    name: str
    system_prompt: str = ""
    description: str = ""
    model_id: str = ""
    temperature: float = 0.7
    max_tokens: int = 2048


@dataclass(frozen=True)
class CreatedAgentInfo:
    """已创建 Agent 的跨模块传输对象。"""

    id: int
    name: str
    status: str


# ── V2: Blueprint-based Agent 创建 ──


@dataclass(frozen=True)
class PersonaData:
    """Agent 角色定义 (跨模块值对象)。"""

    role: str
    background: str
    tone: str = ""


@dataclass(frozen=True)
class ToolBindingData:
    """Agent 工具绑定 (跨模块值对象)。"""

    tool_id: int
    display_name: str
    usage_hint: str = ""


@dataclass(frozen=True)
class GuardrailData:
    """Agent 安全护栏 (跨模块值对象)。"""

    rule: str
    severity: str = "warn"


@dataclass(frozen=True)
class BlueprintData:
    """Blueprint 数据 — 用于创建 workspace-based Agent。"""

    persona: PersonaData
    skill_ids: tuple[int, ...] = ()
    skill_paths: tuple[str, ...] = ()
    tool_bindings: tuple[ToolBindingData, ...] = ()
    guardrails: tuple[GuardrailData, ...] = ()
    memory_enabled: bool = False
    memory_retain_fields: tuple[str, ...] = ()


@dataclass
class CreateAgentWithBlueprintRequest:
    """V2: 创建带 Blueprint 的 Agent (workspace + Blueprint 记录 + Agent)。"""

    name: str
    blueprint: BlueprintData
    description: str = ""
    model_id: str = ""
    knowledge_base_ids: list[int] = field(default_factory=list)


class IAgentCreator(ABC):
    """跨模块 Agent 创建接口。"""

    @abstractmethod
    async def create_agent(self, request: CreateAgentRequest, owner_id: int) -> CreatedAgentInfo:
        """V1: 创建简单 Agent (system_prompt 模式)。"""
        ...

    async def create_agent_with_blueprint(
        self,
        request: CreateAgentWithBlueprintRequest,
        owner_id: int,
    ) -> CreatedAgentInfo:
        """V2: 创建带 Blueprint 的 Agent (workspace 模式)。

        默认实现: 回退到 V1 (从 Blueprint.persona 生成 system_prompt)。
        agents 模块的实现会覆写此方法，完整执行 workspace 创建流程。
        """
        system_prompt = f"你是{request.blueprint.persona.role}。{request.blueprint.persona.background}"
        return await self.create_agent(
            CreateAgentRequest(
                name=request.name,
                system_prompt=system_prompt,
                description=request.description,
                model_id=request.model_id,
            ),
            owner_id,
        )

    async def start_testing(self, agent_id: int, operator_id: int) -> CreatedAgentInfo:
        """触发 Agent 进入 TESTING 状态 (创建 Runtime)。

        默认实现: 无操作, 返回当前状态。
        agents 模块的实现会覆写，执行 S3 上传 + Runtime 创建。
        """
        return CreatedAgentInfo(id=agent_id, name="", status="draft")
