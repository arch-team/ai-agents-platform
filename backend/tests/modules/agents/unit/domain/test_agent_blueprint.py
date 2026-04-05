"""Agent Blueprint 值对象 + 状态机扩展测试。"""

import pytest

from src.modules.agents.domain.value_objects.agent_blueprint import (
    Guardrail,
    MemoryConfig,
    Persona,
    ToolBinding,
)
from src.modules.agents.domain.value_objects.agent_status import AgentStatus
from src.shared.domain.exceptions import InvalidStateTransitionError, ValidationError


# ── Persona 值对象 ──────────────────────────────────────────────


class TestPersona:
    def test_create_with_required_fields(self) -> None:
        persona = Persona(role="售后客服专员", background="负责处理退货和换货业务")
        assert persona.role == "售后客服专员"
        assert persona.background == "负责处理退货和换货业务"
        assert persona.tone == ""

    def test_create_with_tone(self) -> None:
        persona = Persona(role="客服", background="处理退货", tone="专业且友善")
        assert persona.tone == "专业且友善"

    def test_immutable(self) -> None:
        persona = Persona(role="客服", background="处理退货")
        with pytest.raises(AttributeError):
            persona.role = "新角色"  # type: ignore[misc]


# ── ToolBinding 值对象 ──────────────────────────────────────────


class TestToolBinding:
    def test_create_with_required_fields(self) -> None:
        binding = ToolBinding(tool_id=1, display_name="订单查询")
        assert binding.tool_id == 1
        assert binding.display_name == "订单查询"
        assert binding.usage_hint == ""

    def test_create_with_usage_hint(self) -> None:
        binding = ToolBinding(tool_id=2, display_name="退货单 API", usage_hint="客户确认退货后调用")
        assert binding.usage_hint == "客户确认退货后调用"

    def test_immutable(self) -> None:
        binding = ToolBinding(tool_id=1, display_name="查询")
        with pytest.raises(AttributeError):
            binding.tool_id = 2  # type: ignore[misc]


# ── MemoryConfig 值对象 ─────────────────────────────────────────


class TestMemoryConfig:
    def test_default_disabled(self) -> None:
        config = MemoryConfig()
        assert config.enabled is False
        assert config.strategy == "conversation"
        assert config.retain_fields == ()

    def test_create_enabled(self) -> None:
        config = MemoryConfig(enabled=True, strategy="session", retain_fields=("订单号", "客户诉求"))
        assert config.enabled is True
        assert config.strategy == "session"
        assert config.retain_fields == ("订单号", "客户诉求")

    def test_immutable(self) -> None:
        config = MemoryConfig(enabled=True)
        with pytest.raises(AttributeError):
            config.enabled = False  # type: ignore[misc]


# ── Guardrail 值对象 ────────────────────────────────────────────


class TestGuardrail:
    def test_create_with_default_severity(self) -> None:
        guardrail = Guardrail(rule="不能承诺超出政策的退款")
        assert guardrail.rule == "不能承诺超出政策的退款"
        assert guardrail.severity == "warn"

    def test_create_with_block_severity(self) -> None:
        guardrail = Guardrail(rule="不能泄露其他客户信息", severity="block")
        assert guardrail.severity == "block"

    def test_immutable(self) -> None:
        guardrail = Guardrail(rule="规则")
        with pytest.raises(AttributeError):
            guardrail.rule = "新规则"  # type: ignore[misc]


# ── AgentStatus TESTING 扩展 ────────────────────────────────────


class TestAgentStatusTesting:
    def test_testing_status_exists(self) -> None:
        assert AgentStatus.TESTING == "testing"
        assert AgentStatus.TESTING.value == "testing"

    def test_all_statuses(self) -> None:
        statuses = {s.value for s in AgentStatus}
        assert statuses == {"draft", "testing", "active", "archived"}


# ── Agent 状态转换 ──────────────────────────────────────────────


class TestAgentStateTransitions:
    """Agent 状态机: DRAFT→TESTING→ACTIVE→ARCHIVED (+ V1 兼容路径)。"""

    def _make_agent(self, status: AgentStatus, system_prompt: str = "") -> "Agent":
        from tests.modules.agents.conftest import make_agent

        return make_agent(status=status, system_prompt=system_prompt)

    # DRAFT → TESTING (Blueprint 模式)
    def test_start_testing_from_draft(self) -> None:
        agent = self._make_agent(AgentStatus.DRAFT)
        agent.start_testing()
        assert agent.status == AgentStatus.TESTING

    def test_start_testing_from_active_raises(self) -> None:
        agent = self._make_agent(AgentStatus.ACTIVE, system_prompt="prompt")
        with pytest.raises(InvalidStateTransitionError):
            agent.start_testing()

    def test_start_testing_from_archived_raises(self) -> None:
        agent = self._make_agent(AgentStatus.ARCHIVED)
        with pytest.raises(InvalidStateTransitionError):
            agent.start_testing()

    # TESTING → ACTIVE (Blueprint 上线)
    def test_activate_from_testing(self) -> None:
        agent = self._make_agent(AgentStatus.TESTING)
        agent.activate()
        assert agent.status == AgentStatus.ACTIVE

    # DRAFT → ACTIVE (V1 兼容路径, 需要 system_prompt)
    def test_activate_from_draft_with_prompt(self) -> None:
        agent = self._make_agent(AgentStatus.DRAFT, system_prompt="你是客服")
        agent.activate()
        assert agent.status == AgentStatus.ACTIVE

    def test_activate_from_draft_without_prompt_raises(self) -> None:
        agent = self._make_agent(AgentStatus.DRAFT, system_prompt="")
        with pytest.raises(ValidationError, match="系统提示词"):
            agent.activate()

    # TESTING 激活不需要 system_prompt (Blueprint 模式用 CLAUDE.md)
    def test_activate_from_testing_without_prompt_ok(self) -> None:
        agent = self._make_agent(AgentStatus.TESTING)
        agent.activate()  # 不应抛异常
        assert agent.status == AgentStatus.ACTIVE

    # ARCHIVED 不能激活
    def test_activate_from_archived_raises(self) -> None:
        agent = self._make_agent(AgentStatus.ARCHIVED)
        with pytest.raises(InvalidStateTransitionError):
            agent.activate()

    # Archive 路径: DRAFT/TESTING/ACTIVE → ARCHIVED
    def test_archive_from_draft(self) -> None:
        agent = self._make_agent(AgentStatus.DRAFT)
        agent.archive()
        assert agent.status == AgentStatus.ARCHIVED

    def test_archive_from_testing(self) -> None:
        agent = self._make_agent(AgentStatus.TESTING)
        agent.archive()
        assert agent.status == AgentStatus.ARCHIVED

    def test_archive_from_active(self) -> None:
        agent = self._make_agent(AgentStatus.ACTIVE, system_prompt="prompt")
        agent.archive()
        assert agent.status == AgentStatus.ARCHIVED

    def test_archive_from_archived_raises(self) -> None:
        agent = self._make_agent(AgentStatus.ARCHIVED)
        with pytest.raises(InvalidStateTransitionError):
            agent.archive()
