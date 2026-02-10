"""KnowledgeBaseStatus 枚举单元测试。"""

import pytest

from src.modules.knowledge.domain.value_objects.knowledge_base_status import (
    KnowledgeBaseStatus,
)


@pytest.mark.unit
class TestKnowledgeBaseStatus:
    """KnowledgeBaseStatus 枚举值验证。"""

    def test_creating_value(self) -> None:
        assert KnowledgeBaseStatus.CREATING == "creating"

    def test_active_value(self) -> None:
        assert KnowledgeBaseStatus.ACTIVE == "active"

    def test_syncing_value(self) -> None:
        assert KnowledgeBaseStatus.SYNCING == "syncing"

    def test_failed_value(self) -> None:
        assert KnowledgeBaseStatus.FAILED == "failed"

    def test_deleted_value(self) -> None:
        assert KnowledgeBaseStatus.DELETED == "deleted"

    def test_status_count(self) -> None:
        assert len(KnowledgeBaseStatus) == 5

    def test_is_str_enum(self) -> None:
        assert isinstance(KnowledgeBaseStatus.CREATING, str)
