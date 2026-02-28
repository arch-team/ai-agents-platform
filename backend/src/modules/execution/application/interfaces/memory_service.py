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

    async def recall_memory(self, agent_id: int, query: str, *, max_results: int = 5) -> list[MemoryItem]:
        """从 AgentCore Memory 检索相关记忆。"""
        ...

    async def list_memories(self, agent_id: int, *, max_results: int = 20) -> list[MemoryItem]:
        """列出 Agent 的长期记忆列表。"""
        ...

    async def get_memory(self, agent_id: int, memory_id: str) -> MemoryItem | None:
        """获取单条记忆，不存在返回 None。"""
        ...

    async def delete_memory(self, agent_id: int, memory_id: str) -> bool:
        """删除单条记忆，返回是否成功。"""
        ...
