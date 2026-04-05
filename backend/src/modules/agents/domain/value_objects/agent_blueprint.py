"""Agent Blueprint 值对象 — 构成 Blueprint 的不可变组件。"""

from dataclasses import dataclass


@dataclass(frozen=True)
class Persona:
    """Agent 角色定义。"""

    role: str
    background: str
    tone: str = ""


@dataclass(frozen=True)
class ToolBinding:
    """Agent 工具绑定 — 带业务语义的工具引用。"""

    tool_id: int
    display_name: str
    usage_hint: str = ""


@dataclass(frozen=True)
class MemoryConfig:
    """Agent 记忆配置。"""

    enabled: bool = False
    strategy: str = "conversation"
    retain_fields: tuple[str, ...] = ()


@dataclass(frozen=True)
class Guardrail:
    """Agent 安全护栏规则。"""

    rule: str
    severity: str = "warn"  # "warn" | "block"
