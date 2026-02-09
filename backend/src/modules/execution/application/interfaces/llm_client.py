"""LLM 客户端接口和数据结构。"""

from abc import ABC, abstractmethod
from collections.abc import AsyncIterator
from dataclasses import dataclass


@dataclass
class LLMMessage:
    """LLM 消息数据结构。"""

    role: str  # "user" | "assistant"
    content: str


@dataclass
class LLMResponse:
    """LLM 同步响应。"""

    content: str
    input_tokens: int
    output_tokens: int


@dataclass
class LLMStreamChunk:
    """LLM 流式响应片段。"""

    content: str = ""
    done: bool = False
    input_tokens: int = 0  # 仅 done=True 时有值
    output_tokens: int = 0  # 仅 done=True 时有值


class ILLMClient(ABC):
    """LLM 客户端抽象接口。"""

    @abstractmethod
    async def invoke(
        self,
        model_id: str,
        messages: list[LLMMessage],
        *,
        system_prompt: str = "",
        temperature: float = 0.7,
        max_tokens: int = 2048,
        top_p: float = 1.0,
        stop_sequences: tuple[str, ...] = (),
    ) -> LLMResponse:
        """同步调用 LLM。"""

    @abstractmethod
    async def invoke_stream(
        self,
        model_id: str,
        messages: list[LLMMessage],
        *,
        system_prompt: str = "",
        temperature: float = 0.7,
        max_tokens: int = 2048,
        top_p: float = 1.0,
        stop_sequences: tuple[str, ...] = (),
    ) -> AsyncIterator[LLMStreamChunk]:
        """流式调用 LLM。"""
