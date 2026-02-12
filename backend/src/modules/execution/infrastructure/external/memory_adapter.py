"""AgentCore Memory 适配器。

SDK-First: 薄封装层，通过 boto3 调用 AgentCore Memory API。
未配置 memory_id 时降级为 NoOp（save 返回空字符串，recall 返回空列表）。
"""

import asyncio
from functools import lru_cache
from typing import Any

import boto3
import structlog

from src.modules.execution.application.interfaces import MemoryItem


logger = structlog.get_logger(__name__)


class MemoryAdapter:
    """AgentCore Memory 读写适配器。"""

    def __init__(self, *, memory_id: str, region: str) -> None:
        self._memory_id = memory_id
        self._region = region

    @lru_cache(maxsize=1)  # noqa: B019
    def _get_client(self) -> Any:  # noqa: ANN401
        """获取 bedrock-agentcore 客户端 (懒加载单例)。"""
        return boto3.client("bedrock-agentcore", region_name=self._region)

    async def save_memory(self, agent_id: int, content: str, topic: str) -> str:
        """保存到 AgentCore Memory，返回 memory_id。

        未配置 memory_id 时降级为 NoOp。
        """
        if not self._memory_id:
            logger.debug("memory_save_skip", agent_id=agent_id, reason="memory_id 未配置")
            return ""

        try:
            client = self._get_client()
            response = await asyncio.to_thread(
                client.create_memory_record,
                memoryId=self._memory_id,
                content=content,
                metadata={"agent_id": str(agent_id), "topic": topic},
            )
        except Exception:
            logger.exception("memory_save_failed", agent_id=agent_id)
            return ""

        record_id: str = response.get("memoryRecordId", "")
        logger.info("memory_saved", agent_id=agent_id, record_id=record_id, topic=topic)
        return record_id

    async def recall_memory(
        self,
        agent_id: int,
        query: str,
        *,
        max_results: int = 5,
    ) -> list[MemoryItem]:
        """从 AgentCore Memory 检索相关记忆。

        未配置 memory_id 时降级为 NoOp。
        """
        if not self._memory_id:
            logger.debug("memory_recall_skip", agent_id=agent_id, reason="memory_id 未配置")
            return []

        try:
            client = self._get_client()
            response = await asyncio.to_thread(
                client.search_memory,
                memoryId=self._memory_id,
                query=query,
                maxResults=max_results,
                filter={"agent_id": str(agent_id)},
            )
        except Exception:
            logger.exception("memory_recall_failed", agent_id=agent_id)
            return []

        return [
            MemoryItem(
                memory_id=record.get("memoryRecordId", ""),
                content=record.get("content", ""),
                topic=record.get("metadata", {}).get("topic", ""),
                relevance_score=record.get("score", 0.0),
            )
            for record in response.get("memoryRecords", [])
        ]
