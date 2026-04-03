"""事件订阅注册模块测试。

覆盖 src/presentation/api/event_subscriptions.py 中的各注册函数，
验证事件总线正确订阅了对应处理器，以及事件触发后的回调逻辑。
"""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest


@pytest.fixture(autouse=True)
def _clean_event_bus():
    """每个测试前后清理全局 event_bus，防止注册残留。"""
    from src.shared.domain.event_bus import event_bus

    event_bus.clear()
    yield
    event_bus.clear()


def _make_mock_session_factory():
    """创建模拟 session factory 和 session 对象。"""
    mock_session = AsyncMock()
    mock_session.commit = AsyncMock()
    mock_session.rollback = AsyncMock()

    mock_factory = MagicMock()
    mock_factory.return_value.__aenter__ = AsyncMock(return_value=mock_session)
    mock_factory.return_value.__aexit__ = AsyncMock(return_value=False)
    return mock_factory, mock_session


@pytest.mark.unit
class TestRegisterAuditEventSubscriptions:
    """测试审计事件订阅注册。"""

    @patch("src.shared.infrastructure.database.get_session_factory")
    def test_registers_all_audit_event_types(self, mock_get_sf):
        """注册后，event_bus 应包含所有审计事件类型的处理器。"""
        mock_get_sf.return_value = MagicMock()

        from src.presentation.api.event_subscriptions import _register_audit_event_subscriptions

        _register_audit_event_subscriptions()

        from src.modules.agents.domain.events import AgentCreatedEvent, AgentUpdatedEvent
        from src.modules.execution.domain.events import ConversationCreatedEvent
        from src.modules.knowledge.domain.events import KnowledgeBaseCreatedEvent
        from src.modules.templates.domain.events import TemplateCreatedEvent
        from src.modules.tool_catalog.domain.events import ToolCreatedEvent
        from src.shared.domain.event_bus import event_bus

        for event_type in [
            AgentCreatedEvent,
            AgentUpdatedEvent,
            ConversationCreatedEvent,
            ToolCreatedEvent,
            KnowledgeBaseCreatedEvent,
            TemplateCreatedEvent,
        ]:
            assert len(event_bus._handlers[event_type]) >= 1, f"{event_type.__name__} 应有至少 1 个处理器"

    @patch("src.shared.infrastructure.database.get_session_factory")
    @pytest.mark.anyio
    async def test_audit_handler_commits_on_success(self, mock_get_sf):
        """审计事件处理器成功时应提交事务。"""
        mock_factory, mock_session = _make_mock_session_factory()
        mock_get_sf.return_value = mock_factory

        from src.presentation.api.event_subscriptions import _register_audit_event_subscriptions

        _register_audit_event_subscriptions()

        from src.modules.agents.domain.events import AgentCreatedEvent
        from src.shared.domain.event_bus import event_bus

        event = AgentCreatedEvent(agent_id=1, owner_id=1)
        handlers = event_bus._handlers[AgentCreatedEvent]
        assert len(handlers) >= 1

        with patch(
            "src.modules.audit.infrastructure.event_subscriber.AuditEventSubscriber.handle",
            new_callable=AsyncMock,
        ):
            await handlers[0](event)

        mock_session.commit.assert_awaited_once()

    @patch("src.shared.infrastructure.database.get_session_factory")
    @pytest.mark.anyio
    async def test_audit_handler_rollbacks_on_error(self, mock_get_sf):
        """审计事件处理器异常时应回滚事务。"""
        mock_factory, mock_session = _make_mock_session_factory()
        mock_get_sf.return_value = mock_factory

        from src.presentation.api.event_subscriptions import _register_audit_event_subscriptions

        _register_audit_event_subscriptions()

        from src.modules.agents.domain.events import AgentCreatedEvent
        from src.shared.domain.event_bus import event_bus

        event = AgentCreatedEvent(agent_id=1, owner_id=1)
        handlers = event_bus._handlers[AgentCreatedEvent]

        with patch(
            "src.modules.audit.infrastructure.event_subscriber.AuditEventSubscriber.handle",
            new_callable=AsyncMock,
            side_effect=RuntimeError("数据库错误"),
        ):
            # 不应抛异常到外部（被 except 捕获）
            await handlers[0](event)

        mock_session.rollback.assert_awaited_once()


@pytest.mark.unit
class TestRegisterGatewayEventSubscriptions:
    """测试 Gateway 事件订阅注册。"""

    @patch("src.presentation.api.providers.get_gateway_sync")
    @patch("src.shared.infrastructure.database.get_session_factory")
    def test_registers_gateway_event_types(self, mock_get_sf, mock_get_gw):
        """注册后，event_bus 应包含 ToolApproved 和 ToolDeprecated 处理器。"""
        mock_get_sf.return_value = MagicMock()
        mock_get_gw.return_value = MagicMock()

        from src.presentation.api.event_subscriptions import _register_gateway_event_subscriptions

        _register_gateway_event_subscriptions()

        from src.modules.tool_catalog.domain.events import ToolApprovedEvent, ToolDeprecatedEvent
        from src.shared.domain.event_bus import event_bus

        assert len(event_bus._handlers[ToolApprovedEvent]) >= 1
        assert len(event_bus._handlers[ToolDeprecatedEvent]) >= 1

    @patch(
        "src.modules.tool_catalog.infrastructure.external.gateway_event_handlers.handle_tool_approved",
        new_callable=AsyncMock,
    )
    @patch("src.presentation.api.providers.get_gateway_sync")
    @patch("src.shared.infrastructure.database.get_session_factory")
    @pytest.mark.anyio
    async def test_on_tool_approved_commits(self, mock_get_sf, mock_get_gw, mock_handle):
        """ToolApproved 处理器成功时应提交事务。"""
        mock_factory, mock_session = _make_mock_session_factory()
        mock_get_sf.return_value = mock_factory
        mock_get_gw.return_value = MagicMock()

        from src.presentation.api.event_subscriptions import _register_gateway_event_subscriptions

        _register_gateway_event_subscriptions()

        from src.modules.tool_catalog.domain.events import ToolApprovedEvent
        from src.shared.domain.event_bus import event_bus

        event = ToolApprovedEvent(tool_id=1, creator_id=1, reviewer_id=2)
        handlers = event_bus._handlers[ToolApprovedEvent]
        await handlers[0](event)

        mock_session.commit.assert_awaited_once()

    @patch(
        "src.modules.tool_catalog.infrastructure.external.gateway_event_handlers.handle_tool_approved",
        new_callable=AsyncMock,
        side_effect=RuntimeError("Gateway 错误"),
    )
    @patch("src.presentation.api.providers.get_gateway_sync")
    @patch("src.shared.infrastructure.database.get_session_factory")
    @pytest.mark.anyio
    async def test_on_tool_approved_rollbacks_on_error(self, mock_get_sf, mock_get_gw, mock_handle):
        """ToolApproved 处理器异常时应回滚并重新抛出。"""
        mock_factory, mock_session = _make_mock_session_factory()
        mock_get_sf.return_value = mock_factory
        mock_get_gw.return_value = MagicMock()

        from src.presentation.api.event_subscriptions import _register_gateway_event_subscriptions

        _register_gateway_event_subscriptions()

        from src.modules.tool_catalog.domain.events import ToolApprovedEvent
        from src.shared.domain.event_bus import event_bus

        event = ToolApprovedEvent(tool_id=1, creator_id=1, reviewer_id=2)
        handlers = event_bus._handlers[ToolApprovedEvent]

        with pytest.raises(RuntimeError, match="Gateway 错误"):
            await handlers[0](event)

        mock_session.rollback.assert_awaited_once()

    @patch(
        "src.modules.tool_catalog.infrastructure.external.gateway_event_handlers.handle_tool_deprecated",
        new_callable=AsyncMock,
    )
    @patch("src.presentation.api.providers.get_gateway_sync")
    @patch("src.shared.infrastructure.database.get_session_factory")
    @pytest.mark.anyio
    async def test_on_tool_deprecated_commits(self, mock_get_sf, mock_get_gw, mock_handle):
        """ToolDeprecated 处理器成功时应提交事务。"""
        mock_factory, mock_session = _make_mock_session_factory()
        mock_get_sf.return_value = mock_factory
        mock_get_gw.return_value = MagicMock()

        from src.presentation.api.event_subscriptions import _register_gateway_event_subscriptions

        _register_gateway_event_subscriptions()

        from src.modules.tool_catalog.domain.events import ToolDeprecatedEvent
        from src.shared.domain.event_bus import event_bus

        event = ToolDeprecatedEvent(tool_id=1, creator_id=1)
        handlers = event_bus._handlers[ToolDeprecatedEvent]
        await handlers[0](event)

        mock_session.commit.assert_awaited_once()

    @patch(
        "src.modules.tool_catalog.infrastructure.external.gateway_event_handlers.handle_tool_deprecated",
        new_callable=AsyncMock,
        side_effect=RuntimeError("Gateway 注销失败"),
    )
    @patch("src.presentation.api.providers.get_gateway_sync")
    @patch("src.shared.infrastructure.database.get_session_factory")
    @pytest.mark.anyio
    async def test_on_tool_deprecated_rollbacks_on_error(self, mock_get_sf, mock_get_gw, mock_handle):
        """ToolDeprecated 处理器异常时应回滚并重新抛出。"""
        mock_factory, mock_session = _make_mock_session_factory()
        mock_get_sf.return_value = mock_factory
        mock_get_gw.return_value = MagicMock()

        from src.presentation.api.event_subscriptions import _register_gateway_event_subscriptions

        _register_gateway_event_subscriptions()

        from src.modules.tool_catalog.domain.events import ToolDeprecatedEvent
        from src.shared.domain.event_bus import event_bus

        event = ToolDeprecatedEvent(tool_id=1, creator_id=1)
        handlers = event_bus._handlers[ToolDeprecatedEvent]

        with pytest.raises(RuntimeError, match="Gateway 注销失败"):
            await handlers[0](event)

        mock_session.rollback.assert_awaited_once()


@pytest.mark.unit
class TestRegisterTeamExecutionEventSubscriptions:
    """测试团队执行完成事件订阅注册。"""

    @patch("src.shared.infrastructure.database.get_session_factory")
    def test_registers_team_execution_completed(self, mock_get_sf):
        """注册后，event_bus 应包含 TeamExecutionCompletedEvent 处理器。"""
        mock_get_sf.return_value = MagicMock()

        from src.presentation.api.event_subscriptions import _register_team_execution_event_subscriptions

        _register_team_execution_event_subscriptions()

        from src.modules.execution.domain.events import TeamExecutionCompletedEvent
        from src.shared.domain.event_bus import event_bus

        assert len(event_bus._handlers[TeamExecutionCompletedEvent]) >= 1

    @patch("src.shared.infrastructure.database.get_session_factory")
    @pytest.mark.anyio
    async def test_handler_skips_zero_tokens(self, mock_get_sf):
        """input_tokens 和 output_tokens 都为 0 时应跳过处理。"""
        mock_factory = MagicMock()
        mock_get_sf.return_value = mock_factory

        from src.presentation.api.event_subscriptions import _register_team_execution_event_subscriptions

        _register_team_execution_event_subscriptions()

        from src.modules.execution.domain.events import TeamExecutionCompletedEvent
        from src.shared.domain.event_bus import event_bus

        event = TeamExecutionCompletedEvent(
            execution_id=1,
            user_id=1,
            input_tokens=0,
            output_tokens=0,
        )
        handlers = event_bus._handlers[TeamExecutionCompletedEvent]
        await handlers[0](event)

        # session_factory() 不应被调用（因为 tokens 为 0 时提前返回）
        mock_factory.assert_not_called()

    @patch("src.shared.infrastructure.database.get_session_factory")
    @pytest.mark.anyio
    async def test_handler_records_usage_on_nonzero_tokens(self, mock_get_sf):
        """有 token 消耗时应记录 usage 并提交。"""
        mock_factory, mock_session = _make_mock_session_factory()
        mock_get_sf.return_value = mock_factory

        from src.presentation.api.event_subscriptions import _register_team_execution_event_subscriptions

        _register_team_execution_event_subscriptions()

        from src.modules.execution.domain.events import TeamExecutionCompletedEvent
        from src.shared.domain.event_bus import event_bus

        event = TeamExecutionCompletedEvent(
            execution_id=1,
            user_id=1,
            input_tokens=100,
            output_tokens=50,
            model_id="claude-3",
        )
        handlers = event_bus._handlers[TeamExecutionCompletedEvent]

        mock_execution = MagicMock()
        mock_execution.agent_id = 1
        mock_execution.conversation_id = 1

        with (
            patch(
                "src.modules.execution.infrastructure.persistence.repositories"
                ".team_execution_repository_impl.TeamExecutionRepositoryImpl.get_by_id",
                new_callable=AsyncMock,
                return_value=mock_execution,
            ),
            patch(
                "src.modules.insights.application.services.insights_service.InsightsService.record_usage",
                new_callable=AsyncMock,
            ) as mock_record,
        ):
            await handlers[0](event)

        mock_record.assert_awaited_once()
        mock_session.commit.assert_awaited_once()

    @patch("src.shared.infrastructure.database.get_session_factory")
    @pytest.mark.anyio
    async def test_handler_skips_when_execution_not_found(self, mock_get_sf):
        """execution 不存在时应跳过（不 commit）。"""
        mock_factory, mock_session = _make_mock_session_factory()
        mock_get_sf.return_value = mock_factory

        from src.presentation.api.event_subscriptions import _register_team_execution_event_subscriptions

        _register_team_execution_event_subscriptions()

        from src.modules.execution.domain.events import TeamExecutionCompletedEvent
        from src.shared.domain.event_bus import event_bus

        event = TeamExecutionCompletedEvent(
            execution_id=999,
            user_id=1,
            input_tokens=100,
            output_tokens=50,
        )
        handlers = event_bus._handlers[TeamExecutionCompletedEvent]

        with patch(
            "src.modules.execution.infrastructure.persistence.repositories"
            ".team_execution_repository_impl.TeamExecutionRepositoryImpl.get_by_id",
            new_callable=AsyncMock,
            return_value=None,
        ):
            await handlers[0](event)

        mock_session.commit.assert_not_awaited()

    @patch("src.shared.infrastructure.database.get_session_factory")
    @pytest.mark.anyio
    async def test_handler_rollbacks_on_error(self, mock_get_sf):
        """团队执行处理器异常时应回滚（不抛出）。"""
        mock_factory, mock_session = _make_mock_session_factory()
        mock_get_sf.return_value = mock_factory

        from src.presentation.api.event_subscriptions import _register_team_execution_event_subscriptions

        _register_team_execution_event_subscriptions()

        from src.modules.execution.domain.events import TeamExecutionCompletedEvent
        from src.shared.domain.event_bus import event_bus

        event = TeamExecutionCompletedEvent(
            execution_id=1,
            user_id=1,
            input_tokens=100,
            output_tokens=50,
        )
        handlers = event_bus._handlers[TeamExecutionCompletedEvent]

        with patch(
            "src.modules.execution.infrastructure.persistence.repositories"
            ".team_execution_repository_impl.TeamExecutionRepositoryImpl.get_by_id",
            new_callable=AsyncMock,
            side_effect=RuntimeError("DB 错误"),
        ):
            await handlers[0](event)

        mock_session.rollback.assert_awaited_once()


@pytest.mark.unit
class TestRegisterMessageReceivedEventSubscriptions:
    """测试消息接收事件订阅注册。"""

    @patch("src.shared.infrastructure.database.get_session_factory")
    def test_registers_message_received(self, mock_get_sf):
        """注册后，event_bus 应包含 MessageReceivedEvent 处理器。"""
        mock_get_sf.return_value = MagicMock()

        from src.presentation.api.event_subscriptions import _register_message_received_event_subscriptions

        _register_message_received_event_subscriptions()

        from src.modules.execution.domain.events import MessageReceivedEvent
        from src.shared.domain.event_bus import event_bus

        assert len(event_bus._handlers[MessageReceivedEvent]) >= 1

    @patch("src.shared.infrastructure.database.get_session_factory")
    @pytest.mark.anyio
    async def test_handler_skips_zero_token_count(self, mock_get_sf):
        """token_count 为 0 时应跳过处理。"""
        mock_factory = MagicMock()
        mock_get_sf.return_value = mock_factory

        from src.presentation.api.event_subscriptions import _register_message_received_event_subscriptions

        _register_message_received_event_subscriptions()

        from src.modules.execution.domain.events import MessageReceivedEvent
        from src.shared.domain.event_bus import event_bus

        event = MessageReceivedEvent(conversation_id=1, message_id=1, token_count=0)
        handlers = event_bus._handlers[MessageReceivedEvent]
        await handlers[0](event)

        mock_factory.assert_not_called()

    @patch("src.shared.infrastructure.database.get_session_factory")
    @pytest.mark.anyio
    async def test_handler_records_usage_on_nonzero_tokens(self, mock_get_sf):
        """有 token 消耗时应记录 usage 并提交。"""
        mock_factory, mock_session = _make_mock_session_factory()
        mock_get_sf.return_value = mock_factory

        from src.presentation.api.event_subscriptions import _register_message_received_event_subscriptions

        _register_message_received_event_subscriptions()

        from src.modules.execution.domain.events import MessageReceivedEvent
        from src.shared.domain.event_bus import event_bus

        event = MessageReceivedEvent(
            conversation_id=1,
            message_id=1,
            token_count=500,
            model_id="claude-3",
        )
        handlers = event_bus._handlers[MessageReceivedEvent]

        mock_conversation = MagicMock()
        mock_conversation.user_id = 1
        mock_conversation.agent_id = 1

        with (
            patch(
                "src.modules.execution.infrastructure.persistence.repositories"
                ".conversation_repository_impl.ConversationRepositoryImpl.get_by_id",
                new_callable=AsyncMock,
                return_value=mock_conversation,
            ),
            patch(
                "src.modules.insights.application.services.insights_service.InsightsService.record_usage",
                new_callable=AsyncMock,
            ) as mock_record,
        ):
            await handlers[0](event)

        mock_record.assert_awaited_once()
        mock_session.commit.assert_awaited_once()

    @patch("src.shared.infrastructure.database.get_session_factory")
    @pytest.mark.anyio
    async def test_handler_skips_when_conversation_not_found(self, mock_get_sf):
        """conversation 不存在时应跳过（不 commit）。"""
        mock_factory, mock_session = _make_mock_session_factory()
        mock_get_sf.return_value = mock_factory

        from src.presentation.api.event_subscriptions import _register_message_received_event_subscriptions

        _register_message_received_event_subscriptions()

        from src.modules.execution.domain.events import MessageReceivedEvent
        from src.shared.domain.event_bus import event_bus

        event = MessageReceivedEvent(conversation_id=999, message_id=1, token_count=500)
        handlers = event_bus._handlers[MessageReceivedEvent]

        with patch(
            "src.modules.execution.infrastructure.persistence.repositories"
            ".conversation_repository_impl.ConversationRepositoryImpl.get_by_id",
            new_callable=AsyncMock,
            return_value=None,
        ):
            await handlers[0](event)

        mock_session.commit.assert_not_awaited()

    @patch("src.shared.infrastructure.database.get_session_factory")
    @pytest.mark.anyio
    async def test_handler_rollbacks_on_error(self, mock_get_sf):
        """消息处理器异常时应回滚（不抛出）。"""
        mock_factory, mock_session = _make_mock_session_factory()
        mock_get_sf.return_value = mock_factory

        from src.presentation.api.event_subscriptions import _register_message_received_event_subscriptions

        _register_message_received_event_subscriptions()

        from src.modules.execution.domain.events import MessageReceivedEvent
        from src.shared.domain.event_bus import event_bus

        event = MessageReceivedEvent(conversation_id=1, message_id=1, token_count=500)
        handlers = event_bus._handlers[MessageReceivedEvent]

        with patch(
            "src.modules.execution.infrastructure.persistence.repositories"
            ".conversation_repository_impl.ConversationRepositoryImpl.get_by_id",
            new_callable=AsyncMock,
            side_effect=RuntimeError("DB 错误"),
        ):
            await handlers[0](event)

        mock_session.rollback.assert_awaited_once()


@pytest.mark.unit
class TestRegisterMemoryExtractionEventSubscriptions:
    """测试记忆提取事件订阅注册。"""

    @patch("src.presentation.api.event_subscriptions.get_settings")
    def test_skips_when_disabled(self, mock_get_settings):
        """MEMORY_EXTRACTION_ENABLED=False 时不注册事件。"""
        mock_settings = MagicMock()
        mock_settings.MEMORY_EXTRACTION_ENABLED = False
        mock_get_settings.return_value = mock_settings

        from src.presentation.api.event_subscriptions import _register_memory_extraction_event_subscriptions

        _register_memory_extraction_event_subscriptions()

        from src.modules.execution.domain.events import ConversationCompletedEvent
        from src.shared.domain.event_bus import event_bus

        assert len(event_bus._handlers[ConversationCompletedEvent]) == 0

    @patch("src.shared.infrastructure.database.get_session_factory")
    @patch("src.presentation.api.event_subscriptions.get_settings")
    def test_registers_when_enabled(self, mock_get_settings, mock_get_sf):
        """MEMORY_EXTRACTION_ENABLED=True 时注册 ConversationCompleted 处理器。"""
        mock_settings = MagicMock()
        mock_settings.MEMORY_EXTRACTION_ENABLED = True
        mock_settings.AGENTCORE_MEMORY_ID = "mem-123"
        mock_settings.AWS_REGION = "us-east-1"
        mock_get_settings.return_value = mock_settings
        mock_get_sf.return_value = MagicMock()

        from src.presentation.api.event_subscriptions import _register_memory_extraction_event_subscriptions

        with (
            patch("src.modules.execution.infrastructure.external.memory_adapter.MemoryAdapter"),
            patch("src.modules.execution.infrastructure.external.memory_extraction_handler.MemoryExtractionHandler"),
        ):
            _register_memory_extraction_event_subscriptions()

        from src.modules.execution.domain.events import ConversationCompletedEvent
        from src.shared.domain.event_bus import event_bus

        assert len(event_bus._handlers[ConversationCompletedEvent]) >= 1


@pytest.mark.unit
class TestRegisterAllEventSubscriptions:
    """测试统一注册入口。"""

    @patch("src.presentation.api.event_subscriptions._register_audit_event_subscriptions")
    @patch("src.presentation.api.event_subscriptions._register_memory_extraction_event_subscriptions")
    @patch("src.presentation.api.event_subscriptions._register_message_received_event_subscriptions")
    @patch("src.presentation.api.event_subscriptions._register_team_execution_event_subscriptions")
    @patch("src.presentation.api.event_subscriptions._register_gateway_event_subscriptions")
    def test_calls_all_registration_functions(
        self,
        mock_gw,
        mock_te,
        mock_mr,
        mock_me,
        mock_audit,
    ):
        """register_all_event_subscriptions 应调用所有注册函数。"""
        from src.presentation.api.event_subscriptions import register_all_event_subscriptions

        register_all_event_subscriptions()

        mock_gw.assert_called_once()
        mock_te.assert_called_once()
        mock_mr.assert_called_once()
        mock_me.assert_called_once()
        mock_audit.assert_called_once()
