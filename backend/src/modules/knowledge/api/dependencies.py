"""Knowledge API 依赖注入。"""

from functools import lru_cache
from typing import Annotated

import boto3
from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from src.modules.knowledge.application.services.knowledge_service import KnowledgeService
from src.modules.knowledge.infrastructure.external.bedrock_knowledge_adapter import BedrockKnowledgeAdapter
from src.modules.knowledge.infrastructure.external.knowledge_config_builder import BedrockKBConfig
from src.modules.knowledge.infrastructure.external.s3_document_storage import S3DocumentStorage
from src.modules.knowledge.infrastructure.persistence.repositories.document_repository_impl import (
    DocumentRepositoryImpl,
)
from src.modules.knowledge.infrastructure.persistence.repositories.knowledge_base_repository_impl import (
    KnowledgeBaseRepositoryImpl,
)
from src.shared.infrastructure.database import get_db
from src.shared.infrastructure.settings import get_settings


@lru_cache
def get_bedrock_knowledge_client() -> BedrockKnowledgeAdapter:
    """创建 BedrockKnowledgeAdapter 单例。"""
    settings = get_settings()
    agent_client = boto3.client("bedrock-agent", region_name=settings.AWS_REGION)
    runtime_client = boto3.client("bedrock-agent-runtime", region_name=settings.AWS_REGION)
    # 有配置时传入 KB 参数, 开发环境允许为空 (创建时会校验)
    kb_config = None
    if settings.BEDROCK_KB_ROLE_ARN and settings.BEDROCK_KB_EMBEDDING_MODEL_ARN:
        kb_config = BedrockKBConfig(
            role_arn=settings.BEDROCK_KB_ROLE_ARN,
            embedding_model_arn=settings.BEDROCK_KB_EMBEDDING_MODEL_ARN,
            collection_arn=settings.BEDROCK_KB_COLLECTION_ARN,
        )
    return BedrockKnowledgeAdapter(agent_client, runtime_client, kb_config=kb_config)


@lru_cache
def get_s3_storage() -> S3DocumentStorage:
    """创建 S3DocumentStorage 单例。"""
    settings = get_settings()
    s3_client = boto3.client("s3", region_name=settings.AWS_REGION)
    return S3DocumentStorage(s3_client, bucket=f"{settings.APP_NAME}-knowledge")


async def get_knowledge_service(
    session: Annotated[AsyncSession, Depends(get_db)],
) -> KnowledgeService:
    """创建 KnowledgeService 实例。"""
    return KnowledgeService(
        kb_repo=KnowledgeBaseRepositoryImpl(session=session),
        doc_repo=DocumentRepositoryImpl(session=session),
        knowledge_svc=get_bedrock_knowledge_client(),
        doc_storage=get_s3_storage(),
    )
