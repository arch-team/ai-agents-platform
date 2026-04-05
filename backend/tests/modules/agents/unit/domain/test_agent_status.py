"""AgentStatus 枚举单元测试。"""

import pytest

from src.modules.agents.domain.value_objects.agent_status import AgentStatus


@pytest.mark.unit
class TestAgentStatus:
    def test_draft_value(self) -> None:
        assert AgentStatus.DRAFT == "draft"

    def test_active_value(self) -> None:
        assert AgentStatus.ACTIVE == "active"

    def test_archived_value(self) -> None:
        assert AgentStatus.ARCHIVED == "archived"

    def test_is_str_enum(self) -> None:
        assert isinstance(AgentStatus.DRAFT, str)

    def test_all_members(self) -> None:
        members = {s.value for s in AgentStatus}
        assert members == {"draft", "testing", "active", "archived"}
