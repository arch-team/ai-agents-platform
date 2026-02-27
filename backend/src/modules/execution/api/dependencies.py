"""Execution API 依赖注入。"""

from collections.abc import Awaitable, Callable
from functools import lru_cache
from typing import Annotated

import boto3
from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from src.modules.execution.application.dto.execution_dto import ContextWindowConfig
from src.modules.execution.application.interfaces.agent_runtime import IAgentRuntime
from src.modules.execution.application.services.execution_service import ExecutionService
from src.modules.execution.application.services.team_execution_service import TeamExecutionService
from src.modules.execution.infrastructure.external.bedrock_llm_client import BedrockLLMClient
from src.modules.execution.infrastructure.external.claude_agent_adapter import ClaudeAgentAdapter
from src.modules.execution.infrastructure.persistence.repositories.conversation_repository_impl import (
    ConversationRepositoryImpl,
)
from src.modules.execution.infrastructure.persistence.repositories.message_repository_impl import (
    MessageRepositoryImpl,
)
from src.modules.execution.infrastructure.persistence.repositories.team_execution_repository_impl import (
    TeamExecutionLogRepositoryImpl,
    TeamExecutionRepositoryImpl,
)
from src.presentation.api.providers import get_agent_querier, get_knowledge_querier, get_tool_querier
from src.shared.domain.interfaces.agent_querier import IAgentQuerier
from src.shared.domain.interfaces.knowledge_querier import IKnowledgeQuerier
from src.shared.domain.interfaces.tool_querier import IToolQuerier
from src.shared.infrastructure.database import get_db, get_session_factory
from src.shared.infrastructure.settings import get_settings


@lru_cache
def get_bedrock_client() -> BedrockLLMClient:
    """创建 BedrockLLMClient 单例。"""
    settings = get_settings()
    client = boto3.client("bedrock-runtime", region_name=settings.AWS_REGION)
    return BedrockLLMClient(client=client)


@lru_cache
def get_agent_runtime() -> IAgentRuntime:
    """根据 AGENT_RUNTIME_MODE 配置创建 Agent 运行时单例。

    - in_process: ClaudeAgentAdapter (本地 Claude Agent SDK)
    - agentcore_runtime: AgentCoreRuntimeAdapter (远程 AgentCore Runtime API)
    """
    settings = get_settings()
    mode = settings.AGENT_RUNTIME_MODE

    if mode == "agentcore_runtime":
        from src.modules.execution.infrastructure.external.agentcore_runtime_adapter import (
            AgentCoreRuntimeAdapter,
        )

        if not settings.AGENTCORE_RUNTIME_ARN:
            import structlog

            structlog.get_logger(__name__).warning("AGENTCORE_RUNTIME_ARN 未配置, 降级到 in_process")
        else:
            from botocore.config import Config

            # Agent Loop 可能运行数分钟, 增加 read timeout (默认 60s 不够)
            agentcore_config = Config(read_timeout=600, connect_timeout=10, retries={"max_attempts": 0})
            client = boto3.client("bedrock-agentcore", region_name=settings.AWS_REGION, config=agentcore_config)
            return AgentCoreRuntimeAdapter(
                client=client,
                runtime_arn=settings.AGENTCORE_RUNTIME_ARN,
            )

    # 默认: in_process 模式
    return ClaudeAgentAdapter()


async def get_execution_service(
    session: Annotated[AsyncSession, Depends(get_db)],
    agent_querier: Annotated[IAgentQuerier, Depends(get_agent_querier)],
    tool_querier: Annotated[IToolQuerier, Depends(get_tool_querier)],
    knowledge_querier: Annotated[IKnowledgeQuerier, Depends(get_knowledge_querier)],
) -> ExecutionService:
    """创建 ExecutionService 实例。

    stream_finalize_repos 使用独立 session 创建, 避免 SSE 流式响应中
    DI session 已关闭后 DB 写操作失败的问题。
    """
    conversation_repo = ConversationRepositoryImpl(session=session)
    message_repo = MessageRepositoryImpl(session=session)
    llm_client = get_bedrock_client()
    agent_runtime = get_agent_runtime()

    # 为流后 DB 写操作创建独立 session 的 repos
    stream_session = get_session_factory()()
    stream_finalize_repos = (
        MessageRepositoryImpl(session=stream_session),
        ConversationRepositoryImpl(session=stream_session),
    )

    settings = get_settings()
    context_window = ContextWindowConfig(
        max_context_tokens=settings.MAX_CONTEXT_TOKENS,
        system_prompt_token_budget=settings.SYSTEM_PROMPT_TOKEN_BUDGET,
    )
    return ExecutionService(
        conversation_repo=conversation_repo,
        message_repo=message_repo,
        llm_client=llm_client,
        agent_querier=agent_querier,
        stream_finalize_repos=stream_finalize_repos,
        knowledge_querier=knowledge_querier,
        agent_runtime=agent_runtime,
        tool_querier=tool_querier,
        gateway_url=settings.AGENTCORE_GATEWAY_URL,
        context_window=context_window,
        stream_session_commit=stream_session.commit,
        stream_session_close=stream_session.close,
    )


async def get_team_execution_service(
    session: Annotated[AsyncSession, Depends(get_db)],
    agent_querier: Annotated[IAgentQuerier, Depends(get_agent_querier)],
) -> TeamExecutionService:
    """创建 TeamExecutionService 实例。

    bg_repo_factory 为后台 asyncio.Task 提供独立 DB session 的 repos,
    避免请求级 session 关闭后后台任务 DB 操作失败 (与 stream_finalize_repos 同理)。
    """
    execution_repo = TeamExecutionRepositoryImpl(session=session)
    log_repo = TeamExecutionLogRepositoryImpl(session=session)
    agent_runtime = get_agent_runtime()
    settings = get_settings()

    def _bg_repo_factory() -> tuple[
        TeamExecutionRepositoryImpl,
        TeamExecutionLogRepositoryImpl,
        Callable[[], Awaitable[None]],
        Callable[[], Awaitable[None]],
    ]:
        """为后台任务创建独立 session 的 repos。"""
        bg_session = get_session_factory()()
        return (
            TeamExecutionRepositoryImpl(session=bg_session),
            TeamExecutionLogRepositoryImpl(session=bg_session),
            bg_session.commit,
            bg_session.close,
        )

    return TeamExecutionService(
        execution_repo=execution_repo,
        log_repo=log_repo,
        agent_runtime=agent_runtime,
        agent_querier=agent_querier,
        gateway_url=settings.AGENTCORE_GATEWAY_URL,
        max_turns=settings.TEAM_EXECUTION_MAX_TURNS,
        timeout_seconds=settings.TEAM_EXECUTION_TIMEOUT_SECONDS,
        max_concurrent=settings.TEAM_EXECUTION_MAX_CONCURRENT,
        bg_repo_factory=_bg_repo_factory,
    )
