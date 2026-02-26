"""BuilderService 单元测试。"""

import json
from collections.abc import AsyncIterator
from unittest.mock import AsyncMock

import pytest

from src.modules.builder.application.dto.builder_dto import TriggerBuilderDTO
from src.modules.builder.application.services.builder_service import BuilderService
from src.modules.builder.domain.exceptions import BuilderSessionNotFoundError
from src.modules.builder.domain.value_objects.builder_status import BuilderStatus
from src.shared.domain.exceptions import ForbiddenError, InvalidStateTransitionError
from src.shared.domain.interfaces.agent_creator import CreatedAgentInfo
from tests.modules.builder.conftest import SAMPLE_GENERATED_CONFIG, make_builder_session


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
class TestBuilderServiceGenerateStream:
    """generate_config_stream 测试。"""

    @pytest.mark.asyncio
    async def test_generate_stream_success(
        self,
        builder_service: BuilderService,
        mock_session_repo: AsyncMock,
        mock_llm_service: AsyncMock,
    ) -> None:
        session = make_builder_session(session_id=1, user_id=100, status=BuilderStatus.PENDING)
        updated_session = make_builder_session(session_id=1, user_id=100, status=BuilderStatus.GENERATING)
        mock_session_repo.get_by_id.return_value = session
        mock_session_repo.update.return_value = updated_session

        # 模拟 LLM 流式返回
        config_json = json.dumps(SAMPLE_GENERATED_CONFIG)

        async def mock_generate(_prompt: str) -> AsyncIterator[str]:
            yield config_json

        mock_llm_service.generate_config.return_value = mock_generate(session.prompt)

        chunks: list[str] = []
        async for chunk in builder_service.generate_config_stream(1, 100):
            chunks.append(chunk)

        assert len(chunks) == 1
        assert chunks[0] == config_json
        assert mock_session_repo.update.call_count >= 1

    @pytest.mark.asyncio
    async def test_generate_stream_strips_markdown_fences(
        self,
        builder_service: BuilderService,
        mock_session_repo: AsyncMock,
        mock_llm_service: AsyncMock,
    ) -> None:
        """LLM 返回 markdown 代码围栏包裹的 JSON 时应正确解析。"""
        session = make_builder_session(session_id=1, user_id=100, status=BuilderStatus.PENDING)
        updated_session = make_builder_session(session_id=1, user_id=100, status=BuilderStatus.GENERATING)
        mock_session_repo.get_by_id.return_value = session
        mock_session_repo.update.return_value = updated_session

        fenced_json = "```json\n" + json.dumps(SAMPLE_GENERATED_CONFIG) + "\n```"

        async def mock_generate(_prompt: str) -> AsyncIterator[str]:
            yield fenced_json

        mock_llm_service.generate_config.return_value = mock_generate(session.prompt)

        chunks: list[str] = []
        async for chunk in builder_service.generate_config_stream(1, 100):
            chunks.append(chunk)

        assert len(chunks) == 1
        # complete_generation 应被调用（说明 JSON 被成功解析）
        update_calls = mock_session_repo.update.call_args_list
        assert len(update_calls) >= 2  # start_generation + complete_generation

    @pytest.mark.asyncio
    async def test_generate_stream_not_found_raises(
        self,
        builder_service: BuilderService,
        mock_session_repo: AsyncMock,
    ) -> None:
        mock_session_repo.get_by_id.return_value = None

        with pytest.raises(BuilderSessionNotFoundError):
            async for _chunk in builder_service.generate_config_stream(999, 100):
                pass

    @pytest.mark.asyncio
    async def test_generate_stream_wrong_owner_raises(
        self,
        builder_service: BuilderService,
        mock_session_repo: AsyncMock,
    ) -> None:
        session = make_builder_session(session_id=1, user_id=100)
        mock_session_repo.get_by_id.return_value = session

        with pytest.raises(ForbiddenError):
            async for _chunk in builder_service.generate_config_stream(1, 999):
                pass


@pytest.mark.unit
class TestBuilderServiceConfirm:
    """confirm_session 测试。"""

    @pytest.mark.asyncio
    async def test_confirm_session_success(
        self,
        builder_service: BuilderService,
        mock_session_repo: AsyncMock,
        mock_agent_creator: AsyncMock,
    ) -> None:
        session = make_builder_session(
            session_id=1,
            user_id=100,
            status=BuilderStatus.CONFIRMED,
            generated_config=SAMPLE_GENERATED_CONFIG,
            agent_name="代码审查助手",
        )
        mock_session_repo.get_by_id.return_value = session

        agent_info = CreatedAgentInfo(id=42, name="代码审查助手", status="draft")
        mock_agent_creator.create_agent.return_value = agent_info

        confirmed_session = make_builder_session(
            session_id=1,
            user_id=100,
            status=BuilderStatus.CONFIRMED,
            generated_config=SAMPLE_GENERATED_CONFIG,
            agent_name="代码审查助手",
            created_agent_id=42,
        )
        mock_session_repo.update.return_value = confirmed_session

        result = await builder_service.confirm_session(1, 100)

        assert result.created_agent_id == 42
        mock_agent_creator.create_agent.assert_called_once()

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
