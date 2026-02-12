"""Memory MCP Server 配置工厂。

将 AgentCore Memory 能力封装为 MCP Server 的 stdio 配置,
供 ClaudeAgentAdapter 注入到 Claude Agent SDK 的 mcp_servers。

Memory MCP Server 作为子进程运行, 通过环境变量接收 Memory ID 和 Region,
内部调用 boto3 AgentCore Memory API 实现 save_memory / recall_memory 工具。

未配置 memory_id 时返回空配置 (降级为无 Memory)。
"""

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class MemoryMcpConfig:
    """AgentCore Memory MCP Server 配置值对象。"""

    memory_id: str  # AgentCore Memory 资源 ID
    region: str  # AWS Region


def build_memory_mcp_server_config(config: MemoryMcpConfig) -> dict[str, Any]:
    """构建 Memory MCP Server 的 stdio 配置。

    Returns:
        MCP Server 配置字典, 未配置 memory_id 时返回空字典。
    """
    if not config.memory_id:
        return {}

    return {
        "type": "stdio",
        "command": "python",
        "args": ["-m", "src.modules.execution.infrastructure.external.memory_server_entrypoint"],
        "env": {
            "AGENTCORE_MEMORY_ID": config.memory_id,
            "AWS_REGION": config.region,
        },
    }
