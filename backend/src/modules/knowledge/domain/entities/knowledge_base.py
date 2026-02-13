"""知识库领域实体。"""

from pydantic import Field

from src.modules.knowledge.domain.value_objects.knowledge_base_status import (
    KnowledgeBaseStatus,
)
from src.shared.domain.base_entity import PydanticEntity


_FAILABLE = frozenset({KnowledgeBaseStatus.CREATING, KnowledgeBaseStatus.SYNCING})
_DELETABLE = frozenset({KnowledgeBaseStatus.ACTIVE, KnowledgeBaseStatus.FAILED})


class KnowledgeBase(PydanticEntity):
    """知识库实体。"""

    name: str = Field(min_length=1, max_length=100)
    description: str = ""
    status: KnowledgeBaseStatus = KnowledgeBaseStatus.CREATING
    owner_id: int
    agent_id: int | None = None
    bedrock_kb_id: str = ""
    s3_prefix: str = ""
    error_message: str = ""

    def activate(self) -> None:
        """激活知识库。CREATING -> ACTIVE。"""
        self._require_status(self.status, KnowledgeBaseStatus.CREATING, KnowledgeBaseStatus.ACTIVE.value)
        self.status = KnowledgeBaseStatus.ACTIVE
        self.touch()

    def start_sync(self) -> None:
        """开始同步。ACTIVE -> SYNCING。"""
        self._require_status(self.status, KnowledgeBaseStatus.ACTIVE, KnowledgeBaseStatus.SYNCING.value)
        self.status = KnowledgeBaseStatus.SYNCING
        self.touch()

    def complete_sync(self) -> None:
        """完成同步。SYNCING -> ACTIVE。"""
        self._require_status(self.status, KnowledgeBaseStatus.SYNCING, KnowledgeBaseStatus.ACTIVE.value)
        self.status = KnowledgeBaseStatus.ACTIVE
        self.touch()

    def fail(self, reason: str = "") -> None:
        """标记失败。CREATING/SYNCING -> FAILED。"""
        self._require_status(self.status, _FAILABLE, KnowledgeBaseStatus.FAILED.value)
        self.status = KnowledgeBaseStatus.FAILED
        self.error_message = reason
        self.touch()

    def mark_deleted(self) -> None:
        """标记删除。ACTIVE/FAILED -> DELETED。"""
        self._require_status(self.status, _DELETABLE, KnowledgeBaseStatus.DELETED.value)
        self.status = KnowledgeBaseStatus.DELETED
        self.touch()
