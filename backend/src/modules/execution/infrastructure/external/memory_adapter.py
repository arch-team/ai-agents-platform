"""AgentCore Memory 适配器。

SDK-First: 使用 bedrock_agentcore.memory.MemorySessionManager 高级 API。
未配置 memory_id 时降级为 NoOp（save 返回空字符串，recall/list 返回空列表）。
"""

import asyncio
from functools import lru_cache

import structlog
from bedrock_agentcore.memory import MemorySessionManager
from bedrock_agentcore.memory.constants import ConversationalMessage, MessageRole

from src.modules.execution.application.interfaces import MemoryItem


logger = structlog.get_logger(__name__)


class MemoryAdapter:
    """AgentCore Memory 读写适配器 (SDK MemorySessionManager 封装)。"""

    def __init__(self, *, memory_id: str, region: str) -> None:
        self._memory_id = memory_id
        self._region = region

    @lru_cache(maxsize=1)  # noqa: B019
    def _get_manager(self) -> MemorySessionManager:
        """获取 MemorySessionManager (懒加载单例)。"""
        return MemorySessionManager(memory_id=self._memory_id, region_name=self._region)

    def _namespace(self, agent_id: int) -> str:
        """按 agent_id 隔离 namespace。"""
        return f"agent-{agent_id}"

    async def save_memory(self, agent_id: int, content: str, topic: str) -> str:
        """保存到 AgentCore Memory，返回 event_id。未配置时降级 NoOp。"""
        if not self._memory_id:
            logger.debug("memory_save_skip", agent_id=agent_id, reason="memory_id 未配置")
            return ""
        try:
            mgr = self._get_manager()
            ns = self._namespace(agent_id)
            msg = ConversationalMessage(text=f"[{topic}] {content}", role=MessageRole.USER)
            event = await asyncio.to_thread(mgr.add_turns, actor_id=ns, session_id=ns, messages=[msg])
        except Exception:
            logger.exception("memory_save_failed", agent_id=agent_id)
            return ""
        else:
            event_id: str = event.get("eventId", "")
            logger.info("memory_saved", agent_id=agent_id, event_id=event_id, topic=topic)
            return event_id

    async def recall_memory(self, agent_id: int, query: str, *, max_results: int = 5) -> list[MemoryItem]:
        """从 AgentCore Memory 检索相关记忆。未配置时降级 NoOp。"""
        if not self._memory_id:
            logger.debug("memory_recall_skip", agent_id=agent_id, reason="memory_id 未配置")
            return []
        try:
            mgr = self._get_manager()
            ns = self._namespace(agent_id)
            records = await asyncio.to_thread(
                mgr.search_long_term_memories,
                query=query,
                namespace_prefix=ns,
                max_results=max_results,
            )
            return [self._to_memory_item(r) for r in records]
        except Exception:
            logger.exception("memory_recall_failed", agent_id=agent_id)
            return []

    async def list_memories(self, agent_id: int, *, max_results: int = 20) -> list[MemoryItem]:
        """列出 Agent 的长期记忆列表。"""
        if not self._memory_id:
            return []
        try:
            mgr = self._get_manager()
            ns = self._namespace(agent_id)
            records = await asyncio.to_thread(
                mgr.list_long_term_memory_records,
                namespace_prefix=ns,
                max_results=max_results,
            )
            return [self._to_memory_item(r) for r in records]
        except Exception:
            logger.exception("memory_list_failed", agent_id=agent_id)
            return []

    async def get_memory(self, agent_id: int, memory_id: str) -> MemoryItem | None:
        """获取单条记忆。"""
        if not self._memory_id:
            return None
        try:
            mgr = self._get_manager()
            record = await asyncio.to_thread(mgr.get_memory_record, record_id=memory_id)
            return self._to_memory_item(record)
        except Exception:
            logger.exception("memory_get_failed", agent_id=agent_id, memory_id=memory_id)
            return None

    async def delete_memory(self, agent_id: int, memory_id: str) -> bool:
        """删除单条记忆。"""
        if not self._memory_id:
            return False
        try:
            mgr = self._get_manager()
            await asyncio.to_thread(mgr.delete_memory_record, record_id=memory_id)
        except Exception:
            logger.exception("memory_delete_failed", agent_id=agent_id, memory_id=memory_id)
            return False
        else:
            logger.info("memory_deleted", agent_id=agent_id, memory_id=memory_id)
            return True

    async def extract_memories(self, agent_id: int, conversation_content: str, *, session_id: str = "") -> int:
        """从对话内容中提取记忆 (通过 add_turns 写入，由 Memory 策略异步提取)。

        返回写入的 event 数。未配置时返回 0。
        """
        if not self._memory_id:
            return 0
        try:
            mgr = self._get_manager()
            ns = self._namespace(agent_id)
            sid = session_id or ns
            msg = ConversationalMessage(text=conversation_content, role=MessageRole.ASSISTANT)
            await asyncio.to_thread(mgr.add_turns, actor_id=ns, session_id=sid, messages=[msg])
        except Exception:
            logger.exception("memory_extraction_failed", agent_id=agent_id)
            return 0
        else:
            logger.info("memory_extracted", agent_id=agent_id, session_id=sid)
            return 1

    @staticmethod
    def _to_memory_item(record: object) -> MemoryItem:
        """将 SDK MemoryRecord (DictWrapper) 转换为 MemoryItem。"""
        get = getattr(record, "get", lambda _k, d=None: d)
        return MemoryItem(
            memory_id=get("recordId", "") or get("memoryRecordId", "") or "",
            content=get("content", "") or get("text", "") or "",
            topic=get("namespace", "") or get("topic", "") or "",
            relevance_score=float(get("score", 0.0) or 0.0),
        )
