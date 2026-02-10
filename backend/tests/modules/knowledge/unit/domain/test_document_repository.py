"""IDocumentRepository 接口测试。"""

import pytest

from src.modules.knowledge.domain.repositories.document_repository import (
    IDocumentRepository,
)
from src.shared.domain.repositories import IRepository


@pytest.mark.unit
class TestIDocumentRepository:
    def test_is_abstract(self) -> None:
        assert hasattr(IDocumentRepository, "list_by_knowledge_base")
        assert hasattr(IDocumentRepository, "count_by_knowledge_base")

    def test_inherits_irepository(self) -> None:
        assert issubclass(IDocumentRepository, IRepository)
