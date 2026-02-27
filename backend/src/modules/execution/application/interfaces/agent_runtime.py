"""Agent 运行时接口和数据结构。

支持 Agent Loop（工具调用 → 执行 → 返回结果 → 继续推理）。
ILLMClient 仅支持单轮问答，IAgentRuntime 支持完整 Agent 循环。
两者并存，由 AgentConfig.runtime_type 决定使用哪个。
"""

from abc import ABC, abstractmethod
from collections.abc import AsyncIterator
from dataclasses import dataclass, field
from typing import Any

from src.modules.execution.application.interfaces.llm_client import LLMMessage
from src.shared.domain.constants import AGENT_DEFAULT_MAX_TOKENS, AGENT_DEFAULT_TEMPERATURE


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
    temperature: float = AGENT_DEFAULT_TEMPERATURE
    max_tokens: int = AGENT_DEFAULT_MAX_TOKENS
    gateway_url: str = ""  # AgentCore Gateway MCP 端点
    memory_id: str = ""  # AgentCore Memory 资源 ID
    max_turns: int = 20  # Agent Loop 最大轮次
    cwd: str = ""  # Agent 工作目录
    enable_teams: bool = False  # 启用 Agent Teams 协作能力


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
    """Agent 运行时抽象接口。

    支持 Agent Loop（Claude Agent SDK 的 tool_use → 执行 → tool_result 循环）。
    """

    @abstractmethod
    async def execute(self, request: AgentRequest) -> AgentResponseChunk:
        """同步执行 Agent（等待完整结果）。"""

    @abstractmethod
    async def execute_stream(self, request: AgentRequest) -> AsyncIterator[AgentResponseChunk]:
        """流式执行 Agent（逐步返回结果）。"""
