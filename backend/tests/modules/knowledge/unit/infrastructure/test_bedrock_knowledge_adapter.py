"""BedrockKnowledgeAdapter 单元测试。"""

import pytest
from unittest.mock import MagicMock

from src.modules.knowledge.infrastructure.external.bedrock_knowledge_adapter import BedrockKnowledgeAdapter


@pytest.mark.unit
class TestBedrockKnowledgeAdapter:
    @pytest.mark.asyncio
    async def test_create_knowledge_base(self) -> None:
        agent_client = MagicMock()
        agent_client.create_knowledge_base.return_value = {
            "knowledgeBase": {"knowledgeBaseId": "kb-123"},
        }
        adapter = BedrockKnowledgeAdapter(agent_client, MagicMock())
        result = await adapter.create_knowledge_base("test", s3_bucket="b", s3_prefix="p/")
        assert result.bedrock_kb_id == "kb-123"

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
