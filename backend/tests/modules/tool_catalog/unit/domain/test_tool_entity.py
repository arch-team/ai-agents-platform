"""Tool 实体单元测试。"""

import pytest
from pydantic import ValidationError

from src.modules.tool_catalog.domain.entities.tool import Tool
from src.modules.tool_catalog.domain.value_objects.tool_config import ToolConfig
from src.modules.tool_catalog.domain.value_objects.tool_status import ToolStatus
from src.modules.tool_catalog.domain.value_objects.tool_type import ToolType
from src.shared.domain.exceptions import InvalidStateTransitionError
from src.shared.domain.exceptions import ValidationError as DomainValidationError


# --- 创建 ---


@pytest.mark.unit
class TestToolCreation:
    def test_create_tool_with_defaults(self) -> None:
        tool = Tool(name="MCP Tool", tool_type=ToolType.MCP_SERVER, creator_id=1)
        assert tool.name == "MCP Tool"
        assert tool.description == ""
        assert tool.tool_type == ToolType.MCP_SERVER
        assert tool.version == "1.0.0"
        assert tool.status == ToolStatus.DRAFT
        assert tool.creator_id == 1
        assert tool.config == ToolConfig()
        assert tool.reviewer_id is None
        assert tool.review_comment == ""
        assert tool.reviewed_at is None
        assert tool.allowed_roles == ("admin", "developer")

    def test_create_tool_with_custom_fields(self) -> None:
        config = ToolConfig(server_url="http://localhost:3000", transport="sse")
        tool = Tool(
            name="Custom Tool",
            description="一个自定义工具",
            tool_type=ToolType.MCP_SERVER,
            version="2.0.0",
            creator_id=2,
            config=config,
            allowed_roles=("admin",),
        )
        assert tool.name == "Custom Tool"
        assert tool.description == "一个自定义工具"
        assert tool.version == "2.0.0"
        assert tool.config.server_url == "http://localhost:3000"
        assert tool.allowed_roles == ("admin",)

    def test_create_tool_inherits_pydantic_entity(self) -> None:
        tool = Tool(name="Test", tool_type=ToolType.API, creator_id=1)
        assert tool.id is None
        assert tool.created_at is not None
        assert tool.updated_at is not None

    def test_empty_name_raises(self) -> None:
        with pytest.raises(ValidationError, match="name"):
            Tool(name="", tool_type=ToolType.API, creator_id=1)

    def test_name_too_long_raises(self) -> None:
        with pytest.raises(ValidationError, match="name"):
            Tool(name="A" * 101, tool_type=ToolType.API, creator_id=1)

    def test_description_too_long_raises(self) -> None:
        with pytest.raises(ValidationError, match="description"):
            Tool(
                name="Test",
                tool_type=ToolType.API,
                creator_id=1,
                description="A" * 1001,
            )

    def test_version_too_long_raises(self) -> None:
        with pytest.raises(ValidationError, match="version"):
            Tool(
                name="Test",
                tool_type=ToolType.API,
                creator_id=1,
                version="A" * 51,
            )

    def test_review_comment_too_long_raises(self) -> None:
        with pytest.raises(ValidationError, match="review_comment"):
            Tool(
                name="Test",
                tool_type=ToolType.API,
                creator_id=1,
                review_comment="A" * 1001,
            )


# --- submit ---


@pytest.mark.unit
class TestToolSubmit:
    @pytest.fixture
    def mcp_tool(self) -> Tool:
        return Tool(
            name="MCP Tool",
            description="一个 MCP 工具",
            tool_type=ToolType.MCP_SERVER,
            creator_id=1,
            config=ToolConfig(server_url="http://localhost:3000"),
        )

    @pytest.fixture
    def api_tool(self) -> Tool:
        return Tool(
            name="API Tool",
            description="一个 API 工具",
            tool_type=ToolType.API,
            creator_id=1,
            config=ToolConfig(endpoint_url="https://api.example.com"),
        )

    @pytest.fixture
    def function_tool(self) -> Tool:
        return Tool(
            name="Function Tool",
            description="一个 Function 工具",
            tool_type=ToolType.FUNCTION,
            creator_id=1,
            config=ToolConfig(runtime="python3.12", handler="index.handler"),
        )

    def test_submit_from_draft_succeeds(self, mcp_tool: Tool) -> None:
        mcp_tool.submit()
        assert mcp_tool.status == ToolStatus.PENDING_REVIEW

    def test_submit_updates_timestamp(self, mcp_tool: Tool) -> None:
        original = mcp_tool.updated_at
        mcp_tool.submit()
        assert mcp_tool.updated_at is not None
        assert original is not None
        assert mcp_tool.updated_at >= original

    def test_submit_api_tool_succeeds(self, api_tool: Tool) -> None:
        api_tool.submit()
        assert api_tool.status == ToolStatus.PENDING_REVIEW

    def test_submit_function_tool_succeeds(self, function_tool: Tool) -> None:
        function_tool.submit()
        assert function_tool.status == ToolStatus.PENDING_REVIEW

    def test_submit_from_non_draft_raises(self, mcp_tool: Tool) -> None:
        mcp_tool.submit()
        with pytest.raises(InvalidStateTransitionError):
            mcp_tool.submit()

    def test_submit_from_approved_raises(self, mcp_tool: Tool) -> None:
        mcp_tool.submit()
        mcp_tool.approve(reviewer_id=99)
        with pytest.raises(InvalidStateTransitionError):
            mcp_tool.submit()

    def test_submit_without_description_raises(self) -> None:
        tool = Tool(
            name="Test",
            tool_type=ToolType.MCP_SERVER,
            creator_id=1,
            config=ToolConfig(server_url="http://localhost"),
        )
        with pytest.raises(DomainValidationError, match="描述"):
            tool.submit()

    def test_submit_with_blank_description_raises(self) -> None:
        tool = Tool(
            name="Test",
            description="   ",
            tool_type=ToolType.MCP_SERVER,
            creator_id=1,
            config=ToolConfig(server_url="http://localhost"),
        )
        with pytest.raises(DomainValidationError, match="描述"):
            tool.submit()

    def test_submit_mcp_without_server_url_raises(self) -> None:
        tool = Tool(
            name="Test",
            description="有描述",
            tool_type=ToolType.MCP_SERVER,
            creator_id=1,
        )
        with pytest.raises(DomainValidationError, match="server_url"):
            tool.submit()

    def test_submit_api_without_endpoint_url_raises(self) -> None:
        tool = Tool(
            name="Test",
            description="有描述",
            tool_type=ToolType.API,
            creator_id=1,
        )
        with pytest.raises(DomainValidationError, match="endpoint_url"):
            tool.submit()

    def test_submit_function_without_runtime_raises(self) -> None:
        tool = Tool(
            name="Test",
            description="有描述",
            tool_type=ToolType.FUNCTION,
            creator_id=1,
            config=ToolConfig(handler="index.handler"),
        )
        with pytest.raises(DomainValidationError, match="runtime"):
            tool.submit()

    def test_submit_function_without_handler_raises(self) -> None:
        tool = Tool(
            name="Test",
            description="有描述",
            tool_type=ToolType.FUNCTION,
            creator_id=1,
            config=ToolConfig(runtime="python3.12"),
        )
        with pytest.raises(DomainValidationError, match="handler"):
            tool.submit()


# --- approve ---


@pytest.mark.unit
class TestToolApprove:
    @pytest.fixture
    def pending_tool(self) -> Tool:
        tool = Tool(
            name="Test Tool",
            description="一个测试工具",
            tool_type=ToolType.MCP_SERVER,
            creator_id=1,
            config=ToolConfig(server_url="http://localhost:3000"),
        )
        tool.submit()
        return tool

    def test_approve_from_pending_succeeds(self, pending_tool: Tool) -> None:
        pending_tool.approve(reviewer_id=99)
        assert pending_tool.status == ToolStatus.APPROVED

    def test_approve_records_reviewer_id(self, pending_tool: Tool) -> None:
        pending_tool.approve(reviewer_id=99)
        assert pending_tool.reviewer_id == 99

    def test_approve_records_reviewed_at(self, pending_tool: Tool) -> None:
        pending_tool.approve(reviewer_id=99)
        assert pending_tool.reviewed_at is not None

    def test_approve_updates_timestamp(self, pending_tool: Tool) -> None:
        original = pending_tool.updated_at
        pending_tool.approve(reviewer_id=99)
        assert pending_tool.updated_at is not None
        assert original is not None
        assert pending_tool.updated_at >= original

    def test_approve_from_draft_raises(self) -> None:
        tool = Tool(name="Test", tool_type=ToolType.API, creator_id=1)
        with pytest.raises(InvalidStateTransitionError):
            tool.approve(reviewer_id=99)

    def test_approve_from_approved_raises(self, pending_tool: Tool) -> None:
        pending_tool.approve(reviewer_id=99)
        with pytest.raises(InvalidStateTransitionError):
            pending_tool.approve(reviewer_id=100)

    def test_approve_from_rejected_raises(self, pending_tool: Tool) -> None:
        pending_tool.reject(reviewer_id=99, comment="不行")
        with pytest.raises(InvalidStateTransitionError):
            pending_tool.approve(reviewer_id=100)


# --- reject ---


@pytest.mark.unit
class TestToolReject:
    @pytest.fixture
    def pending_tool(self) -> Tool:
        tool = Tool(
            name="Test Tool",
            description="一个测试工具",
            tool_type=ToolType.MCP_SERVER,
            creator_id=1,
            config=ToolConfig(server_url="http://localhost:3000"),
        )
        tool.submit()
        return tool

    def test_reject_from_pending_succeeds(self, pending_tool: Tool) -> None:
        pending_tool.reject(reviewer_id=99, comment="配置不完整")
        assert pending_tool.status == ToolStatus.REJECTED

    def test_reject_records_reviewer_id(self, pending_tool: Tool) -> None:
        pending_tool.reject(reviewer_id=99, comment="配置不完整")
        assert pending_tool.reviewer_id == 99

    def test_reject_records_comment(self, pending_tool: Tool) -> None:
        pending_tool.reject(reviewer_id=99, comment="配置不完整")
        assert pending_tool.review_comment == "配置不完整"

    def test_reject_records_reviewed_at(self, pending_tool: Tool) -> None:
        pending_tool.reject(reviewer_id=99, comment="配置不完整")
        assert pending_tool.reviewed_at is not None

    def test_reject_updates_timestamp(self, pending_tool: Tool) -> None:
        original = pending_tool.updated_at
        pending_tool.reject(reviewer_id=99, comment="不行")
        assert pending_tool.updated_at is not None
        assert original is not None
        assert pending_tool.updated_at >= original

    def test_reject_from_draft_raises(self) -> None:
        tool = Tool(name="Test", tool_type=ToolType.API, creator_id=1)
        with pytest.raises(InvalidStateTransitionError):
            tool.reject(reviewer_id=99, comment="不行")

    def test_reject_from_approved_raises(self, pending_tool: Tool) -> None:
        pending_tool.approve(reviewer_id=99)
        with pytest.raises(InvalidStateTransitionError):
            pending_tool.reject(reviewer_id=100, comment="不行")


# --- resubmit ---


@pytest.mark.unit
class TestToolResubmit:
    @pytest.fixture
    def rejected_tool(self) -> Tool:
        tool = Tool(
            name="Test Tool",
            description="一个测试工具",
            tool_type=ToolType.MCP_SERVER,
            creator_id=1,
            config=ToolConfig(server_url="http://localhost:3000"),
        )
        tool.submit()
        tool.reject(reviewer_id=99, comment="配置不完整")
        return tool

    def test_resubmit_from_rejected_succeeds(self, rejected_tool: Tool) -> None:
        rejected_tool.resubmit()
        assert rejected_tool.status == ToolStatus.PENDING_REVIEW

    def test_resubmit_clears_reviewer_id(self, rejected_tool: Tool) -> None:
        rejected_tool.resubmit()
        assert rejected_tool.reviewer_id is None

    def test_resubmit_clears_review_comment(self, rejected_tool: Tool) -> None:
        rejected_tool.resubmit()
        assert rejected_tool.review_comment == ""

    def test_resubmit_clears_reviewed_at(self, rejected_tool: Tool) -> None:
        rejected_tool.resubmit()
        assert rejected_tool.reviewed_at is None

    def test_resubmit_updates_timestamp(self, rejected_tool: Tool) -> None:
        original = rejected_tool.updated_at
        rejected_tool.resubmit()
        assert rejected_tool.updated_at is not None
        assert original is not None
        assert rejected_tool.updated_at >= original

    def test_resubmit_from_draft_raises(self) -> None:
        tool = Tool(name="Test", tool_type=ToolType.API, creator_id=1)
        with pytest.raises(InvalidStateTransitionError):
            tool.resubmit()

    def test_resubmit_from_pending_raises(self) -> None:
        tool = Tool(
            name="Test",
            description="有描述",
            tool_type=ToolType.MCP_SERVER,
            creator_id=1,
            config=ToolConfig(server_url="http://localhost"),
        )
        tool.submit()
        with pytest.raises(InvalidStateTransitionError):
            tool.resubmit()

    def test_resubmit_from_approved_raises(self) -> None:
        tool = Tool(
            name="Test",
            description="有描述",
            tool_type=ToolType.MCP_SERVER,
            creator_id=1,
            config=ToolConfig(server_url="http://localhost"),
        )
        tool.submit()
        tool.approve(reviewer_id=99)
        with pytest.raises(InvalidStateTransitionError):
            tool.resubmit()


# --- deprecate ---


@pytest.mark.unit
class TestToolDeprecate:
    @pytest.fixture
    def approved_tool(self) -> Tool:
        tool = Tool(
            name="Test Tool",
            description="一个测试工具",
            tool_type=ToolType.MCP_SERVER,
            creator_id=1,
            config=ToolConfig(server_url="http://localhost:3000"),
        )
        tool.submit()
        tool.approve(reviewer_id=99)
        return tool

    def test_deprecate_from_approved_succeeds(self, approved_tool: Tool) -> None:
        approved_tool.deprecate()
        assert approved_tool.status == ToolStatus.DEPRECATED

    def test_deprecate_updates_timestamp(self, approved_tool: Tool) -> None:
        original = approved_tool.updated_at
        approved_tool.deprecate()
        assert approved_tool.updated_at is not None
        assert original is not None
        assert approved_tool.updated_at >= original

    def test_deprecate_from_draft_raises(self) -> None:
        tool = Tool(name="Test", tool_type=ToolType.API, creator_id=1)
        with pytest.raises(InvalidStateTransitionError):
            tool.deprecate()

    def test_deprecate_from_pending_raises(self) -> None:
        tool = Tool(
            name="Test",
            description="有描述",
            tool_type=ToolType.MCP_SERVER,
            creator_id=1,
            config=ToolConfig(server_url="http://localhost"),
        )
        tool.submit()
        with pytest.raises(InvalidStateTransitionError):
            tool.deprecate()

    def test_deprecate_from_rejected_raises(self) -> None:
        tool = Tool(
            name="Test",
            description="有描述",
            tool_type=ToolType.MCP_SERVER,
            creator_id=1,
            config=ToolConfig(server_url="http://localhost"),
        )
        tool.submit()
        tool.reject(reviewer_id=99, comment="不行")
        with pytest.raises(InvalidStateTransitionError):
            tool.deprecate()

    def test_deprecate_from_deprecated_raises(self, approved_tool: Tool) -> None:
        approved_tool.deprecate()
        with pytest.raises(InvalidStateTransitionError):
            approved_tool.deprecate()
