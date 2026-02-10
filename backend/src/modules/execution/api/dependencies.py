"""Execution API 依赖注入。"""

from functools import lru_cache
from typing import Annotated

import boto3
from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from src.modules.execution.application.services.execution_service import ExecutionService
from src.modules.execution.infrastructure.external.bedrock_llm_client import BedrockLLMClient
from src.modules.execution.infrastructure.persistence.repositories.conversation_repository_impl import (
    ConversationRepositoryImpl,
)
from src.modules.execution.infrastructure.persistence.repositories.message_repository_impl import (
    MessageRepositoryImpl,
)
from src.presentation.api.providers import get_agent_querier
from src.shared.domain.interfaces.agent_querier import IAgentQuerier
from src.shared.infrastructure.database import get_db, get_session_factory
from src.shared.infrastructure.settings import get_settings


@lru_cache
def get_bedrock_client() -> BedrockLLMClient:
    """创建 BedrockLLMClient 单例。"""
    settings = get_settings()
    client = boto3.client("bedrock-runtime", region_name=settings.AWS_REGION)
    return BedrockLLMClient(client=client)


async def get_execution_service(
    session: Annotated[AsyncSession, Depends(get_db)],
    agent_querier: Annotated[IAgentQuerier, Depends(get_agent_querier)],
) -> ExecutionService:
    """创建 ExecutionService 实例。

    stream_finalize_repos 使用独立 session 创建, 避免 SSE 流式响应中
    DI session 已关闭后 DB 写操作失败的问题。
    """
    conversation_repo = ConversationRepositoryImpl(session=session)
    message_repo = MessageRepositoryImpl(session=session)
    llm_client = get_bedrock_client()

    # 为流后 DB 写操作创建独立 session 的 repos
    stream_session = get_session_factory()()
    stream_finalize_repos = (
        MessageRepositoryImpl(session=stream_session),
        ConversationRepositoryImpl(session=stream_session),
    )

    return ExecutionService(
        conversation_repo=conversation_repo,
        message_repo=message_repo,
        llm_client=llm_client,
        agent_querier=agent_querier,
        stream_finalize_repos=stream_finalize_repos,
    )
