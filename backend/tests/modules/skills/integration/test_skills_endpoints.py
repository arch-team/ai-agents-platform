"""Skills API 端点集成测试。"""

from datetime import datetime
from unittest.mock import AsyncMock

import pytest
from fastapi.testclient import TestClient

from src.modules.auth.api.dependencies import get_current_user
from src.modules.auth.application.dto.user_dto import UserDTO
from src.modules.skills.api.dependencies import get_skill_service
from src.modules.skills.application.dto.skill_dto import SkillDTO
from src.modules.skills.domain.exceptions import SkillNotFoundError
from src.presentation.api.main import create_app
from src.shared.application.dtos import PagedResult
from src.shared.domain.exceptions import ForbiddenError, InvalidStateTransitionError


def _make_user_dto(*, user_id: int = 1, role: str = "developer") -> UserDTO:
    return UserDTO(id=user_id, email="test@example.com", name="测试用户", role=role, is_active=True)


def _make_skill_dto(
    *,
    skill_id: int = 1,
    name: str = "退货处理",
    status: str = "draft",
    creator_id: int = 1,
) -> SkillDTO:
    now = datetime.now()
    return SkillDTO(
        id=skill_id,
        name=name,
        description="处理退货咨询",
        category="customer_service",
        trigger_description="退货时使用",
        status=status,
        creator_id=creator_id,
        version=1,
        usage_count=0,
        file_path="drafts/return-processing",
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
def app(mock_service: AsyncMock, mock_user: UserDTO):
    test_app = create_app()
    test_app.dependency_overrides[get_skill_service] = lambda: mock_service
    test_app.dependency_overrides[get_current_user] = lambda: mock_user
    return test_app


@pytest.fixture
def client(app) -> TestClient:
    return TestClient(app)


@pytest.mark.integration
class TestCreateSkillEndpoint:
    """POST /api/v1/skills"""

    def test_create_success(self, client: TestClient, mock_service: AsyncMock) -> None:
        mock_service.create_skill.return_value = _make_skill_dto()

        response = client.post(
            "/api/v1/skills",
            json={"name": "退货处理", "description": "处理退货", "category": "customer_service"},
        )

        assert response.status_code == 201
        data = response.json()
        assert data["name"] == "退货处理"
        assert data["status"] == "draft"
        mock_service.create_skill.assert_called_once()

    def test_create_invalid_name_empty(self, client: TestClient) -> None:
        response = client.post("/api/v1/skills", json={"name": ""})
        assert response.status_code == 422


@pytest.mark.integration
class TestListSkillsEndpoint:
    """GET /api/v1/skills"""

    def test_list_success(self, client: TestClient, mock_service: AsyncMock) -> None:
        mock_service.list_published_skills.return_value = PagedResult(
            items=[_make_skill_dto(status="published")],
            total=1,
            page=1,
            page_size=20,
        )

        response = client.get("/api/v1/skills")

        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 1
        assert len(data["items"]) == 1
        assert data["total_pages"] == 1

    def test_list_with_category_filter(self, client: TestClient, mock_service: AsyncMock) -> None:
        mock_service.list_published_skills.return_value = PagedResult(
            items=[],
            total=0,
            page=1,
            page_size=20,
        )

        response = client.get("/api/v1/skills?category=customer_service")

        assert response.status_code == 200
        mock_service.list_published_skills.assert_called_once()

    def test_list_with_keyword(self, client: TestClient, mock_service: AsyncMock) -> None:
        mock_service.list_published_skills.return_value = PagedResult(
            items=[],
            total=0,
            page=1,
            page_size=20,
        )

        response = client.get("/api/v1/skills?keyword=退货")

        assert response.status_code == 200


@pytest.mark.integration
class TestListMySkillsEndpoint:
    """GET /api/v1/skills/mine"""

    def test_list_mine_success(self, client: TestClient, mock_service: AsyncMock) -> None:
        mock_service.list_my_skills.return_value = PagedResult(
            items=[_make_skill_dto()],
            total=1,
            page=1,
            page_size=20,
        )

        response = client.get("/api/v1/skills/mine")

        assert response.status_code == 200
        data = response.json()
        assert len(data["items"]) == 1


@pytest.mark.integration
class TestGetSkillEndpoint:
    """GET /api/v1/skills/{id}"""

    def test_get_success(self, client: TestClient, mock_service: AsyncMock) -> None:
        mock_service.get_skill_with_content.return_value = (_make_skill_dto(skill_id=42), "# SKILL.md 内容")

        response = client.get("/api/v1/skills/42")

        assert response.status_code == 200
        data = response.json()
        assert data["id"] == 42
        assert data["skill_md_content"] == "# SKILL.md 内容"

    def test_get_not_found(self, client: TestClient, mock_service: AsyncMock) -> None:
        mock_service.get_skill_with_content.side_effect = SkillNotFoundError(999)

        response = client.get("/api/v1/skills/999")

        assert response.status_code == 404
        assert "NOT_FOUND" in response.json()["code"]


@pytest.mark.integration
class TestUpdateSkillEndpoint:
    """PUT /api/v1/skills/{id}"""

    def test_update_success(self, client: TestClient, mock_service: AsyncMock) -> None:
        mock_service.update_skill.return_value = _make_skill_dto(name="更新后")

        response = client.put("/api/v1/skills/1", json={"name": "更新后"})

        assert response.status_code == 200
        assert response.json()["name"] == "更新后"

    def test_update_non_draft_rejected(self, client: TestClient, mock_service: AsyncMock) -> None:
        mock_service.update_skill.side_effect = InvalidStateTransitionError(
            entity_type="Skill",
            current_state="published",
            target_state="updated",
        )

        response = client.put("/api/v1/skills/1", json={"name": "x"})

        assert response.status_code == 409

    def test_update_forbidden(self, client: TestClient, mock_service: AsyncMock) -> None:
        mock_service.update_skill.side_effect = ForbiddenError(message="无权操作")

        response = client.put("/api/v1/skills/1", json={"name": "x"})

        assert response.status_code == 403


@pytest.mark.integration
class TestDeleteSkillEndpoint:
    """DELETE /api/v1/skills/{id}"""

    def test_delete_success(self, client: TestClient, mock_service: AsyncMock) -> None:
        mock_service.delete_skill.return_value = None

        response = client.delete("/api/v1/skills/1")

        assert response.status_code == 204
        mock_service.delete_skill.assert_called_once_with(1, 1)

    def test_delete_non_draft_rejected(self, client: TestClient, mock_service: AsyncMock) -> None:
        mock_service.delete_skill.side_effect = InvalidStateTransitionError(
            entity_type="Skill",
            current_state="published",
            target_state="deleted",
        )

        response = client.delete("/api/v1/skills/1")

        assert response.status_code == 409


@pytest.mark.integration
class TestPublishSkillEndpoint:
    """POST /api/v1/skills/{id}/publish"""

    def test_publish_success(self, client: TestClient, mock_service: AsyncMock) -> None:
        mock_service.publish_skill.return_value = _make_skill_dto(status="published")

        response = client.post("/api/v1/skills/1/publish")

        assert response.status_code == 200
        assert response.json()["status"] == "published"
        mock_service.publish_skill.assert_called_once_with(1, 1)


@pytest.mark.integration
class TestArchiveSkillEndpoint:
    """POST /api/v1/skills/{id}/archive"""

    def test_archive_success(self, client: TestClient, mock_service: AsyncMock) -> None:
        mock_service.archive_skill.return_value = _make_skill_dto(status="archived")

        response = client.post("/api/v1/skills/1/archive")

        assert response.status_code == 200
        assert response.json()["status"] == "archived"
        mock_service.archive_skill.assert_called_once_with(1, 1)

    def test_archive_already_archived(self, client: TestClient, mock_service: AsyncMock) -> None:
        mock_service.archive_skill.side_effect = InvalidStateTransitionError(
            entity_type="Skill",
            current_state="archived",
            target_state="archived",
        )

        response = client.post("/api/v1/skills/1/archive")

        assert response.status_code == 409


@pytest.mark.integration
class TestSkillsEndpointsStructure:
    """路由结构验证。"""

    def test_skills_routes_exist(self, app) -> None:
        routes = [r.path for r in app.routes]
        assert "/api/v1/skills" in routes
        assert "/api/v1/skills/mine" in routes
        assert "/api/v1/skills/{skill_id}" in routes
        assert "/api/v1/skills/{skill_id}/publish" in routes
        assert "/api/v1/skills/{skill_id}/archive" in routes
