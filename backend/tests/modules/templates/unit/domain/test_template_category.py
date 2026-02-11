"""TemplateCategory 枚举单元测试。"""

import pytest

from src.modules.templates.domain.value_objects.template_category import (
    TemplateCategory,
)


@pytest.mark.unit
class TestTemplateCategory:
    """TemplateCategory 枚举值验证。"""

    def test_customer_service_value(self) -> None:
        assert TemplateCategory.CUSTOMER_SERVICE == "customer_service"

    def test_code_assistant_value(self) -> None:
        assert TemplateCategory.CODE_ASSISTANT == "code_assistant"

    def test_data_analysis_value(self) -> None:
        assert TemplateCategory.DATA_ANALYSIS == "data_analysis"

    def test_content_creation_value(self) -> None:
        assert TemplateCategory.CONTENT_CREATION == "content_creation"

    def test_research_value(self) -> None:
        assert TemplateCategory.RESEARCH == "research"

    def test_workflow_automation_value(self) -> None:
        assert TemplateCategory.WORKFLOW_AUTOMATION == "workflow_automation"

    def test_general_value(self) -> None:
        assert TemplateCategory.GENERAL == "general"

    def test_category_count(self) -> None:
        assert len(TemplateCategory) == 7

    def test_is_str_enum(self) -> None:
        assert isinstance(TemplateCategory.GENERAL, str)
