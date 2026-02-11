"""ITemplateRepository 接口测试。"""

import pytest

from src.modules.templates.domain.repositories.template_repository import (
    ITemplateRepository,
)
from src.shared.domain.repositories import IRepository


@pytest.mark.unit
class TestITemplateRepository:
    """验证 ITemplateRepository 接口定义。"""

    def test_inherits_irepository(self) -> None:
        assert issubclass(ITemplateRepository, IRepository)

    def test_has_list_published(self) -> None:
        assert hasattr(ITemplateRepository, "list_published")

    def test_has_list_by_creator(self) -> None:
        assert hasattr(ITemplateRepository, "list_by_creator")

    def test_has_list_by_category(self) -> None:
        assert hasattr(ITemplateRepository, "list_by_category")

    def test_has_search(self) -> None:
        assert hasattr(ITemplateRepository, "search")

    def test_has_increment_usage_count(self) -> None:
        assert hasattr(ITemplateRepository, "increment_usage_count")

    def test_has_get_by_name(self) -> None:
        assert hasattr(ITemplateRepository, "get_by_name")
