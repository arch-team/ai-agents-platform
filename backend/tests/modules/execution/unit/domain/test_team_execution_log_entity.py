"""TeamExecutionLog 实体单元测试。"""

import pytest

from src.modules.execution.domain.entities.team_execution_log import TeamExecutionLog


@pytest.mark.unit
class TestTeamExecutionLogCreation:
    """TeamExecutionLog 创建测试。"""

    def test_create_log_default_values(self) -> None:
        """验证默认值: sequence=0, log_type="progress", content=""。"""
        # Arrange & Act
        log = TeamExecutionLog(execution_id=1)

        # Assert
        assert log.execution_id == 1
        assert log.sequence == 0
        assert log.log_type == "progress"
        assert log.content == ""

    def test_create_log_with_content(self) -> None:
        """验证自定义字段。"""
        # Arrange & Act
        log = TeamExecutionLog(
            execution_id=42,
            sequence=5,
            log_type="content",
            content="任务执行中...",
        )

        # Assert
        assert log.execution_id == 42
        assert log.sequence == 5
        assert log.log_type == "content"
        assert log.content == "任务执行中..."

    def test_create_log_inherits_pydantic_entity(self) -> None:
        """验证继承 PydanticEntity 的基础字段。"""
        log = TeamExecutionLog(execution_id=1)
        assert log.id is None
        assert log.created_at is not None
        assert log.updated_at is not None
