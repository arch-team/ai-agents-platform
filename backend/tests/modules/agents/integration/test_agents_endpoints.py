"""Agents API endpoint integration tests."""

from datetime import datetime
from unittest.mock import AsyncMock

import pytest
from fastapi.testclient import TestClient

from src.modules.agents.api.dependencies import get_agent_service
from src.modules.agents.application.dto.agent_dto import AgentDTO
from src.modules.agents.domain.exceptions import AgentNameDuplicateError, AgentNotFoundError
from src.modules.auth.api.dependencies import get_current_user
from src.modules.auth.application.dto.user_dto import UserDTO
from src.presentation.api.main import create_app
from src.presentation.api.providers import get_agent_creator
from src.shared.application.dtos import PagedResult
from src.shared.domain.constants import MODEL_CLAUDE_HAIKU_45
from src.shared.domain.exceptions import InvalidStateTransitionError, ValidationError


def _make_user_dto(
    *,
    user_id: int = 1,
    email: str = "test@example.com",
    name: str = "Test User",
    role: str = "developer",
    is_active: bool = True,
) -> UserDTO:
    return UserDTO(id=user_id, email=email, name=name, role=role, is_active=is_active)


def _make_agent_dto(
    *,
    agent_id: int = 1,
    name: str = "test-agent",
    description: str = "Agent 描述",
    system_prompt: str = "You are helpful.",
    status: str = "draft",
    owner_id: int = 1,
    model_id: str = MODEL_CLAUDE_HAIKU_45,
    temperature: float = 0.7,
    max_tokens: int = 2048,
    top_p: float = 1.0,
    runtime_type: str = "agent",
    enable_teams: bool = False,
    enable_memory: bool = False,
) -> AgentDTO:
    now = datetime.now()
    return AgentDTO(
        id=agent_id,
        name=name,
        description=description,
        system_prompt=system_prompt,
        status=status,
        owner_id=owner_id,
        model_id=model_id,
        temperature=temperature,
        max_tokens=max_tokens,
        top_p=top_p,
        runtime_type=runtime_type,
        enable_teams=enable_teams,
        enable_memory=enable_memory,
        created_at=now,
        updated_at=now,
    )


@pytest.fixture
def mock_service() -> AsyncMock:
    return AsyncMock()


@pytest.fixture
def mock_creator() -> AsyncMock:
    """IAgentCreator Mock (用于 POST /agents Blueprint 创建)。"""
    return AsyncMock()


@pytest.fixture
def mock_user() -> UserDTO:
    return _make_user_dto()


@pytest.fixture
def app(mock_service: AsyncMock, mock_creator: AsyncMock, mock_user: UserDTO):
    test_app = create_app()
    test_app.dependency_overrides[get_agent_service] = lambda: mock_service
    test_app.dependency_overrides[get_agent_creator] = lambda: mock_creator
    test_app.dependency_overrides[get_current_user] = lambda: mock_user
    return test_app


@pytest.fixture
def client(app) -> TestClient:
    return TestClient(app)


@pytest.mark.integration
class TestCreateAgentEndpoint:
    """POST /api/v1/agents tests."""

    def test_create_success(self, client: TestClient, mock_creator: AsyncMock, mock_service: AsyncMock) -> None:
        """201 + 返回 AgentResponse (通过 IAgentCreator 创建 Blueprint)。"""
        from src.shared.domain.interfaces.agent_creator import CreatedAgentInfo

        mock_creator.create_agent_with_blueprint.return_value = CreatedAgentInfo(
            id=1,
            name="test-agent",
            status="draft",
        )
        mock_service.get_owned_agent.return_value = _make_agent_dto()

        response = client.post(
            "/api/v1/agents",
            json={"name": "test-agent", "description": "Agent 描述"},
        )

        assert response.status_code == 201
        data = response.json()
        assert data["name"] == "test-agent"
        assert data["status"] == "draft"
        assert "config" in data
        assert data["config"]["model_id"] == MODEL_CLAUDE_HAIKU_45
        mock_creator.create_agent_with_blueprint.assert_called_once()

    def test_create_duplicate_name(self, client: TestClient, mock_creator: AsyncMock) -> None:
        """409 名称重复。"""
        mock_creator.create_agent_with_blueprint.side_effect = AgentNameDuplicateError("test-agent")

        response = client.post(
            "/api/v1/agents",
            json={"name": "test-agent"},
        )

        assert response.status_code == 409
        data = response.json()
        assert "DUPLICATE" in data["code"]

    def test_create_without_auth(self, mock_service: AsyncMock, mock_creator: AsyncMock) -> None:
        """401 未认证。"""
        test_app = create_app()
        test_app.dependency_overrides[get_agent_service] = lambda: mock_service
        test_app.dependency_overrides[get_agent_creator] = lambda: mock_creator
        unauthenticated_client = TestClient(test_app)

        response = unauthenticated_client.post(
            "/api/v1/agents",
            json={"name": "test-agent"},
        )

        assert response.status_code in (401, 403)

    def test_create_viewer_role_forbidden(self, mock_service: AsyncMock, mock_creator: AsyncMock) -> None:
        """403 VIEWER 角色无权创建 Agent。"""
        viewer_user = _make_user_dto(role="viewer")
        test_app = create_app()
        test_app.dependency_overrides[get_agent_service] = lambda: mock_service
        test_app.dependency_overrides[get_agent_creator] = lambda: mock_creator
        test_app.dependency_overrides[get_current_user] = lambda: viewer_user
        viewer_client = TestClient(test_app)

        response = viewer_client.post(
            "/api/v1/agents",
            json={"name": "test-agent"},
        )

        assert response.status_code == 403
        mock_creator.create_agent_with_blueprint.assert_not_called()

    def test_create_invalid_name_empty(self, client: TestClient) -> None:
        """422 空名称。"""
        response = client.post(
            "/api/v1/agents",
            json={"name": ""},
        )

        assert response.status_code == 422


@pytest.mark.integration
class TestListAgentsEndpoint:
    """GET /api/v1/agents tests."""

    def test_list_success(self, client: TestClient, mock_service: AsyncMock) -> None:
        """200 + 返回 AgentListResponse。"""
        mock_service.list_agents.return_value = PagedResult(
            items=[_make_agent_dto()],
            total=1,
            page=1,
            page_size=20,
        )

        response = client.get("/api/v1/agents")

        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 1
        assert len(data["items"]) == 1
        assert data["page"] == 1
        assert data["total_pages"] == 1

    def test_list_empty(self, client: TestClient, mock_service: AsyncMock) -> None:
        """200 + 空列表。"""
        mock_service.list_agents.return_value = PagedResult(
            items=[],
            total=0,
            page=1,
            page_size=20,
        )

        response = client.get("/api/v1/agents")

        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 0
        assert data["items"] == []
        assert data["total_pages"] == 0

    def test_list_with_status_filter(self, client: TestClient, mock_service: AsyncMock) -> None:
        """200 + 按状态筛选。"""
        mock_service.list_agents.return_value = PagedResult(
            items=[_make_agent_dto(status="active")],
            total=1,
            page=1,
            page_size=20,
        )

        response = client.get("/api/v1/agents?status=active")

        assert response.status_code == 200
        mock_service.list_agents.assert_called_once()
        # 验证 status 参数被传递
        call_kwargs = mock_service.list_agents.call_args
        assert call_kwargs.kwargs.get("status") is not None


@pytest.mark.integration
class TestGetAgentEndpoint:
    """GET /api/v1/agents/{id} tests."""

    def test_get_success(self, client: TestClient, mock_service: AsyncMock) -> None:
        """200 + 返回 AgentResponse。"""
        mock_service.get_owned_agent.return_value = _make_agent_dto(agent_id=42)

        response = client.get("/api/v1/agents/42")

        assert response.status_code == 200
        data = response.json()
        assert data["id"] == 42
        mock_service.get_owned_agent.assert_called_once_with(42, 1)

    def test_get_not_found(self, client: TestClient, mock_service: AsyncMock) -> None:
        """404 Agent 不存在。"""
        mock_service.get_owned_agent.side_effect = AgentNotFoundError(999)

        response = client.get("/api/v1/agents/999")

        assert response.status_code == 404
        data = response.json()
        assert "NOT_FOUND" in data["code"]


@pytest.mark.integration
class TestUpdateAgentEndpoint:
    """PUT /api/v1/agents/{id} tests."""

    def test_update_success(self, client: TestClient, mock_service: AsyncMock) -> None:
        """200 + 返回更新后的 AgentResponse。"""
        mock_service.update_agent.return_value = _make_agent_dto(name="updated-name")

        response = client.put(
            "/api/v1/agents/1",
            json={"name": "updated-name"},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "updated-name"
        mock_service.update_agent.assert_called_once()

    def test_update_non_draft_rejected(self, client: TestClient, mock_service: AsyncMock) -> None:
        """409 非 DRAFT 状态不允许更新。"""
        mock_service.update_agent.side_effect = InvalidStateTransitionError(
            entity_type="Agent",
            current_state="active",
            target_state="updated",
        )

        response = client.put(
            "/api/v1/agents/1",
            json={"name": "new-name"},
        )

        assert response.status_code == 409


@pytest.mark.integration
class TestDeleteAgentEndpoint:
    """DELETE /api/v1/agents/{id} tests."""

    def test_delete_success(self, client: TestClient, mock_service: AsyncMock) -> None:
        """204 删除成功。"""
        mock_service.delete_agent.return_value = None

        response = client.delete("/api/v1/agents/1")

        assert response.status_code == 204
        mock_service.delete_agent.assert_called_once_with(1, 1)

    def test_delete_non_draft_rejected(self, client: TestClient, mock_service: AsyncMock) -> None:
        """409 非 DRAFT 状态不允许删除。"""
        mock_service.delete_agent.side_effect = InvalidStateTransitionError(
            entity_type="Agent",
            current_state="active",
            target_state="deleted",
        )

        response = client.delete("/api/v1/agents/1")

        assert response.status_code == 409


@pytest.mark.integration
class TestActivateAgentEndpoint:
    """POST /api/v1/agents/{id}/activate tests."""

    def test_activate_success(self, client: TestClient, mock_service: AsyncMock) -> None:
        """200 + 返回激活后的 AgentResponse。"""
        mock_service.activate_agent.return_value = _make_agent_dto(status="active")

        response = client.post("/api/v1/agents/1/activate")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "active"
        mock_service.activate_agent.assert_called_once_with(1, 1)

    def test_activate_without_system_prompt(
        self,
        client: TestClient,
        mock_service: AsyncMock,
    ) -> None:
        """422 缺少 system_prompt。"""
        mock_service.activate_agent.side_effect = ValidationError(
            message="Agent 缺少 system_prompt，无法激活",
        )

        response = client.post("/api/v1/agents/1/activate")

        assert response.status_code == 422


@pytest.mark.integration
class TestArchiveAgentEndpoint:
    """POST /api/v1/agents/{id}/archive tests."""

    def test_archive_success(self, client: TestClient, mock_service: AsyncMock) -> None:
        """200 + 返回归档后的 AgentResponse。"""
        mock_service.archive_agent.return_value = _make_agent_dto(status="archived")

        response = client.post("/api/v1/agents/1/archive")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "archived"
        mock_service.archive_agent.assert_called_once_with(1, 1)

    def test_archive_already_archived(
        self,
        client: TestClient,
        mock_service: AsyncMock,
    ) -> None:
        """409 已归档不可重复归档。"""
        mock_service.archive_agent.side_effect = InvalidStateTransitionError(
            entity_type="Agent",
            current_state="archived",
            target_state="archived",
        )

        response = client.post("/api/v1/agents/1/archive")

        assert response.status_code == 409


@pytest.mark.integration
class TestAgentsEndpointsStructure:
    """Agents endpoint route structure tests."""

    def test_agents_list_endpoint_exists(self, app) -> None:
        routes = [r.path for r in app.routes]
        assert "/api/v1/agents" in routes

    def test_agents_detail_endpoint_exists(self, app) -> None:
        routes = [r.path for r in app.routes]
        assert "/api/v1/agents/{agent_id}" in routes

    def test_activate_endpoint_exists(self, app) -> None:
        routes = [r.path for r in app.routes]
        assert "/api/v1/agents/{agent_id}/activate" in routes

    def test_archive_endpoint_exists(self, app) -> None:
        routes = [r.path for r in app.routes]
        assert "/api/v1/agents/{agent_id}/archive" in routes
