"""AgentCore Memory 服务接口。"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol


@dataclass(frozen=True)
class MemoryItem:
    """AgentCore Memory 检索结果。"""

    memory_id: str
    content: str
    topic: str
    relevance_score: float = 0.0


class IMemoryService(Protocol):
    """AgentCore Memory 服务抽象接口。"""

    async def save_memory(self, agent_id: int, content: str, topic: str) -> str:
        """保存到 AgentCore Memory，返回 memory_id。"""
        ...

    async def recall_memory(
        self,
        agent_id: int,
        query: str,
        *,
        max_results: int = 5,
    ) -> list[MemoryItem]:
        """从 AgentCore Memory 检索相关记忆。"""
        ...
