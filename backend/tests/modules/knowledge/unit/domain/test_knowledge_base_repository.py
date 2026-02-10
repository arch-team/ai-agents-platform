"""IKnowledgeBaseRepository 接口测试。"""

import pytest

from src.modules.knowledge.domain.repositories.knowledge_base_repository import (
    IKnowledgeBaseRepository,
)
from src.shared.domain.repositories import IRepository


@pytest.mark.unit
class TestIKnowledgeBaseRepository:
    def test_is_abstract(self) -> None:
        assert hasattr(IKnowledgeBaseRepository, "get_by_name_and_owner")
        assert hasattr(IKnowledgeBaseRepository, "list_by_owner")
        assert hasattr(IKnowledgeBaseRepository, "count_by_owner")

    def test_inherits_irepository(self) -> None:
        assert issubclass(IKnowledgeBaseRepository, IRepository)
