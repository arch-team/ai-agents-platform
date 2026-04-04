"""Claude Builder 适配器。

SDK-First 薄封装层：委托 claude_agent_sdk 生成 Agent 配置/Blueprint,
仅做 prompt 组装 + 流式输出转换。封装层 < 100 行。

V1: generate_config — 单轮 JSON 配置生成 (向后兼容)
V2: generate_blueprint — 多轮 SOP 引导式 Blueprint 生成
"""

from collections.abc import AsyncIterator

import structlog
from claude_agent_sdk import query
from claude_agent_sdk.types import ClaudeAgentOptions, ResultMessage

from src.modules.builder.application.interfaces.builder_llm_service import (
    BuilderMessage,
    IBuilderLLMService,
    PlatformContext,
)
from src.modules.builder.infrastructure.external.builder_prompts import (
    build_system_prompt,
    format_platform_context,
)
from src.shared.domain.constants import AGENT_DEFAULT_MODEL_ID
from src.shared.domain.exceptions import DomainError


log = structlog.get_logger(__name__)

_V1_SYSTEM_PROMPT = (
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
        """V1: 单轮 JSON 配置生成。"""
        full_prompt = f"请根据以下需求生成 Agent 配置:\n{prompt}"
        yield await self._call_sdk(full_prompt, _V1_SYSTEM_PROMPT)

    async def generate_blueprint(
        self,
        messages: list[BuilderMessage],
        platform_context: PlatformContext | None = None,
    ) -> AsyncIterator[str]:
        """V2: 多轮 SOP 引导式 Blueprint 生成。"""
        ctx = platform_context or PlatformContext()
        tools_dicts = [{"id": t.id, "name": t.name, "description": t.description} for t in ctx.available_tools]
        skills_dicts = [
            {"id": s.id, "name": s.name, "description": s.description, "category": s.category}
            for s in ctx.available_skills
        ]
        ctx_text = format_platform_context(tools_dicts, skills_dicts)
        system_prompt = build_system_prompt(platform_context_text=ctx_text)

        # 构建多轮 prompt: 将历史消息拼接为单次请求 (SDK 不支持多轮)
        prompt_parts: list[str] = []
        for msg in messages:
            prefix = "用户" if msg.role == "user" else "助手"
            prompt_parts.append(f"[{prefix}]: {msg.content}")
        full_prompt = "\n\n".join(prompt_parts)

        yield await self._call_sdk(full_prompt, system_prompt)

    @staticmethod
    async def _call_sdk(prompt: str, system_prompt: str) -> str:
        """调用 Claude Agent SDK 并返回结果文本。"""
        options = ClaudeAgentOptions(system_prompt=system_prompt)
        try:
            result_text = ""
            async for message in query(prompt=prompt, options=options):
                if isinstance(message, ResultMessage):
                    result_text = message.result or ""
        except Exception as e:
            log.exception("claude_builder_sdk_failed", prompt_preview=prompt[:100])
            raise DomainError(message="Agent 配置生成失败", code="BUILDER_GENERATION_FAILED") from e
        return result_text if result_text else ""
