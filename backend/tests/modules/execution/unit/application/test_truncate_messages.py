"""对话历史滑动窗口 (_truncate_messages) 单元测试。"""

import pytest

# 直接测试静态方法, 无需构建完整 ExecutionService
from src.modules.execution.application.services.execution_service import (
    ExecutionService,
)
from src.modules.execution.domain.entities.message import Message
from src.modules.execution.domain.value_objects.message_role import MessageRole


def _make_messages(count: int, *, token_count: int = 100) -> list[Message]:
    """创建指定数量的测试消息。"""
    messages = []
    for i in range(count):
        role = MessageRole.USER if i % 2 == 0 else MessageRole.ASSISTANT
        messages.append(
            Message(
                id=i + 1,
                conversation_id=1,
                role=role,
                content=f"消息 {i + 1}",
                token_count=token_count,
            ),
        )
    return messages


@pytest.mark.unit
class TestTruncateMessages:
    """_truncate_messages 静态方法测试。"""

    def test_empty_list_returns_empty(self) -> None:
        """空消息列表应返回空列表。"""
        result = ExecutionService._truncate_messages([], max_tokens=30000)
        assert result == []

    def test_single_message_within_budget(self) -> None:
        """单条消息在预算内应保留。"""
        messages = _make_messages(1, token_count=100)
        result = ExecutionService._truncate_messages(messages, max_tokens=30000)
        assert len(result) == 1

    def test_all_messages_within_budget(self) -> None:
        """所有消息总量在预算内应全部保留。"""
        messages = _make_messages(5, token_count=100)
        result = ExecutionService._truncate_messages(messages, max_tokens=30000)
        assert len(result) == 5

    def test_truncates_old_messages(self) -> None:
        """超出预算时应保留首条 + 最新消息, 丢弃中间消息。"""
        messages = _make_messages(10, token_count=1000)
        # max_tokens=3000 容纳 3 条: 首条(id=1) + 最新 2 条(id=9,10)
        result = ExecutionService._truncate_messages(messages, max_tokens=3000)
        assert len(result) == 3
        assert result[0].id == 1  # 首条保留
        assert result[1].id == 9
        assert result[2].id == 10

    def test_preserves_time_order(self) -> None:
        """截取后的消息应保持时间正序。"""
        messages = _make_messages(10, token_count=500)
        result = ExecutionService._truncate_messages(messages, max_tokens=2000)
        ids = [m.id for m in result]
        assert ids == sorted(ids)

    def test_exact_budget_includes_all(self) -> None:
        """消息总量刚好等于预算时应全部保留。"""
        messages = _make_messages(5, token_count=200)
        # 5 * 200 = 1000
        result = ExecutionService._truncate_messages(messages, max_tokens=1000)
        assert len(result) == 5

    def test_uses_char_estimation_when_token_count_zero(self) -> None:
        """token_count 为 0 时应使用字符估算 (2 chars/token)。"""
        messages = [
            Message(
                id=1,
                conversation_id=1,
                role=MessageRole.USER,
                content="a" * 2000,  # ~1000 tokens (2 chars/token)
                token_count=0,
            ),
            Message(
                id=2,
                conversation_id=1,
                role=MessageRole.ASSISTANT,
                content="b" * 2000,
                token_count=0,
            ),
            Message(
                id=3,
                conversation_id=1,
                role=MessageRole.USER,
                content="c" * 2000,
                token_count=0,
            ),
        ]
        # max_tokens=2000, 每条估算 ~1000 tokens
        # 保留首条(id=1, 1000 tokens) + 最新 1 条(id=3, 1000 tokens) = 2 条
        result = ExecutionService._truncate_messages(messages, max_tokens=2000)
        assert len(result) == 2
        assert result[0].id == 1  # 首条保留
        assert result[1].id == 3

    def test_hundred_messages_truncated(self) -> None:
        """100 条消息时应正确截取。"""
        messages = _make_messages(100, token_count=500)
        # max_tokens=28000, system prompt 预留后可容纳 28000/500 = 56 条
        result = ExecutionService._truncate_messages(messages, max_tokens=28000)
        assert len(result) == 56
        assert len(result) < 100
