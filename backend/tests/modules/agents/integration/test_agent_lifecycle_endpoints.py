"""Agent 上线/下线 API 端点集成测试 — start-testing / go-live / take-offline。"""

from datetime import datetime
from unittest.mock import AsyncMock

import pytest
from fastapi.testclient import TestClient

from src.modules.agents.api.dependencies import get_lifecycle_agent_service
from src.modules.agents.application.dto.agent_dto import AgentDTO
from src.modules.agents.domain.exceptions import AgentNotFoundError
from src.modules.auth.api.dependencies import get_current_user
from src.modules.auth.application.dto.user_dto import UserDTO
from src.presentation.api.main import create_app
from src.shared.domain.constants import MODEL_CLAUDE_HAIKU_45
from src.shared.domain.exceptions import DomainError, InvalidStateTransitionError


def _make_user_dto(*, user_id: int = 1, role: str = "developer") -> UserDTO:
    return UserDTO(id=user_id, email="test@example.com", name="Test User", role=role, is_active=True)


def _make_agent_dto(*, agent_id: int = 1, status: str = "draft", owner_id: int = 1) -> AgentDTO:
    now = datetime.now()
    return AgentDTO(
        id=agent_id,
        name="test-agent",
        description="描述",
        system_prompt="",
        status=status,
        owner_id=owner_id,
        model_id=MODEL_CLAUDE_HAIKU_45,
        temperature=0.7,
        max_tokens=2048,
        top_p=1.0,
        runtime_type="agent",
        enable_teams=False,
        enable_memory=False,
        created_at=now,
        updated_at=now,
    )


@pytest.fixture
def mock_lifecycle_service() -> AsyncMock:
    return AsyncMock()


@pytest.fixture
def mock_user() -> UserDTO:
    return _make_user_dto()


@pytest.fixture
def app(mock_lifecycle_service: AsyncMock, mock_user: UserDTO):
    test_app = create_app()
    test_app.dependency_overrides[get_lifecycle_agent_service] = lambda: mock_lifecycle_service
    test_app.dependency_overrides[get_current_user] = lambda: mock_user
    return test_app


@pytest.fixture
def client(app) -> TestClient:
    return TestClient(app)


@pytest.mark.integration
class TestStartTestingEndpoint:
    """POST /api/v1/agents/{id}/start-testing tests."""

    def test_start_testing_success(self, client: TestClient, mock_lifecycle_service: AsyncMock) -> None:
        """200 + 返回 TESTING 状态的 AgentResponse。"""
        mock_lifecycle_service.start_testing.return_value = _make_agent_dto(status="testing")

        response = client.post("/api/v1/agents/1/start-testing")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "testing"
        mock_lifecycle_service.start_testing.assert_called_once_with(1, 1)

    def test_start_testing_not_found(self, client: TestClient, mock_lifecycle_service: AsyncMock) -> None:
        """404 Agent 不存在。"""
        mock_lifecycle_service.start_testing.side_effect = AgentNotFoundError(999)

        response = client.post("/api/v1/agents/999/start-testing")

        assert response.status_code == 404

    def test_start_testing_invalid_state(self, client: TestClient, mock_lifecycle_service: AsyncMock) -> None:
        """409 非 DRAFT 状态。"""
        mock_lifecycle_service.start_testing.side_effect = InvalidStateTransitionError(
            entity_type="Agent",
            current_state="active",
            target_state="testing",
        )

        response = client.post("/api/v1/agents/1/start-testing")

        assert response.status_code == 409

    def test_start_testing_no_blueprint(self, client: TestClient, mock_lifecycle_service: AsyncMock) -> None:
        """400 没有 Blueprint (DomainError → 400)。"""
        mock_lifecycle_service.start_testing.side_effect = DomainError(
            message="Agent 没有 Blueprint, 无法开始测试",
            code="BLUEPRINT_NOT_FOUND",
        )

        response = client.post("/api/v1/agents/1/start-testing")

        assert response.status_code == 400
        data = response.json()
        assert "BLUEPRINT_NOT_FOUND" in data["code"]

    def test_start_testing_provision_failure(self, client: TestClient, mock_lifecycle_service: AsyncMock) -> None:
        """400 Runtime 创建失败 (DomainError → 400)。"""
        mock_lifecycle_service.start_testing.side_effect = DomainError(
            message="Runtime 创建失败",
            code="RUNTIME_PROVISION_ERROR",
        )

        response = client.post("/api/v1/agents/1/start-testing")

        assert response.status_code == 400


@pytest.mark.integration
class TestGoLiveEndpoint:
    """POST /api/v1/agents/{id}/go-live tests."""

    def test_go_live_success(self, client: TestClient, mock_lifecycle_service: AsyncMock) -> None:
        """200 + 返回 ACTIVE 状态。"""
        mock_lifecycle_service.go_live.return_value = _make_agent_dto(status="active")

        response = client.post("/api/v1/agents/1/go-live")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "active"
        mock_lifecycle_service.go_live.assert_called_once_with(1, 1)

    def test_go_live_not_testing(self, client: TestClient, mock_lifecycle_service: AsyncMock) -> None:
        """409 非 TESTING 状态。"""
        mock_lifecycle_service.go_live.side_effect = InvalidStateTransitionError(
            entity_type="Agent",
            current_state="draft",
            target_state="active",
        )

        response = client.post("/api/v1/agents/1/go-live")

        assert response.status_code == 409


@pytest.mark.integration
class TestTakeOfflineEndpoint:
    """POST /api/v1/agents/{id}/take-offline tests."""

    def test_take_offline_success(self, client: TestClient, mock_lifecycle_service: AsyncMock) -> None:
        """200 + 返回 ARCHIVED 状态。"""
        mock_lifecycle_service.take_offline.return_value = _make_agent_dto(status="archived")

        response = client.post("/api/v1/agents/1/take-offline")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "archived"
        mock_lifecycle_service.take_offline.assert_called_once_with(1, 1)

    def test_take_offline_not_active(self, client: TestClient, mock_lifecycle_service: AsyncMock) -> None:
        """409 非 ACTIVE 状态。"""
        mock_lifecycle_service.take_offline.side_effect = InvalidStateTransitionError(
            entity_type="Agent",
            current_state="draft",
            target_state="archived",
        )

        response = client.post("/api/v1/agents/1/take-offline")

        assert response.status_code == 409

    def test_take_offline_not_found(self, client: TestClient, mock_lifecycle_service: AsyncMock) -> None:
        """404 Agent 不存在。"""
        mock_lifecycle_service.take_offline.side_effect = AgentNotFoundError(999)

        response = client.post("/api/v1/agents/999/take-offline")

        assert response.status_code == 404


@pytest.mark.integration
class TestLifecycleEndpointsStructure:
    """Blueprint 生命周期端点路由结构验证。"""

    def test_start_testing_endpoint_exists(self, app) -> None:
        routes = [r.path for r in app.routes]
        assert "/api/v1/agents/{agent_id}/start-testing" in routes

    def test_go_live_endpoint_exists(self, app) -> None:
        routes = [r.path for r in app.routes]
        assert "/api/v1/agents/{agent_id}/go-live" in routes

    def test_take_offline_endpoint_exists(self, app) -> None:
        routes = [r.path for r in app.routes]
        assert "/api/v1/agents/{agent_id}/take-offline" in routes
