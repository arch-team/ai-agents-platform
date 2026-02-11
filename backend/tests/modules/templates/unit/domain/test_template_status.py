"""TemplateStatus 枚举单元测试。"""

import pytest

from src.modules.templates.domain.value_objects.template_status import TemplateStatus


@pytest.mark.unit
class TestTemplateStatus:
    """TemplateStatus 枚举值验证。"""

    def test_draft_value(self) -> None:
        assert TemplateStatus.DRAFT == "draft"

    def test_published_value(self) -> None:
        assert TemplateStatus.PUBLISHED == "published"

    def test_archived_value(self) -> None:
        assert TemplateStatus.ARCHIVED == "archived"

    def test_status_count(self) -> None:
        assert len(TemplateStatus) == 3

    def test_is_str_enum(self) -> None:
        assert isinstance(TemplateStatus.DRAFT, str)
