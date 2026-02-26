"""Agent 预览端点集成测试。"""

from unittest.mock import AsyncMock

import pytest
from fastapi.testclient import TestClient

from src.modules.auth.api.dependencies import get_current_user
from src.modules.auth.application.dto.user_dto import UserDTO
from src.modules.execution.api.dependencies import get_agent_runtime
from src.modules.execution.application.interfaces.agent_runtime import AgentResponseChunk
from src.presentation.api.main import create_app
from src.presentation.api.providers import get_agent_querier
from src.shared.domain.interfaces.agent_querier import ActiveAgentInfo


def _make_user_dto(*, user_id: int = 1) -> UserDTO:
    return UserDTO(id=user_id, email="test@example.com", name="Test User", role="developer", is_active=True)


def _make_active_agent_info(
    *, agent_id: int = 1, model_id: str = "us.anthropic.claude-haiku-4-5-20251001-v1:0",
) -> ActiveAgentInfo:
    return ActiveAgentInfo(
        id=agent_id, name="test-agent", system_prompt="You are helpful.",
        model_id=model_id, temperature=0.7, max_tokens=2048, top_p=1.0,
    )


@pytest.fixture
def mock_user() -> UserDTO:
    return _make_user_dto()


@pytest.fixture
def mock_agent_querier() -> AsyncMock:
    return AsyncMock()


@pytest.fixture
def mock_agent_runtime() -> AsyncMock:
    return AsyncMock()


@pytest.fixture
def app(mock_user: UserDTO, mock_agent_querier: AsyncMock, mock_agent_runtime: AsyncMock):
    test_app = create_app()
    test_app.dependency_overrides[get_current_user] = lambda: mock_user
    test_app.dependency_overrides[get_agent_querier] = lambda: mock_agent_querier
    test_app.dependency_overrides[get_agent_runtime] = lambda: mock_agent_runtime
    return test_app


@pytest.fixture
def client(app) -> TestClient:
    return TestClient(app)


@pytest.mark.integration
class TestPreviewAgentEndpoint:
    """POST /api/v1/agents/{agent_id}/preview 集成测试。"""

    def test_preview_success(
        self, client: TestClient, mock_agent_querier: AsyncMock, mock_agent_runtime: AsyncMock,
    ) -> None:
        """200 + 返回 AgentPreviewResponse。"""
        mock_agent_querier.get_active_agent.return_value = _make_active_agent_info()
        mock_agent_runtime.execute.return_value = AgentResponseChunk(
            content="你好! 我是 AI 助手。", done=True, input_tokens=15, output_tokens=25,
        )

        response = client.post("/api/v1/agents/1/preview", json={"prompt": "你好"})

        assert response.status_code == 200
        data = response.json()
        assert data["content"] == "你好! 我是 AI 助手。"
        assert data["model_id"] == "us.anthropic.claude-haiku-4-5-20251001-v1:0"
        assert data["tokens_input"] == 15
        assert data["tokens_output"] == 25

    def test_preview_agent_not_available(self, client: TestClient, mock_agent_querier: AsyncMock) -> None:
        """409 Agent 不可用 (不存在或非 ACTIVE)。"""
        mock_agent_querier.get_active_agent.return_value = None

        response = client.post("/api/v1/agents/999/preview", json={"prompt": "你好"})

        assert response.status_code == 409

    def test_preview_draft_agent_returns_409(self, client: TestClient, mock_agent_querier: AsyncMock) -> None:
        """409 非 ACTIVE Agent。"""
        mock_agent_querier.get_active_agent.return_value = None

        response = client.post("/api/v1/agents/1/preview", json={"prompt": "你好"})

        assert response.status_code == 409

    def test_preview_empty_prompt_returns_422(self, client: TestClient) -> None:
        """422 空 prompt。"""
        response = client.post("/api/v1/agents/1/preview", json={"prompt": ""})

        assert response.status_code == 422

    def test_preview_missing_prompt_returns_422(self, client: TestClient) -> None:
        """422 缺少 prompt 字段。"""
        response = client.post("/api/v1/agents/1/preview", json={})

        assert response.status_code == 422

    def test_preview_endpoint_exists(self, app) -> None:
        """路由 /api/v1/agents/{agent_id}/preview 已注册。"""
        routes = [r.path for r in app.routes]
        assert "/api/v1/agents/{agent_id}/preview" in routes
