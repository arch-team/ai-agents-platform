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


@pytest.mark.unit
class TestBuilderSessionV2Extensions:
    """V2 扩展字段和多轮迭代。"""

    def test_default_v2_fields(self) -> None:
        """V2 字段默认值正确。"""
        session = BuilderSession(user_id=1, prompt="测试")
        assert session.messages == []
        assert session.template_id is None
        assert session.selected_skill_ids == []
        assert session.generated_blueprint is None

    def test_create_with_messages(self) -> None:
        session = BuilderSession(
            user_id=1,
            prompt="测试",
            messages=[{"role": "user", "content": "你好"}],
        )
        assert len(session.messages) == 1
        assert session.messages[0]["role"] == "user"

    def test_create_with_template_and_skills(self) -> None:
        session = BuilderSession(
            user_id=1,
            prompt="测试",
            template_id=5,
            selected_skill_ids=[10, 20],
        )
        assert session.template_id == 5
        assert session.selected_skill_ids == [10, 20]

    def test_add_message(self) -> None:
        """添加消息到对话历史。"""
        session = make_builder_session()
        session.add_message("user", "请创建一个客服 Agent")
        session.add_message("assistant", "好的，让我们开始定义角色。")

        assert len(session.messages) == 2
        assert session.messages[0]["role"] == "user"
        assert session.messages[1]["role"] == "assistant"

    def test_complete_generation_with_blueprint(self) -> None:
        """V2: complete_generation 同时保存 blueprint。"""
        session = make_builder_session(status=BuilderStatus.GENERATING)
        blueprint = {"persona": {"role": "客服"}, "skills": []}
        session.complete_generation(config={}, name="测试", blueprint=blueprint)

        assert session.status == BuilderStatus.CONFIRMED
        assert session.generated_blueprint == blueprint

    def test_start_refinement_from_confirmed(self) -> None:
        """CONFIRMED -> GENERATING (多轮迭代)。"""
        session = make_builder_session(
            status=BuilderStatus.CONFIRMED,
            generated_config=SAMPLE_GENERATED_CONFIG,
        )
        session.start_refinement()
        assert session.status == BuilderStatus.GENERATING

    def test_start_refinement_from_pending_raises(self) -> None:
        session = make_builder_session(status=BuilderStatus.PENDING)
        with pytest.raises(InvalidStateTransitionError):
            session.start_refinement()

    def test_start_refinement_from_cancelled_raises(self) -> None:
        session = make_builder_session(status=BuilderStatus.CANCELLED)
        with pytest.raises(InvalidStateTransitionError):
            session.start_refinement()

    def test_full_v2_lifecycle_with_refinement(self) -> None:
        """V2 完整生命周期: PENDING → GENERATING → CONFIRMED → GENERATING → CONFIRMED → create"""
        session = make_builder_session(status=BuilderStatus.PENDING)

        # 第一轮
        session.start_generation()
        blueprint_v1 = {"persona": {"role": "客服v1"}}
        session.complete_generation(config={}, name="v1", blueprint=blueprint_v1)
        assert session.generated_blueprint == blueprint_v1

        # 用户要求修改 → 多轮迭代
        session.start_refinement()
        assert session.status == BuilderStatus.GENERATING

        blueprint_v2 = {"persona": {"role": "客服v2"}, "skills": [{"name": "退货"}]}
        session.complete_generation(config={}, name="v2", blueprint=blueprint_v2)
        assert session.generated_blueprint == blueprint_v2

        # 确认创建
        session.confirm_creation(agent_id=99)
        assert session.created_agent_id == 99
