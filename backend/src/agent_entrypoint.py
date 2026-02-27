"""AgentCore Runtime 入口点。

将 Claude Agent SDK 包装为 AgentCore Runtime 可部署的应用。
部署到 AgentCore Runtime 后，通过 invoke_agent_runtime() API 调用。
"""

import os
from typing import Any

from bedrock_agentcore.runtime import BedrockAgentCoreApp
from claude_agent_sdk import ClaudeAgentOptions, query

from src.modules.execution.infrastructure.external.sdk_message_utils import (
    extract_content,
    extract_usage,
)


app = BedrockAgentCoreApp()


def _build_mcp_servers(gateway_url: str, *, memory_id: str = "") -> dict[str, Any]:
    """根据 gateway_url 和 memory_id 构建 MCP 服务器配置。"""
    servers: dict[str, Any] = {}

    if gateway_url:
        servers["gateway"] = {"type": "sse", "url": gateway_url}

    # Memory MCP Server (与 ClaudeAgentAdapter._build_mcp_config 对齐)
    if memory_id:
        region = os.environ.get("AWS_REGION", "us-east-1")
        servers["memory"] = {
            "type": "stdio",
            "command": "python",
            "args": ["-m", "src.modules.execution.infrastructure.external.memory_server_entrypoint"],
            "env": {
                "AGENTCORE_MEMORY_ID": memory_id,
                "AWS_REGION": region,
            },
        }

    return servers


@app.entrypoint
async def invoke(payload: dict[str, object]) -> dict[str, object]:
    """AgentCore Runtime 入口函数。

    payload 格式 (与 AgentCoreRuntimeAdapter._build_payload 对齐):
    {
        "prompt": "用户消息",
        "system_prompt": "系统提示词",
        "model_id": "claude-sonnet-4-20250514",  # 可选
        "gateway_url": "AgentCore Gateway MCP 端点",  # 可选
        "allowed_tools": ["mcp__gateway__*"],  # 可选
        "max_turns": 20,  # 可选
        "cwd": "/workspace",  # 可选
        "enable_teams": false,  # 可选
        "memory_id": "agentcore-memory-id",  # 可选
    }
    """
    prompt = str(payload.get("prompt", ""))
    system_prompt = str(payload.get("system_prompt", ""))
    model_id = str(payload.get("model_id", ""))
    gateway_url = str(payload.get("gateway_url", ""))
    allowed_tools_raw = payload.get("allowed_tools", [])
    allowed_tools: list[str] = list(allowed_tools_raw) if isinstance(allowed_tools_raw, list) else []
    max_turns_raw = payload.get("max_turns", 20)
    max_turns: int = int(max_turns_raw) if isinstance(max_turns_raw, int) else 20
    cwd = str(payload.get("cwd", ""))
    enable_teams = bool(payload.get("enable_teams", False))
    memory_id = str(payload.get("memory_id", ""))

    # Agent Teams: 注入环境变量 (与 ClaudeAgentAdapter._build_options 对齐)
    env: dict[str, str] = {}
    if enable_teams:
        os.environ["CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS"] = "1"
        env["CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS"] = "1"
        # 团队模式默认提升 max_turns
        if max_turns <= 20:
            max_turns = 200

    # 构建 MCP 配置
    mcp_servers = _build_mcp_servers(gateway_url, memory_id=memory_id)

    # 构建 SDK 选项
    kwargs: dict[str, Any] = {
        "system_prompt": system_prompt,
        "allowed_tools": allowed_tools,
        "mcp_servers": mcp_servers,
        "permission_mode": "bypassPermissions",
        "max_turns": max_turns,
    }
    if model_id:
        kwargs["model"] = model_id
    if cwd:
        kwargs["cwd"] = cwd
    if env:
        kwargs["env"] = env

    options = ClaudeAgentOptions(**kwargs)

    # 收集 Agent 响应 (使用统一的 SDK 消息解析工具)
    collected_content = ""
    total_input_tokens = 0
    total_output_tokens = 0
    session_id: str | None = None

    async for msg in query(prompt=prompt, options=options):
        msg_content = extract_content(msg)
        if msg_content:
            collected_content += msg_content
        msg_input, msg_output = extract_usage(msg)
        total_input_tokens += msg_input
        total_output_tokens += msg_output
        # 提取 session_id
        if hasattr(msg, "session_id"):
            session_id = msg.session_id

    return {
        "content": collected_content,
        "input_tokens": total_input_tokens,
        "output_tokens": total_output_tokens,
        "session_id": session_id,
    }


if __name__ == "__main__":
    app.run()
