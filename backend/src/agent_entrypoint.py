"""AgentCore Runtime 入口点。

将 Claude Agent SDK 包装为 AgentCore Runtime 可部署的应用。
部署到 AgentCore Runtime 后，通过 invoke_agent_runtime() API 调用。
"""

from __future__ import annotations

from typing import Any

from bedrock_agentcore.runtime import BedrockAgentCoreApp
from claude_agent_sdk import ClaudeAgentOptions, query


app = BedrockAgentCoreApp()


def _build_mcp_servers(gateway_url: str) -> dict[str, Any]:
    """根据 gateway_url 构建 MCP 服务器配置。"""
    if not gateway_url:
        return {}
    return {"gateway": {"type": "sse", "url": gateway_url}}


@app.entrypoint
async def invoke(payload: dict[str, object]) -> dict[str, object]:
    """AgentCore Runtime 入口函数。

    payload 格式:
    {
        "prompt": "用户消息",
        "system_prompt": "系统提示词",
        "gateway_url": "AgentCore Gateway MCP 端点 (可选)",
        "allowed_tools": ["mcp__gateway__*"],  # 可选
        "max_turns": 20,  # 可选
        "cwd": "/workspace",  # 可选
    }
    """
    prompt = str(payload.get("prompt", ""))
    system_prompt = str(payload.get("system_prompt", ""))
    gateway_url = str(payload.get("gateway_url", ""))
    allowed_tools_raw = payload.get("allowed_tools", [])
    allowed_tools: list[str] = list(allowed_tools_raw) if isinstance(allowed_tools_raw, list) else []
    max_turns_raw = payload.get("max_turns", 20)
    max_turns: int = int(max_turns_raw) if isinstance(max_turns_raw, int) else 20
    cwd = str(payload.get("cwd", ""))

    # 构建 MCP 配置
    mcp_servers = _build_mcp_servers(gateway_url)

    options = ClaudeAgentOptions(
        system_prompt=system_prompt,
        allowed_tools=allowed_tools,
        mcp_servers=mcp_servers,
        permission_mode="bypassPermissions",
        max_turns=max_turns,
        cwd=cwd if cwd else None,
    )

    # 收集 Agent 响应
    collected_content = ""
    usage: dict[str, object] = {}
    session_id: str | None = None

    async for msg in query(prompt=prompt, options=options):
        # 提取内容
        if hasattr(msg, "content"):
            content = msg.content
            blocks = content if isinstance(content, list) else [content]
            for block in blocks:
                if hasattr(block, "text"):
                    collected_content += block.text
                elif isinstance(block, str):
                    collected_content += block
        # 提取 usage
        if hasattr(msg, "usage") and msg.usage:
            usage = msg.usage if isinstance(msg.usage, dict) else {}
        # 提取 session_id
        if hasattr(msg, "session_id"):
            session_id = msg.session_id

    return {
        "content": collected_content,
        "input_tokens": usage.get("input_tokens", 0),
        "output_tokens": usage.get("output_tokens", 0),
        "session_id": session_id,
    }


if __name__ == "__main__":
    app.run()
