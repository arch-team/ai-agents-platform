"""DocumentStatus 枚举测试。"""

import pytest

from src.modules.knowledge.domain.value_objects.document_status import DocumentStatus


@pytest.mark.unit
class TestDocumentStatus:
    def test_uploading_value(self) -> None:
        assert DocumentStatus.UPLOADING == "uploading"

    def test_processing_value(self) -> None:
        assert DocumentStatus.PROCESSING == "processing"

    def test_indexed_value(self) -> None:
        assert DocumentStatus.INDEXED == "indexed"

    def test_failed_value(self) -> None:
        assert DocumentStatus.FAILED == "failed"

    def test_status_count(self) -> None:
        assert len(DocumentStatus) == 4

    def test_is_str_enum(self) -> None:
        assert isinstance(DocumentStatus.UPLOADING, str)
