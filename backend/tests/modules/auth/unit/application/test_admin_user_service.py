"""Admin 用户管理 Service 测试。"""

from unittest.mock import AsyncMock

import pytest

from src.modules.auth.application.dto.user_dto import (
    AdminCreateUserDTO,
    ChangeRoleDTO,
    UserListDTO,
)
from src.modules.auth.domain.entities.user import User
from src.modules.auth.domain.exceptions import (
    AuthorizationError,
    UserAlreadyExistsError,
)
from src.modules.auth.domain.repositories.user_repository import IUserRepository
from src.modules.auth.domain.value_objects.role import Role
from src.shared.domain.exceptions import EntityNotFoundError

from .conftest import make_service, make_user


@pytest.mark.unit
class TestAdminListUsers:
    """管理员列出所有用户。"""

    @pytest.mark.asyncio
    async def test_list_users_returns_paginated_result(self) -> None:
        mock_repo = AsyncMock(spec=IUserRepository)
        users = [make_user(user_id=i, email=f"user{i}@example.com") for i in range(1, 4)]
        mock_repo.list.return_value = users
        mock_repo.count.return_value = 3

        service = make_service(mock_repo)
        result = await service.list_all_users(page=1, page_size=20)

        assert isinstance(result, UserListDTO)
        assert result.total == 3
        assert len(result.items) == 3
        assert result.items[0].id == 1
        mock_repo.list.assert_called_once_with(offset=0, limit=20)

    @pytest.mark.asyncio
    async def test_list_users_page_2(self) -> None:
        mock_repo = AsyncMock(spec=IUserRepository)
        users = [make_user(user_id=21, email="user21@example.com")]
        mock_repo.list.return_value = users
        mock_repo.count.return_value = 21

        service = make_service(mock_repo)
        result = await service.list_all_users(page=2, page_size=20)

        assert result.total == 21
        assert result.total_pages == 2
        assert len(result.items) == 1
        mock_repo.list.assert_called_once_with(offset=20, limit=20)

    @pytest.mark.asyncio
    async def test_list_users_empty(self) -> None:
        mock_repo = AsyncMock(spec=IUserRepository)
        mock_repo.list.return_value = []
        mock_repo.count.return_value = 0

        service = make_service(mock_repo)
        result = await service.list_all_users(page=1, page_size=20)

        assert result.total == 0
        assert result.total_pages == 0
        assert result.items == []


@pytest.mark.unit
class TestAdminCreateUser:
    """管理员创建用户。"""

    @pytest.mark.asyncio
    async def test_create_user_with_role(self) -> None:
        mock_repo = AsyncMock(spec=IUserRepository)
        mock_repo.get_by_email.return_value = None
        mock_repo.create.side_effect = lambda u: make_user(
            email=u.email,
            name=u.name,
            role=u.role,
        )

        service = make_service(mock_repo)
        dto = AdminCreateUserDTO(
            email="admin-created@example.com",
            password="StrongPass1",
            name="New Admin User",
            role="developer",
        )
        result = await service.create_user_with_role(dto)

        assert result.email == "admin-created@example.com"
        assert result.name == "New Admin User"
        assert result.role == "developer"
        mock_repo.create.assert_called_once()

    @pytest.mark.asyncio
    async def test_create_user_default_viewer_role(self) -> None:
        mock_repo = AsyncMock(spec=IUserRepository)
        mock_repo.get_by_email.return_value = None
        mock_repo.create.side_effect = lambda u: make_user(
            email=u.email,
            name=u.name,
            role=u.role,
        )

        service = make_service(mock_repo)
        dto = AdminCreateUserDTO(
            email="viewer@example.com",
            password="StrongPass1",
            name="Viewer User",
        )
        result = await service.create_user_with_role(dto)

        assert result.role == "viewer"

    @pytest.mark.asyncio
    async def test_create_user_duplicate_email_raises(self) -> None:
        mock_repo = AsyncMock(spec=IUserRepository)
        mock_repo.get_by_email.return_value = make_user()

        service = make_service(mock_repo)
        dto = AdminCreateUserDTO(
            email="test@example.com",
            password="StrongPass1",
            name="Dup User",
        )

        with pytest.raises(UserAlreadyExistsError):
            await service.create_user_with_role(dto)

    @pytest.mark.asyncio
    async def test_create_user_hashes_password(self) -> None:
        mock_repo = AsyncMock(spec=IUserRepository)
        mock_repo.get_by_email.return_value = None
        created_user: User | None = None

        async def capture_create(user: User) -> User:
            nonlocal created_user
            created_user = user
            return make_user(email=user.email, name=user.name, role=user.role)

        mock_repo.create.side_effect = capture_create
        service = make_service(mock_repo)

        dto = AdminCreateUserDTO(
            email="new@example.com",
            password="PlainPass1",
            name="Hash Test",
        )
        await service.create_user_with_role(dto)

        assert created_user is not None
        assert created_user.hashed_password != "PlainPass1"
        assert created_user.hashed_password.startswith("$2b$")


@pytest.mark.unit
class TestAdminChangeRole:
    """管理员变更用户角色。"""

    @pytest.mark.asyncio
    async def test_change_role_success(self) -> None:
        mock_repo = AsyncMock(spec=IUserRepository)
        user = make_user(user_id=2, role=Role.VIEWER)
        mock_repo.get_by_id.return_value = user
        mock_repo.update.side_effect = lambda u: u

        service = make_service(mock_repo)
        dto = ChangeRoleDTO(user_id=2, new_role="developer")
        result = await service.change_user_role(dto, operator_id=1)

        assert result.role == "developer"
        mock_repo.update.assert_called_once()

    @pytest.mark.asyncio
    async def test_change_role_user_not_found_raises(self) -> None:
        mock_repo = AsyncMock(spec=IUserRepository)
        mock_repo.get_by_id.return_value = None

        service = make_service(mock_repo)
        dto = ChangeRoleDTO(user_id=999, new_role="admin")

        with pytest.raises(EntityNotFoundError):
            await service.change_user_role(dto, operator_id=1)

    @pytest.mark.asyncio
    async def test_change_own_role_raises(self) -> None:
        """管理员不能修改自己的角色。"""
        mock_repo = AsyncMock(spec=IUserRepository)
        user = make_user(user_id=1, role=Role.ADMIN)
        mock_repo.get_by_id.return_value = user

        service = make_service(mock_repo)
        dto = ChangeRoleDTO(user_id=1, new_role="viewer")

        with pytest.raises(AuthorizationError, match="不能修改自己的角色"):
            await service.change_user_role(dto, operator_id=1)

    @pytest.mark.asyncio
    async def test_change_role_revokes_tokens(self) -> None:
        """角色变更后应撤销目标用户的所有 Refresh Token。"""
        mock_repo = AsyncMock(spec=IUserRepository)
        mock_rt_repo = AsyncMock()
        mock_rt_repo.revoke_by_user_id.return_value = 2
        user = make_user(user_id=2, role=Role.VIEWER)
        mock_repo.get_by_id.return_value = user
        mock_repo.update.side_effect = lambda u: u

        service = make_service(mock_repo, mock_rt_repo=mock_rt_repo)
        dto = ChangeRoleDTO(user_id=2, new_role="admin")
        await service.change_user_role(dto, operator_id=1)

        mock_rt_repo.revoke_by_user_id.assert_called_once_with(2)
