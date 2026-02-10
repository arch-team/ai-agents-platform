"""文档状态枚举。"""

from enum import StrEnum


class DocumentStatus(StrEnum):
    """文档生命周期状态。"""

    UPLOADING = "uploading"
    PROCESSING = "processing"
    INDEXED = "indexed"
    FAILED = "failed"
