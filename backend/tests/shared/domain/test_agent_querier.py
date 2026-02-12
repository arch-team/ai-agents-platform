"""跨模块 Agent 查询接口的单元测试。"""

import pytest

from src.shared.domain.interfaces import ActiveAgentInfo, IAgentQuerier


@pytest.mark.unit
class TestActiveAgentInfo:
    """ActiveAgentInfo 数据结构测试。"""

    def test_create_with_required_fields(self) -> None:
        info = ActiveAgentInfo(
            id=1,
            name="Test Agent",
            system_prompt="You are helpful.",
            model_id="us.anthropic.claude-3-5-sonnet-20241022-v2:0",
            temperature=0.7,
            max_tokens=2048,
            top_p=1.0,
        )
        assert info.id == 1
        assert info.name == "Test Agent"
        assert info.system_prompt == "You are helpful."
        assert info.model_id == "us.anthropic.claude-3-5-sonnet-20241022-v2:0"
        assert info.temperature == 0.7
        assert info.max_tokens == 2048
        assert info.top_p == 1.0
        assert info.stop_sequences == ()
        assert info.runtime_type == "agent"

    def test_create_with_stop_sequences(self) -> None:
        info = ActiveAgentInfo(
            id=2,
            name="Agent",
            system_prompt="Prompt",
            model_id="model",
            temperature=0.5,
            max_tokens=1024,
            top_p=0.9,
            stop_sequences=("Human:", "Assistant:"),
        )
        assert info.stop_sequences == ("Human:", "Assistant:")

    def test_create_with_runtime_type_basic(self) -> None:
        info = ActiveAgentInfo(
            id=3,
            name="Basic Agent",
            system_prompt="Prompt",
            model_id="model",
            temperature=0.7,
            max_tokens=2048,
            top_p=1.0,
            runtime_type="basic",
        )
        assert info.runtime_type == "basic"

    def test_frozen_immutable(self) -> None:
        info = ActiveAgentInfo(
            id=1,
            name="Test",
            system_prompt="Prompt",
            model_id="model",
            temperature=0.7,
            max_tokens=2048,
            top_p=1.0,
        )
        with pytest.raises(AttributeError):
            info.name = "Changed"  # type: ignore[misc]

    def test_equality_by_value(self) -> None:
        kwargs = {
            "id": 1,
            "name": "A",
            "system_prompt": "P",
            "model_id": "M",
            "temperature": 0.7,
            "max_tokens": 2048,
            "top_p": 1.0,
        }
        assert ActiveAgentInfo(**kwargs) == ActiveAgentInfo(**kwargs)

    def test_inequality_different_values(self) -> None:
        base = {
            "id": 1,
            "name": "A",
            "system_prompt": "P",
            "model_id": "M",
            "temperature": 0.7,
            "max_tokens": 2048,
            "top_p": 1.0,
        }
        different = {**base, "id": 2}
        assert ActiveAgentInfo(**base) != ActiveAgentInfo(**different)


@pytest.mark.unit
class TestIAgentQuerier:
    """IAgentQuerier 接口测试。"""

    def test_cannot_instantiate_abc(self) -> None:
        with pytest.raises(TypeError):
            IAgentQuerier()  # type: ignore[abstract]

    def test_has_abstract_method(self) -> None:
        assert hasattr(IAgentQuerier, "get_active_agent")
        assert getattr(
            IAgentQuerier.get_active_agent, "__isabstractmethod__", False
        )

    def test_concrete_implementation(self) -> None:
        """具体实现类可以正确实例化。"""

        class ConcreteQuerier(IAgentQuerier):
            async def get_active_agent(
                self, agent_id: int
            ) -> ActiveAgentInfo | None:
                return None

        querier = ConcreteQuerier()
        assert isinstance(querier, IAgentQuerier)
