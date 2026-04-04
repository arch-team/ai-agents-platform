"""Builder LLM 服务接口（外部 Agent 调用抽象）。"""

from abc import ABC, abstractmethod
from collections.abc import AsyncIterator
from dataclasses import dataclass


@dataclass(frozen=True)
class BuilderMessage:
    """Builder 对话消息。"""

    role: str  # "user" | "assistant"
    content: str


@dataclass(frozen=True)
class PlatformToolInfo:
    """平台工具信息 (用于 LLM 上下文注入)。"""

    id: int
    name: str
    description: str


@dataclass(frozen=True)
class PlatformSkillInfo:
    """平台 Skill 信息 (用于 LLM 上下文注入)。"""

    id: int
    name: str
    description: str
    category: str


@dataclass(frozen=True)
class PlatformContext:
    """平台上下文 — 注入 LLM prompt 让 AI 推荐匹配的工具和 Skills。"""

    available_tools: tuple[PlatformToolInfo, ...] = ()
    available_skills: tuple[PlatformSkillInfo, ...] = ()


class IBuilderLLMService(ABC):
    """Builder LLM 服务接口，负责调用 Claude Agent 生成 Agent 配置。

    V1: generate_config — 单轮 JSON 配置生成
    V2: generate_blueprint — 多轮 SOP 引导式 Blueprint 生成
    """

    @abstractmethod
    async def generate_config(self, prompt: str) -> AsyncIterator[str]:
        """V1: 根据用户 prompt 流式生成 Agent 配置 (JSON)。

        Yields:
            SSE 数据块（JSON 字符串片段）
        """
        ...
        yield ""  # pragma: no cover

    @abstractmethod
    async def generate_blueprint(
        self,
        messages: list[BuilderMessage],
        platform_context: PlatformContext | None = None,
    ) -> AsyncIterator[str]:
        """V2: 多轮 SOP 引导式 Blueprint 生成。

        Args:
            messages: 对话历史 (user/assistant 交替)
            platform_context: 平台可用工具和 Skills (None 时使用空上下文)

        Yields:
            SSE 数据块 (包含结构化标记的自然语言)
        """
        ...
        yield ""  # pragma: no cover
