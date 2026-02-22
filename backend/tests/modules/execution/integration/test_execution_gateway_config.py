"""集成测试: execution 模块 Gateway URL → MCP 配置完整构建链路。

验证 ClaudeAgentAdapter._build_mcp_config / _build_allowed_tools 及
ExecutionService._build_agent_request 中 gateway_url 的传递与格式正确性。
"""

from __future__ import annotations

from unittest.mock import AsyncMock

import pytest

from src.modules.execution.application.interfaces.agent_runtime import (
    AgentRequest,
    AgentTool,
)
from src.modules.execution.infrastructure.external.claude_agent_adapter import (
    ClaudeAgentAdapter,
)


# 集成测试需直接调用 private 方法验证内部构建逻辑
# ruff: noqa: SLF001


pytestmark = pytest.mark.integration


# ── Fixture ──


@pytest.fixture
def adapter() -> ClaudeAgentAdapter:
    """无 memory 的 ClaudeAgentAdapter 实例。"""
    return ClaudeAgentAdapter(memory_id="", region="us-east-1")


def _make_mcp_tool(name: str = "mcp-tool-1") -> AgentTool:
    return AgentTool(
        name=name,
        description="MCP 测试工具",
        input_schema={},
        tool_type="mcp_server",
        config={"server_url": "http://mcp.example.com"},
    )


def _make_api_tool(name: str = "api-tool-1") -> AgentTool:
    return AgentTool(
        name=name,
        description="API 测试工具",
        input_schema={},
        tool_type="api",
        config={"endpoint_url": "http://api.example.com", "method": "POST"},
    )


def _make_function_tool(name: str = "func-tool-1") -> AgentTool:
    return AgentTool(
        name=name,
        description="Function 测试工具",
        input_schema={},
        tool_type="function",
        config={"runtime": "python3.11", "handler": "index.handler"},
    )


# ── 测试: MCP 配置构建 ──


class TestBuildMcpConfig:
    """验证 ClaudeAgentAdapter._build_mcp_config 构建逻辑。"""

    def test_mcp_config_with_mcp_tools_and_gateway(self, adapter: ClaudeAgentAdapter) -> None:
        """MCP 工具 + gateway_url → mcp_servers 包含 gateway。"""
        request = AgentRequest(
            prompt="你好",
            tools=[_make_mcp_tool()],
            gateway_url="https://gateway.example.com/mcp",
        )
        mcp_servers = adapter._build_mcp_config(request)

        assert "gateway" in mcp_servers
        assert mcp_servers["gateway"] == {"type": "sse", "url": "https://gateway.example.com/mcp"}

    def test_mcp_config_without_gateway_url(self, adapter: ClaudeAgentAdapter) -> None:
        """无 gateway_url → mcp_servers 不包含 gateway。"""
        request = AgentRequest(
            prompt="你好",
            tools=[_make_mcp_tool()],
            gateway_url="",
        )
        mcp_servers = adapter._build_mcp_config(request)

        assert "gateway" not in mcp_servers

    def test_mcp_config_only_api_tools(self, adapter: ClaudeAgentAdapter) -> None:
        """仅 API 工具 → 无 gateway，有 platform-tools。"""
        request = AgentRequest(
            prompt="你好",
            tools=[_make_api_tool()],
            gateway_url="https://gateway.example.com/mcp",
        )
        mcp_servers = adapter._build_mcp_config(request)

        assert "gateway" not in mcp_servers
        assert "platform-tools" in mcp_servers

    def test_mcp_config_mixed_tools(self, adapter: ClaudeAgentAdapter) -> None:
        """混合工具类型 → gateway + platform-tools 共存。"""
        request = AgentRequest(
            prompt="你好",
            tools=[_make_mcp_tool(), _make_api_tool()],
            gateway_url="https://gateway.example.com/mcp",
        )
        mcp_servers = adapter._build_mcp_config(request)

        assert "gateway" in mcp_servers
        assert "platform-tools" in mcp_servers


class TestBuildAllowedTools:
    """验证 ClaudeAgentAdapter._build_allowed_tools 命名格式。"""

    def test_allowed_tools_mcp_naming(self, adapter: ClaudeAgentAdapter) -> None:
        """MCP 工具白名单命名: mcp__gateway__{name}。"""
        request = AgentRequest(prompt="你好", tools=[_make_mcp_tool("search")])
        allowed = adapter._build_allowed_tools(request)

        assert "mcp__gateway__search" in allowed

    def test_allowed_tools_api_naming(self, adapter: ClaudeAgentAdapter) -> None:
        """API 工具白名单命名: mcp__platform-tools__{name}。"""
        request = AgentRequest(prompt="你好", tools=[_make_api_tool("weather")])
        allowed = adapter._build_allowed_tools(request)

        assert "mcp__platform-tools__weather" in allowed


class TestGatewayUrlFlowsThrough:
    """验证 ExecutionService → AgentRequest 的 gateway_url 传递。"""

    @pytest.mark.asyncio
    async def test_gateway_url_flows_through_service(self) -> None:
        """ExecutionService._build_agent_request 将 gateway_url 传入 AgentRequest。"""
        from src.modules.execution.application.services.execution_service import (
            ExecutionService,
            _SendContext,
        )
        from src.modules.execution.domain.entities.conversation import Conversation
        from src.modules.execution.domain.entities.message import Message
        from src.modules.execution.domain.value_objects.message_role import MessageRole
        from src.shared.domain.interfaces.agent_querier import ActiveAgentInfo

        service = ExecutionService(
            conversation_repo=AsyncMock(),
            message_repo=AsyncMock(),
            llm_client=AsyncMock(),
            agent_querier=AsyncMock(),
            agent_runtime=AsyncMock(),
            gateway_url="https://gw.test.com/mcp",
        )

        ctx = _SendContext(
            conversation=Conversation(id=1, title="测试", agent_id=1, user_id=1),
            agent_info=ActiveAgentInfo(
                id=1,
                name="Agent",
                system_prompt="",
                model_id="claude-3",
                temperature=0.7,
                max_tokens=4096,
                top_p=1.0,
                runtime_type="agent",
            ),
            created_user_msg=Message(id=1, conversation_id=1, role=MessageRole.USER, content="hi"),
            llm_messages=[],
        )

        request = service._build_agent_request(ctx, tools=[])

        assert request.gateway_url == "https://gw.test.com/mcp"
