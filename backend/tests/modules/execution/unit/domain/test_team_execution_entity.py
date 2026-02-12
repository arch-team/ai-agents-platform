"""TeamExecution 实体单元测试。"""

import pytest

from src.modules.execution.domain.entities.team_execution import TeamExecution
from src.modules.execution.domain.value_objects.team_execution_status import (
    TeamExecutionStatus,
)
from src.shared.domain.exceptions import InvalidStateTransitionError


def _make_team_execution(**overrides) -> TeamExecution:  # type: ignore[no-untyped-def]
    """创建测试用 TeamExecution 实体。"""
    defaults = {
        "agent_id": 1,
        "user_id": 100,
        "prompt": "请帮我完成任务",
    }
    defaults.update(overrides)
    return TeamExecution(**defaults)


@pytest.mark.unit
class TestTeamExecutionCreation:
    """TeamExecution 创建测试。"""

    def test_create_team_execution_default_values(self) -> None:
        """验证默认值: status=PENDING, result="", input_tokens=0 等。"""
        # Arrange & Act
        execution = _make_team_execution()

        # Assert
        assert execution.status == TeamExecutionStatus.PENDING
        assert execution.result == ""
        assert execution.error_message == ""
        assert execution.input_tokens == 0
        assert execution.output_tokens == 0
        assert execution.started_at is None
        assert execution.completed_at is None
        assert execution.conversation_id is None
        assert execution.agent_id == 1
        assert execution.user_id == 100
        assert execution.prompt == "请帮我完成任务"

    def test_create_team_execution_inherits_pydantic_entity(self) -> None:
        """验证继承 PydanticEntity 的基础字段。"""
        execution = _make_team_execution()
        assert execution.id is None
        assert execution.created_at is not None
        assert execution.updated_at is not None

    def test_create_team_execution_with_conversation_id(self) -> None:
        """验证设置 conversation_id。"""
        execution = _make_team_execution(conversation_id=42)
        assert execution.conversation_id == 42


@pytest.mark.unit
class TestTeamExecutionStart:
    """TeamExecution.start() 状态机测试。"""

    def test_start_from_pending(self) -> None:
        """PENDING -> RUNNING，设置 started_at。"""
        # Arrange
        execution = _make_team_execution()

        # Act
        execution.start()

        # Assert
        assert execution.status == TeamExecutionStatus.RUNNING
        assert execution.started_at is not None

    def test_start_updates_timestamp(self) -> None:
        """start() 调用 touch() 更新 updated_at。"""
        execution = _make_team_execution()
        original_updated_at = execution.updated_at
        execution.start()
        assert execution.updated_at is not None
        assert original_updated_at is not None
        assert execution.updated_at >= original_updated_at

    @pytest.mark.parametrize(
        "setup_status",
        [
            TeamExecutionStatus.RUNNING,
            TeamExecutionStatus.COMPLETED,
            TeamExecutionStatus.FAILED,
            TeamExecutionStatus.CANCELLED,
        ],
        ids=["from_running", "from_completed", "from_failed", "from_cancelled"],
    )
    def test_start_from_non_pending_raises(
        self, setup_status: TeamExecutionStatus
    ) -> None:
        """从非 PENDING 状态调用 start() 抛出 InvalidStateTransitionError。"""
        # Arrange - 创建处于指定状态的 execution
        execution = _make_team_execution()
        if setup_status == TeamExecutionStatus.RUNNING:
            execution.start()
        elif setup_status == TeamExecutionStatus.COMPLETED:
            execution.start()
            execution.complete(result="done", input_tokens=10, output_tokens=20)
        elif setup_status == TeamExecutionStatus.FAILED:
            execution.start()
            execution.fail(error_message="错误")
        elif setup_status == TeamExecutionStatus.CANCELLED:
            execution.cancel()

        # Act & Assert
        with pytest.raises(InvalidStateTransitionError):
            execution.start()


@pytest.mark.unit
class TestTeamExecutionComplete:
    """TeamExecution.complete() 状态机测试。"""

    def test_complete_from_running(self) -> None:
        """RUNNING -> COMPLETED，设置 result/tokens/completed_at。"""
        # Arrange
        execution = _make_team_execution()
        execution.start()

        # Act
        execution.complete(result="任务完成", input_tokens=100, output_tokens=200)

        # Assert
        assert execution.status == TeamExecutionStatus.COMPLETED
        assert execution.result == "任务完成"
        assert execution.input_tokens == 100
        assert execution.output_tokens == 200
        assert execution.completed_at is not None

    def test_complete_updates_timestamp(self) -> None:
        """complete() 调用 touch() 更新 updated_at。"""
        execution = _make_team_execution()
        execution.start()
        original_updated_at = execution.updated_at
        execution.complete(result="done", input_tokens=0, output_tokens=0)
        assert execution.updated_at is not None
        assert original_updated_at is not None
        assert execution.updated_at >= original_updated_at

    @pytest.mark.parametrize(
        "setup_action",
        ["pending", "completed", "failed", "cancelled"],
        ids=["from_pending", "from_completed", "from_failed", "from_cancelled"],
    )
    def test_complete_from_non_running_raises(self, setup_action: str) -> None:
        """从非 RUNNING 状态调用 complete() 抛出 InvalidStateTransitionError。"""
        execution = _make_team_execution()
        if setup_action == "pending":
            pass  # 默认 PENDING
        elif setup_action == "completed":
            execution.start()
            execution.complete(result="done", input_tokens=0, output_tokens=0)
        elif setup_action == "failed":
            execution.start()
            execution.fail(error_message="错误")
        elif setup_action == "cancelled":
            execution.cancel()

        with pytest.raises(InvalidStateTransitionError):
            execution.complete(result="retry", input_tokens=0, output_tokens=0)


@pytest.mark.unit
class TestTeamExecutionFail:
    """TeamExecution.fail() 状态机测试。"""

    def test_fail_from_running(self) -> None:
        """RUNNING -> FAILED，设置 error_message/completed_at。"""
        # Arrange
        execution = _make_team_execution()
        execution.start()

        # Act
        execution.fail(error_message="超时错误")

        # Assert
        assert execution.status == TeamExecutionStatus.FAILED
        assert execution.error_message == "超时错误"
        assert execution.completed_at is not None

    def test_fail_updates_timestamp(self) -> None:
        """fail() 调用 touch() 更新 updated_at。"""
        execution = _make_team_execution()
        execution.start()
        original_updated_at = execution.updated_at
        execution.fail(error_message="错误")
        assert execution.updated_at is not None
        assert original_updated_at is not None
        assert execution.updated_at >= original_updated_at

    @pytest.mark.parametrize(
        "setup_action",
        ["pending", "completed", "failed", "cancelled"],
        ids=["from_pending", "from_completed", "from_failed", "from_cancelled"],
    )
    def test_fail_from_non_running_raises(self, setup_action: str) -> None:
        """从非 RUNNING 状态调用 fail() 抛出 InvalidStateTransitionError。"""
        execution = _make_team_execution()
        if setup_action == "pending":
            pass
        elif setup_action == "completed":
            execution.start()
            execution.complete(result="done", input_tokens=0, output_tokens=0)
        elif setup_action == "failed":
            execution.start()
            execution.fail(error_message="已失败")
        elif setup_action == "cancelled":
            execution.cancel()

        with pytest.raises(InvalidStateTransitionError):
            execution.fail(error_message="再次失败")


@pytest.mark.unit
class TestTeamExecutionCancel:
    """TeamExecution.cancel() 状态机测试。"""

    def test_cancel_from_pending(self) -> None:
        """PENDING -> CANCELLED。"""
        # Arrange
        execution = _make_team_execution()

        # Act
        execution.cancel()

        # Assert
        assert execution.status == TeamExecutionStatus.CANCELLED
        assert execution.completed_at is not None

    def test_cancel_from_running(self) -> None:
        """RUNNING -> CANCELLED。"""
        # Arrange
        execution = _make_team_execution()
        execution.start()

        # Act
        execution.cancel()

        # Assert
        assert execution.status == TeamExecutionStatus.CANCELLED
        assert execution.completed_at is not None

    def test_cancel_updates_timestamp(self) -> None:
        """cancel() 调用 touch() 更新 updated_at。"""
        execution = _make_team_execution()
        original_updated_at = execution.updated_at
        execution.cancel()
        assert execution.updated_at is not None
        assert original_updated_at is not None
        assert execution.updated_at >= original_updated_at

    @pytest.mark.parametrize(
        "setup_action",
        ["completed", "failed", "cancelled"],
        ids=["from_completed", "from_failed", "from_cancelled"],
    )
    def test_cancel_from_terminal_state_raises(self, setup_action: str) -> None:
        """从 COMPLETED/FAILED/CANCELLED 调用 cancel() 抛出 InvalidStateTransitionError。"""
        execution = _make_team_execution()
        if setup_action == "completed":
            execution.start()
            execution.complete(result="done", input_tokens=0, output_tokens=0)
        elif setup_action == "failed":
            execution.start()
            execution.fail(error_message="错误")
        elif setup_action == "cancelled":
            execution.cancel()

        with pytest.raises(InvalidStateTransitionError):
            execution.cancel()
