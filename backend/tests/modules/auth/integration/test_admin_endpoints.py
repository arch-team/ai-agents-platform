"""Admin 用户管理 API 集成测试。"""

from unittest.mock import AsyncMock

import pytest
from fastapi.testclient import TestClient

from src.modules.auth.api.dependencies import get_current_user, get_user_service
from src.modules.auth.application.dto.user_dto import UserDTO, UserListDTO
from src.modules.auth.domain.exceptions import AuthorizationError, UserAlreadyExistsError
from src.presentation.api.main import create_app
from src.shared.api.middleware.rate_limit import limiter
from src.shared.domain.exceptions import EntityNotFoundError


def _make_admin_dto(*, user_id: int = 1) -> UserDTO:
    return UserDTO(id=user_id, email="admin@example.com", name="Admin", role="admin", is_active=True)


def _make_user_dto(*, user_id: int = 2, email: str = "user@example.com", role: str = "viewer") -> UserDTO:
    return UserDTO(id=user_id, email=email, name="User", role=role, is_active=True)


@pytest.fixture
def mock_service():
    return AsyncMock()


@pytest.fixture
def app(mock_service):
    test_app = create_app()
    test_app.dependency_overrides[get_user_service] = lambda: mock_service
    # 注入 admin 用户作为当前用户
    admin_dto = _make_admin_dto()
    test_app.dependency_overrides[get_current_user] = lambda: admin_dto
    limiter.reset()
    return test_app


@pytest.fixture
def client(app):
    return TestClient(app)


@pytest.mark.integration
class TestAdminListUsersEndpoint:
    """GET /api/v1/admin/users 测试。"""

    def test_list_users_success(self, client, mock_service) -> None:
        """200 + 返回分页用户列表。"""
        mock_service.list_all_users.return_value = UserListDTO(
            items=[_make_user_dto()],
            total=1,
            page=1,
            page_size=20,
            total_pages=1,
        )

        response = client.get(
            "/api/v1/admin/users",
            headers={"Authorization": "Bearer admin-token"},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 1
        assert len(data["items"]) == 1
        assert data["items"][0]["email"] == "user@example.com"

    def test_list_users_with_pagination_params(self, client, mock_service) -> None:
        """分页参数正确传递。"""
        mock_service.list_all_users.return_value = UserListDTO(
            items=[],
            total=0,
            page=2,
            page_size=10,
            total_pages=0,
        )

        response = client.get(
            "/api/v1/admin/users?page=2&page_size=10",
            headers={"Authorization": "Bearer admin-token"},
        )

        assert response.status_code == 200
        mock_service.list_all_users.assert_called_once_with(page=2, page_size=10)

    def test_list_users_forbidden_for_non_admin(self, app, mock_service) -> None:
        """非管理员用户返回 403。"""
        viewer_dto = _make_user_dto(role="viewer")
        app.dependency_overrides[get_current_user] = lambda: viewer_dto
        client = TestClient(app)

        response = client.get(
            "/api/v1/admin/users",
            headers={"Authorization": "Bearer viewer-token"},
        )

        assert response.status_code == 403


@pytest.mark.integration
class TestAdminCreateUserEndpoint:
    """POST /api/v1/admin/users 测试。"""

    def test_create_user_success(self, client, mock_service) -> None:
        """201 + 返回创建的用户。"""
        mock_service.create_user_with_role.return_value = _make_user_dto(
            email="new@example.com",
            role="developer",
        )

        response = client.post(
            "/api/v1/admin/users",
            json={
                "email": "new@example.com",
                "password": "StrongPass1",
                "name": "New User",
                "role": "developer",
            },
            headers={"Authorization": "Bearer admin-token"},
        )

        assert response.status_code == 201
        data = response.json()
        assert data["email"] == "new@example.com"
        assert data["role"] == "developer"

    def test_create_user_duplicate_email(self, client, mock_service) -> None:
        """409 邮箱已存在。"""
        mock_service.create_user_with_role.side_effect = UserAlreadyExistsError("dup@example.com")

        response = client.post(
            "/api/v1/admin/users",
            json={
                "email": "dup@example.com",
                "password": "StrongPass1",
                "name": "Dup User",
            },
            headers={"Authorization": "Bearer admin-token"},
        )

        assert response.status_code == 409

    def test_create_user_invalid_email(self, client) -> None:
        """422 无效邮箱格式。"""
        response = client.post(
            "/api/v1/admin/users",
            json={
                "email": "not-email",
                "password": "StrongPass1",
                "name": "Bad",
            },
            headers={"Authorization": "Bearer admin-token"},
        )

        assert response.status_code == 422

    def test_create_user_forbidden_for_non_admin(self, app, mock_service) -> None:
        """非管理员用户返回 403。"""
        viewer_dto = _make_user_dto(role="viewer")
        app.dependency_overrides[get_current_user] = lambda: viewer_dto
        client = TestClient(app)

        response = client.post(
            "/api/v1/admin/users",
            json={
                "email": "new@example.com",
                "password": "StrongPass1",
                "name": "New User",
            },
            headers={"Authorization": "Bearer viewer-token"},
        )

        assert response.status_code == 403


@pytest.mark.integration
class TestAdminChangeRoleEndpoint:
    """PATCH /api/v1/admin/users/{id}/role 测试。"""

    def test_change_role_success(self, client, mock_service) -> None:
        """200 + 返回更新后的用户。"""
        mock_service.change_user_role.return_value = _make_user_dto(role="admin")

        response = client.patch(
            "/api/v1/admin/users/2/role",
            json={"role": "admin"},
            headers={"Authorization": "Bearer admin-token"},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["role"] == "admin"

    def test_change_role_user_not_found(self, client, mock_service) -> None:
        """404 用户不存在。"""
        mock_service.change_user_role.side_effect = EntityNotFoundError(
            entity_type="User",
            entity_id=999,
        )

        response = client.patch(
            "/api/v1/admin/users/999/role",
            json={"role": "admin"},
            headers={"Authorization": "Bearer admin-token"},
        )

        assert response.status_code == 404

    def test_change_own_role_forbidden(self, client, mock_service) -> None:
        """403 不能修改自己的角色。"""
        mock_service.change_user_role.side_effect = AuthorizationError("不能修改自己的角色")

        response = client.patch(
            "/api/v1/admin/users/1/role",
            json={"role": "viewer"},
            headers={"Authorization": "Bearer admin-token"},
        )

        assert response.status_code == 403

    def test_change_role_invalid_role(self, client) -> None:
        """422 无效角色值。"""
        response = client.patch(
            "/api/v1/admin/users/2/role",
            json={"role": "superadmin"},
            headers={"Authorization": "Bearer admin-token"},
        )

        assert response.status_code == 422

    def test_change_role_forbidden_for_non_admin(self, app, mock_service) -> None:
        """非管理员用户返回 403。"""
        viewer_dto = _make_user_dto(role="viewer")
        app.dependency_overrides[get_current_user] = lambda: viewer_dto
        client = TestClient(app)

        response = client.patch(
            "/api/v1/admin/users/2/role",
            json={"role": "admin"},
            headers={"Authorization": "Bearer viewer-token"},
        )

        assert response.status_code == 403


@pytest.mark.integration
class TestAdminEndpointsStructure:
    """Admin 路由结构测试。"""

    def test_admin_users_route_exists(self, app) -> None:
        routes = [r.path for r in app.routes]
        assert "/api/v1/admin/users" in routes

    def test_admin_change_role_route_exists(self, app) -> None:
        routes = [r.path for r in app.routes]
        assert "/api/v1/admin/users/{user_id}/role" in routes
