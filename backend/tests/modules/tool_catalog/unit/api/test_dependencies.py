"""Tool Catalog API dependencies 单元测试。"""

from unittest.mock import AsyncMock

import pytest

from src.modules.tool_catalog.api.dependencies import get_tool_service


@pytest.mark.unit
class TestGetToolService:
    """get_tool_service 依赖函数测试。"""

    @pytest.mark.asyncio
    async def test_returns_tool_service_instance(self) -> None:
        mock_session = AsyncMock()
        service = await get_tool_service(session=mock_session)
        assert service is not None
        assert hasattr(service, "create_tool")
        assert hasattr(service, "get_tool")
        assert hasattr(service, "list_tools")
        assert hasattr(service, "update_tool")
        assert hasattr(service, "delete_tool")
        assert hasattr(service, "submit_for_review")
        assert hasattr(service, "approve_tool")
        assert hasattr(service, "reject_tool")
        assert hasattr(service, "deprecate_tool")

    def test_is_callable(self) -> None:
        assert callable(get_tool_service)
