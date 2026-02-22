"""Builder API 端点集成测试。"""

from datetime import datetime
from typing import Any
from unittest.mock import AsyncMock

import pytest
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient

from src.modules.builder.api.dependencies import get_builder_service
from src.modules.builder.api.endpoints import router
from src.modules.builder.application.dto.builder_dto import BuilderSessionDTO
from src.modules.builder.application.services.builder_service import BuilderService


def _make_session_dto(
    *,
    session_id: int = 1,
    user_id: int = 100,
    status: str = "pending",
    generated_config: dict[str, Any] | None = None,
    agent_name: str | None = None,
    created_agent_id: int | None = None,
) -> BuilderSessionDTO:
    return BuilderSessionDTO(
        id=session_id,
        user_id=user_id,
        prompt="测试 prompt",
        status=status,
        generated_config=generated_config,
        agent_name=agent_name,
        created_agent_id=created_agent_id,
        created_at=datetime.now(),
        updated_at=datetime.now(),
    )


def _build_test_app(mock_service: AsyncMock) -> FastAPI:
    """构建测试用 FastAPI 应用。"""
    app = FastAPI()
    app.include_router(router)

    # 覆盖认证依赖
    from src.modules.auth.api.dependencies import get_current_user
    from src.modules.auth.application.dto.user_dto import UserDTO

    async def _mock_current_user() -> UserDTO:
        return UserDTO(id=100, email="test@test.com", name="测试", role="user", is_active=True)

    app.dependency_overrides[get_current_user] = _mock_current_user
    app.dependency_overrides[get_builder_service] = lambda: mock_service
    return app


@pytest.mark.integration
class TestBuilderEndpoints:
    """Builder API 端点测试。"""

    @pytest.fixture
    def mock_service(self) -> AsyncMock:
        return AsyncMock(spec=BuilderService)

    @pytest.fixture
    def app(self, mock_service: AsyncMock) -> FastAPI:
        return _build_test_app(mock_service)

    @pytest.mark.asyncio
    async def test_create_session_returns_201(self, app: FastAPI, mock_service: AsyncMock) -> None:
        mock_service.create_session.return_value = _make_session_dto()
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.post(
                "/api/v1/builder/sessions",
                json={"prompt": "创建 Agent"},
            )
        assert response.status_code == 201
        data = response.json()
        assert data["id"] == 1
        assert data["status"] == "pending"

    @pytest.mark.asyncio
    async def test_create_session_empty_prompt_returns_422(self, app: FastAPI) -> None:
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.post(
                "/api/v1/builder/sessions",
                json={"prompt": ""},
            )
        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_get_session_returns_200(self, app: FastAPI, mock_service: AsyncMock) -> None:
        mock_service.get_session.return_value = _make_session_dto()
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.get("/api/v1/builder/sessions/1")
        assert response.status_code == 200
        assert response.json()["id"] == 1

    @pytest.mark.asyncio
    async def test_confirm_session_returns_200(self, app: FastAPI, mock_service: AsyncMock) -> None:
        mock_service.confirm_session.return_value = _make_session_dto(
            status="confirmed",
            generated_config={"name": "测试"},
            agent_name="测试",
            created_agent_id=42,
        )
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.post(
                "/api/v1/builder/sessions/1/confirm",
                json={},
            )
        assert response.status_code == 200
        assert response.json()["created_agent_id"] == 42

    @pytest.mark.asyncio
    async def test_cancel_session_returns_200(self, app: FastAPI, mock_service: AsyncMock) -> None:
        mock_service.cancel_session.return_value = _make_session_dto(status="cancelled")
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.post("/api/v1/builder/sessions/1/cancel")
        assert response.status_code == 200
        assert response.json()["status"] == "cancelled"
