"""ToolQuerierImpl 单元测试。"""

from unittest.mock import AsyncMock

import pytest

from src.modules.tool_catalog.domain.entities.tool import Tool
from src.modules.tool_catalog.domain.value_objects.tool_config import ToolConfig
from src.modules.tool_catalog.domain.value_objects.tool_status import ToolStatus
from src.modules.tool_catalog.domain.value_objects.tool_type import ToolType
from src.modules.tool_catalog.infrastructure.services.tool_querier_impl import ToolQuerierImpl


def _make_tool(
    *,
    tool_id: int = 1,
    name: str = "test-tool",
    tool_type: ToolType = ToolType.MCP_SERVER,
    server_url: str = "http://mcp.example.com",
) -> Tool:
    tool = Tool(
        name=name,
        description="测试工具",
        tool_type=tool_type,
        status=ToolStatus.APPROVED,
        creator_id=1,
        config=ToolConfig(server_url=server_url),
    )
    object.__setattr__(tool, "id", tool_id)
    return tool


@pytest.mark.unit
@pytest.mark.asyncio(loop_scope="class")
class TestToolQuerierImpl:
    """ToolQuerierImpl 测试。"""

    @pytest.fixture
    def mock_repo(self) -> AsyncMock:
        return AsyncMock()

    @pytest.fixture
    def querier(self, mock_repo: AsyncMock) -> ToolQuerierImpl:
        return ToolQuerierImpl(tool_repository=mock_repo)

    async def test_list_approved_tools_returns_approved_only(
        self, querier: ToolQuerierImpl, mock_repo: AsyncMock
    ) -> None:
        tools = [_make_tool(tool_id=1, name="tool-a"), _make_tool(tool_id=2, name="tool-b")]
        mock_repo.list_filtered.return_value = tools

        result = await querier.list_approved_tools()

        assert len(result) == 2
        mock_repo.list_filtered.assert_called_once_with(
            status=ToolStatus.APPROVED, offset=0, limit=1000
        )

    async def test_list_approved_tools_empty(
        self, querier: ToolQuerierImpl, mock_repo: AsyncMock
    ) -> None:
        mock_repo.list_filtered.return_value = []

        result = await querier.list_approved_tools()

        assert result == []

    async def test_to_approved_tool_info_maps_fields(
        self, querier: ToolQuerierImpl, mock_repo: AsyncMock
    ) -> None:
        tool = _make_tool(
            tool_id=42,
            name="mcp-github",
            tool_type=ToolType.MCP_SERVER,
            server_url="http://github-mcp.example.com",
        )
        mock_repo.list_filtered.return_value = [tool]

        result = await querier.list_approved_tools()

        info = result[0]
        assert info.id == 42
        assert info.name == "mcp-github"
        assert info.tool_type == "mcp_server"
        assert info.server_url == "http://github-mcp.example.com"

    async def test_api_tool_maps_endpoint_url(
        self, querier: ToolQuerierImpl, mock_repo: AsyncMock
    ) -> None:
        tool = Tool(
            name="api-tool",
            description="API 工具",
            tool_type=ToolType.API,
            status=ToolStatus.APPROVED,
            creator_id=1,
            config=ToolConfig(endpoint_url="https://api.example.com/v1", method="POST"),
        )
        object.__setattr__(tool, "id", 10)
        mock_repo.list_filtered.return_value = [tool]

        result = await querier.list_approved_tools()

        info = result[0]
        assert info.tool_type == "api"
        assert info.endpoint_url == "https://api.example.com/v1"
        assert info.method == "POST"

    async def test_function_tool_maps_runtime_handler(
        self, querier: ToolQuerierImpl, mock_repo: AsyncMock
    ) -> None:
        tool = Tool(
            name="fn-tool",
            description="Function 工具",
            tool_type=ToolType.FUNCTION,
            status=ToolStatus.APPROVED,
            creator_id=1,
            config=ToolConfig(runtime="python3.12", handler="index.handler"),
        )
        object.__setattr__(tool, "id", 20)
        mock_repo.list_filtered.return_value = [tool]

        result = await querier.list_approved_tools()

        info = result[0]
        assert info.tool_type == "function"
        assert info.runtime == "python3.12"
        assert info.handler == "index.handler"
