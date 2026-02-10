"""KnowledgeBase 实体单元测试。"""

import pytest
from pydantic import ValidationError

from src.modules.knowledge.domain.entities.knowledge_base import KnowledgeBase
from src.modules.knowledge.domain.value_objects.knowledge_base_status import (
    KnowledgeBaseStatus,
)
from src.shared.domain.exceptions import InvalidStateTransitionError


@pytest.mark.unit
class TestKnowledgeBaseCreation:
    """创建 KnowledgeBase 实体测试。"""

    def test_create_with_defaults(self) -> None:
        kb = KnowledgeBase(name="测试知识库", owner_id=1)
        assert kb.name == "测试知识库"
        assert kb.description == ""
        assert kb.status == KnowledgeBaseStatus.CREATING
        assert kb.owner_id == 1
        assert kb.agent_id is None
        assert kb.bedrock_kb_id == ""
        assert kb.s3_prefix == ""

    def test_create_with_custom_fields(self) -> None:
        kb = KnowledgeBase(
            name="产品文档库",
            description="产品相关文档的知识库",
            owner_id=2,
            agent_id=10,
            bedrock_kb_id="kb-abc123",
            s3_prefix="knowledge/product/",
        )
        assert kb.name == "产品文档库"
        assert kb.description == "产品相关文档的知识库"
        assert kb.owner_id == 2
        assert kb.agent_id == 10
        assert kb.bedrock_kb_id == "kb-abc123"
        assert kb.s3_prefix == "knowledge/product/"

    def test_inherits_pydantic_entity(self) -> None:
        kb = KnowledgeBase(name="测试", owner_id=1)
        assert kb.id is None
        assert kb.created_at is not None
        assert kb.updated_at is not None

    def test_empty_name_raises(self) -> None:
        with pytest.raises(ValidationError, match="name"):
            KnowledgeBase(name="", owner_id=1)

    def test_name_too_long_raises(self) -> None:
        with pytest.raises(ValidationError, match="name"):
            KnowledgeBase(name="A" * 101, owner_id=1)


@pytest.mark.unit
class TestKnowledgeBaseActivate:
    """activate() 状态转换测试。"""

    @pytest.fixture
    def creating_kb(self) -> KnowledgeBase:
        return KnowledgeBase(name="测试知识库", owner_id=1)

    def test_activate_from_creating_succeeds(self, creating_kb: KnowledgeBase) -> None:
        creating_kb.activate()
        assert creating_kb.status == KnowledgeBaseStatus.ACTIVE

    def test_activate_updates_timestamp(self, creating_kb: KnowledgeBase) -> None:
        original = creating_kb.updated_at
        creating_kb.activate()
        assert creating_kb.updated_at is not None
        assert original is not None
        assert creating_kb.updated_at >= original

    @pytest.mark.parametrize(
        "status",
        [
            KnowledgeBaseStatus.ACTIVE,
            KnowledgeBaseStatus.SYNCING,
            KnowledgeBaseStatus.FAILED,
            KnowledgeBaseStatus.DELETED,
        ],
    )
    def test_activate_from_invalid_state_raises(self, status: KnowledgeBaseStatus) -> None:
        kb = KnowledgeBase(name="测试", owner_id=1)
        # 绕过状态机直接设置状态用于测试
        object.__setattr__(kb, "status", status)
        with pytest.raises(InvalidStateTransitionError, match="active"):
            kb.activate()


@pytest.mark.unit
class TestKnowledgeBaseStartSync:
    """start_sync() 状态转换测试。"""

    @pytest.fixture
    def active_kb(self) -> KnowledgeBase:
        kb = KnowledgeBase(name="测试知识库", owner_id=1)
        kb.activate()
        return kb

    def test_start_sync_from_active_succeeds(self, active_kb: KnowledgeBase) -> None:
        active_kb.start_sync()
        assert active_kb.status == KnowledgeBaseStatus.SYNCING

    def test_start_sync_updates_timestamp(self, active_kb: KnowledgeBase) -> None:
        original = active_kb.updated_at
        active_kb.start_sync()
        assert active_kb.updated_at is not None
        assert original is not None
        assert active_kb.updated_at >= original

    @pytest.mark.parametrize(
        "status",
        [
            KnowledgeBaseStatus.CREATING,
            KnowledgeBaseStatus.SYNCING,
            KnowledgeBaseStatus.FAILED,
            KnowledgeBaseStatus.DELETED,
        ],
    )
    def test_start_sync_from_invalid_state_raises(self, status: KnowledgeBaseStatus) -> None:
        kb = KnowledgeBase(name="测试", owner_id=1)
        object.__setattr__(kb, "status", status)
        with pytest.raises(InvalidStateTransitionError, match="syncing"):
            kb.start_sync()


@pytest.mark.unit
class TestKnowledgeBaseCompleteSync:
    """complete_sync() 状态转换测试。"""

    @pytest.fixture
    def syncing_kb(self) -> KnowledgeBase:
        kb = KnowledgeBase(name="测试知识库", owner_id=1)
        kb.activate()
        kb.start_sync()
        return kb

    def test_complete_sync_from_syncing_succeeds(self, syncing_kb: KnowledgeBase) -> None:
        syncing_kb.complete_sync()
        assert syncing_kb.status == KnowledgeBaseStatus.ACTIVE

    def test_complete_sync_updates_timestamp(self, syncing_kb: KnowledgeBase) -> None:
        original = syncing_kb.updated_at
        syncing_kb.complete_sync()
        assert syncing_kb.updated_at is not None
        assert original is not None
        assert syncing_kb.updated_at >= original

    @pytest.mark.parametrize(
        "status",
        [
            KnowledgeBaseStatus.CREATING,
            KnowledgeBaseStatus.ACTIVE,
            KnowledgeBaseStatus.FAILED,
            KnowledgeBaseStatus.DELETED,
        ],
    )
    def test_complete_sync_from_invalid_state_raises(self, status: KnowledgeBaseStatus) -> None:
        kb = KnowledgeBase(name="测试", owner_id=1)
        object.__setattr__(kb, "status", status)
        with pytest.raises(InvalidStateTransitionError, match="active"):
            kb.complete_sync()


@pytest.mark.unit
class TestKnowledgeBaseFail:
    """fail() 状态转换测试。"""

    def test_fail_from_creating_succeeds(self) -> None:
        kb = KnowledgeBase(name="测试知识库", owner_id=1)
        kb.fail("初始化失败")
        assert kb.status == KnowledgeBaseStatus.FAILED

    def test_fail_from_syncing_succeeds(self) -> None:
        kb = KnowledgeBase(name="测试知识库", owner_id=1)
        kb.activate()
        kb.start_sync()
        kb.fail("同步失败")
        assert kb.status == KnowledgeBaseStatus.FAILED

    def test_fail_updates_timestamp(self) -> None:
        kb = KnowledgeBase(name="测试知识库", owner_id=1)
        original = kb.updated_at
        kb.fail()
        assert kb.updated_at is not None
        assert original is not None
        assert kb.updated_at >= original

    def test_fail_with_empty_reason(self) -> None:
        kb = KnowledgeBase(name="测试知识库", owner_id=1)
        kb.fail()
        assert kb.status == KnowledgeBaseStatus.FAILED

    @pytest.mark.parametrize(
        "status",
        [
            KnowledgeBaseStatus.ACTIVE,
            KnowledgeBaseStatus.FAILED,
            KnowledgeBaseStatus.DELETED,
        ],
    )
    def test_fail_from_invalid_state_raises(self, status: KnowledgeBaseStatus) -> None:
        kb = KnowledgeBase(name="测试", owner_id=1)
        object.__setattr__(kb, "status", status)
        with pytest.raises(InvalidStateTransitionError, match="failed"):
            kb.fail()


@pytest.mark.unit
class TestKnowledgeBaseMarkDeleted:
    """mark_deleted() 状态转换测试。"""

    def test_mark_deleted_from_active_succeeds(self) -> None:
        kb = KnowledgeBase(name="测试知识库", owner_id=1)
        kb.activate()
        kb.mark_deleted()
        assert kb.status == KnowledgeBaseStatus.DELETED

    def test_mark_deleted_from_failed_succeeds(self) -> None:
        kb = KnowledgeBase(name="测试知识库", owner_id=1)
        kb.fail()
        kb.mark_deleted()
        assert kb.status == KnowledgeBaseStatus.DELETED

    def test_mark_deleted_updates_timestamp(self) -> None:
        kb = KnowledgeBase(name="测试知识库", owner_id=1)
        kb.activate()
        original = kb.updated_at
        kb.mark_deleted()
        assert kb.updated_at is not None
        assert original is not None
        assert kb.updated_at >= original

    @pytest.mark.parametrize(
        "status",
        [
            KnowledgeBaseStatus.CREATING,
            KnowledgeBaseStatus.SYNCING,
            KnowledgeBaseStatus.DELETED,
        ],
    )
    def test_mark_deleted_from_invalid_state_raises(self, status: KnowledgeBaseStatus) -> None:
        kb = KnowledgeBase(name="测试", owner_id=1)
        object.__setattr__(kb, "status", status)
        with pytest.raises(InvalidStateTransitionError, match="deleted"):
            kb.mark_deleted()
