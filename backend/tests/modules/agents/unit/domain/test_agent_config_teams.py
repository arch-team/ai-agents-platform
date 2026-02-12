"""AgentConfig enable_teams 字段单元测试。"""

import pytest

from src.modules.agents.domain.value_objects.agent_config import AgentConfig


@pytest.mark.unit
class TestAgentConfigTeams:
    """AgentConfig 的 enable_teams 字段测试。"""

    def test_default_enable_teams_false(self) -> None:
        """验证 enable_teams 默认值为 False。"""
        # Arrange & Act
        config = AgentConfig()

        # Assert
        assert config.enable_teams is False

    def test_enable_teams_true(self) -> None:
        """验证显式设置 enable_teams=True。"""
        # Arrange & Act
        config = AgentConfig(enable_teams=True)

        # Assert
        assert config.enable_teams is True

    def test_agent_config_frozen(self) -> None:
        """验证 frozen dataclass 不可变性: enable_teams 不能被修改。"""
        # Arrange
        config = AgentConfig(enable_teams=True)

        # Act & Assert
        with pytest.raises(AttributeError):
            config.enable_teams = False  # type: ignore[misc]

    def test_enable_teams_equality(self) -> None:
        """验证 enable_teams 参与 dataclass 相等性比较。"""
        # Arrange
        config1 = AgentConfig(enable_teams=True)
        config2 = AgentConfig(enable_teams=True)
        config3 = AgentConfig(enable_teams=False)

        # Assert
        assert config1 == config2
        assert config1 != config3
