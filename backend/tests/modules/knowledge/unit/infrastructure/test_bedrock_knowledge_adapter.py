"""BedrockKnowledgeAdapter 单元测试。"""

from unittest.mock import MagicMock

import pytest

from src.modules.knowledge.infrastructure.external.bedrock_knowledge_adapter import BedrockKnowledgeAdapter
from src.modules.knowledge.infrastructure.external.knowledge_config_builder import BedrockKBConfig
from src.shared.domain.exceptions import DomainError


def _make_config() -> BedrockKBConfig:
    """创建测试用 KB 配置。"""
    return BedrockKBConfig(
        role_arn="arn:aws:iam::123456789:role/kb-role",
        embedding_model_arn="arn:aws:bedrock:us-east-1::foundation-model/amazon.titan-embed-text-v1",
        collection_arn="arn:aws:aoss:us-east-1:123456789:collection/abc123",
    )


@pytest.mark.unit
class TestBedrockKnowledgeAdapter:
    @pytest.mark.asyncio
    async def test_create_knowledge_base_with_config(self) -> None:
        """配置完整时，create_knowledge_base 传递正确参数到 Bedrock API。"""
        agent_client = MagicMock()
        agent_client.create_knowledge_base.return_value = {
            "knowledgeBase": {"knowledgeBaseId": "kb-123"},
        }
        cfg = _make_config()
        adapter = BedrockKnowledgeAdapter(agent_client, MagicMock(), kb_config=cfg)
        result = await adapter.create_knowledge_base("test", s3_bucket="b", s3_prefix="p/")

        assert result.bedrock_kb_id == "kb-123"
        assert result.s3_prefix == "p/"

        # 验证 Bedrock API 调用参数
        call_kwargs = agent_client.create_knowledge_base.call_args
        assert call_kwargs.kwargs["roleArn"] == cfg.role_arn
        kb_cfg = call_kwargs.kwargs["knowledgeBaseConfiguration"]
        assert kb_cfg["vectorKnowledgeBaseConfiguration"]["embeddingModelArn"] == cfg.embedding_model_arn
        storage_cfg = call_kwargs.kwargs["storageConfiguration"]
        oss_cfg = storage_cfg["opensearchServerlessConfiguration"]
        assert oss_cfg["collectionArn"] == cfg.collection_arn
        assert oss_cfg["vectorIndexName"] == "kb-test"

    @pytest.mark.asyncio
    async def test_create_knowledge_base_without_config_raises(self) -> None:
        """未配置 kb_config 时，create_knowledge_base 抛出 DomainError。"""
        adapter = BedrockKnowledgeAdapter(MagicMock(), MagicMock())
        with pytest.raises(DomainError, match="配置缺失"):
            await adapter.create_knowledge_base("test", s3_bucket="b", s3_prefix="p/")

    @pytest.mark.asyncio
    async def test_create_knowledge_base_backward_compatible(self) -> None:
        """不传 kb_config 时构造不报错，只在调用 create 时报错。"""
        adapter = BedrockKnowledgeAdapter(MagicMock(), MagicMock())
        # 构造成功
        assert adapter._kb_config is None

    @pytest.mark.asyncio
    async def test_delete_knowledge_base(self) -> None:
        agent_client = MagicMock()
        adapter = BedrockKnowledgeAdapter(agent_client, MagicMock())
        await adapter.delete_knowledge_base("kb-123")
        agent_client.delete_knowledge_base.assert_called_once_with(knowledgeBaseId="kb-123")

    @pytest.mark.asyncio
    async def test_start_sync(self) -> None:
        agent_client = MagicMock()
        agent_client.start_ingestion_job.return_value = {
            "ingestionJob": {"ingestionJobId": "job-1", "status": "IN_PROGRESS"},
        }
        adapter = BedrockKnowledgeAdapter(agent_client, MagicMock())
        result = await adapter.start_sync("kb-123")
        assert result.ingestion_job_id == "job-1"

    @pytest.mark.asyncio
    async def test_retrieve(self) -> None:
        runtime_client = MagicMock()
        runtime_client.retrieve.return_value = {
            "retrievalResults": [
                {"content": {"text": "answer"}, "score": 0.95, "location": {"s3Location": {"uri": "s3://b/k"}}},
            ],
        }
        adapter = BedrockKnowledgeAdapter(MagicMock(), runtime_client)
        results = await adapter.retrieve("kb-123", "query", top_k=3)
        assert len(results) == 1
        assert results[0].content == "answer"
        assert results[0].score == 0.95


@pytest.mark.unit
class TestBedrockKBConfig:
    """BedrockKBConfig 数据类测试。"""

    def test_config_frozen(self) -> None:
        """BedrockKBConfig 应为不可变。"""
        cfg = _make_config()
        with pytest.raises(AttributeError):
            cfg.role_arn = "new-arn"  # type: ignore[misc]

    def test_config_fields(self) -> None:
        """BedrockKBConfig 字段正确赋值。"""
        cfg = _make_config()
        assert cfg.role_arn.startswith("arn:aws:iam")
        assert cfg.embedding_model_arn.startswith("arn:aws:bedrock")
        assert cfg.collection_arn.startswith("arn:aws:aoss")
