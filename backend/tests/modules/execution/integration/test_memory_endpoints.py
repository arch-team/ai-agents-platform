"""Memory API endpoint integration tests."""

from unittest.mock import AsyncMock

import pytest
from fastapi.testclient import TestClient

from src.modules.auth.api.dependencies import get_current_user
from src.modules.auth.application.dto.user_dto import UserDTO
from src.modules.execution.api.dependencies import get_memory_service
from src.modules.execution.application.interfaces import IMemoryService, MemoryItem
from src.presentation.api.main import create_app
from src.presentation.api.providers import get_agent_querier
from src.shared.domain.interfaces.agent_querier import ActiveAgentInfo, IAgentQuerier


def _make_user_dto(
    *,
    user_id: int = 1,
    email: str = "test@example.com",
    name: str = "Test User",
    role: str = "developer",
    is_active: bool = True,
) -> UserDTO:
    return UserDTO(id=user_id, email=email, name=name, role=role, is_active=is_active)


def _make_active_agent_info(*, agent_id: int = 1, enable_memory: bool = True) -> ActiveAgentInfo:
    return ActiveAgentInfo(
        id=agent_id,
        name="Test Agent",
        system_prompt="You are helpful.",
        model_id="model-1",
        temperature=0.7,
        max_tokens=2048,
        top_p=1.0,
        stop_sequences=(),
        runtime_type="agent",
        enable_teams=False,
        enable_memory=enable_memory,
        tool_ids=(),
    )


def _make_memory_item(
    *,
    memory_id: str = "mem-001",
    content: str = "用户喜欢简洁的回答",
    topic: str = "偏好",
    relevance_score: float = 0.95,
) -> MemoryItem:
    return MemoryItem(
        memory_id=memory_id,
        content=content,
        topic=topic,
        relevance_score=relevance_score,
    )


@pytest.fixture
def mock_memory_service() -> AsyncMock:
    return AsyncMock(spec=IMemoryService)


@pytest.fixture
def mock_agent_querier() -> AsyncMock:
    return AsyncMock(spec=IAgentQuerier)


@pytest.fixture
def mock_user() -> UserDTO:
    return _make_user_dto()


@pytest.fixture
def app(
    mock_memory_service: AsyncMock,
    mock_agent_querier: AsyncMock,
    mock_user: UserDTO,
):
    test_app = create_app()
    test_app.dependency_overrides[get_memory_service] = lambda: mock_memory_service
    test_app.dependency_overrides[get_agent_querier] = lambda: mock_agent_querier
    test_app.dependency_overrides[get_current_user] = lambda: mock_user
    return test_app


@pytest.fixture
def client(app) -> TestClient:
    return TestClient(app)


@pytest.mark.integration
class TestListMemoriesEndpoint:
    """GET /api/v1/agents/{agent_id}/memories tests."""

    def test_list_success(
        self,
        client: TestClient,
        mock_memory_service: AsyncMock,
        mock_agent_querier: AsyncMock,
    ) -> None:
        """200 + 返回 Memory 列表。"""
        mock_agent_querier.get_active_agent.return_value = _make_active_agent_info()
        mock_memory_service.list_memories.return_value = [
            _make_memory_item(memory_id="m1"),
            _make_memory_item(memory_id="m2"),
        ]

        response = client.get("/api/v1/agents/1/memories")

        assert response.status_code == 200
        data = response.json()
        assert len(data) == 2
        assert data[0]["memory_id"] == "m1"
        assert data[1]["memory_id"] == "m2"

    def test_list_empty(
        self,
        client: TestClient,
        mock_memory_service: AsyncMock,
        mock_agent_querier: AsyncMock,
    ) -> None:
        """200 + 空列表。"""
        mock_agent_querier.get_active_agent.return_value = _make_active_agent_info()
        mock_memory_service.list_memories.return_value = []

        response = client.get("/api/v1/agents/1/memories")

        assert response.status_code == 200
        assert response.json() == []

    def test_list_memory_not_enabled(
        self,
        client: TestClient,
        mock_agent_querier: AsyncMock,
    ) -> None:
        """400 Memory 未启用。"""
        mock_agent_querier.get_active_agent.return_value = _make_active_agent_info(enable_memory=False)

        response = client.get("/api/v1/agents/1/memories")

        assert response.status_code == 400
        data = response.json()
        assert "MEMORY_NOT_ENABLED" in data["code"]

    def test_list_agent_not_found(
        self,
        client: TestClient,
        mock_agent_querier: AsyncMock,
    ) -> None:
        """400 Agent 不存在 (querier 返回 None)。"""
        mock_agent_querier.get_active_agent.return_value = None

        response = client.get("/api/v1/agents/999/memories")

        assert response.status_code == 400

    def test_list_with_max_results(
        self,
        client: TestClient,
        mock_memory_service: AsyncMock,
        mock_agent_querier: AsyncMock,
    ) -> None:
        """200 + 传递 max_results 参数。"""
        mock_agent_querier.get_active_agent.return_value = _make_active_agent_info()
        mock_memory_service.list_memories.return_value = []

        response = client.get("/api/v1/agents/1/memories?max_results=5")

        assert response.status_code == 200
        mock_memory_service.list_memories.assert_called_once_with(1, max_results=5)


@pytest.mark.integration
class TestSaveMemoryEndpoint:
    """POST /api/v1/agents/{agent_id}/memories tests."""

    def test_save_success(
        self,
        client: TestClient,
        mock_memory_service: AsyncMock,
        mock_agent_querier: AsyncMock,
    ) -> None:
        """201 + 返回 memory_id。"""
        mock_agent_querier.get_active_agent.return_value = _make_active_agent_info()
        mock_memory_service.save_memory.return_value = "mem-new-001"

        response = client.post(
            "/api/v1/agents/1/memories",
            json={"content": "用户偏好简洁", "topic": "偏好"},
        )

        assert response.status_code == 201
        data = response.json()
        assert data["memory_id"] == "mem-new-001"
        mock_memory_service.save_memory.assert_called_once_with(1, "用户偏好简洁", "偏好")

    def test_save_memory_not_enabled(
        self,
        client: TestClient,
        mock_agent_querier: AsyncMock,
    ) -> None:
        """400 Memory 未启用。"""
        mock_agent_querier.get_active_agent.return_value = _make_active_agent_info(enable_memory=False)

        response = client.post(
            "/api/v1/agents/1/memories",
            json={"content": "test", "topic": "test"},
        )

        assert response.status_code == 400

    def test_save_empty_content_raises(
        self,
        client: TestClient,
        mock_agent_querier: AsyncMock,
    ) -> None:
        """422 内容为空。"""
        mock_agent_querier.get_active_agent.return_value = _make_active_agent_info()

        response = client.post(
            "/api/v1/agents/1/memories",
            json={"content": "", "topic": "test"},
        )

        assert response.status_code == 422

    def test_save_empty_topic_raises(
        self,
        client: TestClient,
        mock_agent_querier: AsyncMock,
    ) -> None:
        """422 主题为空。"""
        mock_agent_querier.get_active_agent.return_value = _make_active_agent_info()

        response = client.post(
            "/api/v1/agents/1/memories",
            json={"content": "some content", "topic": ""},
        )

        assert response.status_code == 422


@pytest.mark.integration
class TestSearchMemoriesEndpoint:
    """POST /api/v1/agents/{agent_id}/memories/search tests."""

    def test_search_success(
        self,
        client: TestClient,
        mock_memory_service: AsyncMock,
        mock_agent_querier: AsyncMock,
    ) -> None:
        """200 + 返回搜索结果。"""
        mock_agent_querier.get_active_agent.return_value = _make_active_agent_info()
        mock_memory_service.recall_memory.return_value = [
            _make_memory_item(memory_id="m1", relevance_score=0.95),
        ]

        response = client.post(
            "/api/v1/agents/1/memories/search",
            json={"query": "用户偏好", "max_results": 3},
        )

        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["memory_id"] == "m1"
        assert data[0]["relevance_score"] == 0.95
        mock_memory_service.recall_memory.assert_called_once_with(1, "用户偏好", max_results=3)

    def test_search_empty_results(
        self,
        client: TestClient,
        mock_memory_service: AsyncMock,
        mock_agent_querier: AsyncMock,
    ) -> None:
        """200 + 空搜索结果。"""
        mock_agent_querier.get_active_agent.return_value = _make_active_agent_info()
        mock_memory_service.recall_memory.return_value = []

        response = client.post(
            "/api/v1/agents/1/memories/search",
            json={"query": "不存在的内容"},
        )

        assert response.status_code == 200
        assert response.json() == []

    def test_search_memory_not_enabled(
        self,
        client: TestClient,
        mock_agent_querier: AsyncMock,
    ) -> None:
        """400 Memory 未启用。"""
        mock_agent_querier.get_active_agent.return_value = _make_active_agent_info(enable_memory=False)

        response = client.post(
            "/api/v1/agents/1/memories/search",
            json={"query": "test"},
        )

        assert response.status_code == 400

    def test_search_empty_query_raises(
        self,
        client: TestClient,
        mock_agent_querier: AsyncMock,
    ) -> None:
        """422 查询为空。"""
        mock_agent_querier.get_active_agent.return_value = _make_active_agent_info()

        response = client.post(
            "/api/v1/agents/1/memories/search",
            json={"query": ""},
        )

        assert response.status_code == 422


@pytest.mark.integration
class TestGetMemoryEndpoint:
    """GET /api/v1/agents/{agent_id}/memories/{memory_id} tests."""

    def test_get_success(
        self,
        client: TestClient,
        mock_memory_service: AsyncMock,
        mock_agent_querier: AsyncMock,
    ) -> None:
        """200 + 返回单条 Memory。"""
        mock_agent_querier.get_active_agent.return_value = _make_active_agent_info()
        mock_memory_service.get_memory.return_value = _make_memory_item(memory_id="mem-42")

        response = client.get("/api/v1/agents/1/memories/mem-42")

        assert response.status_code == 200
        data = response.json()
        assert data["memory_id"] == "mem-42"
        assert data["content"] == "用户喜欢简洁的回答"
        assert data["topic"] == "偏好"
        mock_memory_service.get_memory.assert_called_once_with(1, "mem-42")

    def test_get_not_found(
        self,
        client: TestClient,
        mock_memory_service: AsyncMock,
        mock_agent_querier: AsyncMock,
    ) -> None:
        """404 Memory 不存在。"""
        mock_agent_querier.get_active_agent.return_value = _make_active_agent_info()
        mock_memory_service.get_memory.return_value = None

        response = client.get("/api/v1/agents/1/memories/nonexistent")

        assert response.status_code == 404
        data = response.json()
        assert "NOT_FOUND" in data["code"]

    def test_get_memory_not_enabled(
        self,
        client: TestClient,
        mock_agent_querier: AsyncMock,
    ) -> None:
        """400 Memory 未启用。"""
        mock_agent_querier.get_active_agent.return_value = _make_active_agent_info(enable_memory=False)

        response = client.get("/api/v1/agents/1/memories/mem-42")

        assert response.status_code == 400


@pytest.mark.integration
class TestDeleteMemoryEndpoint:
    """DELETE /api/v1/agents/{agent_id}/memories/{memory_id} tests."""

    def test_delete_success(
        self,
        client: TestClient,
        mock_memory_service: AsyncMock,
        mock_agent_querier: AsyncMock,
    ) -> None:
        """204 删除成功。"""
        mock_agent_querier.get_active_agent.return_value = _make_active_agent_info()
        mock_memory_service.delete_memory.return_value = None

        response = client.delete("/api/v1/agents/1/memories/mem-42")

        assert response.status_code == 204
        mock_memory_service.delete_memory.assert_called_once_with(1, "mem-42")

    def test_delete_memory_not_enabled(
        self,
        client: TestClient,
        mock_agent_querier: AsyncMock,
    ) -> None:
        """400 Memory 未启用。"""
        mock_agent_querier.get_active_agent.return_value = _make_active_agent_info(enable_memory=False)

        response = client.delete("/api/v1/agents/1/memories/mem-42")

        assert response.status_code == 400
