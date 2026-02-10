"""文档领域实体。"""

from pydantic import Field

from src.modules.knowledge.domain.value_objects.document_status import (
    DocumentStatus,
)
from src.shared.domain.base_entity import PydanticEntity


_FAILABLE = frozenset({DocumentStatus.UPLOADING, DocumentStatus.PROCESSING})


class Document(PydanticEntity):
    """文档实体。"""

    knowledge_base_id: int
    filename: str = Field(min_length=1, max_length=255)
    s3_key: str = ""
    file_size: int = Field(default=0, ge=0)
    status: DocumentStatus = DocumentStatus.UPLOADING
    content_type: str = "application/octet-stream"
    chunk_count: int = Field(default=0, ge=0)

    def start_processing(self) -> None:
        """开始处理。UPLOADING -> PROCESSING。"""
        self._require_status(self.status, DocumentStatus.UPLOADING, DocumentStatus.PROCESSING.value)
        self.status = DocumentStatus.PROCESSING
        self.touch()

    def complete_indexing(self, *, chunk_count: int) -> None:
        """完成索引。PROCESSING -> INDEXED。"""
        self._require_status(self.status, DocumentStatus.PROCESSING, DocumentStatus.INDEXED.value)
        self.chunk_count = chunk_count
        self.status = DocumentStatus.INDEXED
        self.touch()

    def fail(self) -> None:
        """标记失败。UPLOADING/PROCESSING -> FAILED。"""
        self._require_status(self.status, _FAILABLE, DocumentStatus.FAILED.value)
        self.status = DocumentStatus.FAILED
        self.touch()
