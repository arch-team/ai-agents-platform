"""BuilderSession Repository 集成测试（SQLite 内存库）。"""

import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncSession

from src.modules.builder.domain.entities.builder_session import BuilderSession
from src.modules.builder.domain.value_objects.builder_status import BuilderStatus
from src.modules.builder.infrastructure.persistence.repositories.builder_session_repository_impl import (
    BuilderSessionRepositoryImpl,
)
from tests.modules.builder.conftest import SAMPLE_GENERATED_CONFIG


@pytest.mark.integration
class TestBuilderSessionRepository:
    """BuilderSession 仓储集成测试。"""

    @pytest_asyncio.fixture
    async def repo(self, sqlite_session: AsyncSession) -> BuilderSessionRepositoryImpl:
        return BuilderSessionRepositoryImpl(session=sqlite_session)

    @pytest.mark.asyncio
    async def test_create_and_get_by_id(self, repo: BuilderSessionRepositoryImpl) -> None:
        session = BuilderSession(user_id=1, prompt="创建Agent")
        created = await repo.create(session)

        assert created.id is not None
        assert created.user_id == 1
        assert created.status == BuilderStatus.PENDING

        fetched = await repo.get_by_id(created.id)
        assert fetched is not None
        assert fetched.prompt == "创建Agent"

    @pytest.mark.asyncio
    async def test_update_status_and_config(self, repo: BuilderSessionRepositoryImpl) -> None:
        session = BuilderSession(user_id=1, prompt="测试")
        created = await repo.create(session)
        assert created.id is not None

        # 更新状态和配置
        created.status = BuilderStatus.CONFIRMED
        created.generated_config = SAMPLE_GENERATED_CONFIG
        created.agent_name = "测试Agent"
        created.touch()
        updated = await repo.update(created)

        assert updated.status == BuilderStatus.CONFIRMED
        assert updated.generated_config is not None
        assert updated.generated_config["name"] == "代码审查助手"
        assert updated.agent_name == "测试Agent"

    @pytest.mark.asyncio
    async def test_list_by_user(self, repo: BuilderSessionRepositoryImpl) -> None:
        # 创建两个不同用户的会话
        await repo.create(BuilderSession(user_id=1, prompt="用户1"))
        await repo.create(BuilderSession(user_id=1, prompt="用户1-2"))
        await repo.create(BuilderSession(user_id=2, prompt="用户2"))

        user1_sessions = await repo.list_by_user(1)
        assert len(user1_sessions) == 2

        user2_sessions = await repo.list_by_user(2)
        assert len(user2_sessions) == 1
        assert user2_sessions[0].prompt == "用户2"

    @pytest.mark.asyncio
    async def test_get_by_id_not_found(self, repo: BuilderSessionRepositoryImpl) -> None:
        result = await repo.get_by_id(999)
        assert result is None

    @pytest.mark.asyncio
    async def test_delete(self, repo: BuilderSessionRepositoryImpl) -> None:
        session = BuilderSession(user_id=1, prompt="待删除")
        created = await repo.create(session)
        assert created.id is not None

        await repo.delete(created.id)
        result = await repo.get_by_id(created.id)
        assert result is None

    @pytest.mark.asyncio
    async def test_update_created_agent_id(self, repo: BuilderSessionRepositoryImpl) -> None:
        session = BuilderSession(user_id=1, prompt="测试")
        created = await repo.create(session)
        assert created.id is not None

        created.status = BuilderStatus.CONFIRMED
        created.generated_config = SAMPLE_GENERATED_CONFIG
        created.agent_name = "测试"
        created.created_agent_id = 42
        created.touch()
        updated = await repo.update(created)

        assert updated.created_agent_id == 42
