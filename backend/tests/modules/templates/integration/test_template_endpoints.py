"""Template API 端点集成测试。"""

from datetime import UTC, datetime
from unittest.mock import AsyncMock

import pytest
from fastapi.testclient import TestClient

from src.modules.auth.api.dependencies import get_current_user
from src.modules.auth.application.dto.user_dto import UserDTO
from src.modules.templates.api.dependencies import get_template_service
from src.modules.templates.application.dto.template_dto import TemplateDTO
from src.modules.templates.domain.exceptions import (
    DuplicateTemplateNameError,
    TemplateNotFoundError,
)
from src.presentation.api.main import create_app
from src.shared.application.dtos import PagedResult
from src.shared.domain.exceptions import DomainError, InvalidStateTransitionError


def _make_user() -> UserDTO:
    return UserDTO(id=1, email="test@example.com", name="Test", role="developer", is_active=True)


def _now() -> datetime:
    return datetime.now(UTC)


def _make_template_dto(
    template_id: int = 1,
    name: str = "测试模板",
    status: str = "draft",
) -> TemplateDTO:
    now = _now()
    return TemplateDTO(
        id=template_id,
        name=name,
        description="测试描述",
        category="general",
        status=status,
        creator_id=1,
        system_prompt="你是一个助手",
        model_id="anthropic.claude-v3",
        temperature=0.7,
        max_tokens=4096,
        tool_ids=[],
        knowledge_base_ids=[],
        tags=["测试"],
        usage_count=0,
        is_featured=False,
        created_at=now,
        updated_at=now,
    )


@pytest.fixture
def mock_service() -> AsyncMock:
    return AsyncMock()


@pytest.fixture
def client(mock_service: AsyncMock) -> TestClient:
    app = create_app()
    app.dependency_overrides[get_current_user] = lambda: _make_user()
    app.dependency_overrides[get_template_service] = lambda: mock_service
    yield TestClient(app)
    app.dependency_overrides.clear()


@pytest.mark.integration
class TestCreateTemplateEndpoint:
    """POST /api/v1/templates 测试。"""

    def test_create_returns_201(self, client: TestClient, mock_service: AsyncMock) -> None:
        mock_service.create_template.return_value = _make_template_dto()
        resp = client.post(
            "/api/v1/templates",
            json={
                "name": "测试模板",
                "description": "测试描述",
                "category": "general",
                "system_prompt": "你是一个助手",
                "model_id": "anthropic.claude-v3",
            },
        )
        assert resp.status_code == 201
        assert resp.json()["name"] == "测试模板"
        assert resp.json()["status"] == "draft"

    def test_create_duplicate_name_returns_409(self, client: TestClient, mock_service: AsyncMock) -> None:
        mock_service.create_template.side_effect = DuplicateTemplateNameError("已存在")
        resp = client.post(
            "/api/v1/templates",
            json={
                "name": "已存在",
                "system_prompt": "提示",
                "model_id": "model-1",
            },
        )
        assert resp.status_code == 409

    def test_create_missing_required_field_returns_422(self, client: TestClient) -> None:
        resp = client.post("/api/v1/templates", json={"name": "测试"})
        assert resp.status_code == 422


@pytest.mark.integration
class TestListTemplatesEndpoint:
    """GET /api/v1/templates 测试。"""

    def test_list_returns_200(self, client: TestClient, mock_service: AsyncMock) -> None:
        mock_service.list_templates.return_value = PagedResult(
            items=[_make_template_dto()],
            total=1,
            page=1,
            page_size=20,
        )
        resp = client.get("/api/v1/templates")
        assert resp.status_code == 200
        data = resp.json()
        assert data["total"] == 1
        assert len(data["items"]) == 1
        assert "total_pages" in data

    def test_list_with_category_filter(self, client: TestClient, mock_service: AsyncMock) -> None:
        mock_service.list_templates.return_value = PagedResult(
            items=[], total=0, page=1, page_size=20,
        )
        resp = client.get("/api/v1/templates?category=code_assistant")
        assert resp.status_code == 200
        mock_service.list_templates.assert_called_once()

    def test_list_with_keyword(self, client: TestClient, mock_service: AsyncMock) -> None:
        mock_service.list_templates.return_value = PagedResult(
            items=[], total=0, page=1, page_size=20,
        )
        resp = client.get("/api/v1/templates?keyword=Python")
        assert resp.status_code == 200


@pytest.mark.integration
class TestListMyTemplatesEndpoint:
    """GET /api/v1/templates/mine 测试。"""

    def test_mine_returns_200(self, client: TestClient, mock_service: AsyncMock) -> None:
        mock_service.list_my_templates.return_value = PagedResult(
            items=[_make_template_dto()],
            total=1,
            page=1,
            page_size=20,
        )
        resp = client.get("/api/v1/templates/mine")
        assert resp.status_code == 200
        assert resp.json()["total"] == 1


@pytest.mark.integration
class TestGetTemplateEndpoint:
    """GET /api/v1/templates/{id} 测试。"""

    def test_get_returns_200(self, client: TestClient, mock_service: AsyncMock) -> None:
        mock_service.get_template.return_value = _make_template_dto()
        resp = client.get("/api/v1/templates/1")
        assert resp.status_code == 200
        assert resp.json()["id"] == 1

    def test_get_not_found_returns_404(self, client: TestClient, mock_service: AsyncMock) -> None:
        mock_service.get_template.side_effect = TemplateNotFoundError(999)
        resp = client.get("/api/v1/templates/999")
        assert resp.status_code == 404


@pytest.mark.integration
class TestUpdateTemplateEndpoint:
    """PUT /api/v1/templates/{id} 测试。"""

    def test_update_returns_200(self, client: TestClient, mock_service: AsyncMock) -> None:
        mock_service.update_template.return_value = _make_template_dto(name="新名称")
        resp = client.put("/api/v1/templates/1", json={"name": "新名称"})
        assert resp.status_code == 200
        assert resp.json()["name"] == "新名称"

    def test_update_non_draft_returns_409(self, client: TestClient, mock_service: AsyncMock) -> None:
        mock_service.update_template.side_effect = InvalidStateTransitionError(
            entity_type="Template", current_state="published", target_state="update",
        )
        resp = client.put("/api/v1/templates/1", json={"name": "新名称"})
        assert resp.status_code == 409

    def test_update_forbidden_returns_domain_error(self, client: TestClient, mock_service: AsyncMock) -> None:
        mock_service.update_template.side_effect = DomainError(
            message="无权操作此模板", code="FORBIDDEN_TEMPLATE",
        )
        resp = client.put("/api/v1/templates/1", json={"name": "新名称"})
        assert resp.status_code == 500 or resp.status_code == 400  # DomainError 默认映射


@pytest.mark.integration
class TestDeleteTemplateEndpoint:
    """DELETE /api/v1/templates/{id} 测试。"""

    def test_delete_returns_204(self, client: TestClient, mock_service: AsyncMock) -> None:
        mock_service.delete_template.return_value = None
        resp = client.delete("/api/v1/templates/1")
        assert resp.status_code == 204

    def test_delete_not_found_returns_404(self, client: TestClient, mock_service: AsyncMock) -> None:
        mock_service.delete_template.side_effect = TemplateNotFoundError(999)
        resp = client.delete("/api/v1/templates/999")
        assert resp.status_code == 404


@pytest.mark.integration
class TestPublishTemplateEndpoint:
    """POST /api/v1/templates/{id}/publish 测试。"""

    def test_publish_returns_200(self, client: TestClient, mock_service: AsyncMock) -> None:
        mock_service.publish_template.return_value = _make_template_dto(status="published")
        resp = client.post("/api/v1/templates/1/publish")
        assert resp.status_code == 200
        assert resp.json()["status"] == "published"

    def test_publish_already_published_returns_409(self, client: TestClient, mock_service: AsyncMock) -> None:
        mock_service.publish_template.side_effect = InvalidStateTransitionError(
            entity_type="Template", current_state="published", target_state="published",
        )
        resp = client.post("/api/v1/templates/1/publish")
        assert resp.status_code == 409


@pytest.mark.integration
class TestArchiveTemplateEndpoint:
    """POST /api/v1/templates/{id}/archive 测试。"""

    def test_archive_returns_200(self, client: TestClient, mock_service: AsyncMock) -> None:
        mock_service.archive_template.return_value = _make_template_dto(status="archived")
        resp = client.post("/api/v1/templates/1/archive")
        assert resp.status_code == 200
        assert resp.json()["status"] == "archived"

    def test_archive_from_draft_returns_409(self, client: TestClient, mock_service: AsyncMock) -> None:
        mock_service.archive_template.side_effect = InvalidStateTransitionError(
            entity_type="Template", current_state="draft", target_state="archived",
        )
        resp = client.post("/api/v1/templates/1/archive")
        assert resp.status_code == 409
