"""MemoryAdapter 单元测试 (SDK MemorySessionManager 封装)。"""

from unittest.mock import MagicMock, patch

import pytest

from src.modules.execution.application.interfaces import MemoryItem
from src.modules.execution.infrastructure.external.memory_adapter import MemoryAdapter


def _make_adapter(*, memory_id: str = "mem-test-123", region: str = "us-east-1") -> MemoryAdapter:
    """工厂: 创建 MemoryAdapter 实例。"""
    return MemoryAdapter(memory_id=memory_id, region=region)


def _make_record(
    *,
    record_id: str = "rec-1",
    content: str = "测试内容",
    namespace: str = "agent-1",
    score: float = 0.9,
) -> MagicMock:
    """工厂: 模拟 SDK MemoryRecord (DictWrapper)。"""
    data = {"recordId": record_id, "content": content, "namespace": namespace, "score": score}
    record = MagicMock()
    record.get = lambda k, d=None: data.get(k, d)
    return record


def _make_event(*, event_id: str = "evt-abc") -> MagicMock:
    """工厂: 模拟 SDK Event (DictWrapper)。"""
    data = {"eventId": event_id}
    event = MagicMock()
    event.get = lambda k, d=None: data.get(k, d)
    return event


# -- NoOp 降级测试 --


@pytest.mark.unit
@pytest.mark.asyncio(loop_scope="class")
class TestMemoryAdapterNoOp:
    """memory_id 为空时所有操作降级为 NoOp。"""

    async def test_save_returns_empty_string(self) -> None:
        adapter = _make_adapter(memory_id="")
        result = await adapter.save_memory(agent_id=1, content="c", topic="t")
        assert result == ""

    async def test_recall_returns_empty_list(self) -> None:
        adapter = _make_adapter(memory_id="")
        result = await adapter.recall_memory(agent_id=1, query="q")
        assert result == []

    async def test_list_returns_empty_list(self) -> None:
        adapter = _make_adapter(memory_id="")
        result = await adapter.list_memories(agent_id=1)
        assert result == []

    async def test_get_returns_none(self) -> None:
        adapter = _make_adapter(memory_id="")
        result = await adapter.get_memory(agent_id=1, memory_id="rec-1")
        assert result is None

    async def test_delete_returns_false(self) -> None:
        adapter = _make_adapter(memory_id="")
        result = await adapter.delete_memory(agent_id=1, memory_id="rec-1")
        assert result is False

    async def test_extract_returns_zero(self) -> None:
        adapter = _make_adapter(memory_id="")
        result = await adapter.extract_memories(agent_id=1, conversation_content="对话内容")
        assert result == 0


# -- save_memory 测试 --


@pytest.mark.unit
@pytest.mark.asyncio(loop_scope="class")
class TestMemoryAdapterSave:
    """save_memory 测试。"""

    @patch("src.modules.execution.infrastructure.external.memory_adapter.MemorySessionManager")
    async def test_save_calls_add_turns_and_returns_event_id(self, mock_mgr_cls: MagicMock) -> None:
        mock_mgr = MagicMock()
        mock_mgr.add_turns.return_value = _make_event(event_id="evt-new")
        mock_mgr_cls.return_value = mock_mgr

        adapter = _make_adapter()
        result = await adapter.save_memory(agent_id=42, content="用户偏好简洁回复", topic="偏好")

        assert result == "evt-new"
        mock_mgr.add_turns.assert_called_once()
        call_kwargs = mock_mgr.add_turns.call_args
        assert call_kwargs.kwargs["actor_id"] == "agent-42"
        assert call_kwargs.kwargs["session_id"] == "agent-42"
        assert len(call_kwargs.kwargs["messages"]) == 1

    @patch("src.modules.execution.infrastructure.external.memory_adapter.MemorySessionManager")
    async def test_save_returns_empty_on_sdk_error(self, mock_mgr_cls: MagicMock) -> None:
        mock_mgr = MagicMock()
        mock_mgr.add_turns.side_effect = RuntimeError("SDK 错误")
        mock_mgr_cls.return_value = mock_mgr

        adapter = _make_adapter()
        result = await adapter.save_memory(agent_id=1, content="c", topic="t")
        assert result == ""


# -- recall_memory 测试 --


@pytest.mark.unit
@pytest.mark.asyncio(loop_scope="class")
class TestMemoryAdapterRecall:
    """recall_memory 测试。"""

    @patch("src.modules.execution.infrastructure.external.memory_adapter.MemorySessionManager")
    async def test_recall_returns_memory_items(self, mock_mgr_cls: MagicMock) -> None:
        mock_mgr = MagicMock()
        mock_mgr.search_long_term_memories.return_value = [
            _make_record(record_id="rec-1", content="偏好简洁", namespace="agent-42", score=0.95),
            _make_record(record_id="rec-2", content="喜欢中文", namespace="agent-42", score=0.8),
        ]
        mock_mgr_cls.return_value = mock_mgr

        adapter = _make_adapter()
        result = await adapter.recall_memory(agent_id=42, query="偏好", max_results=10)

        assert len(result) == 2
        assert isinstance(result[0], MemoryItem)
        assert result[0].memory_id == "rec-1"
        assert result[0].content == "偏好简洁"
        assert result[0].relevance_score == 0.95
        mock_mgr.search_long_term_memories.assert_called_once_with(
            query="偏好",
            namespace_prefix="agent-42",
            max_results=10,
        )

    @patch("src.modules.execution.infrastructure.external.memory_adapter.MemorySessionManager")
    async def test_recall_returns_empty_on_sdk_error(self, mock_mgr_cls: MagicMock) -> None:
        mock_mgr = MagicMock()
        mock_mgr.search_long_term_memories.side_effect = RuntimeError("SDK 错误")
        mock_mgr_cls.return_value = mock_mgr

        adapter = _make_adapter()
        result = await adapter.recall_memory(agent_id=1, query="q")
        assert result == []


# -- list_memories 测试 --


@pytest.mark.unit
@pytest.mark.asyncio(loop_scope="class")
class TestMemoryAdapterList:
    """list_memories 测试。"""

    @patch("src.modules.execution.infrastructure.external.memory_adapter.MemorySessionManager")
    async def test_list_returns_memory_items(self, mock_mgr_cls: MagicMock) -> None:
        mock_mgr = MagicMock()
        mock_mgr.list_long_term_memory_records.return_value = [
            _make_record(record_id="rec-a", content="事实1"),
        ]
        mock_mgr_cls.return_value = mock_mgr

        adapter = _make_adapter()
        result = await adapter.list_memories(agent_id=5, max_results=10)

        assert len(result) == 1
        assert result[0].memory_id == "rec-a"
        mock_mgr.list_long_term_memory_records.assert_called_once_with(
            namespace_prefix="agent-5",
            max_results=10,
        )

    @patch("src.modules.execution.infrastructure.external.memory_adapter.MemorySessionManager")
    async def test_list_returns_empty_on_error(self, mock_mgr_cls: MagicMock) -> None:
        mock_mgr = MagicMock()
        mock_mgr.list_long_term_memory_records.side_effect = RuntimeError("SDK 错误")
        mock_mgr_cls.return_value = mock_mgr

        adapter = _make_adapter()
        result = await adapter.list_memories(agent_id=1)
        assert result == []


# -- get_memory 测试 --


@pytest.mark.unit
@pytest.mark.asyncio(loop_scope="class")
class TestMemoryAdapterGet:
    """get_memory 测试。"""

    @patch("src.modules.execution.infrastructure.external.memory_adapter.MemorySessionManager")
    async def test_get_returns_memory_item(self, mock_mgr_cls: MagicMock) -> None:
        mock_mgr = MagicMock()
        mock_mgr.get_memory_record.return_value = _make_record(record_id="rec-x", content="重要信息")
        mock_mgr_cls.return_value = mock_mgr

        adapter = _make_adapter()
        result = await adapter.get_memory(agent_id=3, memory_id="rec-x")

        assert result is not None
        assert result.memory_id == "rec-x"
        assert result.content == "重要信息"
        mock_mgr.get_memory_record.assert_called_once_with(record_id="rec-x")

    @patch("src.modules.execution.infrastructure.external.memory_adapter.MemorySessionManager")
    async def test_get_returns_none_on_error(self, mock_mgr_cls: MagicMock) -> None:
        mock_mgr = MagicMock()
        mock_mgr.get_memory_record.side_effect = RuntimeError("不存在")
        mock_mgr_cls.return_value = mock_mgr

        adapter = _make_adapter()
        result = await adapter.get_memory(agent_id=1, memory_id="rec-bad")
        assert result is None


# -- delete_memory 测试 --


@pytest.mark.unit
@pytest.mark.asyncio(loop_scope="class")
class TestMemoryAdapterDelete:
    """delete_memory 测试。"""

    @patch("src.modules.execution.infrastructure.external.memory_adapter.MemorySessionManager")
    async def test_delete_returns_true_on_success(self, mock_mgr_cls: MagicMock) -> None:
        mock_mgr = MagicMock()
        mock_mgr.delete_memory_record.return_value = None
        mock_mgr_cls.return_value = mock_mgr

        adapter = _make_adapter()
        result = await adapter.delete_memory(agent_id=7, memory_id="rec-del")

        assert result is True
        mock_mgr.delete_memory_record.assert_called_once_with(record_id="rec-del")

    @patch("src.modules.execution.infrastructure.external.memory_adapter.MemorySessionManager")
    async def test_delete_returns_false_on_error(self, mock_mgr_cls: MagicMock) -> None:
        mock_mgr = MagicMock()
        mock_mgr.delete_memory_record.side_effect = RuntimeError("删除失败")
        mock_mgr_cls.return_value = mock_mgr

        adapter = _make_adapter()
        result = await adapter.delete_memory(agent_id=1, memory_id="rec-bad")
        assert result is False


# -- extract_memories 测试 --


@pytest.mark.unit
@pytest.mark.asyncio(loop_scope="class")
class TestMemoryAdapterExtract:
    """extract_memories 测试。"""

    @patch("src.modules.execution.infrastructure.external.memory_adapter.MemorySessionManager")
    async def test_extract_calls_add_turns_and_returns_one(self, mock_mgr_cls: MagicMock) -> None:
        mock_mgr = MagicMock()
        mock_mgr.add_turns.return_value = _make_event()
        mock_mgr_cls.return_value = mock_mgr

        adapter = _make_adapter()
        result = await adapter.extract_memories(agent_id=10, conversation_content="对话文本", session_id="sess-1")

        assert result == 1
        mock_mgr.add_turns.assert_called_once()
        call_kwargs = mock_mgr.add_turns.call_args.kwargs
        assert call_kwargs["actor_id"] == "agent-10"
        assert call_kwargs["session_id"] == "sess-1"

    @patch("src.modules.execution.infrastructure.external.memory_adapter.MemorySessionManager")
    async def test_extract_uses_namespace_as_default_session_id(self, mock_mgr_cls: MagicMock) -> None:
        mock_mgr = MagicMock()
        mock_mgr.add_turns.return_value = _make_event()
        mock_mgr_cls.return_value = mock_mgr

        adapter = _make_adapter()
        await adapter.extract_memories(agent_id=5, conversation_content="内容")

        call_kwargs = mock_mgr.add_turns.call_args.kwargs
        assert call_kwargs["session_id"] == "agent-5"

    @patch("src.modules.execution.infrastructure.external.memory_adapter.MemorySessionManager")
    async def test_extract_returns_zero_on_error(self, mock_mgr_cls: MagicMock) -> None:
        mock_mgr = MagicMock()
        mock_mgr.add_turns.side_effect = RuntimeError("提取失败")
        mock_mgr_cls.return_value = mock_mgr

        adapter = _make_adapter()
        result = await adapter.extract_memories(agent_id=1, conversation_content="内容")
        assert result == 0


# -- _to_memory_item 静态方法测试 --


@pytest.mark.unit
class TestToMemoryItem:
    """_to_memory_item 转换测试。"""

    def test_converts_standard_record(self) -> None:
        record = _make_record(record_id="rec-1", content="内容", namespace="agent-1", score=0.85)
        item = MemoryAdapter._to_memory_item(record)

        assert item.memory_id == "rec-1"
        assert item.content == "内容"
        assert item.topic == "agent-1"
        assert item.relevance_score == 0.85

    def test_handles_missing_fields_gracefully(self) -> None:
        """缺失字段时返回空默认值。"""
        record = MagicMock()
        record.get = lambda k, d=None: d
        item = MemoryAdapter._to_memory_item(record)

        assert item.memory_id == ""
        assert item.content == ""
        assert item.topic == ""
        assert item.relevance_score == 0.0

    def test_fallback_to_alternative_keys(self) -> None:
        """recordId 不存在时 fallback 到 memoryRecordId。"""
        data: dict[str, object] = {
            "memoryRecordId": "mrec-1",
            "text": "文本",
            "topic": "主题",
            "score": 0.7,
        }
        record = MagicMock()
        record.get = lambda k, d=None: data.get(k, d)
        item = MemoryAdapter._to_memory_item(record)

        assert item.memory_id == "mrec-1"
        assert item.content == "文本"
        assert item.topic == "主题"
        assert item.relevance_score == 0.7


# -- namespace 隔离测试 --


@pytest.mark.unit
class TestNamespaceIsolation:
    """namespace 按 agent_id 隔离。"""

    def test_namespace_format(self) -> None:
        adapter = _make_adapter()
        assert adapter._namespace(42) == "agent-42"
        assert adapter._namespace(0) == "agent-0"
