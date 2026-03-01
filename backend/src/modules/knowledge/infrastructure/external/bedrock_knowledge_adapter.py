"""Bedrock Knowledge Bases API 薄封装适配器。"""

import asyncio
from typing import Any

import structlog

from src.modules.knowledge.application.interfaces.knowledge_service import (
    IKnowledgeService,
    KBCreateResult,
    KBSyncResult,
    RetrievalChunk,
)
from src.modules.knowledge.infrastructure.external.knowledge_config_builder import (
    BedrockKBConfig,
    build_kb_configuration,
    build_storage_configuration,
)
from src.shared.domain.exceptions import DomainError


logger = structlog.get_logger(__name__)


class BedrockKnowledgeAdapter(IKnowledgeService):
    """Bedrock Knowledge Bases 适配器。SDK-First, < 100 行。"""

    def __init__(
        self,
        bedrock_agent_client: Any,
        bedrock_runtime_client: Any,
        *,
        kb_config: BedrockKBConfig | None = None,
    ) -> None:
        self._agent = bedrock_agent_client
        self._runtime = bedrock_runtime_client
        self._kb_config = kb_config

    async def create_knowledge_base(self, name: str, *, s3_bucket: str, s3_prefix: str) -> KBCreateResult:
        if self._kb_config is None:
            raise DomainError(
                message="Bedrock KB 配置缺失, 请设置 BEDROCK_KB_* 环境变量",
                code="BEDROCK_KB_CONFIG_MISSING",
            )
        try:
            cfg = self._kb_config
            resp = await asyncio.to_thread(
                self._agent.create_knowledge_base,
                name=name,
                roleArn=cfg.role_arn,
                knowledgeBaseConfiguration=build_kb_configuration(cfg),
                storageConfiguration=build_storage_configuration(cfg, name),
            )
            kb_id = resp["knowledgeBase"]["knowledgeBaseId"]
            return KBCreateResult(bedrock_kb_id=kb_id, s3_prefix=s3_prefix)
        except DomainError:
            raise
        except Exception as e:
            logger.exception("Bedrock KB 创建失败")
            raise DomainError(message="Bedrock KB 创建失败, 请稍后重试", code="BEDROCK_KB_CREATE_FAILED") from e

    async def delete_knowledge_base(self, bedrock_kb_id: str) -> None:
        try:
            await asyncio.to_thread(self._agent.delete_knowledge_base, knowledgeBaseId=bedrock_kb_id)
        except Exception as e:
            logger.exception("Bedrock KB 删除失败")
            raise DomainError(message="Bedrock KB 删除失败, 请稍后重试", code="BEDROCK_KB_DELETE_FAILED") from e

    async def start_sync(self, bedrock_kb_id: str) -> KBSyncResult:
        try:
            resp = await asyncio.to_thread(
                self._agent.start_ingestion_job,
                knowledgeBaseId=bedrock_kb_id,
                dataSourceId="default",
            )
            job = resp["ingestionJob"]
            return KBSyncResult(ingestion_job_id=job["ingestionJobId"], status=job["status"])
        except Exception as e:
            logger.exception("Bedrock 同步失败")
            raise DomainError(message="Bedrock 同步失败, 请稍后重试", code="BEDROCK_SYNC_FAILED") from e

    async def retrieve(self, bedrock_kb_id: str, query: str, *, top_k: int = 5) -> list[RetrievalChunk]:
        try:
            resp = await asyncio.to_thread(
                self._runtime.retrieve,
                knowledgeBaseId=bedrock_kb_id,
                retrievalQuery={"text": query},
                retrievalConfiguration={"vectorSearchConfiguration": {"numberOfResults": top_k}},
            )
            return [
                RetrievalChunk(
                    content=r.get("content", {}).get("text", ""),
                    score=r.get("score", 0.0),
                    document_id=r.get("location", {}).get("s3Location", {}).get("uri", ""),
                )
                for r in resp.get("retrievalResults", [])
            ]
        except Exception as e:
            logger.exception("Bedrock 检索失败")
            raise DomainError(message="Bedrock 检索失败, 请稍后重试", code="BEDROCK_RETRIEVE_FAILED") from e
