"""Execution API schemas 单元测试。"""

from datetime import datetime

import pytest
from pydantic import ValidationError

from src.modules.execution.api.schemas.requests import CreateConversationRequest, SendMessageRequest
from src.modules.execution.api.schemas.responses import (
    ConversationDetailResponse,
    ConversationListResponse,
    ConversationResponse,
    MessageResponse,
)


@pytest.mark.unit
class TestCreateConversationRequest:
    """CreateConversationRequest 验证测试。"""

    def test_valid_request_with_defaults(self) -> None:
        req = CreateConversationRequest(agent_id=1)
        assert req.agent_id == 1
        assert req.title == ""

    def test_valid_request_with_title(self) -> None:
        req = CreateConversationRequest(agent_id=1, title="测试对话")
        assert req.title == "测试对话"

    def test_title_too_long_raises(self) -> None:
        with pytest.raises(ValidationError, match="title"):
            CreateConversationRequest(agent_id=1, title="a" * 201)

    def test_missing_agent_id_raises(self) -> None:
        with pytest.raises(ValidationError, match="agent_id"):
            CreateConversationRequest()  # type: ignore[call-arg]


@pytest.mark.unit
class TestSendMessageRequest:
    """SendMessageRequest 验证测试。"""

    def test_valid_request(self) -> None:
        req = SendMessageRequest(content="你好")
        assert req.content == "你好"

    def test_empty_content_raises(self) -> None:
        with pytest.raises(ValidationError, match="content"):
            SendMessageRequest(content="")

    def test_content_too_long_raises(self) -> None:
        with pytest.raises(ValidationError, match="content"):
            SendMessageRequest(content="a" * 100001)

    def test_missing_content_raises(self) -> None:
        with pytest.raises(ValidationError, match="content"):
            SendMessageRequest()  # type: ignore[call-arg]


@pytest.mark.unit
class TestMessageResponse:
    """MessageResponse 序列化测试。"""

    def test_valid_response(self) -> None:
        now = datetime.now()
        resp = MessageResponse(
            id=1,
            conversation_id=10,
            role="user",
            content="你好",
            token_count=5,
            created_at=now,
        )
        assert resp.id == 1
        assert resp.conversation_id == 10
        assert resp.role == "user"


@pytest.mark.unit
class TestConversationResponse:
    """ConversationResponse 序列化测试。"""

    def test_valid_response(self) -> None:
        now = datetime.now()
        resp = ConversationResponse(
            id=1,
            title="测试对话",
            agent_id=1,
            user_id=1,
            status="active",
            message_count=0,
            total_tokens=0,
            created_at=now,
            updated_at=now,
        )
        assert resp.id == 1
        assert resp.status == "active"


@pytest.mark.unit
class TestConversationDetailResponse:
    """ConversationDetailResponse 序列化测试。"""

    def test_valid_response(self) -> None:
        now = datetime.now()
        conv = ConversationResponse(
            id=1, title="测试", agent_id=1, user_id=1,
            status="active", message_count=1, total_tokens=10,
            created_at=now, updated_at=now,
        )
        msg = MessageResponse(
            id=1, conversation_id=1, role="user",
            content="你好", token_count=5, created_at=now,
        )
        resp = ConversationDetailResponse(conversation=conv, messages=[msg])
        assert resp.conversation.id == 1
        assert len(resp.messages) == 1

    def test_empty_messages(self) -> None:
        now = datetime.now()
        conv = ConversationResponse(
            id=1, title="测试", agent_id=1, user_id=1,
            status="active", message_count=0, total_tokens=0,
            created_at=now, updated_at=now,
        )
        resp = ConversationDetailResponse(conversation=conv, messages=[])
        assert resp.messages == []


@pytest.mark.unit
class TestConversationListResponse:
    """ConversationListResponse 序列化测试。"""

    def test_empty_list(self) -> None:
        resp = ConversationListResponse(
            items=[], total=0, page=1, page_size=20, total_pages=0,
        )
        assert resp.items == []
        assert resp.total == 0

    def test_with_items(self) -> None:
        now = datetime.now()
        item = ConversationResponse(
            id=1, title="测试", agent_id=1, user_id=1,
            status="active", message_count=0, total_tokens=0,
            created_at=now, updated_at=now,
        )
        resp = ConversationListResponse(
            items=[item], total=1, page=1, page_size=20, total_pages=1,
        )
        assert len(resp.items) == 1
        assert resp.total_pages == 1
