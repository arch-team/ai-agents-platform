"""knowledge 模块异常测试。"""

import pytest

from src.modules.knowledge.domain.exceptions import (
    DocumentNotFoundError,
    KnowledgeBaseNameDuplicateError,
    KnowledgeBaseNotFoundError,
)
from src.shared.domain.exceptions import (
    DomainError,
    DuplicateEntityError,
    EntityNotFoundError,
)


@pytest.mark.unit
class TestKnowledgeBaseNotFoundError:
    def test_message(self) -> None:
        err = KnowledgeBaseNotFoundError(42)
        assert "42" in str(err.message)
        assert err.code == "NOT_FOUND_KNOWLEDGEBASE"
        assert isinstance(err, EntityNotFoundError)
        assert isinstance(err, DomainError)

    def test_entity_attributes(self) -> None:
        err = KnowledgeBaseNotFoundError(42)
        assert err.entity_type == "KnowledgeBase"
        assert err.entity_id == 42


@pytest.mark.unit
class TestKnowledgeBaseNameDuplicateError:
    def test_message(self) -> None:
        err = KnowledgeBaseNameDuplicateError("test-kb", 10)
        assert "test-kb" in str(err.message)
        assert err.code == "DUPLICATE_KNOWLEDGEBASE"
        assert isinstance(err, DuplicateEntityError)

    def test_owner_id(self) -> None:
        err = KnowledgeBaseNameDuplicateError("test-kb", 10)
        assert err.owner_id == 10


@pytest.mark.unit
class TestDocumentNotFoundError:
    def test_message(self) -> None:
        err = DocumentNotFoundError(99)
        assert "99" in str(err.message)
        assert err.code == "NOT_FOUND_DOCUMENT"
        assert isinstance(err, EntityNotFoundError)
