"""Bedrock Knowledge Bases API 薄封装适配器。"""

import asyncio
from dataclasses import dataclass
from typing import Any

from src.modules.knowledge.application.interfaces.knowledge_service import (
    IKnowledgeService,
    KBCreateResult,
    KBSyncResult,
    RetrievalChunk,
)
from src.shared.domain.exceptions import DomainError


@dataclass(frozen=True)
class BedrockKBConfig:
    """Bedrock Knowledge Base 创建所需的配置参数。"""

    role_arn: str
    embedding_model_arn: str
    collection_arn: str


class BedrockKnowledgeAdapter(IKnowledgeService):
    """Bedrock Knowledge Bases 适配器。SDK-First, < 100 行。"""

    def __init__(
        self,
        bedrock_agent_client: Any,  # noqa: ANN401
        bedrock_runtime_client: Any,  # noqa: ANN401
        *,
        kb_config: BedrockKBConfig | None = None,
    ) -> None:
        self._agent = bedrock_agent_client    # boto3.client("bedrock-agent")
        self._runtime = bedrock_runtime_client  # boto3.client("bedrock-agent-runtime")
        self._kb_config = kb_config

    async def create_knowledge_base(
        self, name: str, *, s3_bucket: str, s3_prefix: str,  # noqa: ARG002
    ) -> KBCreateResult:
        """创建 Bedrock Knowledge Base。"""
        if self._kb_config is None:
            raise DomainError(
                message="Bedrock KB 配置缺失，请设置 BEDROCK_KB_* 环境变量",
                code="BEDROCK_KB_CONFIG_MISSING",
            )
        try:
            cfg = self._kb_config
            kb_configuration = {
                "type": "VECTOR",
                "vectorKnowledgeBaseConfiguration": {
                    "embeddingModelArn": cfg.embedding_model_arn,
                },
            }
            storage_config = {
                "type": "OPENSEARCH_SERVERLESS",
                "opensearchServerlessConfiguration": {
                    "collectionArn": cfg.collection_arn,
                    "vectorIndexName": f"kb-{name}",
                    "fieldMapping": {
                        "vectorField": "embedding",
                        "textField": "text",
                        "metadataField": "metadata",
                    },
                },
            }
            resp = await asyncio.to_thread(
                self._agent.create_knowledge_base,
                name=name,
                roleArn=cfg.role_arn,
                knowledgeBaseConfiguration=kb_configuration,
                storageConfiguration=storage_config,
            )
            kb_id = resp["knowledgeBase"]["knowledgeBaseId"]
            return KBCreateResult(bedrock_kb_id=kb_id, s3_prefix=s3_prefix)
        except DomainError:
            raise
        except Exception as e:
            raise DomainError(message=f"Bedrock KB 创建失败: {e}", code="BEDROCK_KB_CREATE_FAILED") from e

    async def delete_knowledge_base(self, bedrock_kb_id: str) -> None:
        """删除 Bedrock Knowledge Base。"""
        try:
            await asyncio.to_thread(self._agent.delete_knowledge_base, knowledgeBaseId=bedrock_kb_id)
        except Exception as e:
            raise DomainError(message=f"Bedrock KB 删除失败: {e}", code="BEDROCK_KB_DELETE_FAILED") from e

    async def start_sync(self, bedrock_kb_id: str) -> KBSyncResult:
        """触发数据源同步。"""
        try:
            resp = await asyncio.to_thread(
                self._agent.start_ingestion_job, knowledgeBaseId=bedrock_kb_id, dataSourceId="default",
            )
            job = resp["ingestionJob"]
            return KBSyncResult(ingestion_job_id=job["ingestionJobId"], status=job["status"])
        except Exception as e:
            raise DomainError(message=f"Bedrock 同步失败: {e}", code="BEDROCK_SYNC_FAILED") from e

    async def retrieve(self, bedrock_kb_id: str, query: str, *, top_k: int = 5) -> list[RetrievalChunk]:
        """语义检索。"""
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
            raise DomainError(message=f"Bedrock 检索失败: {e}", code="BEDROCK_RETRIEVE_FAILED") from e
