"""Tool Catalog 模块测试配置和 Fixture。"""

from unittest.mock import AsyncMock, patch

import pytest

from src.modules.tool_catalog.application.services.tool_service import (
    ToolCatalogService,
)
from src.modules.tool_catalog.domain.entities.tool import Tool
from src.modules.tool_catalog.domain.repositories.tool_repository import (
    IToolRepository,
)
from src.modules.tool_catalog.domain.value_objects.tool_config import ToolConfig
from src.modules.tool_catalog.domain.value_objects.tool_status import ToolStatus
from src.modules.tool_catalog.domain.value_objects.tool_type import ToolType


def make_tool(
    *,
    tool_id: int = 1,
    name: str = "测试 Tool",
    description: str = "描述",
    tool_type: ToolType = ToolType.MCP_SERVER,
    version: str = "1.0.0",
    status: ToolStatus = ToolStatus.DRAFT,
    creator_id: int = 100,
    config: ToolConfig | None = None,
    reviewer_id: int | None = None,
    review_comment: str = "",
    allowed_roles: tuple[str, ...] = ("admin", "developer"),
) -> Tool:
    """创建测试用 Tool 实体。"""
    return Tool(
        id=tool_id,
        name=name,
        description=description,
        tool_type=tool_type,
        version=version,
        status=status,
        creator_id=creator_id,
        config=config or ToolConfig(server_url="http://localhost:3000"),
        reviewer_id=reviewer_id,
        review_comment=review_comment,
        allowed_roles=allowed_roles,
    )


@pytest.fixture
def mock_tool_repo() -> AsyncMock:
    """Tool 仓库 Mock。"""
    return AsyncMock(spec=IToolRepository)


@pytest.fixture
def tool_service(mock_tool_repo: AsyncMock) -> ToolCatalogService:
    """ToolCatalogService 实例（注入 mock 仓库）。"""
    return ToolCatalogService(mock_tool_repo)


@pytest.fixture
def mock_event_bus():
    """Mock event_bus，自动 patch ToolCatalogService 中的 event_bus。"""
    with patch(
        "src.modules.tool_catalog.application.services.tool_service.event_bus",
    ) as mock_bus:
        mock_bus.publish_async = AsyncMock()
        yield mock_bus
