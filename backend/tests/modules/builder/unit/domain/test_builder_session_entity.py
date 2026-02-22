"""BuilderSession 实体单元测试 — 状态机全路径。"""

import pytest

from src.modules.builder.domain.entities.builder_session import BuilderSession
from src.modules.builder.domain.value_objects.builder_status import BuilderStatus
from src.shared.domain.exceptions import InvalidStateTransitionError
from tests.modules.builder.conftest import SAMPLE_GENERATED_CONFIG, make_builder_session


@pytest.mark.unit
class TestBuilderSessionEntity:
    """BuilderSession 实体测试。"""

    def test_create_default_status_is_pending(self) -> None:
        session = BuilderSession(user_id=1, prompt="测试提示")
        assert session.status == BuilderStatus.PENDING
        assert session.generated_config is None
        assert session.agent_name is None
        assert session.created_agent_id is None

    # ── 合法状态转换 ──

    def test_start_generation_from_pending(self) -> None:
        session = make_builder_session(status=BuilderStatus.PENDING)
        session.start_generation()
        assert session.status == BuilderStatus.GENERATING

    def test_complete_generation_from_generating(self) -> None:
        session = make_builder_session(status=BuilderStatus.GENERATING)
        session.complete_generation(config=SAMPLE_GENERATED_CONFIG, name="测试Agent")
        assert session.status == BuilderStatus.CONFIRMED
        assert session.generated_config == SAMPLE_GENERATED_CONFIG
        assert session.agent_name == "测试Agent"

    def test_confirm_creation_from_confirmed(self) -> None:
        session = make_builder_session(
            status=BuilderStatus.CONFIRMED,
            generated_config=SAMPLE_GENERATED_CONFIG,
            agent_name="测试Agent",
        )
        session.confirm_creation(agent_id=42)
        assert session.status == BuilderStatus.CONFIRMED
        assert session.created_agent_id == 42

    def test_cancel_from_pending(self) -> None:
        session = make_builder_session(status=BuilderStatus.PENDING)
        session.cancel()
        assert session.status == BuilderStatus.CANCELLED

    def test_cancel_from_generating(self) -> None:
        session = make_builder_session(status=BuilderStatus.GENERATING)
        session.cancel()
        assert session.status == BuilderStatus.CANCELLED

    # ── 非法状态转换 ──

    def test_start_generation_from_generating_raises(self) -> None:
        session = make_builder_session(status=BuilderStatus.GENERATING)
        with pytest.raises(InvalidStateTransitionError):
            session.start_generation()

    def test_start_generation_from_confirmed_raises(self) -> None:
        session = make_builder_session(status=BuilderStatus.CONFIRMED)
        with pytest.raises(InvalidStateTransitionError):
            session.start_generation()

    def test_start_generation_from_cancelled_raises(self) -> None:
        session = make_builder_session(status=BuilderStatus.CANCELLED)
        with pytest.raises(InvalidStateTransitionError):
            session.start_generation()

    def test_complete_generation_from_pending_raises(self) -> None:
        session = make_builder_session(status=BuilderStatus.PENDING)
        with pytest.raises(InvalidStateTransitionError):
            session.complete_generation(config={}, name="x")

    def test_complete_generation_from_confirmed_raises(self) -> None:
        session = make_builder_session(status=BuilderStatus.CONFIRMED)
        with pytest.raises(InvalidStateTransitionError):
            session.complete_generation(config={}, name="x")

    def test_complete_generation_from_cancelled_raises(self) -> None:
        session = make_builder_session(status=BuilderStatus.CANCELLED)
        with pytest.raises(InvalidStateTransitionError):
            session.complete_generation(config={}, name="x")

    def test_confirm_creation_from_pending_raises(self) -> None:
        session = make_builder_session(status=BuilderStatus.PENDING)
        with pytest.raises(InvalidStateTransitionError):
            session.confirm_creation(agent_id=1)

    def test_confirm_creation_from_generating_raises(self) -> None:
        session = make_builder_session(status=BuilderStatus.GENERATING)
        with pytest.raises(InvalidStateTransitionError):
            session.confirm_creation(agent_id=1)

    def test_confirm_creation_from_cancelled_raises(self) -> None:
        session = make_builder_session(status=BuilderStatus.CANCELLED)
        with pytest.raises(InvalidStateTransitionError):
            session.confirm_creation(agent_id=1)

    def test_cancel_from_confirmed_raises(self) -> None:
        session = make_builder_session(status=BuilderStatus.CONFIRMED)
        with pytest.raises(InvalidStateTransitionError):
            session.cancel()

    def test_cancel_from_cancelled_raises(self) -> None:
        session = make_builder_session(status=BuilderStatus.CANCELLED)
        with pytest.raises(InvalidStateTransitionError):
            session.cancel()

    # ── touch 时间戳更新 ──

    def test_start_generation_updates_timestamp(self) -> None:
        session = make_builder_session(status=BuilderStatus.PENDING)
        old_updated = session.updated_at
        session.start_generation()
        assert session.updated_at is not None
        assert old_updated is not None
        assert session.updated_at >= old_updated

    # ── 完整生命周期 ──

    def test_full_lifecycle_pending_to_confirmed_with_agent(self) -> None:
        """PENDING -> GENERATING -> CONFIRMED -> confirm_creation"""
        session = make_builder_session(status=BuilderStatus.PENDING)
        session.start_generation()
        assert session.status == BuilderStatus.GENERATING
        session.complete_generation(config=SAMPLE_GENERATED_CONFIG, name="测试")
        assert session.status == BuilderStatus.CONFIRMED
        session.confirm_creation(agent_id=99)
        assert session.created_agent_id == 99

    def test_full_lifecycle_pending_to_cancelled(self) -> None:
        """PENDING -> CANCELLED"""
        session = make_builder_session(status=BuilderStatus.PENDING)
        session.cancel()
        assert session.status == BuilderStatus.CANCELLED

    def test_full_lifecycle_generating_to_cancelled(self) -> None:
        """PENDING -> GENERATING -> CANCELLED"""
        session = make_builder_session(status=BuilderStatus.PENDING)
        session.start_generation()
        session.cancel()
        assert session.status == BuilderStatus.CANCELLED
