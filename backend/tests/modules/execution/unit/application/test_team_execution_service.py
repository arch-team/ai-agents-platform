"""TeamExecutionService 单元测试。"""

from datetime import UTC, datetime
from unittest.mock import AsyncMock, patch

import pytest

from src.modules.execution.application.dto.team_execution_dto import (
    CreateTeamExecutionDTO,
    TeamExecutionDTO,
)
from src.modules.execution.application.interfaces.agent_runtime import (
    IAgentRuntime,
)
from src.modules.execution.application.services.team_execution_service import (
    TeamExecutionService,
)
from src.modules.execution.domain.entities.team_execution import TeamExecution
from src.modules.execution.domain.entities.team_execution_log import TeamExecutionLog
from src.modules.execution.domain.exceptions import (
    TeamExecutionNotCancellableError,
    TeamExecutionNotFoundError,
)
from src.modules.execution.domain.repositories.team_execution_repository import (
    ITeamExecutionLogRepository,
    ITeamExecutionRepository,
)
from src.modules.execution.domain.value_objects.team_execution_status import (
    TeamExecutionStatus,
)
from src.shared.domain.exceptions import DomainError, ForbiddenError
from src.shared.domain.interfaces.agent_querier import (
    ActiveAgentInfo,
    IAgentQuerier,
)


# -- 测试辅助工厂 --


def _make_agent_info(
    *,
    agent_id: int = 1,
    name: str = "测试 Agent",
    system_prompt: str = "你是一个助手",
    model_id: str = "anthropic.claude-3-5-sonnet",
    temperature: float = 0.7,
    max_tokens: int = 2048,
    top_p: float = 1.0,
    stop_sequences: tuple[str, ...] = (),
    runtime_type: str = "agent",
    enable_teams: bool = True,
) -> ActiveAgentInfo:
    return ActiveAgentInfo(
        id=agent_id,
        name=name,
        system_prompt=system_prompt,
        model_id=model_id,
        temperature=temperature,
        max_tokens=max_tokens,
        top_p=top_p,
        stop_sequences=stop_sequences,
        runtime_type=runtime_type,
        enable_teams=enable_teams,
    )


def _make_team_execution(
    *,
    exec_id: int = 1,
    agent_id: int = 1,
    user_id: int = 100,
    prompt: str = "测试任务",
    status: TeamExecutionStatus = TeamExecutionStatus.PENDING,
    result: str = "",
    error_message: str = "",
    input_tokens: int = 0,
    output_tokens: int = 0,
    started_at: datetime | None = None,
    completed_at: datetime | None = None,
) -> TeamExecution:
    now = datetime.now(UTC)
    return TeamExecution(
        id=exec_id,
        agent_id=agent_id,
        user_id=user_id,
        prompt=prompt,
        status=status,
        result=result,
        error_message=error_message,
        input_tokens=input_tokens,
        output_tokens=output_tokens,
        started_at=started_at,
        completed_at=completed_at,
        created_at=now,
        updated_at=now,
    )


def _make_team_execution_log(
    *,
    log_id: int = 1,
    execution_id: int = 1,
    sequence: int = 1,
    log_type: str = "content",
    content: str = "日志内容",
) -> TeamExecutionLog:
    now = datetime.now(UTC)
    return TeamExecutionLog(
        id=log_id,
        execution_id=execution_id,
        sequence=sequence,
        log_type=log_type,
        content=content,
        created_at=now,
        updated_at=now,
    )


def _make_service(
    *,
    execution_repo: AsyncMock | None = None,
    log_repo: AsyncMock | None = None,
    agent_runtime: AsyncMock | None = None,
    agent_querier: AsyncMock | None = None,
) -> TeamExecutionService:
    return TeamExecutionService(
        execution_repo=execution_repo or AsyncMock(spec=ITeamExecutionRepository),
        log_repo=log_repo or AsyncMock(spec=ITeamExecutionLogRepository),
        agent_runtime=agent_runtime or AsyncMock(spec=IAgentRuntime),
        agent_querier=agent_querier or AsyncMock(spec=IAgentQuerier),
    )


# -- submit() 测试 --


@pytest.mark.unit
class TestTeamExecutionServiceSubmit:
    """TeamExecutionService.submit() 测试。"""

    @pytest.mark.asyncio
    async def test_submit_success(self) -> None:
        """mock agent_querier 返回启用 teams 的 agent，验证创建和返回 DTO。"""
        # Arrange
        agent_querier = AsyncMock(spec=IAgentQuerier)
        agent_querier.get_active_agent.return_value = _make_agent_info(enable_teams=True)

        execution_repo = AsyncMock(spec=ITeamExecutionRepository)
        execution_repo.create.side_effect = lambda e: _make_team_execution(
            agent_id=e.agent_id,
            user_id=e.user_id,
            prompt=e.prompt,
        )

        service = _make_service(
            execution_repo=execution_repo,
            agent_querier=agent_querier,
        )
        dto = CreateTeamExecutionDTO(agent_id=1, prompt="完成任务")

        # Act - patch _execute_in_background 为空协程，避免后台任务运行
        with patch.object(
            service, "_execute_in_background", new_callable=AsyncMock,
        ):
            result = await service.submit(dto, user_id=100)

        # Assert
        assert isinstance(result, TeamExecutionDTO)
        assert result.agent_id == 1
        assert result.user_id == 100
        assert result.prompt == "完成任务"
        assert result.status == "pending"
        execution_repo.create.assert_called_once()

    @pytest.mark.asyncio
    async def test_submit_agent_not_available(self) -> None:
        """mock agent_querier 返回 None，验证抛出 DomainError。"""
        # Arrange
        agent_querier = AsyncMock(spec=IAgentQuerier)
        agent_querier.get_active_agent.return_value = None

        service = _make_service(agent_querier=agent_querier)
        dto = CreateTeamExecutionDTO(agent_id=999, prompt="测试")

        # Act & Assert
        with pytest.raises(DomainError, match="不可用"):
            await service.submit(dto, user_id=100)

    @pytest.mark.asyncio
    async def test_submit_agent_teams_not_enabled(self) -> None:
        """mock agent_querier 返回 enable_teams=False 的 agent，验证抛出 DomainError。"""
        # Arrange
        agent_querier = AsyncMock(spec=IAgentQuerier)
        agent_querier.get_active_agent.return_value = _make_agent_info(
            enable_teams=False,
        )

        service = _make_service(agent_querier=agent_querier)
        dto = CreateTeamExecutionDTO(agent_id=1, prompt="测试")

        # Act & Assert
        with pytest.raises(DomainError, match="未启用 Teams"):
            await service.submit(dto, user_id=100)

    @pytest.mark.asyncio
    async def test_submit_with_conversation_id(self) -> None:
        """提交时携带 conversation_id。"""
        # Arrange
        agent_querier = AsyncMock(spec=IAgentQuerier)
        agent_querier.get_active_agent.return_value = _make_agent_info(enable_teams=True)

        execution_repo = AsyncMock(spec=ITeamExecutionRepository)
        execution_repo.create.side_effect = lambda e: _make_team_execution(
            agent_id=e.agent_id,
            user_id=e.user_id,
            prompt=e.prompt,
        )

        service = _make_service(
            execution_repo=execution_repo,
            agent_querier=agent_querier,
        )
        dto = CreateTeamExecutionDTO(agent_id=1, prompt="任务", conversation_id=42)

        # Act - patch _execute_in_background 为空协程，避免后台任务运行
        with patch.object(
            service, "_execute_in_background", new_callable=AsyncMock,
        ):
            result = await service.submit(dto, user_id=100)

        # Assert
        assert isinstance(result, TeamExecutionDTO)
        execution_repo.create.assert_called_once()
        # 验证传入 repo 的 execution 带有 conversation_id
        created_entity = execution_repo.create.call_args.args[0]
        assert created_entity.conversation_id == 42


# -- get() 测试 --


@pytest.mark.unit
class TestTeamExecutionServiceGet:
    """TeamExecutionService.get() 测试。"""

    @pytest.mark.asyncio
    async def test_get_success(self) -> None:
        """mock repo 返回 execution，验证返回 DTO。"""
        # Arrange
        execution_repo = AsyncMock(spec=ITeamExecutionRepository)
        execution_repo.get_by_id.return_value = _make_team_execution(
            user_id=100,
        )

        service = _make_service(execution_repo=execution_repo)

        # Act
        result = await service.get(execution_id=1, user_id=100)

        # Assert
        assert isinstance(result, TeamExecutionDTO)
        assert result.id == 1
        assert result.user_id == 100
        assert result.status == "pending"

    @pytest.mark.asyncio
    async def test_get_not_found(self) -> None:
        """mock repo 返回 None，验证抛出 TeamExecutionNotFoundError。"""
        # Arrange
        execution_repo = AsyncMock(spec=ITeamExecutionRepository)
        execution_repo.get_by_id.return_value = None

        service = _make_service(execution_repo=execution_repo)

        # Act & Assert
        with pytest.raises(TeamExecutionNotFoundError):
            await service.get(execution_id=999, user_id=100)

    @pytest.mark.asyncio
    async def test_get_forbidden(self) -> None:
        """mock repo 返回其他用户的 execution，验证抛出 ForbiddenError。"""
        # Arrange
        execution_repo = AsyncMock(spec=ITeamExecutionRepository)
        execution_repo.get_by_id.return_value = _make_team_execution(
            user_id=100,
        )

        service = _make_service(execution_repo=execution_repo)

        # Act & Assert
        with pytest.raises(ForbiddenError, match="无权操作此资源"):
            await service.get(execution_id=1, user_id=999)


# -- list_by_user() 测试 --


@pytest.mark.unit
class TestTeamExecutionServiceListByUser:
    """TeamExecutionService.list_by_user() 测试。"""

    @pytest.mark.asyncio
    async def test_list_by_user_with_data(self) -> None:
        """mock repo 返回 list 和 count，验证分页结果。"""
        # Arrange
        execution_repo = AsyncMock(spec=ITeamExecutionRepository)
        execution_repo.list_by_user.return_value = [
            _make_team_execution(exec_id=1, user_id=100),
            _make_team_execution(exec_id=2, user_id=100),
        ]
        execution_repo.count_by_user.return_value = 2

        service = _make_service(execution_repo=execution_repo)

        # Act
        result = await service.list_by_user(user_id=100, page=1, page_size=20)

        # Assert
        assert result.total == 2
        assert len(result.items) == 2
        assert result.page == 1
        assert result.page_size == 20

    @pytest.mark.asyncio
    async def test_list_by_user_empty(self) -> None:
        """无数据时返回空列表。"""
        # Arrange
        execution_repo = AsyncMock(spec=ITeamExecutionRepository)
        execution_repo.list_by_user.return_value = []
        execution_repo.count_by_user.return_value = 0

        service = _make_service(execution_repo=execution_repo)

        # Act
        result = await service.list_by_user(user_id=100)

        # Assert
        assert result.total == 0
        assert result.items == []

    @pytest.mark.asyncio
    async def test_list_by_user_pagination(self) -> None:
        """验证分页参数计算正确: page=2, page_size=10 -> offset=10。"""
        # Arrange
        execution_repo = AsyncMock(spec=ITeamExecutionRepository)
        execution_repo.list_by_user.return_value = []
        execution_repo.count_by_user.return_value = 0

        service = _make_service(execution_repo=execution_repo)

        # Act
        await service.list_by_user(user_id=100, page=2, page_size=10)

        # Assert
        execution_repo.list_by_user.assert_called_once_with(
            user_id=100,
            offset=10,
            limit=10,
        )


# -- cancel() 测试 --


@pytest.mark.unit
class TestTeamExecutionServiceCancel:
    """TeamExecutionService.cancel() 测试。"""

    @pytest.mark.asyncio
    async def test_cancel_from_pending(self) -> None:
        """PENDING 状态可取消。"""
        # Arrange
        execution_repo = AsyncMock(spec=ITeamExecutionRepository)
        execution = _make_team_execution(
            status=TeamExecutionStatus.PENDING,
            user_id=100,
        )
        execution_repo.get_by_id.return_value = execution
        execution_repo.update.side_effect = lambda e: e

        service = _make_service(execution_repo=execution_repo)

        # Act
        result = await service.cancel(execution_id=1, user_id=100)

        # Assert
        assert result.status == "cancelled"
        execution_repo.update.assert_called_once()

    @pytest.mark.asyncio
    async def test_cancel_from_running(self) -> None:
        """RUNNING 状态可取消。"""
        # Arrange
        now = datetime.now(UTC)
        execution_repo = AsyncMock(spec=ITeamExecutionRepository)
        execution = _make_team_execution(
            status=TeamExecutionStatus.RUNNING,
            user_id=100,
            started_at=now,
        )
        execution_repo.get_by_id.return_value = execution
        execution_repo.update.side_effect = lambda e: e

        service = _make_service(execution_repo=execution_repo)

        # Act
        result = await service.cancel(execution_id=1, user_id=100)

        # Assert
        assert result.status == "cancelled"

    @pytest.mark.asyncio
    async def test_cancel_from_completed_raises(self) -> None:
        """COMPLETED 状态不可取消，抛出 TeamExecutionNotCancellableError。"""
        # Arrange
        now = datetime.now(UTC)
        execution_repo = AsyncMock(spec=ITeamExecutionRepository)
        execution = _make_team_execution(
            status=TeamExecutionStatus.COMPLETED,
            user_id=100,
            started_at=now,
            completed_at=now,
            result="完成",
        )
        execution_repo.get_by_id.return_value = execution

        service = _make_service(execution_repo=execution_repo)

        # Act & Assert
        with pytest.raises(TeamExecutionNotCancellableError):
            await service.cancel(execution_id=1, user_id=100)

    @pytest.mark.asyncio
    async def test_cancel_from_failed_raises(self) -> None:
        """FAILED 状态不可取消。"""
        # Arrange
        now = datetime.now(UTC)
        execution_repo = AsyncMock(spec=ITeamExecutionRepository)
        execution = _make_team_execution(
            status=TeamExecutionStatus.FAILED,
            user_id=100,
            started_at=now,
            completed_at=now,
            error_message="错误",
        )
        execution_repo.get_by_id.return_value = execution

        service = _make_service(execution_repo=execution_repo)

        # Act & Assert
        with pytest.raises(TeamExecutionNotCancellableError):
            await service.cancel(execution_id=1, user_id=100)

    @pytest.mark.asyncio
    async def test_cancel_not_found(self) -> None:
        """不存在的 execution 抛出 TeamExecutionNotFoundError。"""
        # Arrange
        execution_repo = AsyncMock(spec=ITeamExecutionRepository)
        execution_repo.get_by_id.return_value = None

        service = _make_service(execution_repo=execution_repo)

        # Act & Assert
        with pytest.raises(TeamExecutionNotFoundError):
            await service.cancel(execution_id=999, user_id=100)

    @pytest.mark.asyncio
    async def test_cancel_forbidden(self) -> None:
        """非所有者不可取消。"""
        # Arrange
        execution_repo = AsyncMock(spec=ITeamExecutionRepository)
        execution_repo.get_by_id.return_value = _make_team_execution(user_id=100)

        service = _make_service(execution_repo=execution_repo)

        # Act & Assert
        with pytest.raises(ForbiddenError, match="无权操作此资源"):
            await service.cancel(execution_id=1, user_id=999)


# -- get_logs() 测试 --


@pytest.mark.unit
class TestTeamExecutionServiceGetLogs:
    """TeamExecutionService.get_logs() 测试。"""

    @pytest.mark.asyncio
    async def test_get_logs_success(self) -> None:
        """mock log_repo 返回 logs，验证返回 DTO 列表。"""
        # Arrange
        execution_repo = AsyncMock(spec=ITeamExecutionRepository)
        execution_repo.get_by_id.return_value = _make_team_execution(user_id=100)

        log_repo = AsyncMock(spec=ITeamExecutionLogRepository)
        log_repo.list_by_execution.return_value = [
            _make_team_execution_log(log_id=1, sequence=1, content="步骤1"),
            _make_team_execution_log(log_id=2, sequence=2, content="步骤2"),
        ]

        service = _make_service(
            execution_repo=execution_repo,
            log_repo=log_repo,
        )

        # Act
        result = await service.get_logs(execution_id=1, user_id=100)

        # Assert
        assert len(result) == 2
        assert result[0].sequence == 1
        assert result[0].content == "步骤1"
        assert result[1].sequence == 2
        assert result[1].content == "步骤2"

    @pytest.mark.asyncio
    async def test_get_logs_with_after_sequence(self) -> None:
        """验证 after_sequence 参数传递到 repo。"""
        # Arrange
        execution_repo = AsyncMock(spec=ITeamExecutionRepository)
        execution_repo.get_by_id.return_value = _make_team_execution(user_id=100)

        log_repo = AsyncMock(spec=ITeamExecutionLogRepository)
        log_repo.list_by_execution.return_value = []

        service = _make_service(
            execution_repo=execution_repo,
            log_repo=log_repo,
        )

        # Act
        await service.get_logs(execution_id=1, user_id=100, after_sequence=5)

        # Assert
        log_repo.list_by_execution.assert_called_once_with(
            execution_id=1,
            after_sequence=5,
        )

    @pytest.mark.asyncio
    async def test_get_logs_not_found(self) -> None:
        """execution 不存在时抛异常。"""
        # Arrange
        execution_repo = AsyncMock(spec=ITeamExecutionRepository)
        execution_repo.get_by_id.return_value = None

        service = _make_service(execution_repo=execution_repo)

        # Act & Assert
        with pytest.raises(TeamExecutionNotFoundError):
            await service.get_logs(execution_id=999, user_id=100)

    @pytest.mark.asyncio
    async def test_get_logs_forbidden(self) -> None:
        """非所有者访问日志抛 ForbiddenError。"""
        # Arrange
        execution_repo = AsyncMock(spec=ITeamExecutionRepository)
        execution_repo.get_by_id.return_value = _make_team_execution(user_id=100)

        service = _make_service(execution_repo=execution_repo)

        # Act & Assert
        with pytest.raises(ForbiddenError, match="无权操作此资源"):
            await service.get_logs(execution_id=1, user_id=999)

    @pytest.mark.asyncio
    async def test_get_logs_empty(self) -> None:
        """无日志时返回空列表。"""
        # Arrange
        execution_repo = AsyncMock(spec=ITeamExecutionRepository)
        execution_repo.get_by_id.return_value = _make_team_execution(user_id=100)

        log_repo = AsyncMock(spec=ITeamExecutionLogRepository)
        log_repo.list_by_execution.return_value = []

        service = _make_service(
            execution_repo=execution_repo,
            log_repo=log_repo,
        )

        # Act
        result = await service.get_logs(execution_id=1, user_id=100)

        # Assert
        assert result == []
