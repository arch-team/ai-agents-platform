"""跨模块 Agent 创建接口。

builder 模块依赖此接口创建 Agent，
避免直接导入 agents 模块，遵循模块隔离规则。
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import StrEnum


class GuardrailSeverity(StrEnum):
    """安全护栏严重级别。"""

    WARN = "warn"
    BLOCK = "block"


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
    severity: GuardrailSeverity = GuardrailSeverity.WARN


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
    """跨模块 Agent 创建接口 (ISP: 生命周期操作移至 IAgentLifecycle)。"""

    @abstractmethod
    async def create_agent(self, request: CreateAgentRequest, owner_id: int) -> CreatedAgentInfo:
        """V1: 创建简单 Agent (system_prompt 模式)。"""
        ...

    @abstractmethod
    async def create_agent_with_blueprint(
        self,
        request: CreateAgentWithBlueprintRequest,
        owner_id: int,
    ) -> CreatedAgentInfo:
        """V2: 创建带 Blueprint 的 Agent (workspace 模式)。"""
        ...
