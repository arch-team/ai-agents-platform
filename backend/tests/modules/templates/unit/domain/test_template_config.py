"""TemplateConfig 值对象单元测试。"""

import pytest

from src.modules.templates.domain.value_objects.template_config import TemplateConfig


@pytest.mark.unit
class TestTemplateConfigCreation:
    """TemplateConfig 创建测试。"""

    def test_create_with_required_fields(self) -> None:
        config = TemplateConfig(system_prompt="你是一个助手", model_id="anthropic.claude-v3")
        assert config.system_prompt == "你是一个助手"
        assert config.model_id == "anthropic.claude-v3"
        assert config.temperature == 0.7
        assert config.max_tokens == 4096
        assert config.tool_ids == []
        assert config.knowledge_base_ids == []

    def test_create_with_all_fields(self) -> None:
        config = TemplateConfig(
            system_prompt="你是客服助手",
            model_id="anthropic.claude-v3",
            temperature=0.5,
            max_tokens=2048,
            tool_ids=[1, 2, 3],
            knowledge_base_ids=[10, 20],
        )
        assert config.temperature == 0.5
        assert config.max_tokens == 2048
        assert config.tool_ids == [1, 2, 3]
        assert config.knowledge_base_ids == [10, 20]


@pytest.mark.unit
class TestTemplateConfigImmutability:
    """TemplateConfig 不可变性测试。"""

    def test_frozen(self) -> None:
        config = TemplateConfig(system_prompt="测试", model_id="model-1")
        with pytest.raises(AttributeError):
            config.system_prompt = "修改"  # type: ignore[misc]

    def test_equality_by_value(self) -> None:
        config_a = TemplateConfig(system_prompt="测试", model_id="model-1")
        config_b = TemplateConfig(system_prompt="测试", model_id="model-1")
        assert config_a == config_b

    def test_inequality(self) -> None:
        config_a = TemplateConfig(system_prompt="测试A", model_id="model-1")
        config_b = TemplateConfig(system_prompt="测试B", model_id="model-1")
        assert config_a != config_b


@pytest.mark.unit
class TestTemplateConfigValidation:
    """TemplateConfig 验证测试。"""

    def test_empty_system_prompt_raises(self) -> None:
        with pytest.raises((ValueError, TypeError)):
            TemplateConfig(system_prompt="", model_id="model-1")

    def test_empty_model_id_raises(self) -> None:
        with pytest.raises((ValueError, TypeError)):
            TemplateConfig(system_prompt="测试", model_id="")

    def test_temperature_below_zero_raises(self) -> None:
        with pytest.raises((ValueError, TypeError)):
            TemplateConfig(system_prompt="测试", model_id="model-1", temperature=-0.1)

    def test_temperature_above_one_raises(self) -> None:
        with pytest.raises((ValueError, TypeError)):
            TemplateConfig(system_prompt="测试", model_id="model-1", temperature=1.1)

    def test_max_tokens_below_one_raises(self) -> None:
        with pytest.raises((ValueError, TypeError)):
            TemplateConfig(system_prompt="测试", model_id="model-1", max_tokens=0)

    def test_temperature_boundary_zero(self) -> None:
        config = TemplateConfig(system_prompt="测试", model_id="model-1", temperature=0.0)
        assert config.temperature == 0.0

    def test_temperature_boundary_one(self) -> None:
        config = TemplateConfig(system_prompt="测试", model_id="model-1", temperature=1.0)
        assert config.temperature == 1.0
