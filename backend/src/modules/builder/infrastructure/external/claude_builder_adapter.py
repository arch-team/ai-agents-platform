"""Claude Builder 适配器。

SDK-First 薄封装层：委托 claude_agent_sdk 生成 Agent 配置,
仅做 prompt 组装 + 流式输出转换。封装层 < 100 行。
"""

from collections.abc import AsyncIterator

import structlog
from claude_agent_sdk import query
from claude_agent_sdk.types import ClaudeAgentOptions, ResultMessage

from src.modules.builder.application.interfaces.builder_llm_service import IBuilderLLMService
from src.shared.domain.constants import AGENT_DEFAULT_MODEL_ID
from src.shared.domain.exceptions import DomainError


log = structlog.get_logger(__name__)

_SYSTEM_PROMPT = (
    "你是一个 Agent 配置生成助手。根据用户描述,生成一个 JSON 格式的 Agent 配置。\n"
    "请严格返回以下 JSON 格式(不要包含其他文字):\n"
    "{\n"
    '  "name": "Agent 名称",\n'
    '  "description": "Agent 描述",\n'
    '  "system_prompt": "Agent 的系统提示词",\n'
    f'  "model_id": "{AGENT_DEFAULT_MODEL_ID}",\n'
    '  "temperature": 0.7,\n'
    '  "max_tokens": 4096\n'
    "}"
)


class ClaudeBuilderAdapter(IBuilderLLMService):
    """Claude Agent SDK 适配器（SDK-First，薄封装）。"""

    async def generate_config(self, prompt: str) -> AsyncIterator[str]:
        """调用 Claude Agent SDK 流式生成 Agent 配置。

        Raises:
            DomainError: SDK 调用失败
        """
        full_prompt = f"请根据以下需求生成 Agent 配置:\n{prompt}"
        options = ClaudeAgentOptions(system_prompt=_SYSTEM_PROMPT)
        try:
            result_text = ""
            async for message in query(prompt=full_prompt, options=options):
                if isinstance(message, ResultMessage):
                    result_text = message.result or ""
        except Exception as e:
            log.exception("claude_builder_sdk_failed", prompt_preview=prompt[:100])
            raise DomainError(message="Agent 配置生成失败", code="BUILDER_GENERATION_FAILED") from e

        yield result_text if result_text else "{}"
