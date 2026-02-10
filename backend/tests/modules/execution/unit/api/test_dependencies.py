"""Execution API dependencies 单元测试。"""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from src.modules.execution.api.dependencies import get_bedrock_client, get_execution_service


@pytest.mark.unit
class TestGetBedrockClient:
    """get_bedrock_client 依赖函数测试。"""

    def test_is_callable(self) -> None:
        assert callable(get_bedrock_client)


@pytest.mark.unit
class TestGetExecutionService:
    """get_execution_service 依赖函数测试。"""

    @pytest.mark.asyncio
    async def test_returns_execution_service_instance(self) -> None:
        mock_session = AsyncMock()
        mock_agent_querier = AsyncMock()
        mock_session_factory = MagicMock(return_value=AsyncMock())
        with (
            patch(
                "src.modules.execution.api.dependencies.get_bedrock_client",
            ) as mock_get_bedrock,
            patch(
                "src.modules.execution.api.dependencies.get_session_factory",
                return_value=mock_session_factory,
            ),
        ):
            mock_get_bedrock.return_value = AsyncMock()
            service = await get_execution_service(
                session=mock_session,
                agent_querier=mock_agent_querier,
            )
            assert service is not None
            assert hasattr(service, "create_conversation")
            assert hasattr(service, "send_message")
            assert hasattr(service, "send_message_stream")
            assert hasattr(service, "get_conversation")
            assert hasattr(service, "list_conversations")
            assert hasattr(service, "complete_conversation")

    def test_is_callable(self) -> None:
        assert callable(get_execution_service)
