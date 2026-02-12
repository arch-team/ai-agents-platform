"""Memory MCP Server stdio 入口点。

Claude Agent SDK 通过 stdio 启动本模块作为子进程，
提供 save_memory 和 recall_memory 两个 MCP 工具。

启动方式: python -m src.modules.execution.infrastructure.external.memory_server_entrypoint

环境变量:
    AGENTCORE_MEMORY_ID: AgentCore Memory 资源 ID
    AWS_REGION: AWS Region (默认 ap-northeast-1)
"""

from __future__ import annotations

import asyncio
import json
import sys
from typing import Any

import structlog

from src.modules.execution.infrastructure.external.memory_adapter import MemoryAdapter


logger = structlog.get_logger(__name__)

# MCP 协议常量
JSONRPC_VERSION = "2.0"
MCP_PROTOCOL_VERSION = "2024-11-05"
SERVER_NAME = "agentcore-memory"
SERVER_VERSION = "0.1.0"

# 工具定义
TOOLS = [
    {
        "name": "save_memory",
        "description": "Save important information to AgentCore Memory for cross-session persistence.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "agent_id": {
                    "type": "integer",
                    "description": "Agent ID",
                },
                "content": {
                    "type": "string",
                    "description": "要保存的内容",
                },
                "topic": {
                    "type": "string",
                    "description": "内容主题分类 (如 偏好、上下文、事实)",
                },
            },
            "required": ["agent_id", "content", "topic"],
        },
    },
    {
        "name": "recall_memory",
        "description": "从 AgentCore Memory 检索与查询相关的历史记忆。",
        "inputSchema": {
            "type": "object",
            "properties": {
                "agent_id": {
                    "type": "integer",
                    "description": "Agent ID",
                },
                "query": {
                    "type": "string",
                    "description": "检索查询文本",
                },
                "max_results": {
                    "type": "integer",
                    "description": "最大返回条数 (默认 5)",
                    "default": 5,
                },
            },
            "required": ["agent_id", "query"],
        },
    },
]


def _make_response(request_id: int | str | None, result: dict[str, Any]) -> dict[str, Any]:
    """构建 JSON-RPC 成功响应。"""
    return {
        "jsonrpc": JSONRPC_VERSION,
        "id": request_id,
        "result": result,
    }


def _make_error(
    request_id: int | str | None,
    code: int,
    message: str,
) -> dict[str, Any]:
    """构建 JSON-RPC 错误响应。"""
    return {
        "jsonrpc": JSONRPC_VERSION,
        "id": request_id,
        "error": {"code": code, "message": message},
    }


def _handle_initialize(request_id: int | str | None) -> dict[str, Any]:
    """处理 initialize 请求。"""
    return _make_response(request_id, {
        "protocolVersion": MCP_PROTOCOL_VERSION,
        "capabilities": {"tools": {}},
        "serverInfo": {
            "name": SERVER_NAME,
            "version": SERVER_VERSION,
        },
    })


def _handle_tools_list(request_id: int | str | None) -> dict[str, Any]:
    """处理 tools/list 请求。"""
    return _make_response(request_id, {"tools": TOOLS})


async def _handle_tools_call(
    request_id: int | str | None,
    params: dict[str, Any],
    adapter: MemoryAdapter,
) -> dict[str, Any]:
    """处理 tools/call 请求。"""
    tool_name = params.get("name", "")
    arguments: dict[str, Any] = params.get("arguments", {})

    if tool_name == "save_memory":
        record_id = await adapter.save_memory(
            agent_id=arguments["agent_id"],
            content=arguments["content"],
            topic=arguments["topic"],
        )
        return _make_response(request_id, {
            "content": [{"type": "text", "text": record_id or "memory_save_skipped"}],
        })

    if tool_name == "recall_memory":
        items = await adapter.recall_memory(
            agent_id=arguments["agent_id"],
            query=arguments["query"],
            max_results=arguments.get("max_results", 5),
        )
        results = [
            {
                "memory_id": item.memory_id,
                "content": item.content,
                "topic": item.topic,
                "relevance_score": item.relevance_score,
            }
            for item in items
        ]
        return _make_response(request_id, {
            "content": [{"type": "text", "text": json.dumps(results, ensure_ascii=False)}],
        })

    return _make_error(request_id, -32601, f"未知工具: {tool_name}")


async def handle_message(
    message: dict[str, Any],
    adapter: MemoryAdapter,
) -> dict[str, Any] | None:
    """分发单条 JSON-RPC 消息到对应处理器。

    Returns:
        JSON-RPC 响应字典，notifications 返回 None。
    """
    method = message.get("method", "")
    request_id = message.get("id")
    params: dict[str, Any] = message.get("params", {})

    # notifications (无 id) 不需要响应
    if method == "notifications/initialized":
        return None

    if method == "initialize":
        return _handle_initialize(request_id)

    if method == "tools/list":
        return _handle_tools_list(request_id)

    if method == "tools/call":
        return await _handle_tools_call(request_id, params, adapter)

    return _make_error(request_id, -32601, f"未知方法: {method}")


async def run_stdio_loop(adapter: MemoryAdapter) -> None:
    """stdin→stdout JSON-RPC 消息循环。

    逐行读取 stdin 的 JSON-RPC 消息，处理后写入 stdout。
    """
    reader = asyncio.StreamReader()
    protocol = asyncio.StreamReaderProtocol(reader)
    await asyncio.get_event_loop().connect_read_pipe(lambda: protocol, sys.stdin)

    loop = asyncio.get_event_loop()
    write_transport, _ = await loop.connect_write_pipe(
        asyncio.Protocol, sys.stdout,
    )

    logger.info("memory_mcp_server_started")

    while True:
        line = await reader.readline()
        if not line:
            break

        line_str = line.decode("utf-8").strip()
        if not line_str:
            continue

        try:
            message = json.loads(line_str)
        except json.JSONDecodeError:
            logger.warning("invalid_json_rpc", raw=line_str[:200])
            continue

        response = await handle_message(message, adapter)
        if response is not None:
            output = json.dumps(response, ensure_ascii=False) + "\n"
            write_transport.write(output.encode("utf-8"))


def main() -> None:
    """入口函数: 从环境变量读取配置并启动 stdio 循环。"""
    import os

    memory_id = os.environ.get("AGENTCORE_MEMORY_ID", "")
    region = os.environ.get("AWS_REGION", "ap-northeast-1")

    adapter = MemoryAdapter(memory_id=memory_id, region=region)

    logger.info(
        "memory_mcp_server_init",
        memory_id=memory_id or "(not configured, NoOp fallback)",
        region=region,
    )

    asyncio.run(run_stdio_loop(adapter))


if __name__ == "__main__":
    main()
