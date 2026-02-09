"""Tool Catalog API endpoint 集成测试。"""

from datetime import datetime
from unittest.mock import AsyncMock

import pytest
from fastapi.testclient import TestClient

from src.modules.auth.api.dependencies import get_current_user
from src.modules.auth.application.dto.user_dto import UserDTO
from src.modules.tool_catalog.api.dependencies import get_tool_service
from src.modules.tool_catalog.application.dto.tool_dto import PagedToolDTO, ToolDTO
from src.modules.tool_catalog.domain.exceptions import (
    ToolNameDuplicateError,
    ToolNotFoundError,
)
from src.presentation.api.main import create_app
from src.shared.domain.exceptions import DomainError, InvalidStateTransitionError, ValidationError


def _make_user_dto(
    *,
    user_id: int = 1,
    email: str = "test@example.com",
    name: str = "Test User",
    role: str = "developer",
    is_active: bool = True,
) -> UserDTO:
    return UserDTO(id=user_id, email=email, name=name, role=role, is_active=is_active)


def _make_admin_user_dto() -> UserDTO:
    return _make_user_dto(role="admin")


def _make_tool_dto(
    *,
    tool_id: int = 1,
    name: str = "test-tool",
    description: str = "Tool 描述",
    tool_type: str = "mcp_server",
    version: str = "1.0.0",
    status: str = "draft",
    creator_id: int = 1,
    server_url: str = "http://localhost:3000",
    transport: str = "stdio",
    endpoint_url: str = "",
    method: str = "POST",
    runtime: str = "",
    handler: str = "",
    code_uri: str = "",
    auth_type: str = "none",
    allowed_roles: list[str] | None = None,
    reviewer_id: int | None = None,
    review_comment: str = "",
    reviewed_at: datetime | None = None,
) -> ToolDTO:
    now = datetime.now()
    return ToolDTO(
        id=tool_id,
        name=name,
        description=description,
        tool_type=tool_type,
        version=version,
        status=status,
        creator_id=creator_id,
        server_url=server_url,
        transport=transport,
        endpoint_url=endpoint_url,
        method=method,
        headers=[],
        runtime=runtime,
        handler=handler,
        code_uri=code_uri,
        auth_type=auth_type,
        auth_config=[],
        allowed_roles=allowed_roles or ["admin", "developer"],
        reviewer_id=reviewer_id,
        review_comment=review_comment,
        reviewed_at=reviewed_at,
        created_at=now,
        updated_at=now,
    )


@pytest.fixture
def mock_service() -> AsyncMock:
    return AsyncMock()


@pytest.fixture
def mock_user() -> UserDTO:
    return _make_user_dto()


@pytest.fixture
def mock_admin_user() -> UserDTO:
    return _make_admin_user_dto()


@pytest.fixture
def app(mock_service: AsyncMock, mock_user: UserDTO):  # noqa: ANN201
    test_app = create_app()
    test_app.dependency_overrides[get_tool_service] = lambda: mock_service
    test_app.dependency_overrides[get_current_user] = lambda: mock_user
    return test_app


@pytest.fixture
def client(app) -> TestClient:  # noqa: ANN001
    return TestClient(app)


@pytest.fixture
def admin_app(mock_service: AsyncMock, mock_admin_user: UserDTO):  # noqa: ANN201
    """ADMIN 角色的应用（approve/reject 需要 require_role）。"""
    test_app = create_app()
    test_app.dependency_overrides[get_tool_service] = lambda: mock_service
    test_app.dependency_overrides[get_current_user] = lambda: mock_admin_user
    return test_app


@pytest.fixture
def admin_client(admin_app) -> TestClient:  # noqa: ANN001
    return TestClient(admin_app)


# ── POST /api/v1/tools ──


@pytest.mark.integration
class TestCreateToolEndpoint:
    """POST /api/v1/tools tests."""

    def test_create_success(self, client: TestClient, mock_service: AsyncMock) -> None:
        """201 + 返回 ToolResponse。"""
        mock_service.create_tool.return_value = _make_tool_dto()

        response = client.post(
            "/api/v1/tools",
            json={"name": "test-tool", "tool_type": "mcp_server"},
        )

        assert response.status_code == 201
        data = response.json()
        assert data["name"] == "test-tool"
        assert data["status"] == "draft"
        assert "config" in data
        assert data["config"]["server_url"] == "http://localhost:3000"
        mock_service.create_tool.assert_called_once()

    def test_create_duplicate_name(self, client: TestClient, mock_service: AsyncMock) -> None:
        """409 名称重复。"""
        mock_service.create_tool.side_effect = ToolNameDuplicateError("test-tool", 1)

        response = client.post(
            "/api/v1/tools",
            json={"name": "test-tool", "tool_type": "mcp_server"},
        )

        assert response.status_code == 409
        data = response.json()
        assert "DUPLICATE" in data["code"]

    def test_create_without_auth(self, mock_service: AsyncMock) -> None:
        """401 未认证。"""
        test_app = create_app()
        test_app.dependency_overrides[get_tool_service] = lambda: mock_service
        unauthenticated_client = TestClient(test_app)

        response = unauthenticated_client.post(
            "/api/v1/tools",
            json={"name": "test-tool", "tool_type": "mcp_server"},
        )

        assert response.status_code in (401, 403)

    def test_create_invalid_name_empty(self, client: TestClient) -> None:
        """422 空名称。"""
        response = client.post(
            "/api/v1/tools",
            json={"name": "", "tool_type": "mcp_server"},
        )

        assert response.status_code == 422

    def test_create_missing_tool_type(self, client: TestClient) -> None:
        """422 缺少 tool_type。"""
        response = client.post(
            "/api/v1/tools",
            json={"name": "test-tool"},
        )

        assert response.status_code == 422


# ── GET /api/v1/tools ──


@pytest.mark.integration
class TestListToolsEndpoint:
    """GET /api/v1/tools tests."""

    def test_list_success(self, client: TestClient, mock_service: AsyncMock) -> None:
        """200 + 返回 ToolListResponse。"""
        mock_service.list_tools.return_value = PagedToolDTO(
            items=[_make_tool_dto()],
            total=1,
            page=1,
            page_size=20,
        )

        response = client.get("/api/v1/tools")

        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 1
        assert len(data["items"]) == 1
        assert data["page"] == 1
        assert data["total_pages"] == 1

    def test_list_with_status_filter(self, client: TestClient, mock_service: AsyncMock) -> None:
        """200 + 按 status 筛选。"""
        mock_service.list_tools.return_value = PagedToolDTO(
            items=[_make_tool_dto(status="approved")],
            total=1,
            page=1,
            page_size=20,
        )

        response = client.get("/api/v1/tools?status=approved")

        assert response.status_code == 200
        mock_service.list_tools.assert_called_once()

    def test_list_with_type_filter(self, client: TestClient, mock_service: AsyncMock) -> None:
        """200 + 按 type 筛选。"""
        mock_service.list_tools.return_value = PagedToolDTO(
            items=[], total=0, page=1, page_size=20,
        )

        response = client.get("/api/v1/tools?type=api")

        assert response.status_code == 200
        mock_service.list_tools.assert_called_once()

    def test_list_with_keyword_filter(self, client: TestClient, mock_service: AsyncMock) -> None:
        """200 + 按关键词筛选。"""
        mock_service.list_tools.return_value = PagedToolDTO(
            items=[], total=0, page=1, page_size=20,
        )

        response = client.get("/api/v1/tools?keyword=search")

        assert response.status_code == 200
        mock_service.list_tools.assert_called_once()


# ── GET /api/v1/tools/approved ──


@pytest.mark.integration
class TestListApprovedToolsEndpoint:
    """GET /api/v1/tools/approved tests."""

    def test_list_approved_success(self, client: TestClient, mock_service: AsyncMock) -> None:
        """200 + 返回已批准的 Tool 列表。"""
        mock_service.list_approved_tools.return_value = PagedToolDTO(
            items=[_make_tool_dto(status="approved")],
            total=1,
            page=1,
            page_size=20,
        )

        response = client.get("/api/v1/tools/approved")

        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 1
        assert len(data["items"]) == 1
        mock_service.list_approved_tools.assert_called_once()


# ── GET /api/v1/tools/{id} ──


@pytest.mark.integration
class TestGetToolEndpoint:
    """GET /api/v1/tools/{id} tests."""

    def test_get_success(self, client: TestClient, mock_service: AsyncMock) -> None:
        """200 + 返回 ToolResponse。"""
        mock_service.get_tool.return_value = _make_tool_dto(tool_id=42)

        response = client.get("/api/v1/tools/42")

        assert response.status_code == 200
        data = response.json()
        assert data["id"] == 42
        mock_service.get_tool.assert_called_once_with(42)

    def test_get_not_found(self, client: TestClient, mock_service: AsyncMock) -> None:
        """404 Tool 不存在。"""
        mock_service.get_tool.side_effect = ToolNotFoundError(999)

        response = client.get("/api/v1/tools/999")

        assert response.status_code == 404
        data = response.json()
        assert "NOT_FOUND" in data["code"]


# ── PUT /api/v1/tools/{id} ──


@pytest.mark.integration
class TestUpdateToolEndpoint:
    """PUT /api/v1/tools/{id} tests."""

    def test_update_success(self, client: TestClient, mock_service: AsyncMock) -> None:
        """200 + 返回更新后的 ToolResponse。"""
        mock_service.update_tool.return_value = _make_tool_dto(name="updated-tool")

        response = client.put(
            "/api/v1/tools/1",
            json={"name": "updated-tool"},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "updated-tool"
        mock_service.update_tool.assert_called_once()

    def test_update_non_draft_rejected(self, client: TestClient, mock_service: AsyncMock) -> None:
        """409 非 DRAFT/REJECTED 状态不允许更新。"""
        mock_service.update_tool.side_effect = InvalidStateTransitionError(
            entity_type="Tool", current_state="approved", target_state="updated",
        )

        response = client.put(
            "/api/v1/tools/1",
            json={"name": "new-name"},
        )

        assert response.status_code == 409


# ── DELETE /api/v1/tools/{id} ──


@pytest.mark.integration
class TestDeleteToolEndpoint:
    """DELETE /api/v1/tools/{id} tests."""

    def test_delete_success(self, client: TestClient, mock_service: AsyncMock) -> None:
        """204 删除成功。"""
        mock_service.delete_tool.return_value = None

        response = client.delete("/api/v1/tools/1")

        assert response.status_code == 204
        mock_service.delete_tool.assert_called_once_with(1, 1)

    def test_delete_non_draft_rejected(self, client: TestClient, mock_service: AsyncMock) -> None:
        """409 非 DRAFT 状态不允许删除。"""
        mock_service.delete_tool.side_effect = InvalidStateTransitionError(
            entity_type="Tool", current_state="approved", target_state="deleted",
        )

        response = client.delete("/api/v1/tools/1")

        assert response.status_code == 409


# ── POST /api/v1/tools/{id}/submit ──


@pytest.mark.integration
class TestSubmitForReviewEndpoint:
    """POST /api/v1/tools/{id}/submit tests."""

    def test_submit_success(self, client: TestClient, mock_service: AsyncMock) -> None:
        """200 + 返回 PENDING_REVIEW 状态的 ToolResponse。"""
        mock_service.submit_for_review.return_value = _make_tool_dto(status="pending_review")

        response = client.post("/api/v1/tools/1/submit")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "pending_review"
        mock_service.submit_for_review.assert_called_once_with(1, 1)

    def test_submit_missing_config(self, client: TestClient, mock_service: AsyncMock) -> None:
        """422 缺少必要配置。"""
        mock_service.submit_for_review.side_effect = ValidationError(
            message="MCP Server 类型的 Tool 需要设置 server_url",
            field="config.server_url",
        )

        response = client.post("/api/v1/tools/1/submit")

        assert response.status_code == 422


# ── POST /api/v1/tools/{id}/approve ──


@pytest.mark.integration
class TestApproveToolEndpoint:
    """POST /api/v1/tools/{id}/approve tests."""

    def test_approve_success(
        self, admin_client: TestClient, mock_service: AsyncMock,
    ) -> None:
        """200 + 返回 APPROVED 状态的 ToolResponse (ADMIN)。"""
        mock_service.approve_tool.return_value = _make_tool_dto(
            status="approved", reviewer_id=1,
        )

        response = admin_client.post("/api/v1/tools/1/approve")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "approved"
        mock_service.approve_tool.assert_called_once()


# ── POST /api/v1/tools/{id}/reject ──


@pytest.mark.integration
class TestRejectToolEndpoint:
    """POST /api/v1/tools/{id}/reject tests."""

    def test_reject_success(
        self, admin_client: TestClient, mock_service: AsyncMock,
    ) -> None:
        """200 + 返回 REJECTED 状态的 ToolResponse (ADMIN)。"""
        mock_service.reject_tool.return_value = _make_tool_dto(
            status="rejected",
            reviewer_id=1,
            review_comment="需要改进",
        )

        response = admin_client.post(
            "/api/v1/tools/1/reject",
            json={"comment": "需要改进"},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "rejected"
        assert data["review_comment"] == "需要改进"
        mock_service.reject_tool.assert_called_once()

    def test_reject_empty_comment(self, admin_client: TestClient) -> None:
        """422 空 comment。"""
        response = admin_client.post(
            "/api/v1/tools/1/reject",
            json={"comment": ""},
        )

        assert response.status_code == 422


# ── POST /api/v1/tools/{id}/deprecate ──


@pytest.mark.integration
class TestDeprecateToolEndpoint:
    """POST /api/v1/tools/{id}/deprecate tests."""

    def test_deprecate_success(self, client: TestClient, mock_service: AsyncMock) -> None:
        """200 + 返回 DEPRECATED 状态的 ToolResponse。"""
        mock_service.deprecate_tool.return_value = _make_tool_dto(status="deprecated")

        response = client.post("/api/v1/tools/1/deprecate")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "deprecated"
        mock_service.deprecate_tool.assert_called_once_with(1, 1)

    def test_deprecate_non_approved_rejected(
        self, client: TestClient, mock_service: AsyncMock,
    ) -> None:
        """409 非 APPROVED 状态不允许废弃。"""
        mock_service.deprecate_tool.side_effect = InvalidStateTransitionError(
            entity_type="Tool", current_state="draft", target_state="deprecated",
        )

        response = client.post("/api/v1/tools/1/deprecate")

        assert response.status_code == 409


# ── 路由结构验证 ──


@pytest.mark.integration
class TestToolCatalogEndpointsStructure:
    """Tool Catalog endpoint route structure tests."""

    def test_tools_list_endpoint_exists(self, app) -> None:  # noqa: ANN001
        routes = [r.path for r in app.routes]
        assert "/api/v1/tools" in routes

    def test_tools_approved_endpoint_exists(self, app) -> None:  # noqa: ANN001
        routes = [r.path for r in app.routes]
        assert "/api/v1/tools/approved" in routes

    def test_tools_detail_endpoint_exists(self, app) -> None:  # noqa: ANN001
        routes = [r.path for r in app.routes]
        assert "/api/v1/tools/{tool_id}" in routes

    def test_submit_endpoint_exists(self, app) -> None:  # noqa: ANN001
        routes = [r.path for r in app.routes]
        assert "/api/v1/tools/{tool_id}/submit" in routes

    def test_approve_endpoint_exists(self, app) -> None:  # noqa: ANN001
        routes = [r.path for r in app.routes]
        assert "/api/v1/tools/{tool_id}/approve" in routes

    def test_reject_endpoint_exists(self, app) -> None:  # noqa: ANN001
        routes = [r.path for r in app.routes]
        assert "/api/v1/tools/{tool_id}/reject" in routes

    def test_deprecate_endpoint_exists(self, app) -> None:  # noqa: ANN001
        routes = [r.path for r in app.routes]
        assert "/api/v1/tools/{tool_id}/deprecate" in routes
