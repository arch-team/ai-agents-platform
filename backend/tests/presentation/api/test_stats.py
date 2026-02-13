"""Dashboard 统计端点测试。"""

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession

from src.modules.agents.infrastructure.persistence.models.agent_model import AgentModel
from src.modules.auth.api.dependencies import get_current_user
from src.modules.auth.application.dto.user_dto import UserDTO
from src.modules.execution.infrastructure.persistence.models.conversation_model import ConversationModel
from src.modules.execution.infrastructure.persistence.models.team_execution_model import TeamExecutionModel
from src.presentation.api.main import create_app
from src.shared.infrastructure.database import get_db


def _make_user(*, user_id: int = 1, role: str = "admin") -> UserDTO:
    return UserDTO(id=user_id, email="u@test.com", name="Test", role=role, is_active=True)


async def _seed_data(session: AsyncSession) -> None:
    """向数据库插入测试数据: 2 个 agent (owner_id=1), 1 个 agent (owner_id=2)。"""
    session.add_all([
        AgentModel(name="a1", owner_id=1),
        AgentModel(name="a2", owner_id=1),
        AgentModel(name="a3", owner_id=2),
    ])
    session.add_all([
        ConversationModel(agent_id=1, user_id=1),
        ConversationModel(agent_id=2, user_id=2),
    ])
    session.add_all([
        TeamExecutionModel(agent_id=1, user_id=1, prompt="p1"),
        TeamExecutionModel(agent_id=1, user_id=1, prompt="p2"),
        TeamExecutionModel(agent_id=2, user_id=2, prompt="p3"),
    ])
    await session.commit()


@pytest.mark.integration
class TestStatsSummary:
    """GET /api/v1/stats/summary 测试。"""

    @pytest.mark.anyio
    async def test_admin_sees_all_counts(self, sqlite_engine: AsyncEngine) -> None:
        """管理员用户可查看所有数据的统计。"""
        admin = _make_user(role="admin")
        app = create_app()
        factory = _override_deps(app, sqlite_engine, admin)

        async with factory() as session:
            await _seed_data(session)

        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            resp = await client.get("/api/v1/stats/summary")

        assert resp.status_code == 200
        data = resp.json()
        assert data["agents_total"] == 3
        assert data["conversations_total"] == 2
        assert data["team_executions_total"] == 3

    @pytest.mark.anyio
    async def test_regular_user_sees_own_counts(self, sqlite_engine: AsyncEngine) -> None:
        """普通用户只能查看自己的数据统计。"""
        user = _make_user(user_id=1, role="developer")
        app = create_app()
        factory = _override_deps(app, sqlite_engine, user)

        async with factory() as session:
            await _seed_data(session)

        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            resp = await client.get("/api/v1/stats/summary")

        assert resp.status_code == 200
        data = resp.json()
        assert data["agents_total"] == 2
        assert data["conversations_total"] == 1
        assert data["team_executions_total"] == 2

    @pytest.mark.anyio
    async def test_empty_database_returns_zeros(self, sqlite_engine: AsyncEngine) -> None:
        """空数据库返回全零统计。"""
        admin = _make_user(role="admin")
        app = create_app()
        _override_deps(app, sqlite_engine, admin)

        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            resp = await client.get("/api/v1/stats/summary")

        assert resp.status_code == 200
        data = resp.json()
        assert data["agents_total"] == 0
        assert data["conversations_total"] == 0
        assert data["team_executions_total"] == 0

    @pytest.mark.anyio
    async def test_unauthenticated_returns_401(self) -> None:
        """未认证请求返回 401 (无 Bearer token)。"""
        app = create_app()
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            resp = await client.get("/api/v1/stats/summary")

        # HTTPBearer 在缺少 Authorization header 时返回 403
        assert resp.status_code in (401, 403)


def _override_deps(
    app,  # noqa: ANN001
    engine: AsyncEngine,
    user: UserDTO,
):  # noqa: ANN202
    """覆盖 FastAPI 依赖，返回 session factory 用于 seeding。"""
    from sqlalchemy.ext.asyncio import async_sessionmaker

    factory = async_sessionmaker(engine, expire_on_commit=False)

    async def _get_db():  # noqa: ANN202
        async with factory() as session:
            yield session

    app.dependency_overrides[get_db] = _get_db
    app.dependency_overrides[get_current_user] = lambda: user
    return factory
