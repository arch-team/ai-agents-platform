"""知识库领域实体。"""

from pydantic import Field

from src.modules.knowledge.domain.value_objects.knowledge_base_status import (
    KnowledgeBaseStatus,
)
from src.shared.domain.base_entity import PydanticEntity
from src.shared.domain.exceptions import InvalidStateTransitionError


class KnowledgeBase(PydanticEntity):
    """知识库实体。"""

    name: str = Field(min_length=1, max_length=100)
    description: str = ""
    status: KnowledgeBaseStatus = KnowledgeBaseStatus.CREATING
    owner_id: int
    agent_id: int | None = None
    bedrock_kb_id: str = ""
    s3_prefix: str = ""

    def activate(self) -> None:
        """激活知识库。CREATING -> ACTIVE。"""
        if self.status != KnowledgeBaseStatus.CREATING:
            raise InvalidStateTransitionError(
                entity_type="KnowledgeBase",
                current_state=self.status.value,
                target_state=KnowledgeBaseStatus.ACTIVE.value,
            )
        self.status = KnowledgeBaseStatus.ACTIVE
        self.touch()

    def start_sync(self) -> None:
        """开始同步。ACTIVE -> SYNCING。"""
        if self.status != KnowledgeBaseStatus.ACTIVE:
            raise InvalidStateTransitionError(
                entity_type="KnowledgeBase",
                current_state=self.status.value,
                target_state=KnowledgeBaseStatus.SYNCING.value,
            )
        self.status = KnowledgeBaseStatus.SYNCING
        self.touch()

    def complete_sync(self) -> None:
        """完成同步。SYNCING -> ACTIVE。"""
        if self.status != KnowledgeBaseStatus.SYNCING:
            raise InvalidStateTransitionError(
                entity_type="KnowledgeBase",
                current_state=self.status.value,
                target_state=KnowledgeBaseStatus.ACTIVE.value,
            )
        self.status = KnowledgeBaseStatus.ACTIVE
        self.touch()

    def fail(self, reason: str = "") -> None:  # noqa: ARG002
        """标记失败。CREATING/SYNCING -> FAILED。"""
        if self.status not in {KnowledgeBaseStatus.CREATING, KnowledgeBaseStatus.SYNCING}:
            raise InvalidStateTransitionError(
                entity_type="KnowledgeBase",
                current_state=self.status.value,
                target_state=KnowledgeBaseStatus.FAILED.value,
            )
        self.status = KnowledgeBaseStatus.FAILED
        self.touch()

    def mark_deleted(self) -> None:
        """标记删除。ACTIVE/FAILED -> DELETED。"""
        if self.status not in {KnowledgeBaseStatus.ACTIVE, KnowledgeBaseStatus.FAILED}:
            raise InvalidStateTransitionError(
                entity_type="KnowledgeBase",
                current_state=self.status.value,
                target_state=KnowledgeBaseStatus.DELETED.value,
            )
        self.status = KnowledgeBaseStatus.DELETED
        self.touch()
