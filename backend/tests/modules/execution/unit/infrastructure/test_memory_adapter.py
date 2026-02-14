"""MemoryAdapter 单元测试。"""

from unittest.mock import MagicMock, patch

import pytest

from src.modules.execution.application.interfaces import MemoryItem
from src.modules.execution.infrastructure.external.memory_adapter import MemoryAdapter


# -- NoOp 降级测试 --


@pytest.mark.unit
@pytest.mark.asyncio(loop_scope="class")
class TestMemoryAdapterNoOp:
    """未配置 memory_id 时的 NoOp 降级行为。"""

    async def test_save_memory_returns_empty_string(self) -> None:
        adapter = MemoryAdapter(memory_id="", region="us-east-1")
        result = await adapter.save_memory(agent_id=1, content="测试内容", topic="测试")
        assert result == ""

    async def test_recall_memory_returns_empty_list(self) -> None:
        adapter = MemoryAdapter(memory_id="", region="us-east-1")
        result = await adapter.recall_memory(agent_id=1, query="查询")
        assert result == []

    async def test_configure_strategy_returns_false(self) -> None:
        adapter = MemoryAdapter(memory_id="", region="us-east-1")
        result = await adapter.configure_strategy()
        assert result is False

    async def test_extract_memories_returns_zero(self) -> None:
        adapter = MemoryAdapter(memory_id="", region="us-east-1")
        result = await adapter.extract_memories(agent_id=1, conversation_content="内容")
        assert result == 0


# -- save_memory 正常路径 --


@pytest.mark.unit
@pytest.mark.asyncio(loop_scope="class")
class TestMemoryAdapterSave:
    """save_memory 正常路径测试。"""

    @patch("src.modules.execution.infrastructure.external.memory_adapter.boto3")
    async def test_save_memory_success(self, mock_boto3: MagicMock) -> None:
        mock_client = MagicMock()
        mock_client.create_memory_record.return_value = {"memoryRecordId": "mem-123"}
        mock_boto3.client.return_value = mock_client

        adapter = MemoryAdapter(memory_id="memory-abc", region="us-east-1")
        adapter._get_client.cache_clear()

        result = await adapter.save_memory(agent_id=42, content="重要信息", topic="偏好")
        assert result == "mem-123"
        mock_client.create_memory_record.assert_called_once_with(
            memoryId="memory-abc",
            content="重要信息",
            metadata={"agent_id": "42", "topic": "偏好"},
        )

    @patch("src.modules.execution.infrastructure.external.memory_adapter.boto3")
    async def test_save_memory_client_error_returns_empty(self, mock_boto3: MagicMock) -> None:
        mock_client = MagicMock()
        mock_client.create_memory_record.side_effect = Exception("API 调用失败")
        mock_boto3.client.return_value = mock_client

        adapter = MemoryAdapter(memory_id="memory-abc", region="us-east-1")
        adapter._get_client.cache_clear()

        result = await adapter.save_memory(agent_id=42, content="内容", topic="主题")
        assert result == ""


# -- recall_memory 正常路径 --


@pytest.mark.unit
@pytest.mark.asyncio(loop_scope="class")
class TestMemoryAdapterRecall:
    """recall_memory 正常路径测试。"""

    @patch("src.modules.execution.infrastructure.external.memory_adapter.boto3")
    async def test_recall_memory_success(self, mock_boto3: MagicMock) -> None:
        mock_client = MagicMock()
        mock_client.search_memory.return_value = {
            "memoryRecords": [
                {
                    "memoryRecordId": "mem-1",
                    "content": "用户喜欢简洁回复",
                    "metadata": {"topic": "偏好"},
                    "score": 0.95,
                },
                {
                    "memoryRecordId": "mem-2",
                    "content": "上次讨论了架构设计",
                    "metadata": {"topic": "上下文"},
                    "score": 0.8,
                },
            ],
        }
        mock_boto3.client.return_value = mock_client

        adapter = MemoryAdapter(memory_id="memory-abc", region="us-east-1")
        adapter._get_client.cache_clear()

        result = await adapter.recall_memory(agent_id=42, query="用户偏好")
        assert len(result) == 2
        assert isinstance(result[0], MemoryItem)
        assert result[0].memory_id == "mem-1"
        assert result[0].content == "用户喜欢简洁回复"
        assert result[0].topic == "偏好"
        assert result[0].relevance_score == 0.95
        assert result[1].memory_id == "mem-2"

    @patch("src.modules.execution.infrastructure.external.memory_adapter.boto3")
    async def test_recall_memory_empty_results(self, mock_boto3: MagicMock) -> None:
        mock_client = MagicMock()
        mock_client.search_memory.return_value = {"memoryRecords": []}
        mock_boto3.client.return_value = mock_client

        adapter = MemoryAdapter(memory_id="memory-abc", region="us-east-1")
        adapter._get_client.cache_clear()

        result = await adapter.recall_memory(agent_id=42, query="不存在")
        assert result == []

    @patch("src.modules.execution.infrastructure.external.memory_adapter.boto3")
    async def test_recall_memory_client_error_returns_empty(self, mock_boto3: MagicMock) -> None:
        mock_client = MagicMock()
        mock_client.search_memory.side_effect = Exception("搜索失败")
        mock_boto3.client.return_value = mock_client

        adapter = MemoryAdapter(memory_id="memory-abc", region="us-east-1")
        adapter._get_client.cache_clear()

        result = await adapter.recall_memory(agent_id=42, query="查询")
        assert result == []

    @patch("src.modules.execution.infrastructure.external.memory_adapter.boto3")
    async def test_recall_memory_passes_max_results(self, mock_boto3: MagicMock) -> None:
        mock_client = MagicMock()
        mock_client.search_memory.return_value = {"memoryRecords": []}
        mock_boto3.client.return_value = mock_client

        adapter = MemoryAdapter(memory_id="memory-abc", region="us-east-1")
        adapter._get_client.cache_clear()

        await adapter.recall_memory(agent_id=42, query="查询", max_results=10)
        mock_client.search_memory.assert_called_once_with(
            memoryId="memory-abc",
            query="查询",
            maxResults=10,
            filter={"agent_id": "42"},
        )


# -- configure_strategy 正常路径 --


@pytest.mark.unit
@pytest.mark.asyncio(loop_scope="class")
class TestMemoryAdapterConfigureStrategy:
    """configure_strategy 正常路径测试。"""

    @patch("src.modules.execution.infrastructure.external.memory_adapter.boto3")
    async def test_configure_strategy_success(self, mock_boto3: MagicMock) -> None:
        mock_client = MagicMock()
        mock_client.update_memory.return_value = {}
        mock_boto3.client.return_value = mock_client

        adapter = MemoryAdapter(memory_id="memory-abc", region="us-east-1")
        adapter._get_client.cache_clear()

        result = await adapter.configure_strategy(strategies=["summary", "semantic"])
        assert result is True
        mock_client.update_memory.assert_called_once_with(
            memoryId="memory-abc",
            memoryStrategies=[
                {"strategyType": "summary"},
                {"strategyType": "semantic"},
            ],
        )

    @patch("src.modules.execution.infrastructure.external.memory_adapter.boto3")
    async def test_configure_strategy_default_strategies(self, mock_boto3: MagicMock) -> None:
        mock_client = MagicMock()
        mock_client.update_memory.return_value = {}
        mock_boto3.client.return_value = mock_client

        adapter = MemoryAdapter(memory_id="memory-abc", region="us-east-1")
        adapter._get_client.cache_clear()

        result = await adapter.configure_strategy()
        assert result is True
        mock_client.update_memory.assert_called_once_with(
            memoryId="memory-abc",
            memoryStrategies=[
                {"strategyType": "summary"},
                {"strategyType": "semantic"},
            ],
        )

    @patch("src.modules.execution.infrastructure.external.memory_adapter.boto3")
    async def test_configure_strategy_client_error_returns_false(self, mock_boto3: MagicMock) -> None:
        mock_client = MagicMock()
        mock_client.update_memory.side_effect = Exception("配置失败")
        mock_boto3.client.return_value = mock_client

        adapter = MemoryAdapter(memory_id="memory-abc", region="us-east-1")
        adapter._get_client.cache_clear()

        result = await adapter.configure_strategy()
        assert result is False


# -- extract_memories 正常路径 --


@pytest.mark.unit
@pytest.mark.asyncio(loop_scope="class")
class TestMemoryAdapterExtractMemories:
    """extract_memories 正常路径测试。"""

    @patch("src.modules.execution.infrastructure.external.memory_adapter.boto3")
    async def test_extract_memories_success(self, mock_boto3: MagicMock) -> None:
        mock_client = MagicMock()
        mock_client.create_memory_extraction.return_value = {"extractedCount": 3}
        mock_boto3.client.return_value = mock_client

        adapter = MemoryAdapter(memory_id="memory-abc", region="us-east-1")
        adapter._get_client.cache_clear()

        content = "user: hello\nassistant: Hi there"
        result = await adapter.extract_memories(
            agent_id=42, conversation_content=content, session_id="conv-1",
        )
        assert result == 3
        mock_client.create_memory_extraction.assert_called_once_with(
            memoryId="memory-abc",
            content=content,
            metadata={"agent_id": "42", "session_id": "conv-1"},
        )

    @patch("src.modules.execution.infrastructure.external.memory_adapter.boto3")
    async def test_extract_memories_client_error_returns_zero(self, mock_boto3: MagicMock) -> None:
        mock_client = MagicMock()
        mock_client.create_memory_extraction.side_effect = Exception("提取失败")
        mock_boto3.client.return_value = mock_client

        adapter = MemoryAdapter(memory_id="memory-abc", region="us-east-1")
        adapter._get_client.cache_clear()

        result = await adapter.extract_memories(agent_id=42, conversation_content="内容")
        assert result == 0

    @patch("src.modules.execution.infrastructure.external.memory_adapter.boto3")
    async def test_extract_memories_empty_response(self, mock_boto3: MagicMock) -> None:
        mock_client = MagicMock()
        mock_client.create_memory_extraction.return_value = {}
        mock_boto3.client.return_value = mock_client

        adapter = MemoryAdapter(memory_id="memory-abc", region="us-east-1")
        adapter._get_client.cache_clear()

        result = await adapter.extract_memories(agent_id=42, conversation_content="内容")
        assert result == 0
