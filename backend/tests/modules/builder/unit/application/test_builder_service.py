"""BuilderService 单元测试。"""

from unittest.mock import AsyncMock

import pytest

from src.modules.builder.application.dto.builder_dto import TriggerBuilderDTO
from src.modules.builder.application.services.builder_service import BuilderService
from src.modules.builder.domain.exceptions import BuilderSessionNotFoundError
from src.modules.builder.domain.value_objects.builder_status import BuilderStatus
from src.shared.domain.exceptions import ForbiddenError, InvalidStateTransitionError
from tests.modules.builder.conftest import make_builder_session


@pytest.mark.unit
class TestBuilderServiceCreate:
    """create_session 测试。"""

    @pytest.mark.asyncio
    async def test_create_session_returns_dto(
        self,
        builder_service: BuilderService,
        mock_session_repo: AsyncMock,
    ) -> None:
        created = make_builder_session(session_id=10, user_id=100)
        mock_session_repo.create.return_value = created

        dto = TriggerBuilderDTO(prompt="创建一个 Agent")
        result = await builder_service.create_session(dto, user_id=100)

        assert result.id == 10
        assert result.status == BuilderStatus.PENDING.value
        assert result.prompt == "创建一个代码审查 Agent"
        mock_session_repo.create.assert_called_once()


@pytest.mark.unit
class TestBuilderServiceConfirm:
    """confirm_session 测试。"""

    @pytest.mark.asyncio
    async def test_confirm_session_not_confirmed_raises(
        self,
        builder_service: BuilderService,
        mock_session_repo: AsyncMock,
    ) -> None:
        session = make_builder_session(session_id=1, user_id=100, status=BuilderStatus.PENDING)
        mock_session_repo.get_by_id.return_value = session

        with pytest.raises(InvalidStateTransitionError):
            await builder_service.confirm_session(1, 100)

    @pytest.mark.asyncio
    async def test_confirm_session_no_config_raises(
        self,
        builder_service: BuilderService,
        mock_session_repo: AsyncMock,
    ) -> None:
        session = make_builder_session(
            session_id=1,
            user_id=100,
            status=BuilderStatus.CONFIRMED,
            generated_config=None,
        )
        mock_session_repo.get_by_id.return_value = session

        with pytest.raises(InvalidStateTransitionError):
            await builder_service.confirm_session(1, 100)

    @pytest.mark.asyncio
    async def test_confirm_session_wrong_owner_raises(
        self,
        builder_service: BuilderService,
        mock_session_repo: AsyncMock,
    ) -> None:
        session = make_builder_session(session_id=1, user_id=100, status=BuilderStatus.CONFIRMED)
        mock_session_repo.get_by_id.return_value = session

        with pytest.raises(ForbiddenError):
            await builder_service.confirm_session(1, 999)


@pytest.mark.unit
class TestBuilderServiceGet:
    """get_session 测试。"""

    @pytest.mark.asyncio
    async def test_get_session_success(
        self,
        builder_service: BuilderService,
        mock_session_repo: AsyncMock,
    ) -> None:
        session = make_builder_session(session_id=1, user_id=100)
        mock_session_repo.get_by_id.return_value = session

        result = await builder_service.get_session(1, 100)
        assert result.id == 1

    @pytest.mark.asyncio
    async def test_get_session_not_found_raises(
        self,
        builder_service: BuilderService,
        mock_session_repo: AsyncMock,
    ) -> None:
        mock_session_repo.get_by_id.return_value = None

        with pytest.raises(BuilderSessionNotFoundError):
            await builder_service.get_session(999, 100)


@pytest.mark.unit
class TestBuilderServiceCancel:
    """cancel_session 测试。"""

    @pytest.mark.asyncio
    async def test_cancel_session_from_pending(
        self,
        builder_service: BuilderService,
        mock_session_repo: AsyncMock,
    ) -> None:
        session = make_builder_session(session_id=1, user_id=100, status=BuilderStatus.PENDING)
        mock_session_repo.get_by_id.return_value = session

        cancelled = make_builder_session(session_id=1, user_id=100, status=BuilderStatus.CANCELLED)
        mock_session_repo.update.return_value = cancelled

        result = await builder_service.cancel_session(1, 100)
        assert result.status == BuilderStatus.CANCELLED.value

    @pytest.mark.asyncio
    async def test_cancel_session_from_confirmed_raises(
        self,
        builder_service: BuilderService,
        mock_session_repo: AsyncMock,
    ) -> None:
        session = make_builder_session(session_id=1, user_id=100, status=BuilderStatus.CONFIRMED)
        mock_session_repo.get_by_id.return_value = session

        with pytest.raises(InvalidStateTransitionError):
            await builder_service.cancel_session(1, 100)
