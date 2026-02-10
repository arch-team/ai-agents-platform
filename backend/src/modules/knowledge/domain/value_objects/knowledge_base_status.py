"""知识库状态枚举。"""

from enum import StrEnum


class KnowledgeBaseStatus(StrEnum):
    """知识库生命周期状态。"""

    CREATING = "creating"
    ACTIVE = "active"
    SYNCING = "syncing"
    FAILED = "failed"
    DELETED = "deleted"
