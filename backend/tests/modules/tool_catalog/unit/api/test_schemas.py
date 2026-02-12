"""Tool Catalog API schemas 单元测试。"""

from datetime import datetime

import pytest
from pydantic import ValidationError

from src.modules.tool_catalog.api.schemas.requests import (
    CreateToolRequest,
    RejectToolRequest,
    UpdateToolRequest,
)
from src.modules.tool_catalog.api.schemas.responses import (
    ToolConfigResponse,
    ToolListResponse,
    ToolResponse,
)


@pytest.mark.unit
class TestCreateToolRequest:
    """CreateToolRequest 验证测试。"""

    def test_valid_request_with_defaults(self) -> None:
        req = CreateToolRequest(name="test-tool", tool_type="mcp_server")
        assert req.name == "test-tool"
        assert req.tool_type == "mcp_server"
        assert req.description == ""
        assert req.version == "1.0.0"
        assert req.server_url == ""
        assert req.transport == "stdio"
        assert req.endpoint_url == ""
        assert req.method == "POST"
        assert req.runtime == ""
        assert req.handler == ""
        assert req.code_uri == ""
        assert req.auth_type == "none"

    def test_valid_request_with_all_fields(self) -> None:
        req = CreateToolRequest(
            name="mcp-tool",
            tool_type="mcp_server",
            description="MCP Server Tool",
            version="2.0.0",
            server_url="http://localhost:3000",
            transport="sse",
        )
        assert req.name == "mcp-tool"
        assert req.version == "2.0.0"
        assert req.server_url == "http://localhost:3000"

    def test_empty_name_raises(self) -> None:
        with pytest.raises(ValidationError, match="name"):
            CreateToolRequest(name="", tool_type="mcp_server")

    def test_name_too_long_raises(self) -> None:
        with pytest.raises(ValidationError, match="name"):
            CreateToolRequest(name="a" * 101, tool_type="mcp_server")

    def test_description_too_long_raises(self) -> None:
        with pytest.raises(ValidationError, match="description"):
            CreateToolRequest(
                name="test", tool_type="mcp_server", description="a" * 1001,
            )

    def test_missing_tool_type_raises(self) -> None:
        with pytest.raises(ValidationError, match="tool_type"):
            CreateToolRequest(name="test")  # type: ignore[call-arg]


@pytest.mark.unit
class TestUpdateToolRequest:
    """UpdateToolRequest 验证测试。"""

    def test_all_none_by_default(self) -> None:
        req = UpdateToolRequest()
        assert req.name is None
        assert req.description is None
        assert req.version is None
        assert req.server_url is None
        assert req.transport is None
        assert req.endpoint_url is None
        assert req.method is None
        assert req.runtime is None
        assert req.handler is None
        assert req.code_uri is None
        assert req.auth_type is None

    def test_partial_update(self) -> None:
        req = UpdateToolRequest(name="new-name", version="2.0.0")
        assert req.name == "new-name"
        assert req.version == "2.0.0"
        assert req.description is None

    def test_empty_name_raises(self) -> None:
        with pytest.raises(ValidationError, match="name"):
            UpdateToolRequest(name="")


@pytest.mark.unit
class TestRejectToolRequest:
    """RejectToolRequest 验证测试。"""

    def test_valid_request(self) -> None:
        req = RejectToolRequest(comment="需要改进安全配置")
        assert req.comment == "需要改进安全配置"

    def test_empty_comment_raises(self) -> None:
        with pytest.raises(ValidationError, match="comment"):
            RejectToolRequest(comment="")

    def test_comment_too_long_raises(self) -> None:
        with pytest.raises(ValidationError, match="comment"):
            RejectToolRequest(comment="a" * 1001)


@pytest.mark.unit
class TestToolConfigResponse:
    """ToolConfigResponse 序列化测试。"""

    def test_valid_response(self) -> None:
        resp = ToolConfigResponse(
            server_url="http://localhost:3000",
            transport="stdio",
            endpoint_url="",
            method="POST",
            runtime="",
            handler="",
            code_uri="",
            auth_type="none",
        )
        assert resp.server_url == "http://localhost:3000"
        assert resp.auth_type == "none"


@pytest.mark.unit
class TestToolResponse:
    """ToolResponse 序列化测试。"""

    def test_valid_response(self) -> None:
        now = datetime.now()
        resp = ToolResponse(
            id=1,
            name="test-tool",
            description="desc",
            tool_type="mcp_server",
            version="1.0.0",
            status="draft",
            creator_id=10,
            config=ToolConfigResponse(
                server_url="http://localhost",
                transport="stdio",
                endpoint_url="",
                method="POST",
                runtime="",
                handler="",
                code_uri="",
                auth_type="none",
            ),
            allowed_roles=["admin", "developer"],
            gateway_target_id="",
            reviewer_id=None,
            review_comment="",
            reviewed_at=None,
            created_at=now,
            updated_at=now,
        )
        assert resp.id == 1
        assert resp.config.server_url == "http://localhost"
        assert resp.allowed_roles == ["admin", "developer"]


@pytest.mark.unit
class TestToolListResponse:
    """ToolListResponse 序列化测试。"""

    def test_empty_list(self) -> None:
        resp = ToolListResponse(
            items=[], total=0, page=1, page_size=20, total_pages=0,
        )
        assert resp.items == []
        assert resp.total == 0

    def test_with_items(self) -> None:
        now = datetime.now()
        item = ToolResponse(
            id=1,
            name="tool",
            description="",
            tool_type="api",
            version="1.0.0",
            status="approved",
            creator_id=1,
            config=ToolConfigResponse(
                server_url="",
                transport="stdio",
                endpoint_url="http://api.example.com",
                method="POST",
                runtime="",
                handler="",
                code_uri="",
                auth_type="api_key",
            ),
            allowed_roles=["admin"],
            gateway_target_id="",
            reviewer_id=2,
            review_comment="",
            reviewed_at=now,
            created_at=now,
            updated_at=now,
        )
        resp = ToolListResponse(
            items=[item], total=1, page=1, page_size=20, total_pages=1,
        )
        assert len(resp.items) == 1
        assert resp.total_pages == 1
