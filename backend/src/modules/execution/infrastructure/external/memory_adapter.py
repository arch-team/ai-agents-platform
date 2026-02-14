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

    async def configure_strategy(self, *, strategies: list[str] | None = None) -> bool:
        """配置 AgentCore Memory 提取策略。

        strategies: ["summary", "user_preference", "semantic"]
        未配置 memory_id 时返回 False。
        """
        if not self._memory_id:
            logger.debug("memory_strategy_skip", reason="memory_id 未配置")
            return False

        try:
            client = self._get_client()
            await asyncio.to_thread(
                client.update_memory,
                memoryId=self._memory_id,
                memoryStrategies=[
                    {"strategyType": s} for s in (strategies or ["summary", "semantic"])
                ],
            )
        except Exception:
            logger.exception("memory_strategy_config_failed")
            return False

        logger.info("memory_strategy_configured", strategies=strategies)
        return True

    async def extract_memories(self, agent_id: int, conversation_content: str, *, session_id: str = "") -> int:
        """从对话内容中异步提取记忆。

        返回提取的记忆条数。未配置时返回 0。
        """
        if not self._memory_id:
            return 0

        try:
            client = self._get_client()
            response = await asyncio.to_thread(
                client.create_memory_extraction,
                memoryId=self._memory_id,
                content=conversation_content,
                metadata={"agent_id": str(agent_id), "session_id": session_id},
            )
        except Exception:
            logger.exception("memory_extraction_failed", agent_id=agent_id)
            return 0

        count: int = response.get("extractedCount", 0)
        logger.info("memory_extracted", agent_id=agent_id, count=count)
        return count
