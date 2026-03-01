"""Claude Agent SDK 消息解析工具函数。

统一 ClaudeAgentAdapter 和 agent_entrypoint 的消息解析逻辑,
同时支持 dict 格式和对象属性格式 (SDK 版本演进兼容)。
"""

from typing import Any


def extract_content(message: Any) -> str:
    """从 SDK 消息中提取文本内容。

    兼容两种格式:
    - dict: {"type": "text", "content": "..."} 或 {"content": "..."}
    - object: message.content (str 或 list[block]), block.text
    """
    # dict 格式
    if isinstance(message, dict):
        if message.get("type") == "text":
            return str(message.get("content", ""))
        content = message.get("content")
        return content if isinstance(content, str) else ""

    # object 属性格式
    if hasattr(message, "content"):
        content = message.content
        if isinstance(content, str):
            return content
        if isinstance(content, list):
            return "".join(
                str(block.text) if hasattr(block, "text") else (block if isinstance(block, str) else "")
                for block in content
            )

    return str(message) if isinstance(message, str) else ""


def extract_usage(message: Any) -> tuple[int, int]:
    """从 SDK 消息中提取 Token 用量 (input_tokens, output_tokens)。

    兼容两种格式:
    - dict: {"usage": {"input_tokens": N, "output_tokens": N}}
    - object: message.usage (dict 或带属性的对象)
    """
    usage: Any = None

    if isinstance(message, dict):
        usage = message.get("usage")
    elif hasattr(message, "usage"):
        usage = message.usage

    if usage is None:
        return (0, 0)

    if isinstance(usage, dict):
        return (
            int(usage.get("input_tokens", 0)),
            int(usage.get("output_tokens", 0)),
        )

    return (
        int(getattr(usage, "input_tokens", 0)),
        int(getattr(usage, "output_tokens", 0)),
    )
