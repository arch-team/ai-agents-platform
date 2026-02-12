"""AgentConfig 值对象单元测试。"""

import pytest

from src.modules.agents.domain.value_objects.agent_config import AgentConfig


@pytest.mark.unit
class TestAgentConfigDefaults:
    def test_default_model_id(self) -> None:
        config = AgentConfig()
        assert config.model_id == "us.anthropic.claude-3-5-haiku-20241022-v1:0"

    def test_default_temperature(self) -> None:
        config = AgentConfig()
        assert config.temperature == 0.7

    def test_default_max_tokens(self) -> None:
        config = AgentConfig()
        assert config.max_tokens == 2048

    def test_default_top_p(self) -> None:
        config = AgentConfig()
        assert config.top_p == 1.0

    def test_default_stop_sequences(self) -> None:
        config = AgentConfig()
        assert config.stop_sequences == ()

    def test_default_runtime_type(self) -> None:
        config = AgentConfig()
        assert config.runtime_type == "agent"


@pytest.mark.unit
class TestAgentConfigCustom:
    def test_custom_values(self) -> None:
        config = AgentConfig(
            model_id="anthropic.claude-3-haiku-20240307-v1:0",
            temperature=0.5,
            max_tokens=4096,
            top_p=0.9,
            stop_sequences=("</output>",),
        )
        assert config.model_id == "anthropic.claude-3-haiku-20240307-v1:0"
        assert config.temperature == 0.5
        assert config.max_tokens == 4096
        assert config.top_p == 0.9
        assert config.stop_sequences == ("</output>",)

    def test_custom_runtime_type_basic(self) -> None:
        config = AgentConfig(runtime_type="basic")
        assert config.runtime_type == "basic"

    def test_custom_runtime_type_agent(self) -> None:
        config = AgentConfig(runtime_type="agent")
        assert config.runtime_type == "agent"


@pytest.mark.unit
class TestAgentConfigImmutability:
    def test_frozen_cannot_set_attribute(self) -> None:
        config = AgentConfig()
        with pytest.raises(AttributeError):
            config.temperature = 0.5  # type: ignore[misc]

    def test_frozen_cannot_set_model_id(self) -> None:
        config = AgentConfig()
        with pytest.raises(AttributeError):
            config.model_id = "new-model"  # type: ignore[misc]


@pytest.mark.unit
class TestAgentConfigEquality:
    def test_equal_configs(self) -> None:
        config1 = AgentConfig()
        config2 = AgentConfig()
        assert config1 == config2

    def test_different_configs(self) -> None:
        config1 = AgentConfig(temperature=0.5)
        config2 = AgentConfig(temperature=0.9)
        assert config1 != config2
