"""Builder LLM 服务接口（外部 Agent 调用抽象）。"""

from abc import ABC, abstractmethod
from collections.abc import AsyncIterator


class IBuilderLLMService(ABC):
    """Builder LLM 服务接口，负责调用 Claude Agent 生成 Agent 配置。

    封装层 < 100 行。
    """

    @abstractmethod
    async def generate_config(self, prompt: str) -> AsyncIterator[str]:
        """根据用户 prompt 流式生成 Agent 配置。

        Yields:
            SSE 数据块（JSON 字符串片段）
        """
        ...
        # 使 mypy 满意 —— 抽象方法需要 yield 语句来推断 AsyncIterator 类型
        yield ""  # pragma: no cover
