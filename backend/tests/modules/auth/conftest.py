"""auth 模块测试 Fixture。"""

from unittest.mock import AsyncMock

import pytest

from src.modules.auth.application.services.sso_service import SsoService
from src.modules.auth.domain.entities.user import User
from src.modules.auth.domain.repositories.user_repository import IUserRepository
from src.modules.auth.domain.value_objects.role import Role
from src.modules.auth.domain.value_objects.sso_provider import SsoProvider


def make_user(
    *,
    user_id: int = 1,
    email: str = "test@example.com",
    name: str = "测试用户",
    role: Role = Role.VIEWER,
    is_active: bool = True,
    sso_provider: SsoProvider = SsoProvider.INTERNAL,
    sso_subject: str | None = None,
) -> User:
    """创建测试用 User 实体。"""
    return User(
        id=user_id,
        email=email,
        hashed_password="hashed_password_placeholder",
        name=name,
        role=role,
        is_active=is_active,
        sso_provider=sso_provider,
        sso_subject=sso_subject,
    )


@pytest.fixture
def mock_user_repo() -> AsyncMock:
    return AsyncMock(spec=IUserRepository)


@pytest.fixture
def sso_service(mock_user_repo: AsyncMock) -> SsoService:
    return SsoService(
        mock_user_repo,
        sp_entity_id="https://sp.example.com",
        sp_private_key="fake-private-key",
        sp_certificate="fake-certificate",
        idp_metadata_url="https://idp.example.com/metadata",
        jwt_secret_key="test-secret-key-for-jwt-testing-only",
        jwt_algorithm="HS256",
        jwt_expire_minutes=30,
    )


@pytest.fixture
def unconfigured_sso_service(mock_user_repo: AsyncMock) -> SsoService:
    """未配置的 SsoService（用于测试优雅降级）。"""
    return SsoService(
        mock_user_repo,
        sp_entity_id="",
        sp_private_key="",
        sp_certificate="",
        idp_metadata_url="",
        jwt_secret_key="test-secret-key-for-jwt-testing-only",
    )
