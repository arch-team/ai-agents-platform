"""TeamExecutionStatus 枚举单元测试。"""

import pytest

from src.modules.execution.domain.value_objects.team_execution_status import (
    TeamExecutionStatus,
)


@pytest.mark.unit
class TestTeamExecutionStatus:
    """TeamExecutionStatus 枚举值测试。"""

    def test_all_status_values(self) -> None:
        """验证 5 个状态值存在。"""
        assert len(TeamExecutionStatus) == 5
        assert TeamExecutionStatus.PENDING is not None
        assert TeamExecutionStatus.RUNNING is not None
        assert TeamExecutionStatus.COMPLETED is not None
        assert TeamExecutionStatus.FAILED is not None
        assert TeamExecutionStatus.CANCELLED is not None

    def test_status_string_representation(self) -> None:
        """验证各状态的字符串值。"""
        assert TeamExecutionStatus.PENDING.value == "pending"
        assert TeamExecutionStatus.RUNNING.value == "running"
        assert TeamExecutionStatus.COMPLETED.value == "completed"
        assert TeamExecutionStatus.FAILED.value == "failed"
        assert TeamExecutionStatus.CANCELLED.value == "cancelled"

    def test_status_is_str_enum(self) -> None:
        """验证 TeamExecutionStatus 是 StrEnum，可直接用作字符串。"""
        assert isinstance(TeamExecutionStatus.PENDING, str)
        assert TeamExecutionStatus.PENDING == "pending"
