"""UsageRecord 实体单元测试。"""

from datetime import UTC, datetime

import pytest

from src.modules.insights.domain.entities.usage_record import UsageRecord
from src.shared.domain.base_entity import PydanticEntity


@pytest.mark.unit
class TestUsageRecordCreation:
    """创建 UsageRecord 实体测试。"""

    def test_create_with_required_fields(self) -> None:
        record = UsageRecord(
            user_id=1,
            agent_id=2,
            conversation_id=100,
            model_id="us.anthropic.claude-sonnet-4-6-20260819-v1:0",
            tokens_input=1000,
            tokens_output=500,
            estimated_cost=0.0105,
        )
        assert record.user_id == 1
        assert record.agent_id == 2
        assert record.conversation_id == 100
        assert record.model_id == "us.anthropic.claude-sonnet-4-6-20260819-v1:0"
        assert record.tokens_input == 1000
        assert record.tokens_output == 500
        assert record.estimated_cost == 0.0105
        assert record.recorded_at is not None

    def test_create_with_custom_recorded_at(self) -> None:
        custom_time = datetime(2025, 1, 15, 10, 30, 0, tzinfo=UTC)
        record = UsageRecord(
            user_id=1,
            agent_id=2,
            conversation_id=100,
            model_id="us.anthropic.claude-sonnet-4-6-20260819-v1:0",
            tokens_input=500,
            tokens_output=200,
            estimated_cost=0.005,
            recorded_at=custom_time,
        )
        assert record.recorded_at == custom_time

    def test_inherits_pydantic_entity(self) -> None:
        record = UsageRecord(
            user_id=1,
            agent_id=2,
            conversation_id=100,
            model_id="model-a",
            tokens_input=100,
            tokens_output=50,
            estimated_cost=0.001,
        )
        assert isinstance(record, PydanticEntity)
        assert record.id is None
        assert record.created_at is not None
        assert record.updated_at is not None

    def test_default_recorded_at_is_set(self) -> None:
        """recorded_at 默认应自动设置。"""
        record = UsageRecord(
            user_id=1,
            agent_id=2,
            conversation_id=100,
            model_id="model-a",
            tokens_input=100,
            tokens_output=50,
            estimated_cost=0.001,
        )
        assert record.recorded_at is not None

    def test_create_without_conversation_id(self) -> None:
        """团队执行场景: conversation_id 可为 None。"""
        record = UsageRecord(
            user_id=1,
            agent_id=2,
            model_id="anthropic.claude-sonnet",
            tokens_input=500,
            tokens_output=200,
            estimated_cost=0.005,
        )
        assert record.conversation_id is None
        assert record.user_id == 1

    def test_create_with_explicit_none_conversation_id(self) -> None:
        """显式传入 conversation_id=None。"""
        record = UsageRecord(
            user_id=1,
            agent_id=2,
            conversation_id=None,
            model_id="anthropic.claude-sonnet",
            tokens_input=500,
            tokens_output=200,
            estimated_cost=0.005,
        )
        assert record.conversation_id is None

    def test_total_tokens_property(self) -> None:
        """total_tokens 属性应返回输入和输出 token 的总和。"""
        record = UsageRecord(
            user_id=1,
            agent_id=2,
            conversation_id=100,
            model_id="model-a",
            tokens_input=1000,
            tokens_output=500,
            estimated_cost=0.01,
        )
        assert record.total_tokens == 1500


@pytest.mark.unit
class TestUsageRecordEquality:
    """UsageRecord 相等性测试。"""

    def test_equality_by_id(self) -> None:
        r1 = UsageRecord(
            user_id=1,
            agent_id=2,
            conversation_id=100,
            model_id="model-a",
            tokens_input=100,
            tokens_output=50,
            estimated_cost=0.001,
        )
        r2 = UsageRecord(
            user_id=3,
            agent_id=4,
            conversation_id=200,
            model_id="model-b",
            tokens_input=200,
            tokens_output=100,
            estimated_cost=0.002,
        )
        # 设置相同 id
        object.__setattr__(r1, "id", 1)
        object.__setattr__(r2, "id", 1)
        assert r1 == r2

    def test_none_id_uses_identity(self) -> None:
        r1 = UsageRecord(
            user_id=1,
            agent_id=2,
            conversation_id=100,
            model_id="model-a",
            tokens_input=100,
            tokens_output=50,
            estimated_cost=0.001,
        )
        r2 = UsageRecord(
            user_id=1,
            agent_id=2,
            conversation_id=100,
            model_id="model-a",
            tokens_input=100,
            tokens_output=50,
            estimated_cost=0.001,
        )
        assert r1 != r2  # id 为 None 时使用 identity 比较
