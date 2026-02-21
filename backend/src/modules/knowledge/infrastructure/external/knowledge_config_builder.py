"""Bedrock Knowledge Base 配置构建。

BedrockKnowledgeAdapter 的辅助模块，负责：
- KB 创建所需的 knowledgeBaseConfiguration 构建
- OpenSearch Serverless 存储配置构建
"""

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class BedrockKBConfig:
    """Bedrock Knowledge Base 创建所需的配置参数。"""

    role_arn: str
    embedding_model_arn: str
    collection_arn: str


def build_kb_configuration(cfg: BedrockKBConfig) -> dict[str, Any]:
    """构建 knowledgeBaseConfiguration 参数。"""
    return {
        "type": "VECTOR",
        "vectorKnowledgeBaseConfiguration": {
            "embeddingModelArn": cfg.embedding_model_arn,
        },
    }


def build_storage_configuration(cfg: BedrockKBConfig, name: str) -> dict[str, Any]:
    """构建 OpenSearch Serverless 存储配置。"""
    return {
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
