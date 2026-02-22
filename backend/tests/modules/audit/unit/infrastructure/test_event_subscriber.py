"""事件订阅器单元测试 — 验证 DomainEvent → AuditLog 映射。"""

from dataclasses import dataclass
from unittest.mock import AsyncMock

import pytest

from src.modules.audit.application.dto.audit_log_dto import AuditLogDTO
from src.modules.audit.application.services.audit_service import AuditService
from src.modules.audit.domain.entities.audit_log import AuditAction, AuditCategory
from src.modules.audit.infrastructure.event_subscriber import (
    AuditEventSubscriber,
    EventMapping,
    get_event_mappings,
)
from src.shared.domain.events import DomainEvent


# ── 模拟事件（避免直接导入其他模块 domain） ──


@dataclass
class AgentCreatedEvent(DomainEvent):
    """模拟 Agent 创建事件。"""

    agent_id: int = 0
    owner_id: int = 0
    name: str = ""


@dataclass
class AgentUpdatedEvent(DomainEvent):
    """模拟 Agent 更新事件。"""

    agent_id: int = 0
    owner_id: int = 0
    changed_fields: tuple[str, ...] = ()


@dataclass
class TeamExecutionFailedEvent(DomainEvent):
    """模拟团队执行失败事件。"""

    execution_id: int = 0
    user_id: int = 0
    error_message: str = ""


@dataclass
class ToolCreatedEvent(DomainEvent):
    """模拟 Tool 创建事件。"""

    tool_id: int = 0
    creator_id: int = 0
    name: str = ""
    tool_type: str = ""


@dataclass
class KnowledgeBaseCreatedEvent(DomainEvent):
    """模拟知识库创建事件。"""

    knowledge_base_id: int = 0
    owner_id: int = 0


@dataclass
class TemplateCreatedEvent(DomainEvent):
    """模拟模板创建事件。"""

    template_id: int = 0
    creator_id: int = 0


@dataclass
class UnknownEvent(DomainEvent):
    """未映射的事件。"""

    some_field: str = ""


@pytest.fixture
def mock_service() -> AsyncMock:
    """Mock AuditService。"""
    service = AsyncMock(spec=AuditService)
    # record 返回 AuditLogDTO
    from datetime import UTC, datetime
    service.record.return_value = AuditLogDTO(
        id=1, actor_id=1, actor_name="user:1", action="create",
        category="agent_management", resource_type="agent", resource_id="42",
        resource_name=None, module="agents", ip_address=None, user_agent=None,
        request_method=None, request_path=None, status_code=None,
        result="success", error_message=None, details=None,
        occurred_at=datetime.now(UTC), created_at=datetime.now(UTC),
        updated_at=datetime.now(UTC),
    )
    return service


@pytest.fixture
def subscriber(mock_service: AsyncMock) -> AuditEventSubscriber:
    """AuditEventSubscriber 实例。"""
    return AuditEventSubscriber(service=mock_service)


@pytest.mark.unit
class TestEventMappings:
    """验证事件映射表完整性。"""

    def test_mappings_cover_all_expected_events(self) -> None:
        """映射表包含所有预期事件。"""
        mappings = get_event_mappings()
        expected = [
            "AgentCreatedEvent", "AgentUpdatedEvent", "AgentActivatedEvent",
            "AgentArchivedEvent", "AgentDeletedEvent",
            "ConversationCreatedEvent", "TeamExecutionStartedEvent",
            "TeamExecutionCompletedEvent", "TeamExecutionFailedEvent",
            "ToolCreatedEvent", "ToolUpdatedEvent", "ToolDeletedEvent",
            "ToolSubmittedEvent", "ToolApprovedEvent", "ToolRejectedEvent",
            "ToolDeprecatedEvent",
            "KnowledgeBaseCreatedEvent", "KnowledgeBaseActivatedEvent",
            "KnowledgeBaseDeletedEvent", "DocumentUploadedEvent",
            "TemplateCreatedEvent", "TemplatePublishedEvent", "TemplateArchivedEvent",
        ]
        for event_name in expected:
            assert event_name in mappings, f"缺少事件映射: {event_name}"

    def test_mapping_fields_are_valid(self) -> None:
        """映射表中所有字段值合法。"""
        for event_name, mapping in get_event_mappings().items():
            assert isinstance(mapping, EventMapping), f"{event_name} 映射类型错误"
            assert mapping.action in AuditAction, f"{event_name} action 值非法"
            assert mapping.category in AuditCategory, f"{event_name} category 值非法"
            assert mapping.resource_type, f"{event_name} resource_type 为空"
            assert mapping.module, f"{event_name} module 为空"
            assert mapping.resource_id_field, f"{event_name} resource_id_field 为空"


@pytest.mark.unit
class TestAuditEventSubscriber:
    """验证事件订阅器处理逻辑。"""

    @pytest.mark.asyncio
    async def test_handle_agent_created_event(
        self, subscriber: AuditEventSubscriber, mock_service: AsyncMock,
    ) -> None:
        """Agent 创建事件 → CREATE + AGENT_MANAGEMENT。"""
        event = AgentCreatedEvent(agent_id=42, owner_id=100, name="测试 Agent")

        await subscriber.handle(event)

        mock_service.record.assert_called_once()
        dto = mock_service.record.call_args[0][0]
        assert dto.action == "create"
        assert dto.category == "agent_management"
        assert dto.resource_type == "agent"
        assert dto.resource_id == "42"
        assert dto.resource_name == "测试 Agent"
        assert dto.actor_id == 100
        assert dto.module == "agents"

    @pytest.mark.asyncio
    async def test_handle_agent_updated_event_with_details(
        self, subscriber: AuditEventSubscriber, mock_service: AsyncMock,
    ) -> None:
        """Agent 更新事件 → UPDATE + 包含 changed_fields 详情。"""
        event = AgentUpdatedEvent(
            agent_id=42, owner_id=100, changed_fields=("name", "description"),
        )

        await subscriber.handle(event)

        dto = mock_service.record.call_args[0][0]
        assert dto.action == "update"
        assert dto.details is not None
        assert dto.details["changed_fields"] == "name,description"

    @pytest.mark.asyncio
    async def test_handle_team_execution_failed_event(
        self, subscriber: AuditEventSubscriber, mock_service: AsyncMock,
    ) -> None:
        """团队执行失败 → result=failure + 错误详情。"""
        event = TeamExecutionFailedEvent(
            execution_id=10, user_id=5, error_message="超时错误",
        )

        await subscriber.handle(event)

        dto = mock_service.record.call_args[0][0]
        assert dto.result == "failure"
        assert dto.details is not None
        assert dto.details["error_message"] == "超时错误"

    @pytest.mark.asyncio
    async def test_handle_tool_created_event(
        self, subscriber: AuditEventSubscriber, mock_service: AsyncMock,
    ) -> None:
        """Tool 创建事件 → CREATE + TOOL_MANAGEMENT。"""
        event = ToolCreatedEvent(tool_id=7, creator_id=200, name="搜索工具")

        await subscriber.handle(event)

        dto = mock_service.record.call_args[0][0]
        assert dto.action == "create"
        assert dto.category == "tool_management"
        assert dto.resource_id == "7"
        assert dto.actor_id == 200

    @pytest.mark.asyncio
    async def test_handle_knowledge_base_created_event(
        self, subscriber: AuditEventSubscriber, mock_service: AsyncMock,
    ) -> None:
        """知识库创建事件 → CREATE + KNOWLEDGE_MANAGEMENT。"""
        event = KnowledgeBaseCreatedEvent(knowledge_base_id=3, owner_id=50)

        await subscriber.handle(event)

        dto = mock_service.record.call_args[0][0]
        assert dto.category == "knowledge_management"
        assert dto.resource_id == "3"

    @pytest.mark.asyncio
    async def test_handle_template_created_event(
        self, subscriber: AuditEventSubscriber, mock_service: AsyncMock,
    ) -> None:
        """模板创建事件 → CREATE + TEMPLATE_MANAGEMENT。"""
        event = TemplateCreatedEvent(template_id=8, creator_id=77)

        await subscriber.handle(event)

        dto = mock_service.record.call_args[0][0]
        assert dto.category == "template_management"
        assert dto.actor_id == 77

    @pytest.mark.asyncio
    async def test_handle_unknown_event_is_ignored(
        self, subscriber: AuditEventSubscriber, mock_service: AsyncMock,
    ) -> None:
        """未映射事件被静默忽略。"""
        event = UnknownEvent(some_field="test")

        await subscriber.handle(event)

        mock_service.record.assert_not_called()

    @pytest.mark.asyncio
    async def test_handle_record_failure_does_not_raise(
        self, subscriber: AuditEventSubscriber, mock_service: AsyncMock,
    ) -> None:
        """审计记录失败时不向上抛异常（不影响业务流）。"""
        mock_service.record.side_effect = RuntimeError("数据库连接失败")
        event = AgentCreatedEvent(agent_id=1, owner_id=1, name="test")

        # 不应抛异常
        await subscriber.handle(event)

        mock_service.record.assert_called_once()
