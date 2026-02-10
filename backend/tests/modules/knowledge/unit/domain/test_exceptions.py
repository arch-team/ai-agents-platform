"""knowledge 模块异常测试。"""

import pytest

from src.modules.knowledge.domain.exceptions import (
    DocumentNotFoundError,
    KnowledgeBaseNameDuplicateError,
    KnowledgeBaseNotFoundError,
)
from src.shared.domain.exceptions import DomainError


@pytest.mark.unit
class TestKnowledgeBaseNotFoundError:
    def test_message(self) -> None:
        err = KnowledgeBaseNotFoundError(42)
        assert "42" in str(err.message)
        assert err.code == "KNOWLEDGE_BASE_NOT_FOUND"
        assert isinstance(err, DomainError)


@pytest.mark.unit
class TestKnowledgeBaseNameDuplicateError:
    def test_message(self) -> None:
        err = KnowledgeBaseNameDuplicateError("test-kb", 10)
        assert "test-kb" in str(err.message)
        assert err.code == "KNOWLEDGE_BASE_NAME_DUPLICATE"


@pytest.mark.unit
class TestDocumentNotFoundError:
    def test_message(self) -> None:
        err = DocumentNotFoundError(99)
        assert "99" in str(err.message)
        assert err.code == "DOCUMENT_NOT_FOUND"
