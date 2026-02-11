"""Template DTO 单元测试。"""

import pytest

from src.modules.templates.application.dto.template_dto import (
    CreateTemplateDTO,
    InstantiateTemplateDTO,
    PagedTemplateDTO,
    UpdateTemplateDTO,
)


@pytest.mark.unit
class TestCreateTemplateDTO:
    """CreateTemplateDTO 测试。"""

    def test_create_with_required_fields(self) -> None:
        dto = CreateTemplateDTO(
            name="客服模板",
            description="客服场景",
            category="customer_service",
            system_prompt="你是客服",
            model_id="anthropic.claude-v3",
        )
        assert dto.name == "客服模板"
        assert dto.temperature == 0.7
        assert dto.max_tokens == 4096
        assert dto.tool_ids == []
        assert dto.knowledge_base_ids == []
        assert dto.tags == []

    def test_create_with_all_fields(self) -> None:
        dto = CreateTemplateDTO(
            name="数据分析",
            description="数据分析场景",
            category="data_analysis",
            system_prompt="你是数据分析师",
            model_id="model-1",
            temperature=0.5,
            max_tokens=2048,
            tool_ids=[1, 2],
            knowledge_base_ids=[10],
            tags=["数据"],
        )
        assert dto.tool_ids == [1, 2]
        assert dto.tags == ["数据"]


@pytest.mark.unit
class TestUpdateTemplateDTO:
    """UpdateTemplateDTO 测试。"""

    def test_all_fields_optional(self) -> None:
        dto = UpdateTemplateDTO()
        assert dto.name is None
        assert dto.description is None
        assert dto.category is None
        assert dto.system_prompt is None
        assert dto.model_id is None
        assert dto.temperature is None
        assert dto.max_tokens is None
        assert dto.tool_ids is None
        assert dto.knowledge_base_ids is None
        assert dto.tags is None

    def test_partial_update(self) -> None:
        dto = UpdateTemplateDTO(name="新名称", tags=["标签A"])
        assert dto.name == "新名称"
        assert dto.tags == ["标签A"]
        assert dto.description is None


@pytest.mark.unit
class TestPagedTemplateDTO:
    """PagedTemplateDTO 测试。"""

    def test_empty_page(self) -> None:
        dto = PagedTemplateDTO(items=[], total=0, page=1, page_size=20)
        assert dto.items == []
        assert dto.total == 0


@pytest.mark.unit
class TestInstantiateTemplateDTO:
    """InstantiateTemplateDTO 测试。"""

    def test_create(self) -> None:
        dto = InstantiateTemplateDTO(template_id=1, agent_name="我的助手")
        assert dto.template_id == 1
        assert dto.agent_name == "我的助手"
