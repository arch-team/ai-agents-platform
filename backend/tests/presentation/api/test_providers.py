"""跨模块依赖提供者测试。

覆盖 src/presentation/api/providers.py 中的 DI 工厂函数。
"""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from src.shared.domain.interfaces.agent_querier import IAgentQuerier
from src.shared.domain.interfaces.knowledge_querier import IKnowledgeQuerier
from src.shared.domain.interfaces.tool_querier import IToolQuerier


@pytest.mark.unit
class TestGetGatewaySync:
    """get_gateway_sync 测试。"""

    def test_returns_gateway_sync_adapter(self):
        """应返回 GatewaySyncAdapter 实例。"""
        # 清除 lru_cache 缓存
        from src.presentation.api.providers import get_gateway_sync

        get_gateway_sync.cache_clear()

        with patch("src.presentation.api.providers.get_settings") as mock_settings:
            mock_settings.return_value = MagicMock(
                AGENTCORE_GATEWAY_ID="gw-123",
                AWS_REGION="us-east-1",
            )
            result = get_gateway_sync()

        from src.modules.tool_catalog.infrastructure.external.gateway_sync_adapter import GatewaySyncAdapter

        assert isinstance(result, GatewaySyncAdapter)

        # 清理缓存
        get_gateway_sync.cache_clear()


@pytest.mark.unit
class TestGetAgentQuerier:
    """get_agent_querier 测试。"""

    @pytest.mark.anyio
    async def test_returns_agent_querier(self):
        """应返回 IAgentQuerier 实例。"""
        from src.presentation.api.providers import get_agent_querier

        mock_session = AsyncMock()
        result = await get_agent_querier(session=mock_session)

        assert isinstance(result, IAgentQuerier)


@pytest.mark.unit
class TestGetAgentCreator:
    """get_agent_creator 测试。"""

    @pytest.mark.anyio
    async def test_returns_agent_creator(self):
        """应返回 IAgentCreator 实例。"""
        from src.presentation.api.providers import get_agent_creator
        from src.shared.domain.interfaces.agent_creator import IAgentCreator

        mock_session = AsyncMock()
        result = await get_agent_creator(session=mock_session)

        assert isinstance(result, IAgentCreator)


@pytest.mark.unit
class TestGetToolQuerier:
    """get_tool_querier 测试。"""

    @pytest.mark.anyio
    async def test_returns_tool_querier(self):
        """应返回 IToolQuerier 实例。"""
        from src.presentation.api.providers import get_tool_querier

        mock_session = AsyncMock()
        result = await get_tool_querier(session=mock_session)

        assert isinstance(result, IToolQuerier)


@pytest.mark.unit
class TestGetKnowledgeQuerier:
    """get_knowledge_querier 测试。"""

    @pytest.mark.anyio
    async def test_returns_knowledge_querier(self):
        """应返回 IKnowledgeQuerier 实例。"""
        from src.presentation.api.providers import get_knowledge_querier

        mock_session = AsyncMock()

        with patch("src.presentation.api.providers.get_bedrock_knowledge_client") as mock_kb_client:
            mock_kb_client.return_value = MagicMock()
            result = await get_knowledge_querier(session=mock_session)

        assert isinstance(result, IKnowledgeQuerier)
