"""Execution API endpoint integration tests."""

from datetime import datetime
from unittest.mock import AsyncMock

import pytest
from fastapi.testclient import TestClient

from src.modules.auth.api.dependencies import get_current_user
from src.modules.auth.application.dto.user_dto import UserDTO
from src.modules.execution.api.dependencies import get_execution_service
from src.modules.execution.application.dto.execution_dto import (
    ConversationDetailDTO,
    ConversationDTO,
    MessageDTO,
)
from src.modules.execution.domain.exceptions import (
    AgentNotAvailableError,
    ConversationNotActiveError,
    ConversationNotFoundError,
)
from src.presentation.api.main import create_app
from src.shared.application.dtos import PagedResult
from src.shared.domain.exceptions import DomainError


def _make_user_dto(
    *,
    user_id: int = 1,
    email: str = "test@example.com",
    name: str = "Test User",
    role: str = "developer",
    is_active: bool = True,
) -> UserDTO:
    return UserDTO(id=user_id, email=email, name=name, role=role, is_active=is_active)


def _make_conversation_dto(
    *,
    conversation_id: int = 1,
    title: str = "测试对话",
    agent_id: int = 1,
    user_id: int = 1,
    status: str = "active",
    message_count: int = 0,
    total_tokens: int = 0,
) -> ConversationDTO:
    now = datetime.now()
    return ConversationDTO(
        id=conversation_id,
        title=title,
        agent_id=agent_id,
        user_id=user_id,
        status=status,
        message_count=message_count,
        total_tokens=total_tokens,
        created_at=now,
        updated_at=now,
    )


def _make_message_dto(
    *,
    message_id: int = 1,
    conversation_id: int = 1,
    role: str = "assistant",
    content: str = "你好，有什么可以帮你的？",
    token_count: int = 100,
) -> MessageDTO:
    return MessageDTO(
        id=message_id,
        conversation_id=conversation_id,
        role=role,
        content=content,
        token_count=token_count,
        created_at=datetime.now(),
    )


@pytest.fixture
def mock_service() -> AsyncMock:
    return AsyncMock()


@pytest.fixture
def mock_user() -> UserDTO:
    return _make_user_dto()


@pytest.fixture
def app(mock_service: AsyncMock, mock_user: UserDTO):
    test_app = create_app()
    test_app.dependency_overrides[get_execution_service] = lambda: mock_service
    test_app.dependency_overrides[get_current_user] = lambda: mock_user
    return test_app


@pytest.fixture
def client(app) -> TestClient:
    return TestClient(app)


@pytest.mark.integration
class TestCreateConversationEndpoint:
    """POST /api/v1/conversations tests."""

    def test_create_success(self, client: TestClient, mock_service: AsyncMock) -> None:
        """201 + 返回 ConversationResponse。"""
        mock_service.create_conversation.return_value = _make_conversation_dto()

        response = client.post(
            "/api/v1/conversations",
            json={"agent_id": 1, "title": "测试对话"},
        )

        assert response.status_code == 201
        data = response.json()
        assert data["title"] == "测试对话"
        assert data["status"] == "active"
        assert data["agent_id"] == 1
        mock_service.create_conversation.assert_called_once()

    def test_create_agent_not_available(self, client: TestClient, mock_service: AsyncMock) -> None:
        """409 Agent 不可用。"""
        mock_service.create_conversation.side_effect = AgentNotAvailableError(999)

        response = client.post(
            "/api/v1/conversations",
            json={"agent_id": 999},
        )

        assert response.status_code == 409
        data = response.json()
        assert "AGENT_NOT_AVAILABLE" in data["code"]

    def test_create_without_auth(self, mock_service: AsyncMock) -> None:
        """401 未认证。"""
        test_app = create_app()
        test_app.dependency_overrides[get_execution_service] = lambda: mock_service
        unauthenticated_client = TestClient(test_app)

        response = unauthenticated_client.post(
            "/api/v1/conversations",
            json={"agent_id": 1},
        )

        assert response.status_code in (401, 403)

    def test_create_missing_agent_id(self, client: TestClient) -> None:
        """422 缺少 agent_id。"""
        response = client.post(
            "/api/v1/conversations",
            json={"title": "测试"},
        )

        assert response.status_code == 422


@pytest.mark.integration
class TestListConversationsEndpoint:
    """GET /api/v1/conversations tests."""

    def test_list_success(self, client: TestClient, mock_service: AsyncMock) -> None:
        """200 + 返回 ConversationListResponse。"""
        mock_service.list_conversations.return_value = PagedResult(
            items=[_make_conversation_dto()],
            total=1,
            page=1,
            page_size=20,
        )

        response = client.get("/api/v1/conversations")

        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 1
        assert len(data["items"]) == 1
        assert data["page"] == 1
        assert data["total_pages"] == 1

    def test_list_empty(self, client: TestClient, mock_service: AsyncMock) -> None:
        """200 + 空列表。"""
        mock_service.list_conversations.return_value = PagedResult(
            items=[], total=0, page=1, page_size=20,
        )

        response = client.get("/api/v1/conversations")

        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 0
        assert data["items"] == []
        assert data["total_pages"] == 0

    def test_list_with_agent_id_filter(self, client: TestClient, mock_service: AsyncMock) -> None:
        """200 + 按 agent_id 筛选。"""
        mock_service.list_conversations.return_value = PagedResult(
            items=[_make_conversation_dto()],
            total=1,
            page=1,
            page_size=20,
        )

        response = client.get("/api/v1/conversations?agent_id=1")

        assert response.status_code == 200
        mock_service.list_conversations.assert_called_once()
        call_kwargs = mock_service.list_conversations.call_args
        assert call_kwargs.kwargs.get("agent_id") == 1


@pytest.mark.integration
class TestGetConversationEndpoint:
    """GET /api/v1/conversations/{id} tests."""

    def test_get_success(self, client: TestClient, mock_service: AsyncMock) -> None:
        """200 + 返回 ConversationDetailResponse。"""
        mock_service.get_conversation.return_value = ConversationDetailDTO(
            conversation=_make_conversation_dto(conversation_id=42),
            messages=[_make_message_dto(conversation_id=42)],
        )

        response = client.get("/api/v1/conversations/42")

        assert response.status_code == 200
        data = response.json()
        assert data["conversation"]["id"] == 42
        assert len(data["messages"]) == 1
        mock_service.get_conversation.assert_called_once_with(42, 1)

    def test_get_not_found(self, client: TestClient, mock_service: AsyncMock) -> None:
        """404 对话不存在。"""
        mock_service.get_conversation.side_effect = ConversationNotFoundError(999)

        response = client.get("/api/v1/conversations/999")

        assert response.status_code == 404
        data = response.json()
        assert "NOT_FOUND" in data["code"]

    def test_get_forbidden(self, client: TestClient, mock_service: AsyncMock) -> None:
        """400 无权操作。"""
        mock_service.get_conversation.side_effect = DomainError(
            message="无权操作此对话",
            code="FORBIDDEN_CONVERSATION",
        )

        response = client.get("/api/v1/conversations/1")

        assert response.status_code == 400


@pytest.mark.integration
class TestSendMessageEndpoint:
    """POST /api/v1/conversations/{id}/messages tests."""

    def test_send_success(self, client: TestClient, mock_service: AsyncMock) -> None:
        """201 + 返回 MessageResponse。"""
        mock_service.send_message.return_value = _make_message_dto()

        response = client.post(
            "/api/v1/conversations/1/messages",
            json={"content": "你好"},
        )

        assert response.status_code == 201
        data = response.json()
        assert data["role"] == "assistant"
        assert data["content"] == "你好，有什么可以帮你的？"
        mock_service.send_message.assert_called_once()

    def test_send_conversation_not_found(
        self, client: TestClient, mock_service: AsyncMock,
    ) -> None:
        """404 对话不存在。"""
        mock_service.send_message.side_effect = ConversationNotFoundError(999)

        response = client.post(
            "/api/v1/conversations/999/messages",
            json={"content": "你好"},
        )

        assert response.status_code == 404

    def test_send_conversation_not_active(
        self, client: TestClient, mock_service: AsyncMock,
    ) -> None:
        """409 对话不在活跃状态。"""
        mock_service.send_message.side_effect = ConversationNotActiveError(1)

        response = client.post(
            "/api/v1/conversations/1/messages",
            json={"content": "你好"},
        )

        assert response.status_code == 409

    def test_send_empty_content(self, client: TestClient) -> None:
        """422 空消息内容。"""
        response = client.post(
            "/api/v1/conversations/1/messages",
            json={"content": ""},
        )

        assert response.status_code == 422


@pytest.mark.integration
class TestSendMessageStreamEndpoint:
    """POST /api/v1/conversations/{id}/messages/stream tests."""

    def test_stream_success(self, client: TestClient, mock_service: AsyncMock) -> None:
        """200 SSE 流式响应。"""
        from src.modules.execution.application.dto.execution_dto import StreamChunk

        async def mock_stream(*_args, **_kwargs):  # type: ignore[no-untyped-def]
            yield StreamChunk(content="你好")
            yield StreamChunk(done=True, message_id=1, token_count=10)

        mock_service.send_message_stream.return_value = mock_stream()

        response = client.post(
            "/api/v1/conversations/1/messages/stream",
            json={"content": "你好"},
        )

        assert response.status_code == 200
        assert "text/event-stream" in response.headers.get("content-type", "")
        mock_service.send_message_stream.assert_called_once()


@pytest.mark.integration
class TestCompleteConversationEndpoint:
    """POST /api/v1/conversations/{id}/complete tests."""

    def test_complete_success(self, client: TestClient, mock_service: AsyncMock) -> None:
        """200 + 返回结束后的 ConversationResponse。"""
        mock_service.complete_conversation.return_value = _make_conversation_dto(
            status="completed",
        )

        response = client.post("/api/v1/conversations/1/complete")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "completed"
        mock_service.complete_conversation.assert_called_once_with(1, 1)

    def test_complete_not_found(self, client: TestClient, mock_service: AsyncMock) -> None:
        """404 对话不存在。"""
        mock_service.complete_conversation.side_effect = ConversationNotFoundError(999)

        response = client.post("/api/v1/conversations/999/complete")

        assert response.status_code == 404

    def test_complete_not_active(self, client: TestClient, mock_service: AsyncMock) -> None:
        """409 对话不在活跃状态。"""
        mock_service.complete_conversation.side_effect = ConversationNotActiveError(1)

        response = client.post("/api/v1/conversations/1/complete")

        assert response.status_code == 409


@pytest.mark.integration
class TestConversationEndpointsStructure:
    """Conversation endpoint route structure tests."""

    def test_conversations_list_endpoint_exists(self, app) -> None:
        routes = [r.path for r in app.routes]
        assert "/api/v1/conversations" in routes

    def test_conversations_detail_endpoint_exists(self, app) -> None:
        routes = [r.path for r in app.routes]
        assert "/api/v1/conversations/{conversation_id}" in routes

    def test_messages_endpoint_exists(self, app) -> None:
        routes = [r.path for r in app.routes]
        assert "/api/v1/conversations/{conversation_id}/messages" in routes

    def test_messages_stream_endpoint_exists(self, app) -> None:
        routes = [r.path for r in app.routes]
        assert "/api/v1/conversations/{conversation_id}/messages/stream" in routes

    def test_complete_endpoint_exists(self, app) -> None:
        routes = [r.path for r in app.routes]
        assert "/api/v1/conversations/{conversation_id}/complete" in routes
