"""ClaudeAgentAdapter Agent Teams 环境变量注入测试。"""

import pytest

from src.modules.execution.application.interfaces import AgentRequest
from src.modules.execution.infrastructure.external.claude_agent_adapter import (
    ClaudeAgentAdapter,
)


def _make_request(**overrides) -> AgentRequest:  # type: ignore[no-untyped-def]
    """创建测试用 AgentRequest。"""
    defaults = {"prompt": "你好"}
    defaults.update(overrides)
    return AgentRequest(**defaults)


@pytest.mark.unit
class TestBuildOptionsTeams:
    """ClaudeAgentAdapter._build_options() 的 Agent Teams 相关测试。"""

    def test_build_options_with_teams_enabled(self) -> None:
        """验证 enable_teams=True 时注入 CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS 和 max_turns=200。"""
        # Arrange
        adapter = ClaudeAgentAdapter()
        request = _make_request(enable_teams=True)

        # Act
        options = adapter._build_options(request)

        # Assert
        assert options.env is not None
        assert options.env.get("CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS") == "1"
        assert options.max_turns == 200

    def test_build_options_without_teams(self) -> None:
        """验证 enable_teams=False 时无 env 注入且 max_turns 未被强制设置。"""
        # Arrange
        adapter = ClaudeAgentAdapter()
        request = _make_request(enable_teams=False)

        # Act
        options = adapter._build_options(request)

        # Assert
        # enable_teams=False 时不应设置团队相关环境变量
        if options.env is not None:
            assert "CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS" not in options.env

    def test_build_options_teams_custom_max_turns(self) -> None:
        """验证 enable_teams=True + max_turns=500 时保留自定义值（不被覆盖为 200）。"""
        # Arrange
        adapter = ClaudeAgentAdapter()
        request = _make_request(enable_teams=True, max_turns=500)

        # Act
        options = adapter._build_options(request)

        # Assert
        assert options.env is not None
        assert options.env.get("CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS") == "1"
        # 自定义 max_turns > 20，不会被覆盖
        assert options.max_turns == 500

    def test_build_options_teams_default_low_max_turns_overridden(self) -> None:
        """验证 enable_teams=True + max_turns=20（默认值）时，被提升为 200。"""
        # Arrange
        adapter = ClaudeAgentAdapter()
        request = _make_request(enable_teams=True, max_turns=20)

        # Act
        options = adapter._build_options(request)

        # Assert
        assert options.max_turns == 200
