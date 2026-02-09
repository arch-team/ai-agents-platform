"""Agents API dependencies 单元测试。"""

from unittest.mock import AsyncMock

import pytest

from src.modules.agents.api.dependencies import get_agent_service


@pytest.mark.unit
class TestGetAgentService:
    """get_agent_service 依赖函数测试。"""

    @pytest.mark.asyncio
    async def test_returns_agent_service_instance(self) -> None:
        mock_session = AsyncMock()
        service = await get_agent_service(session=mock_session)
        assert service is not None
        assert hasattr(service, "create_agent")
        assert hasattr(service, "get_agent")
        assert hasattr(service, "list_agents")
        assert hasattr(service, "update_agent")
        assert hasattr(service, "delete_agent")
        assert hasattr(service, "activate_agent")
        assert hasattr(service, "archive_agent")

    def test_is_callable(self) -> None:
        assert callable(get_agent_service)
